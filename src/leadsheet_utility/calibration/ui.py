"""Interactive 4-point calibration UI.

`CalibrationUI` owns the four marker positions, handles its own pygame
events, and renders the marker overlay + a key-outline preview through the
current homography. The host (main app or preview script) is responsible
only for routing pygame events and calling :meth:`render` once per frame.

Five-phase workflow (logical order):

1. RANGE_EDIT — define the projector's physical reach (FULL range only).
   The user moves the low/high endpoints to match the leftmost and
   rightmost keys the projector light can actually hit. A solid green pad
   fills the FULL range on the projector so this is visually verifiable.
2. MAIN — drag the 4 corner markers and tune global black-key ratios so
   the rendered keyboard lines up with the now-known range.
3. BLACK_KEY_TUNE — step through each black key with Tab and nudge its
   canonical position to fix per-key drift the homography can't cover.
4. BAND_EDIT — set the 1-OCT and 2-OCT exercise bands within the FULL
   range. Done after homography is aligned so the user can see the band
   highlighted on the real keys. Bands are clipped to the FULL range.
5. AUDIO_DELAY — tune the audio/projection offset in milliseconds.

Enter advances RANGE_EDIT → MAIN → BLACK_KEY_TUNE → BAND_EDIT →
AUDIO_DELAY → confirmed. Escape cancels from any phase.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

import cv2
import numpy as np
import pygame

from leadsheet_utility.calibration.models import (
    DEFAULT_ONE_OCTAVE_HIGH,
    DEFAULT_ONE_OCTAVE_LOW,
    DEFAULT_TWO_OCTAVE_HIGH,
    DEFAULT_TWO_OCTAVE_LOW,
    MARKER_LABELS,
    NUM_MARKERS,
    Calibration,
    default_markers,
)
from leadsheet_utility.exercises.free import RangeMode
from leadsheet_utility.projection.layout import (
    DEFAULT_BLACK_HEIGHT_RATIO,
    DEFAULT_BLACK_WIDTH_RATIO,
    MIDI_DEFAULT_HIGH,
    MIDI_DEFAULT_LOW,
    MIDI_HIGH,
    MIDI_LOW,
    build_keyboard_layout,
    is_black_key,
)


class CalibrationPhase(Enum):
    RANGE_EDIT = auto()      # FULL range (projector reach)
    MAIN = auto()             # marker drag + black-key ratios
    BLACK_KEY_TUNE = auto()   # per-key offsets
    BAND_EDIT = auto()        # 1-OCT / 2-OCT exercise bands
    AUDIO_DELAY = auto()      # audio offset (ms)


class RangeEndpoint(Enum):
    LOW = auto()
    HIGH = auto()


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
_ACTIVE_BLACK_KEY_FILL = (255, 235, 60)  # yellow — highlights the key being tuned
_RANGE_PAD_FILL = (60, 220, 90)  # solid green pad covering the active range
_AUDIO_DELAY_FILL = (60, 160, 220)
_KEY_EDGE_COLOR = (0, 0, 0)
_NUDGE_STEP = 1
_NUDGE_BIG_STEP = 10

# Per-instrument black-key proportion adjustments (live in calibration mode).
_RATIO_STEP = 0.01
_RATIO_BIG_STEP = 0.05
_RATIO_MIN = 0.30
_RATIO_MAX = 1.20

# Audio-delay tuning step (ms).
_AUDIO_DELAY_STEP = 1
_AUDIO_DELAY_BIG_STEP = 10

# Each range needs at least one octave of headroom — the FreeMode runs that
# use a range need a root slot plus an octave above.
_MIN_RANGE_WIDTH_SEMITONES = 12


def _clamp_ratio(v: float) -> float:
    return max(_RATIO_MIN, min(_RATIO_MAX, round(v, 4)))


def _next_white_key(midi: int, direction: int) -> int:
    """Step *one* white key in `direction` (+1 up, -1 down). Skips blacks."""
    m = midi + direction
    while is_black_key(m):
        m += direction
    return m


@dataclass
class CalibrationSnapshot:
    """Read-only view of the live calibration state, for HUD mirroring.

    The fields are deliberately strings/primitives so the HUD doesn't need
    to import pygame or the UI module.
    """

    phase: CalibrationPhase
    # MAIN phase
    active_marker_label: str
    active_marker_idx: int
    marker_count: int
    marker_pos: tuple[float, float]
    black_width_ratio: float
    black_height_ratio: float
    # RANGE_EDIT phase
    active_range_mode: RangeMode
    active_endpoint: RangeEndpoint
    full_range: tuple[int, int]
    one_octave_range: tuple[int, int]
    two_octave_range: tuple[int, int]
    # AUDIO_DELAY phase
    audio_delay_ms: int
    # BLACK_KEY_TUNE phase
    active_black_midi: int | None
    active_black_offset: tuple[float, float]
    black_key_count: int
    active_black_idx: int


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
        black_width_ratio: float = DEFAULT_BLACK_WIDTH_RATIO,
        black_height_ratio: float = DEFAULT_BLACK_HEIGHT_RATIO,
        black_key_offsets: dict[int, tuple[float, float]] | None = None,
        midi_full_low: int = MIDI_DEFAULT_LOW,
        midi_full_high: int = MIDI_DEFAULT_HIGH,
        midi_one_octave_low: int = DEFAULT_ONE_OCTAVE_LOW,
        midi_one_octave_high: int = DEFAULT_ONE_OCTAVE_HIGH,
        midi_two_octave_low: int = DEFAULT_TWO_OCTAVE_LOW,
        midi_two_octave_high: int = DEFAULT_TWO_OCTAVE_HIGH,
        audio_delay_ms: int = 0,
    ) -> None:
        self.canonical_size = canonical_size
        self.projector_size = projector_size
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

        # RANGE_EDIT state: editable MIDI ranges + which endpoint is active.
        self.midi_full_low: int = midi_full_low
        self.midi_full_high: int = midi_full_high
        self.midi_one_octave_low: int = midi_one_octave_low
        self.midi_one_octave_high: int = midi_one_octave_high
        self.midi_two_octave_low: int = midi_two_octave_low
        self.midi_two_octave_high: int = midi_two_octave_high
        self.active_range_mode: RangeMode = RangeMode.FULL
        self.active_endpoint: RangeEndpoint = RangeEndpoint.LOW

        # AUDIO_DELAY state.
        self.audio_delay_ms: int = audio_delay_ms

        # BLACK_KEY_TUNE state: per-black-key offsets in canonical pixels.
        # Calibration starts on RANGE_EDIT so the user picks the projector's
        # physical span before placing markers against it.
        self.phase: CalibrationPhase = CalibrationPhase.RANGE_EDIT
        self.black_key_offsets: dict[int, tuple[float, float]] = (
            dict(black_key_offsets) if black_key_offsets else {}
        )
        # MIDI notes of the black keys in the active full range, in playing
        # order. Populated when entering BLACK_KEY_TUNE so we always tune
        # what's actually being projected.
        self._black_key_midis: list[int] = []
        self.active_black_idx: int = 0

    # -- state ------------------------------------------------------------

    @property
    def active(self) -> bool:
        return not (self.confirmed or self.cancelled)

    @property
    def midi_range(self) -> tuple[int, int]:
        """Backward-compatible alias for the full projected range."""
        return (self.midi_full_low, self.midi_full_high)

    def build_calibration(self) -> Calibration:
        return Calibration(
            canonical_size=self.canonical_size,
            projector_size=self.projector_size,
            markers=list(self.markers),
            black_width_ratio=self.black_width_ratio,
            black_height_ratio=self.black_height_ratio,
            black_key_offsets=dict(self.black_key_offsets),
            midi_full_low=self.midi_full_low,
            midi_full_high=self.midi_full_high,
            midi_one_octave_low=self.midi_one_octave_low,
            midi_one_octave_high=self.midi_one_octave_high,
            midi_two_octave_low=self.midi_two_octave_low,
            midi_two_octave_high=self.midi_two_octave_high,
            audio_delay_ms=self.audio_delay_ms,
        )

    def homography(self) -> np.ndarray:
        return self.build_calibration().homography()

    def snapshot(self) -> CalibrationSnapshot:
        """Read-only view of the current state for HUD mirroring."""
        active_black: int | None = None
        active_off: tuple[float, float] = (0.0, 0.0)
        if (
            self.phase is CalibrationPhase.BLACK_KEY_TUNE
            and self._black_key_midis
        ):
            active_black = self._black_key_midis[self.active_black_idx]
            active_off = self.black_key_offsets.get(active_black, (0.0, 0.0))
        return CalibrationSnapshot(
            phase=self.phase,
            active_marker_label=MARKER_LABELS[self.active_idx],
            active_marker_idx=self.active_idx,
            marker_count=NUM_MARKERS,
            marker_pos=self.markers[self.active_idx],
            black_width_ratio=self.black_width_ratio,
            black_height_ratio=self.black_height_ratio,
            active_range_mode=self.active_range_mode,
            active_endpoint=self.active_endpoint,
            full_range=(self.midi_full_low, self.midi_full_high),
            one_octave_range=(self.midi_one_octave_low, self.midi_one_octave_high),
            two_octave_range=(self.midi_two_octave_low, self.midi_two_octave_high),
            audio_delay_ms=self.audio_delay_ms,
            active_black_midi=active_black,
            active_black_offset=active_off,
            black_key_count=len(self._black_key_midis),
            active_black_idx=self.active_black_idx,
        )

    # -- event handling ---------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        """Route a single pygame event into the UI."""
        if not self.active:
            return

        if self.phase is CalibrationPhase.RANGE_EDIT:
            self._handle_event_range_edit(event)
        elif self.phase is CalibrationPhase.MAIN:
            self._handle_event_main(event)
        elif self.phase is CalibrationPhase.BLACK_KEY_TUNE:
            self._handle_event_tune(event)
        elif self.phase is CalibrationPhase.BAND_EDIT:
            self._handle_event_band_edit(event)
        else:
            self._handle_event_audio_delay(event)

    # -- phase: RANGE_EDIT (FULL range only) ------------------------------

    # Band cycle for BAND_EDIT phase — FULL is *not* in here because the
    # full range is locked once we leave step 1.
    _BAND_CYCLE: tuple[RangeMode, ...] = (
        RangeMode.TWO_OCTAVE,
        RangeMode.ONE_OCTAVE,
    )

    def _handle_event_range_edit(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        key = event.key
        mods = event.mod
        big = bool(mods & pygame.KMOD_SHIFT)

        # RANGE_EDIT pins active_range_mode to FULL; ignore B here.
        self.active_range_mode = RangeMode.FULL

        if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.phase = CalibrationPhase.MAIN
        elif key == pygame.K_ESCAPE:
            self.cancelled = True
        elif key == pygame.K_TAB:
            self.active_endpoint = (
                RangeEndpoint.HIGH
                if self.active_endpoint is RangeEndpoint.LOW
                else RangeEndpoint.LOW
            )
        elif key == pygame.K_LEFT:
            self._nudge_active_endpoint(-1, big)
        elif key == pygame.K_RIGHT:
            self._nudge_active_endpoint(+1, big)
        elif key == pygame.K_r:
            self._reset_active_range()

    # -- phase: BAND_EDIT (1-OCT / 2-OCT exercise bands) ------------------

    def _handle_event_band_edit(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        key = event.key
        mods = event.mod
        big = bool(mods & pygame.KMOD_SHIFT)

        if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.phase = CalibrationPhase.AUDIO_DELAY
        elif key == pygame.K_ESCAPE:
            self.cancelled = True
        elif key == pygame.K_b:
            idx = self._BAND_CYCLE.index(self.active_range_mode)
            self.active_range_mode = self._BAND_CYCLE[
                (idx + 1) % len(self._BAND_CYCLE)
            ]
        elif key == pygame.K_TAB:
            self.active_endpoint = (
                RangeEndpoint.HIGH
                if self.active_endpoint is RangeEndpoint.LOW
                else RangeEndpoint.LOW
            )
        elif key == pygame.K_LEFT:
            self._nudge_active_endpoint(-1, big)
        elif key == pygame.K_RIGHT:
            self._nudge_active_endpoint(+1, big)
        elif key == pygame.K_r:
            self._reset_active_range()

    def _enter_band_edit(self) -> None:
        """Switch to band editing. Pin active range to a band (not FULL),
        and clip existing bands to the FULL range so the user can't have
        bands extending outside the projector's reach."""
        if self.active_range_mode is RangeMode.FULL:
            self.active_range_mode = RangeMode.TWO_OCTAVE
        self.active_endpoint = RangeEndpoint.LOW
        self._clip_bands_to_full_range()
        self.phase = CalibrationPhase.BAND_EDIT

    def _clip_bands_to_full_range(self) -> None:
        """Clip 1-OCT and 2-OCT band endpoints into [full_low, full_high].

        Honours the minimum-width invariant. If a band would collapse, it
        falls back to a 12-semitone window at the full range's low end.
        """
        full_low, full_high = self.midi_full_low, self.midi_full_high
        for mode in (RangeMode.ONE_OCTAVE, RangeMode.TWO_OCTAVE):
            low, high = self._get_range(mode)
            low = max(full_low, low)
            high = min(full_high, high)
            # Snap to white keys (FULL endpoints are already white, so
            # clamping a band endpoint to them is safe; otherwise step out).
            while is_black_key(low) and low < high:
                low += 1
            while is_black_key(high) and high > low:
                high -= 1
            if high - low < _MIN_RANGE_WIDTH_SEMITONES:
                low = full_low
                high = min(full_high, full_low + _MIN_RANGE_WIDTH_SEMITONES)
                while is_black_key(high) and high > low:
                    high -= 1
            self._set_range(mode, low, high)

    def _get_range(self, mode: RangeMode) -> tuple[int, int]:
        if mode is RangeMode.FULL:
            return (self.midi_full_low, self.midi_full_high)
        if mode is RangeMode.TWO_OCTAVE:
            return (self.midi_two_octave_low, self.midi_two_octave_high)
        return (self.midi_one_octave_low, self.midi_one_octave_high)

    def _set_range(self, mode: RangeMode, low: int, high: int) -> None:
        if mode is RangeMode.FULL:
            self.midi_full_low, self.midi_full_high = low, high
        elif mode is RangeMode.TWO_OCTAVE:
            self.midi_two_octave_low, self.midi_two_octave_high = low, high
        else:
            self.midi_one_octave_low, self.midi_one_octave_high = low, high

    def _nudge_active_endpoint(self, direction: int, big: bool) -> None:
        """Step the active endpoint of the active range by one white key
        (or one octave with Shift). Honours the white-key constraint, the
        minimum range width, and (for 1-OCT/2-OCT bands) the FULL range
        as an upper bound."""
        low, high = self._get_range(self.active_range_mode)

        # Bands are bounded by the FULL range (set in phase 1); FULL itself
        # is bounded by the keyboard limits (MIDI_LOW..MIDI_HIGH).
        if self.active_range_mode is RangeMode.FULL:
            bound_low, bound_high = MIDI_LOW, MIDI_HIGH
        else:
            bound_low, bound_high = self.midi_full_low, self.midi_full_high

        if self.active_endpoint is RangeEndpoint.LOW:
            new = low + 12 * direction if big else _next_white_key(low, direction)
            new = max(bound_low, min(bound_high, new))
            if is_black_key(new):
                new = _next_white_key(new, direction)
            if new < bound_low or new > bound_high:
                return
            if high - new < _MIN_RANGE_WIDTH_SEMITONES:
                return
            self._set_range(self.active_range_mode, new, high)
        else:
            new = high + 12 * direction if big else _next_white_key(high, direction)
            new = max(bound_low, min(bound_high, new))
            if is_black_key(new):
                new = _next_white_key(new, direction)
            if new < bound_low or new > bound_high:
                return
            if new - low < _MIN_RANGE_WIDTH_SEMITONES:
                return
            self._set_range(self.active_range_mode, low, new)

    def _reset_active_range(self) -> None:
        defaults = {
            RangeMode.FULL: (MIDI_DEFAULT_LOW, MIDI_DEFAULT_HIGH),
            RangeMode.TWO_OCTAVE: (DEFAULT_TWO_OCTAVE_LOW, DEFAULT_TWO_OCTAVE_HIGH),
            RangeMode.ONE_OCTAVE: (DEFAULT_ONE_OCTAVE_LOW, DEFAULT_ONE_OCTAVE_HIGH),
        }
        low, high = defaults[self.active_range_mode]
        self._set_range(self.active_range_mode, low, high)

    # -- phase: MAIN ------------------------------------------------------

    def _handle_event_main(self, event: pygame.event.Event) -> None:
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
            self._handle_key_main(event)

    def _handle_key_main(self, event: pygame.event.Event) -> None:
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
            self._enter_black_key_tune()
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

    # -- phase: BLACK_KEY_TUNE -------------------------------------------

    def _enter_black_key_tune(self) -> None:
        """Capture the set of black keys in the active full range and switch phase."""
        midi_low, midi_high = self.midi_full_low, self.midi_full_high
        self._black_key_midis = [
            m for m in range(midi_low, midi_high + 1) if is_black_key(m)
        ]
        if not self._black_key_midis:
            # Degenerate range — skip per-key tuning, go straight to bands.
            self._enter_band_edit()
            return
        self.active_black_idx = 0
        self.phase = CalibrationPhase.BLACK_KEY_TUNE

    def _handle_event_tune(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            self._handle_key_tune(event)

    def _handle_key_tune(self, event: pygame.event.Event) -> None:
        key = event.key
        mods = event.mod
        step = _NUDGE_BIG_STEP if mods & pygame.KMOD_SHIFT else _NUDGE_STEP

        if key == pygame.K_TAB:
            direction = -1 if mods & pygame.KMOD_SHIFT else 1
            self.active_black_idx = (
                self.active_black_idx + direction
            ) % len(self._black_key_midis)
        elif key == pygame.K_LEFT:
            self._nudge_black(-step, 0)
        elif key == pygame.K_RIGHT:
            self._nudge_black(step, 0)
        elif key == pygame.K_UP:
            self._nudge_black(0, -step)
        elif key == pygame.K_DOWN:
            self._nudge_black(0, step)
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self._enter_band_edit()
        elif key == pygame.K_ESCAPE:
            self.cancelled = True
        elif key == pygame.K_r:
            self.black_key_offsets = {}

    # -- phase: AUDIO_DELAY ----------------------------------------------

    def _handle_event_audio_delay(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        key = event.key
        mods = event.mod
        big = bool(mods & pygame.KMOD_SHIFT)
        step = _AUDIO_DELAY_BIG_STEP if big else _AUDIO_DELAY_STEP

        if key == pygame.K_UP:
            self.audio_delay_ms = int(self.audio_delay_ms + step)
        elif key == pygame.K_DOWN:
            self.audio_delay_ms = int(self.audio_delay_ms - step)
        elif key == pygame.K_r:
            self.audio_delay_ms = 0
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.confirmed = True
        elif key == pygame.K_ESCAPE:
            self.cancelled = True

    # -- shared helpers ---------------------------------------------------

    def _nudge_black(self, dx: int, dy: int) -> None:
        midi = self._black_key_midis[self.active_black_idx]
        ox, oy = self.black_key_offsets.get(midi, (0.0, 0.0))
        self.black_key_offsets[midi] = (ox + dx, oy + dy)

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
        if which == "width":
            self.black_width_ratio = _clamp_ratio(self.black_width_ratio + delta)
        elif which == "height":
            self.black_height_ratio = _clamp_ratio(self.black_height_ratio + delta)

    # -- rendering --------------------------------------------------------

    def render(self, surface: pygame.Surface, font: pygame.font.Font | None = None) -> None:
        """Draw the calibration overlay onto `surface`.

        Each phase renders a phase-appropriate scene; the HUD text strip
        below is rendered last (when a font is supplied).
        """
        surface.fill((0, 0, 0))
        if self.phase is CalibrationPhase.RANGE_EDIT:
            self._render_range_edit(surface)
        elif self.phase is CalibrationPhase.AUDIO_DELAY:
            self._render_audio_delay(surface)
        elif self.phase is CalibrationPhase.BAND_EDIT:
            self._render_band_edit(surface)
        else:
            self._render_key_outlines(surface)
        if self.phase is CalibrationPhase.MAIN:
            self._render_markers(surface)
        if font is not None:
            self._render_hud_text(surface, font)

    def _render_key_outlines(self, surface: pygame.Surface) -> None:
        """Warp the canonical key rectangles through H and draw them as filled
        polygons — green for white-key zones, pink for black-key zones — so
        the projected shape is visible against the piano during alignment.
        In BLACK_KEY_TUNE phase the currently selected black key is drawn
        yellow so the user can see which key the arrow keys are nudging."""
        layout = build_keyboard_layout(
            *self.canonical_size,
            midi_low=self.midi_full_low,
            midi_high=self.midi_full_high,
            black_width_ratio=self.black_width_ratio,
            black_height_ratio=self.black_height_ratio,
            black_key_offsets=self.black_key_offsets,
        )
        H = self.homography()

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

        active_midi: int | None = None
        if (
            self.phase is CalibrationPhase.BLACK_KEY_TUNE
            and self._black_key_midis
        ):
            active_midi = self._black_key_midis[self.active_black_idx]

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
            fill = _ACTIVE_BLACK_KEY_FILL if key.midi_note == active_midi else _BLACK_KEY_FILL
            pygame.draw.polygon(surface, fill, poly_i)
            pygame.draw.polygon(surface, _KEY_EDGE_COLOR, poly_i, width=1)

        outer = [(int(round(x)), int(round(y))) for x, y in self.markers]
        pygame.draw.polygon(surface, _OUTLINE_COLOR, outer, width=2)

    def _render_range_edit(self, surface: pygame.Surface) -> None:
        """Fill the active range with a solid green pad — used in RANGE_EDIT
        so the user can confirm the lit area matches the physical keys.

        The FULL range outlines the projector's reach; the *active* range
        fills as a bright pad. When the active range is FULL the two
        coincide. Sub-ranges (1-OCT / 2-OCT) appear as a brighter slice
        inside the FULL outline.
        """
        full_low, full_high = self.midi_full_low, self.midi_full_high
        active_low, active_high = self._get_range(self.active_range_mode)
        active_low = max(active_low, full_low)
        active_high = min(active_high, full_high)

        cw, ch = self.canonical_size
        layout = build_keyboard_layout(
            *self.canonical_size,
            midi_low=full_low,
            midi_high=full_high,
            black_width_ratio=self.black_width_ratio,
            black_height_ratio=self.black_height_ratio,
            black_key_offsets=self.black_key_offsets,
        )
        H = self.homography()

        # Solid pad over the active range.
        if active_high > active_low:
            left = cw
            right = 0
            for k in layout:
                if active_low <= k.midi_note <= active_high:
                    left = min(left, k.x)
                    right = max(right, k.x + k.width)
            if right > left:
                quad = np.array(
                    [[left, 0], [right, 0], [right, ch], [left, ch]],
                    dtype=np.float32,
                ).reshape(-1, 1, 2)
                warped = cv2.perspectiveTransform(quad, H).reshape(-1, 2)
                poly = [(int(round(x)), int(round(y))) for x, y in warped]
                pygame.draw.polygon(surface, _RANGE_PAD_FILL, poly)

        # FULL-range outline frames the whole projector reach.
        full_quad = np.array(
            [[0, 0], [cw, 0], [cw, ch], [0, ch]],
            dtype=np.float32,
        ).reshape(-1, 1, 2)
        full_warped = cv2.perspectiveTransform(full_quad, H).reshape(-1, 2)
        full_poly = [(int(round(x)), int(round(y))) for x, y in full_warped]
        pygame.draw.polygon(surface, _OUTLINE_COLOR, full_poly, width=2)

        self._render_endpoint_markers(surface, layout, H, active_low, active_high)

    def _render_endpoint_markers(
        self,
        surface: pygame.Surface,
        layout: list,
        H: np.ndarray,
        active_low: int,
        active_high: int,
    ) -> None:
        """Draw small indicator triangles above the active range's endpoints
        so the user can see which endpoint they're currently editing."""
        ch = self.canonical_size[1]
        low_rect = next((k for k in layout if k.midi_note == active_low), None)
        high_rect = next((k for k in layout if k.midi_note == active_high), None)
        if low_rect is None or high_rect is None:
            return

        for endpoint, rect in (
            (RangeEndpoint.LOW, low_rect),
            (RangeEndpoint.HIGH, high_rect),
        ):
            cx = rect.x + rect.width / 2
            quad = np.array([[cx, 0], [cx, ch]], dtype=np.float32).reshape(-1, 1, 2)
            warped = cv2.perspectiveTransform(quad, H).reshape(-1, 2)
            tx, ty = warped[0]
            color = (
                _ACTIVE_BLACK_KEY_FILL
                if endpoint is self.active_endpoint
                else _OUTLINE_COLOR
            )
            pts = [
                (int(round(tx)), int(round(ty))),
                (int(round(tx - 12)), int(round(ty - 22))),
                (int(round(tx + 12)), int(round(ty - 22))),
            ]
            pygame.draw.polygon(surface, color, pts)
            pygame.draw.polygon(surface, (0, 0, 0), pts, width=2)

    def _render_audio_delay(self, surface: pygame.Surface) -> None:
        """Plain blue background while tuning audio delay — the value itself
        is read off the HUD, since this phase isn't about visual alignment."""
        surface.fill(_AUDIO_DELAY_FILL)

    def _render_band_edit(self, surface: pygame.Surface) -> None:
        """Show the (now calibrated) keyboard, with the active band's keys
        drawn brightly and keys outside the band dimmed. Lets the user see
        the band relative to the real piano keys before committing to it.
        """
        layout = build_keyboard_layout(
            *self.canonical_size,
            midi_low=self.midi_full_low,
            midi_high=self.midi_full_high,
            black_width_ratio=self.black_width_ratio,
            black_height_ratio=self.black_height_ratio,
            black_key_offsets=self.black_key_offsets,
        )
        H = self.homography()
        active_low, active_high = self._get_range(self.active_range_mode)

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

        dim_white = (40, 90, 50)
        dim_black = (90, 40, 70)

        for key, poly in zip(layout, warped):
            if key.is_black:
                continue
            poly_i = [(int(round(x)), int(round(y))) for x, y in poly]
            in_band = active_low <= key.midi_note <= active_high
            pygame.draw.polygon(
                surface, _WHITE_KEY_FILL if in_band else dim_white, poly_i,
            )
            pygame.draw.polygon(surface, _KEY_EDGE_COLOR, poly_i, width=1)

        for key, poly in zip(layout, warped):
            if not key.is_black:
                continue
            poly_i = [(int(round(x)), int(round(y))) for x, y in poly]
            in_band = active_low <= key.midi_note <= active_high
            pygame.draw.polygon(
                surface, _BLACK_KEY_FILL if in_band else dim_black, poly_i,
            )
            pygame.draw.polygon(surface, _KEY_EDGE_COLOR, poly_i, width=1)

        self._render_endpoint_markers(surface, layout, H, active_low, active_high)

    def _render_markers(self, surface: pygame.Surface) -> None:
        for i, (mx, my) in enumerate(self.markers):
            x, y = int(round(mx)), int(round(my))
            color = _MARKER_COLORS["active"] if i == self.active_idx else _MARKER_COLORS["idle"]
            pygame.draw.circle(surface, _MARKER_COLORS["ring"], (x, y), _MARKER_RADIUS + 3)
            pygame.draw.circle(surface, color, (x, y), _MARKER_RADIUS)
            pygame.draw.line(surface, (0, 0, 0), (x - _MARKER_RADIUS, y), (x + _MARKER_RADIUS, y), 1)
            pygame.draw.line(surface, (0, 0, 0), (x, y - _MARKER_RADIUS), (x, y + _MARKER_RADIUS), 1)

    def _render_hud_text(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        if self.phase is CalibrationPhase.RANGE_EDIT:
            low, high = self.midi_full_low, self.midi_full_high
            ep_label = "LOW" if self.active_endpoint is RangeEndpoint.LOW else "HIGH"
            lines = [
                "Phase 1/5 : FULL range (projector's physical reach)",
                f"Active endpoint: {ep_label}   low MIDI {low}   high MIDI {high}",
                "Tab: switch low/high    Left/Right: nudge (Shift = octave)",
                "R: reset to defaults   Enter: next (markers)   Esc: cancel",
            ]
        elif self.phase is CalibrationPhase.MAIN:
            lines = [
                f"Phase 2/5 : active marker: {MARKER_LABELS[self.active_idx]} ({self.active_idx + 1}/{NUM_MARKERS})",
                "Drag markers, or use arrows (Shift = x10) to nudge. Tab cycles, 1-4 jumps.",
                f"Black-key proportions:  width = {self.black_width_ratio:.2f}  height = {self.black_height_ratio:.2f}",
                "Q / W  narrower / wider    A / S  shorter / longer    (Shift = x5)",
                "R: reset markers   Enter: next (per-key tuning)   Esc: cancel",
            ]
        elif self.phase is CalibrationPhase.BLACK_KEY_TUNE:
            midi = self._black_key_midis[self.active_black_idx]
            ox, oy = self.black_key_offsets.get(midi, (0.0, 0.0))
            lines = [
                f"Phase 3/5 : tuning black key {self.active_black_idx + 1}/{len(self._black_key_midis)} (MIDI {midi})",
                f"Offset: dx = {ox:+.0f}px  dy = {oy:+.0f}px",
                "Arrows: nudge active key (Shift = x10)   Tab / Shift-Tab: prev / next key",
                "R: reset all per-key offsets   Enter: next (exercise bands)   Esc: cancel",
            ]
        elif self.phase is CalibrationPhase.BAND_EDIT:
            low, high = self._get_range(self.active_range_mode)
            band_label = {
                RangeMode.TWO_OCTAVE: "2-OCT band",
                RangeMode.ONE_OCTAVE: "1-OCT band",
                RangeMode.FULL: "(invalid)",
            }[self.active_range_mode]
            ep_label = "LOW" if self.active_endpoint is RangeEndpoint.LOW else "HIGH"
            lines = [
                f"Phase 4/5 : exercise {band_label}   "
                f"(clipped to FULL {self.midi_full_low}-{self.midi_full_high})",
                f"Active endpoint: {ep_label}   low MIDI {low}   high MIDI {high}",
                "B: switch 1-OCT / 2-OCT    Tab: low/high    Left/Right: nudge (Shift = octave)",
                "R: reset active band   Enter: next (audio delay)   Esc: cancel",
            ]
        else:  # AUDIO_DELAY
            lines = [
                "Phase 5/5 : audio delay tuning",
                f"Audio delay: {self.audio_delay_ms:+d} ms",
                "Up / Down: +/- 1 ms (Shift = +/- 10 ms)   R: reset to 0",
                "Enter: confirm and save   Esc: cancel",
            ]
        x, y = 20, 20
        for line in lines:
            text = font.render(line, True, (220, 220, 220))
            shadow = font.render(line, True, (0, 0, 0))
            surface.blit(shadow, (x + 1, y + 1))
            surface.blit(text, (x, y))
            y += text.get_height() + 4
