"""Application entry point: two-window Pygame loop with timeline sync.

Creates a fullscreen projection window on the secondary display and a
windowed HUD on the primary display.  Both are updated each frame from
the same :class:`~leadsheet_utility.timeline.Timeline` state.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pygame

from leadsheet_utility.gui.hud import EXERCISE_NAMES, render_hud
from leadsheet_utility.gui.input import Action, key_to_action
from leadsheet_utility.harmony import analyze
from leadsheet_utility.leadsheet.models import LeadSheet
from leadsheet_utility.leadsheet.parser import parse_leadsheet
from leadsheet_utility.timeline import PlaybackState, Timeline, TimelineState

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_HUD_SIZE = (800, 500)
_FPS = 60
_TEMPO_STEP = 5
_TEMPO_MIN = 40
_TEMPO_MAX = 320


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------


class App:
    """Main application driving two pygame-ce windows from a shared timeline."""

    def __init__(self) -> None:
        pygame.init()
        pygame.mixer.init()

        # -- Query displays ---------------------------------------------------
        desktop_sizes = pygame.display.get_desktop_sizes()
        primary_w, primary_h = desktop_sizes[0]
        has_secondary = len(desktop_sizes) > 1

        # -- Projection window (secondary display, fullscreen) ----------------
        if has_secondary:
            proj_size = desktop_sizes[1]
            self._proj_window = pygame.Window(
                title="Projection",
                size=proj_size,
                position=(primary_w, 0),
                fullscreen_desktop=True,
            )
        else:
            # Fallback: small windowed preview on primary display
            proj_size = (960, 200)
            self._proj_window = pygame.Window(
                title="Projection (preview)",
                size=proj_size,
                position=(50, primary_h - 260),
            )

        # -- HUD window (primary display, windowed) ---------------------------
        self._hud_window = pygame.Window(
            title="leadsheet-utility",
            size=_HUD_SIZE,
            position=pygame.WINDOWPOS_CENTERED,
        )

        # -- Application state ------------------------------------------------
        self._lead_sheet: LeadSheet | None = None
        self._timeline: Timeline | None = None
        self._tempo: int = 120
        self._exercise_idx: int = 0  # 0-indexed into EXERCISE_NAMES
        self._running: bool = True
        self._clock = pygame.time.Clock()

    # -- public interface ----------------------------------------------------

    def run(self) -> None:
        """Run the main event loop until the user quits."""
        try:
            while self._running:
                self._process_events()
                tl_state = self._get_timeline_state()
                self._render_projection()
                self._render_hud(tl_state)
                self._clock.tick(_FPS)
        finally:
            pygame.quit()

    # -- event handling ------------------------------------------------------

    def _process_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False
            elif event.type == pygame.WINDOWCLOSE:
                self._running = False
            elif event.type == pygame.KEYDOWN:
                self._handle_action(key_to_action(event.key))

    def _handle_action(self, action: Action) -> None:
        if action is Action.NONE:
            return

        if action is Action.QUIT:
            self._running = False

        elif action is Action.TOGGLE_PLAY_PAUSE:
            self._toggle_play_pause()

        elif action is Action.STOP:
            if self._timeline:
                self._timeline.stop()

        elif action is Action.OPEN_FILE:
            self._open_file_dialog()

        elif action is Action.TEMPO_UP:
            self._tempo = min(_TEMPO_MAX, self._tempo + _TEMPO_STEP)
            self._rebuild_timeline()

        elif action is Action.TEMPO_DOWN:
            self._tempo = max(_TEMPO_MIN, self._tempo - _TEMPO_STEP)
            self._rebuild_timeline()

        elif action is Action.CALIBRATE:
            logger.info("Calibration mode not yet implemented")

        elif action.name.startswith("EXERCISE_"):
            idx = int(action.name[-1]) - 1
            if 0 <= idx < len(EXERCISE_NAMES):
                self._exercise_idx = idx

    # -- transport -----------------------------------------------------------

    def _toggle_play_pause(self) -> None:
        if self._timeline is None:
            return
        state = self._timeline.playback_state
        if state is PlaybackState.PLAYING:
            self._timeline.pause()
        else:
            self._timeline.play()

    # -- file loading --------------------------------------------------------

    def _open_file_dialog(self) -> None:
        """Open a native file dialog and load the selected lead sheet."""
        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()
            path = filedialog.askopenfilename(
                title="Open Lead Sheet",
                filetypes=[("TSV files", "*.tsv"), ("All files", "*.*")],
            )
            root.destroy()
        except Exception:
            logger.exception("File dialog failed")
            return

        if path:
            self._load_lead_sheet(Path(path))

    def _load_lead_sheet(self, path: Path) -> None:
        try:
            ls = parse_leadsheet(path)
            analyze(ls)
            self._lead_sheet = ls
            self._tempo = ls.default_tempo
            self._rebuild_timeline()
            logger.info("Loaded %s", ls.title)
        except Exception:
            logger.exception("Failed to load %s", path)

    def _rebuild_timeline(self) -> None:
        """(Re)create the timeline for the current lead sheet and tempo."""
        if self._lead_sheet is None:
            return
        was_playing = (
            self._timeline is not None
            and self._timeline.playback_state is PlaybackState.PLAYING
        )
        self._timeline = Timeline(self._lead_sheet, self._tempo)
        if was_playing:
            self._timeline.play()

    # -- rendering -----------------------------------------------------------

    def _get_timeline_state(self) -> TimelineState | None:
        if self._timeline is None:
            return None
        return self._timeline.get_state()

    def _render_projection(self) -> None:
        """Render the projection window (black when stopped, stubs for now)."""
        surface = self._proj_window.get_surface()
        surface.fill((0, 0, 0))
        # TODO: projection rendering (exercises + warpPerspective) goes here
        self._proj_window.flip()

    def _render_hud(self, tl_state: TimelineState | None) -> None:
        """Render the HUD window."""
        surface = self._hud_window.get_surface()
        pb_state = (
            self._timeline.playback_state
            if self._timeline
            else PlaybackState.STOPPED
        )
        render_hud(
            surface,
            self._lead_sheet,
            tl_state,
            pb_state,
            self._exercise_idx,
            self._tempo,
        )
        self._hud_window.flip()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    app = App()
    app.run()
