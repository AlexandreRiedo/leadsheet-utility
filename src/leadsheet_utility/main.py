"""Application entry point: two-window Pygame loop with timeline sync.

Creates a fullscreen projection window on the secondary display and a
windowed HUD on the primary display.  Both are updated each frame from
the same :class:`~leadsheet_utility.timeline.Timeline` state.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pygame

from leadsheet_utility.backing.events import generate_metronome
from leadsheet_utility.backing.renderer import render_backing_track
from leadsheet_utility.backing.walking_bass import generate_walking_bass
from leadsheet_utility.gui.hud import EXERCISE_NAMES, render_hud
from leadsheet_utility.gui.input import Action, key_to_action
from leadsheet_utility.harmony import analyze, midi_note_name, pc_name
from leadsheet_utility.leadsheet.models import ChordEvent, LeadSheet
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
_DEFAULT_SF_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "soundfonts" / "GeneralUser-GS.sf2"


# ---------------------------------------------------------------------------
# Harmony logging helpers
# ---------------------------------------------------------------------------


def _scale_pcs(chord: ChordEvent) -> str:
    """Deduplicated pitch-class names for the chord-scale, rooted on the chord root."""
    from leadsheet_utility.harmony.constants import NOTE_TO_PC

    root_pc = NOTE_TO_PC[chord.root]
    pcs: list[int] = []
    for n in chord.scale_notes:
        pc = n % 12
        if pc not in pcs:
            pcs.append(pc)
    pcs.sort(key=lambda pc: (pc - root_pc) % 12)
    return " ".join(pc_name(p) for p in pcs)


def _log_harmony_summary(ls: LeadSheet) -> None:
    """Print the full harmony analysis for every chord in the lead sheet."""
    logger.info("--- Harmony analysis: %s ---", ls.title)
    header = f"  {'Beat':>6}  {'Chord':14s}  {'Scale':44s}  {'Guide tones'}"
    logger.info(header)
    for chord in ls.chords:
        gt_pcs: list[str] = []
        for n in chord.guide_tones:
            name = pc_name(n)
            if name not in gt_pcs:
                gt_pcs.append(name)
            if len(gt_pcs) == 2:
                break
        logger.info(
            "  %6.1f  %-14s  %-44s  %s",
            chord.start_beat,
            chord.chord_symbol,
            _scale_pcs(chord),
            " ".join(gt_pcs),
        )

    if ls.guide_tone_line:
        logger.info("--- Guide-tone line paths ---")
        for i, path in enumerate(ls.guide_tone_line):
            notes = " ".join(midi_note_name(n) for n in path)
            logger.info("  Path %d: %s", i, notes)


def _log_chord_change(chord: ChordEvent) -> None:
    """Log when the active chord changes during playback."""
    gt_pcs: list[str] = []
    for n in chord.guide_tones:
        name = pc_name(n)
        if name not in gt_pcs:
            gt_pcs.append(name)
        if len(gt_pcs) == 2:
            break
    logger.info(
        "Beat %6.1f | %-14s | scale: %-30s | GT: %s",
        chord.start_beat,
        chord.chord_symbol,
        _scale_pcs(chord),
        " ".join(gt_pcs),
    )


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------


class App:
    """Main application driving two pygame-ce windows from a shared timeline."""

    def __init__(self) -> None:
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2)

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
        self._prev_chord_symbol: str | None = None  # for chord-change logging
        self._clock = pygame.time.Clock()

        # -- Audio state ------------------------------------------------------
        self._sf_path: str | None = str(_DEFAULT_SF_PATH) if _DEFAULT_SF_PATH.exists() else None
        self._sound: pygame.mixer.Sound | None = None
        self._channel: pygame.mixer.Channel | None = None
        self._audio_dirty: bool = True  # re-render needed
        self._metronome_on: bool = False

    # -- public interface ----------------------------------------------------

    def run(self) -> None:
        """Run the main event loop until the user quits."""
        try:
            while self._running:
                self._process_events()
                tl_state = self._get_timeline_state()
                self._check_chord_change(tl_state)
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
            self._stop_playback()

        elif action is Action.OPEN_FILE:
            self._open_file_dialog()

        elif action is Action.TEMPO_UP:
            self._tempo = min(_TEMPO_MAX, self._tempo + _TEMPO_STEP)
            self._stop_playback()
            self._audio_dirty = True
            self._rebuild_timeline()

        elif action is Action.TEMPO_DOWN:
            self._tempo = max(_TEMPO_MIN, self._tempo - _TEMPO_STEP)
            self._stop_playback()
            self._audio_dirty = True
            self._rebuild_timeline()

        elif action is Action.CALIBRATE:
            logger.info("Calibration mode not yet implemented")

        elif action is Action.TOGGLE_METRONOME:
            self._metronome_on = not self._metronome_on
            self._audio_dirty = True
            self._stop_playback()
            self._rebuild_timeline()
            logger.info("Metronome %s", "ON" if self._metronome_on else "OFF")

        elif action.name.startswith("EXERCISE_"):
            idx = int(action.name[-1]) - 1
            if 0 <= idx < len(EXERCISE_NAMES):
                self._exercise_idx = idx

    # -- transport -----------------------------------------------------------

    def _toggle_play_pause(self) -> None:
        if self._timeline is None or self._lead_sheet is None:
            return
        state = self._timeline.playback_state
        if state is PlaybackState.PLAYING:
            self._timeline.pause()
            if self._channel and self._channel.get_busy():
                self._channel.pause()
        else:
            # Render audio if needed
            if self._audio_dirty:
                if not self._ensure_soundfont():
                    return
                self._render_audio()
            if state is PlaybackState.PAUSED:
                self._timeline.play()
                if self._channel:
                    self._channel.unpause()
            else:
                # STOPPED → start fresh
                if self._sound is not None:
                    self._channel = self._sound.play()
                self._timeline.play()

    def _stop_playback(self) -> None:
        if self._channel and self._channel.get_busy():
            self._channel.stop()
        if self._timeline:
            self._timeline.stop()

    def _ensure_soundfont(self) -> bool:
        """Prompt for SoundFont path if not set. Returns True if available."""
        if self._sf_path and Path(self._sf_path).exists():
            return True
        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()
            path = filedialog.askopenfilename(
                title="Select a GM SoundFont (.sf2)",
                filetypes=[("SoundFont files", "*.sf2"), ("All files", "*.*")],
            )
            root.destroy()
        except Exception:
            logger.exception("SoundFont dialog failed")
            return False

        if not path:
            return False
        self._sf_path = path
        logger.info("SoundFont: %s", path)
        return True

    def _render_audio(self) -> None:
        """Pre-render the backing track (walking bass + optional metronome)."""
        if self._lead_sheet is None or self._sf_path is None:
            return

        # Show "Rendering..." on the HUD before blocking
        self._show_status("Rendering audio...")

        total_beats = self._lead_sheet.total_beats * self._lead_sheet.form_repeats
        logger.info("Rendering backing track (%.0f beats at %d BPM)...", total_beats, self._tempo)

        events = generate_walking_bass(
            self._lead_sheet.chords,
            self._tempo,
            form_repeats=self._lead_sheet.form_repeats,
        )
        if self._metronome_on:
            events.extend(generate_metronome(total_beats, self._tempo))

        buf = render_backing_track(events, self._sf_path, total_beats, self._tempo)
        self._sound = pygame.mixer.Sound(buffer=buf)
        self._audio_dirty = False
        logger.info("Render complete.")

    def _show_status(self, message: str) -> None:
        """Flash a status message on the HUD for one frame."""
        surface = self._hud_window.get_surface()
        surface.fill((30, 30, 30))
        font = pygame.font.SysFont("consolas", 22)
        text = font.render(message, True, (220, 220, 220))
        w, h = surface.get_size()
        surface.blit(text, ((w - text.get_width()) // 2, (h - text.get_height()) // 2))
        self._hud_window.flip()

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
            self._audio_dirty = True
            self._rebuild_timeline()
            self._prev_chord_symbol = None  # reset chord-change tracker
            _log_harmony_summary(ls)
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

    # -- chord-change detection ----------------------------------------------

    def _check_chord_change(self, tl_state: TimelineState | None) -> None:
        if tl_state is None:
            return
        sym = tl_state.current_chord.chord_symbol
        if sym != self._prev_chord_symbol:
            self._prev_chord_symbol = sym
            _log_chord_change(tl_state.current_chord)

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
            self._metronome_on,
        )
        self._hud_window.flip()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    app = App()
    app.run()
