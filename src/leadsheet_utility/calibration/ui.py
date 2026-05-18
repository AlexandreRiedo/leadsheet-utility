"""Interactive 4-point calibration UI.

`CalibrationUI` owns the four marker positions, handles its own pygame
events, and renders the marker overlay + a key-outline preview through the
current homography. The host (main app or preview script) is responsible
only for routing pygame events and calling :meth:`render` once per frame.
"""

from __future__ import annotations

import cv2
import numpy as np
import pygame

from leadsheet_utility.calibration.models import (
    MARKER_LABELS,
    NUM_MARKERS,
    Calibration,
    default_markers,
)
from leadsheet_utility.projection.layout import (
    DEFAULT_BLACK_HEIGHT_RATIO,
    DEFAULT_BLACK_WIDTH_RATIO,
    MIDI_DEFAULT_HIGH,
    MIDI_DEFAULT_LOW,
    build_keyboard_layout,
)

# Visual constants.
_MARKER_RADIUS = 14
_MARKER_HIT_RADIUS = 22
_MARKER_COLORS = {
    "idle": (200, 200, 0),
    "active": (255, 255, 255),
    "ring": (0, 0, 0),
}
_OUTLINE_COLOR = (80, 200, 255)
_WHITE_KEY_FILL = (60, 220, 90)  # green
_BLACK_KEY_FILL = (255, 90, 180)  # pink
_KEY_EDGE_COLOR = (0, 0, 0)
_NUDGE_STEP = 1
_NUDGE_BIG_STEP = 10

# Per-instrument black-key proportion adjustments (live in calibration mode).
_RATIO_STEP = 0.01
_RATIO_BIG_STEP = 0.05
_RATIO_MIN = 0.30
_RATIO_MAX = 1.20


def _clamp_ratio(v: float) -> float:
    return max(_RATIO_MIN, min(_RATIO_MAX, round(v, 4)))


class CalibrationUI:
    """Stateful 4-point calibration overlay.

    State machine: the UI is `active` from construction until the user
    confirms (Enter) or cancels (Escape). `confirmed` and `cancelled` flags
    flip at that point. The host should stop routing events to the UI once
    it becomes inactive.
    """

    def __init__(
        self,
        canonical_size: tuple[int, int],
        projector_size: tuple[int, int],
        initial_markers: list[tuple[float, float]] | None = None,
        midi_range: tuple[int, int] = (MIDI_DEFAULT_LOW, MIDI_DEFAULT_HIGH),
        black_width_ratio: float = DEFAULT_BLACK_WIDTH_RATIO,
        black_height_ratio: float = DEFAULT_BLACK_HEIGHT_RATIO,
    ) -> None:
        self.canonical_size = canonical_size
        self.projector_size = projector_size
        self.midi_range = midi_range
        self.markers: list[tuple[float, float]] = list(
            initial_markers or default_markers(projector_size)
        )
        if len(self.markers) != NUM_MARKERS:
            raise ValueError(f"need {NUM_MARKERS} initial markers")
        self.active_idx: int = 0
        self._dragging: bool = False
        self.confirmed: bool = False
        self.cancelled: bool = False
        self.black_width_ratio: float = black_width_ratio
        self.black_height_ratio: float = black_height_ratio

    # -- state ------------------------------------------------------------

    @property
    def active(self) -> bool:
        return not (self.confirmed or self.cancelled)

    def build_calibration(self) -> Calibration:
        return Calibration(
            canonical_size=self.canonical_size,
            projector_size=self.projector_size,
            markers=list(self.markers),
            black_width_ratio=self.black_width_ratio,
            black_height_ratio=self.black_height_ratio,
        )

    def homography(self) -> np.ndarray:
        return self.build_calibration().homography()

    # -- event handling ---------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        """Route a single pygame event into the UI."""
        if not self.active:
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            idx = self._marker_at(event.pos)
            if idx is not None:
                self.active_idx = idx
                self._dragging = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging = False
        elif event.type == pygame.MOUSEMOTION and self._dragging:
            self._set_marker(self.active_idx, event.pos)
        elif event.type == pygame.KEYDOWN:
            self._handle_key(event)

    def _handle_key(self, event: pygame.event.Event) -> None:
        key = event.key
        mods = event.mod
        step = _NUDGE_BIG_STEP if mods & pygame.KMOD_SHIFT else _NUDGE_STEP

        if key == pygame.K_TAB:
            direction = -1 if mods & pygame.KMOD_SHIFT else 1
            self.active_idx = (self.active_idx + direction) % NUM_MARKERS
        elif key == pygame.K_LEFT:
            self._nudge(-step, 0)
        elif key == pygame.K_RIGHT:
            self._nudge(step, 0)
        elif key == pygame.K_UP:
            self._nudge(0, -step)
        elif key == pygame.K_DOWN:
            self._nudge(0, step)
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.confirmed = True
        elif key == pygame.K_ESCAPE:
            self.cancelled = True
        elif key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
            self.active_idx = key - pygame.K_1
        elif key == pygame.K_r:
            self.markers = default_markers(self.projector_size)
            self.active_idx = 0
        elif key in (pygame.K_q, pygame.K_w):
            sign = 1 if key == pygame.K_w else -1
            self._adjust_ratio("width", sign * (_RATIO_BIG_STEP if mods & pygame.KMOD_SHIFT else _RATIO_STEP))
        elif key in (pygame.K_a, pygame.K_s):
            sign = 1 if key == pygame.K_s else -1
            self._adjust_ratio("height", sign * (_RATIO_BIG_STEP if mods & pygame.KMOD_SHIFT else _RATIO_STEP))

    def _marker_at(self, pos: tuple[int, int]) -> int | None:
        x, y = pos
        for i, (mx, my) in enumerate(self.markers):
            if (mx - x) ** 2 + (my - y) ** 2 <= _MARKER_HIT_RADIUS ** 2:
                return i
        return None

    def _set_marker(self, idx: int, pos: tuple[float, float]) -> None:
        pw, ph = self.projector_size
        x = max(0.0, min(float(pos[0]), float(pw - 1)))
        y = max(0.0, min(float(pos[1]), float(ph - 1)))
        self.markers[idx] = (x, y)

    def _nudge(self, dx: int, dy: int) -> None:
        mx, my = self.markers[self.active_idx]
        self._set_marker(self.active_idx, (mx + dx, my + dy))

    def _adjust_ratio(self, which: str, delta: float) -> None:
        """Adjust the black-key width or height ratio, clamped to a sane range."""
        if which == "width":
            self.black_width_ratio = _clamp_ratio(self.black_width_ratio + delta)
        elif which == "height":
            self.black_height_ratio = _clamp_ratio(self.black_height_ratio + delta)

    # -- rendering --------------------------------------------------------

    def render(self, surface: pygame.Surface, font: pygame.font.Font | None = None) -> None:
        """Draw the calibration overlay onto `surface`.

        Renders, in order: background fill, the key-outline wireframe warped
        through the current homography, the marker handles, and a small HUD
        showing which marker is active and the keybinding cheatsheet.
        """
        surface.fill((0, 0, 0))
        self._render_key_outlines(surface)
        self._render_markers(surface)
        if font is not None:
            self._render_hud_text(surface, font)

    def _render_key_outlines(self, surface: pygame.Surface) -> None:
        """Warp the canonical key rectangles through H and draw them as filled
        polygons — green for white-key zones, pink for black-key zones — so
        the projected shape is visible against the piano during alignment."""
        layout = build_keyboard_layout(
            *self.canonical_size,
            midi_low=self.midi_range[0],
            midi_high=self.midi_range[1],
            black_width_ratio=self.black_width_ratio,
            black_height_ratio=self.black_height_ratio,
        )
        H = self.homography()

        # Project all key corners in one shot for efficiency.
        corners = []
        for k in layout:
            corners.extend([
                (k.x, k.y),
                (k.x + k.width, k.y),
                (k.x + k.width, k.y + k.height),
                (k.x, k.y + k.height),
            ])
        pts = np.array(corners, dtype=np.float32).reshape(-1, 1, 2)
        warped = cv2.perspectiveTransform(pts, H).reshape(-1, 4, 2)

        # Draw whites first, then blacks on top — same z-order as the
        # canonical renderer so the black-key zones overwrite the upper
        # portion of adjacent white keys.
        for key, poly in zip(layout, warped):
            if key.is_black:
                continue
            poly_i = [(int(round(x)), int(round(y))) for x, y in poly]
            pygame.draw.polygon(surface, _WHITE_KEY_FILL, poly_i)
            pygame.draw.polygon(surface, _KEY_EDGE_COLOR, poly_i, width=1)

        for key, poly in zip(layout, warped):
            if not key.is_black:
                continue
            poly_i = [(int(round(x)), int(round(y))) for x, y in poly]
            pygame.draw.polygon(surface, _BLACK_KEY_FILL, poly_i)
            pygame.draw.polygon(surface, _KEY_EDGE_COLOR, poly_i, width=1)

        # Outline the keyboard bounding quad so the overall frame is easy to
        # see while dragging, even before alignment is right.
        outer = [(int(round(x)), int(round(y))) for x, y in self.markers]
        pygame.draw.polygon(surface, _OUTLINE_COLOR, outer, width=2)

    def _render_markers(self, surface: pygame.Surface) -> None:
        for i, (mx, my) in enumerate(self.markers):
            x, y = int(round(mx)), int(round(my))
            color = _MARKER_COLORS["active"] if i == self.active_idx else _MARKER_COLORS["idle"]
            pygame.draw.circle(surface, _MARKER_COLORS["ring"], (x, y), _MARKER_RADIUS + 3)
            pygame.draw.circle(surface, color, (x, y), _MARKER_RADIUS)
            # Crosshair for precision targeting.
            pygame.draw.line(surface, (0, 0, 0), (x - _MARKER_RADIUS, y), (x + _MARKER_RADIUS, y), 1)
            pygame.draw.line(surface, (0, 0, 0), (x, y - _MARKER_RADIUS), (x, y + _MARKER_RADIUS), 1)

    def _render_hud_text(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        lines = [
            f"Calibrating — active marker: {MARKER_LABELS[self.active_idx]} ({self.active_idx + 1}/{NUM_MARKERS})",
            "Drag markers, or use arrows (Shift = x10) to nudge. Tab cycles, 1-4 jumps.",
            f"Black-key proportions:  width = {self.black_width_ratio:.2f}  height = {self.black_height_ratio:.2f}",
            "Q / W  narrower / wider    A / S  shorter / longer    (Shift = x5)",
            "R: reset markers   Enter: confirm   Esc: cancel",
        ]
        x, y = 20, 20
        for line in lines:
            text = font.render(line, True, (220, 220, 220))
            shadow = font.render(line, True, (0, 0, 0))
            surface.blit(shadow, (x + 1, y + 1))
            surface.blit(text, (x, y))
            y += text.get_height() + 4
