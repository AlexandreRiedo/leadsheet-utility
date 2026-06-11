"""Application entry point: two-window Pygame loop with timeline sync.

Creates a fullscreen projection window on the secondary display and a
windowed HUD on the primary display.  Both are updated each frame from
the same :class:`~leadsheet_utility.timeline.Timeline` state.
"""

from __future__ import annotations

import logging
import os
import sys
import threading
import time
from dataclasses import replace
from enum import Enum
from math import ceil, floor
from pathlib import Path

# Windows reports a scaled (logical) desktop size unless the process opts into
# DPI awareness — without this we'd open the projector window at e.g. 1280x720
# on a 1920x1080 display and the saved calibration would no longer match.
if sys.platform == "win32":
    try:
        import ctypes

        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

import numpy as np
import pygame

from leadsheet_utility.backing.comping import generate_comping
from leadsheet_utility.backing.events import (
    MidiEvent,
    generate_count_in,
    generate_drums,
    generate_metronome,
)
from leadsheet_utility.backing.renderer import (
    mix_layers,
    render_backing_track,
    render_layer,
)
from leadsheet_utility.backing.walking_bass import generate_walking_bass
from leadsheet_utility.calibration import (
    DEFAULT_CALIBRATION_PATH,
    DEFAULT_ONE_OCTAVE_LOW,
    DEFAULT_TWO_OCTAVE_LOW,
    CalibrationUI,
    load_calibration,
    save_calibration,
)
from leadsheet_utility.exercises import (
    NEXT_GUIDE_TONE_COLOR,
    ChordToneMode,
    ContourPattern,
    ContourSpeed,
    FlowPhrasing,
    FlowPattern,
    PhraseLength,
    RangeMode,
    StartEndPattern,
    WindowWidth,
    apply_chord_tone_highlight,
    apply_contour_window,
    apply_guide_tone_highlight,
    apply_root_highlight,
    apply_start_end_highlight,
    chord_tone_only_highlights,
    free_mode_highlights,
    generate_contour_pattern,
    generate_flow_pattern,
    generate_start_end_pattern,
    guide_tone_midi,
    guide_tone_path_count,
    next_chord_tone_mode,
    next_contour_speed,
    next_flow_phrasing,
    next_phrase_length,
    next_range_mode,
    next_window_width,
)
from leadsheet_utility.gui.chart import render_chart
from leadsheet_utility.gui.hud import EXERCISE_NAMES, render_calibration_hud, render_hud
from leadsheet_utility.gui.input import Action, key_to_action
from leadsheet_utility.harmony import analyze, midi_note_name, pc_name
from leadsheet_utility.leadsheet.models import ChordEvent, LeadSheet
from leadsheet_utility.leadsheet.parser import parse_leadsheet
from leadsheet_utility.projection import (
    DEFAULT_BLACK_HEIGHT_RATIO,
    DEFAULT_BLACK_WIDTH_RATIO,
    MIDI_DEFAULT_HIGH,
    MIDI_DEFAULT_LOW,
    build_keyboard_layout,
    make_canonical_surface,
    make_default_homography,
    render_canonical,
    warp_canonical_to_projector,
)
from leadsheet_utility.timeline import PlaybackState, Timeline, TimelineState

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_HUD_SIZE = (1820, 880)
_FPS = 60
_TEMPO_STEP = 5
_TEMPO_MIN = 40
_TEMPO_MAX = 320
_DEFAULT_SF_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "data"
    / "soundfonts"
    / "GeneralUser-GS.sf2"
)
_CANONICAL_SIZE = (1920, 200)
_SAMPLE_RATE = 44100

# When a loop region is confirmed, its bars are re-rendered (with fresh
# walking-bass/comping variation each pass) and repeated to fill roughly this
# many seconds of audio, so the looped section doesn't sound mechanically
# identical every time around.
_LOOP_TARGET_SECONDS = 240

# Empirically tuned to cover projector input lag + signal/processing delay so
# the lit-up scale lines up with the audio. Bump up if the projector still
# trails the backing track; down if it now leads.
_PROJECTION_LEAD_SECONDS = 0.16


class BackingMode(Enum):
    """How much of the rhythm section is audible.

    Cycled with the G key; remixed instantly from cached per-layer renders so
    toggling doesn't require a fresh FluidSynth pass.
    """

    NONE = 0
    DRUMS = 1
    DRUMS_BASS = 2
    FULL = 3


_BACKING_CYCLE: list[BackingMode] = [
    BackingMode.NONE,
    BackingMode.DRUMS,
    BackingMode.DRUMS_BASS,
    BackingMode.FULL,
]

_BACKING_LABELS: dict[BackingMode, str] = {
    BackingMode.NONE: "NONE",
    BackingMode.DRUMS: "DRUMS",
    BackingMode.DRUMS_BASS: "Drums and Bass",
    BackingMode.FULL: "FULL",
}


def _next_backing_mode(mode: BackingMode) -> BackingMode:
    i = _BACKING_CYCLE.index(mode)
    return _BACKING_CYCLE[(i + 1) % len(_BACKING_CYCLE)]


def _range_mode_label(mode: RangeMode) -> str:
    """Short HUD label for the range cycle."""
    return {
        RangeMode.FULL: "FULL",
        RangeMode.RIGHT_HAND: "R.HAND",
        RangeMode.TWO_OCTAVE: "2 OCT",
        RangeMode.ONE_OCTAVE: "1 OCT",
    }[mode]


def _phrase_length_label(p: PhraseLength) -> str:
    """Short HUD label for the Start/End phrase-length cycle."""
    return {
        PhraseLength.TWO_BARS: "2 BAR",
        PhraseLength.FOUR_BARS: "4 BAR",
        PhraseLength.EIGHT_BARS: "8 BAR",
    }[p]


def _window_width_label(w: WindowWidth) -> str:
    """Short HUD label for the Contour window-width cycle."""
    return {
        WindowWidth.NARROW: "NARROW",
        WindowWidth.MEDIUM: "MEDIUM",
        WindowWidth.WIDE: "WIDE",
    }[w]


def _contour_speed_label(s: ContourSpeed) -> str:
    """Short HUD label for the Contour speed cycle."""
    return {
        ContourSpeed.SLOW: "SLOW",
        ContourSpeed.MEDIUM: "MEDIUM",
        ContourSpeed.FAST: "FAST",
    }[s]


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
        primary_h = desktop_sizes[0][1]
        n_displays = len(desktop_sizes)
        has_secondary = n_displays > 1

        # Per-window display assignment. SDL places a window on display N when
        # its position is WINDOWPOS_CENTERED | N (the constant is a mask);
        # fullscreen_desktop then takes over the display containing the window.
        # Defaults: HUD on 0, chart on 1, projector on the last display —
        # override with the HUD_DISPLAY / CHART_DISPLAY / PROJ_DISPLAY env vars.
        def display_env(name: str, default: int) -> int:
            try:
                idx = int(os.environ.get(name, default))
            except ValueError:
                idx = default
            if not 0 <= idx < n_displays:
                logging.warning("%s=%s out of range; using %d", name, os.environ.get(name), default)
                idx = default
            return idx

        def centered_on(idx: int) -> tuple[int, int]:
            return (pygame.WINDOWPOS_CENTERED | idx, pygame.WINDOWPOS_CENTERED | idx)

        hud_display = display_env("HUD_DISPLAY", 0)
        chart_display = display_env("CHART_DISPLAY", 1 if n_displays >= 3 else 0)
        proj_display = display_env("PROJ_DISPLAY", n_displays - 1)

        # -- Projection window (fullscreen on its own display) -----------------
        if has_secondary:
            proj_size = desktop_sizes[proj_display]
            self._proj_window = pygame.Window(
                title="Projection",
                size=proj_size,
                position=centered_on(proj_display),
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

        # -- HUD window (windowed, centered on its display) --------------------
        self._hud_window = pygame.Window(
            title="leadsheet-utility",
            size=_HUD_SIZE,
            position=centered_on(hud_display),
        )

        # -- Chord chart window (fullscreen on its own display) ----------------
        # iReal Pro-style grid the player reads during playback. Borderless
        # fullscreen on its display; with fewer than three displays it shares
        # the primary and covers the HUD (Alt-Tab to reach the controls). The
        # grid auto-scales to the size.
        chart_size = desktop_sizes[chart_display]
        self._chart_window = pygame.Window(
            title="Chart",
            size=chart_size,
            position=centered_on(chart_display),
            fullscreen_desktop=True,
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
        self._sf_path: str | None = (
            str(_DEFAULT_SF_PATH) if _DEFAULT_SF_PATH.exists() else None
        )
        self._sound: pygame.mixer.Sound | None = None
        self._channel: pygame.mixer.Channel | None = None
        self._audio_dirty: bool = True  # re-render needed
        self._metronome_on: bool = False
        self._backing_mode: BackingMode = BackingMode.FULL
        self._highlight_root: bool = False
        self._range_mode: RangeMode = RangeMode.FULL
        self._chord_tone_mode: ChordToneMode = ChordToneMode.OFF
        # Which precomputed voice-led path the Guide Tone exercise follows.
        # The harmony analyzer emits up to two paths (3rd-led / 7th-led);
        # `H` swaps between them.
        self._guide_tone_path: int = 0
        # Octave nudge applied to the voice-led MIDI before band-snapping.
        # Default +1 lifts the analyzer's E3-E5 line into E4-E6, which is
        # where most right-hand improvisation lives. Up/Down arrows shift it.
        self._guide_tone_octave: int = 1
        # Preview the next chord's voice-led GT in orange so the player can
        # set up the resolution. Toggled with `N`.
        self._show_next_guide_tone: bool = False

        # -- Frozen mode state ------------------------------------------------
        self._frozen_mode: bool = False
        self._frozen_chord_idx: int = 0

        # -- Loop selection state ---------------------------------------------
        # `_loop_select_active` is the editing phase (move/resize the band with
        # Alt/Shift+arrows). On confirm, `_loop_region_bars` holds the active
        # (start_bar, end_bar_exclusive) and the timeline + audio loop over it.
        self._loop_select_active: bool = False
        self._loop_sel_start: int = 0  # selection start bar (0-indexed)
        self._loop_sel_len: int = 4  # selection length in bars (>= 1)
        self._loop_region_bars: tuple[int, int] | None = None  # active loop
        # The looped section becomes its own temporary form: a mini lead sheet
        # (the loop chords) with `form_repeats` set so it spans ~4 min, plus a
        # wrap-around timeline. The projection/exercises/HUD run over *this*
        # while a loop is active, so the game modes treat the loop as a new
        # continuous form (phrases/curves progress across passes) rather than
        # re-playing the same motions. The chart still shows the original tune.
        self._loop_lead_sheet: LeadSheet | None = None
        self._loop_timeline: Timeline | None = None
        # Freshly-rendered per-instrument layers for the looped section (its
        # own short progression × N repeats); kept separate from the full-song
        # `_layers` cache so clearing the loop restores normal playback.
        self._loop_layers: dict[str, np.ndarray] | None = None

        # -- Flow exercise state ----------------------------------------------
        # Pattern is regenerated on phrasing change and on lead-sheet load (its
        # length depends on the form). Tempo doesn't affect it — the pattern is
        # measured in beats, not seconds.
        self._flow_phrasing: FlowPhrasing = FlowPhrasing.MEDIUM
        self._flow_pattern: FlowPattern | None = None

        # -- Start/End exercise state ----------------------------------------
        # Picks are pre-rolled per lead-sheet load, and re-rolled whenever the
        # user changes phrase length, range mode, or hits Shift+P. ``_seed``
        # bumps on each manual re-roll so identical settings still produce a
        # fresh pattern.
        self._phrase_length: PhraseLength = PhraseLength.FOUR_BARS
        self._start_end_pattern: StartEndPattern | None = None
        self._start_end_seed: int = 0

        # -- Contour exercise state ------------------------------------------
        # Smoothed random walk over absolute beats; regenerated on lead-sheet
        # load, on speed change, and on Shift+W (seed bump). Width is the
        # half-width in semitones either side of the curve's current center;
        # speed controls how many bars one arc lasts.
        self._window_width: WindowWidth = WindowWidth.MEDIUM
        self._contour_speed: ContourSpeed = ContourSpeed.MEDIUM
        self._contour_pattern: ContourPattern | None = None
        self._contour_seed: int = 0

        # -- Async render state ----------------------------------------------
        # Layers are cached per-instrument (bass/drums/guitar/metronome) as
        # int16 buffers without normalization, so toggling backing mode or the
        # metronome only triggers a fast numpy sum, not a fresh FluidSynth pass.
        self._render_thread: threading.Thread | None = None
        self._render_result: dict[str, np.ndarray] | None = None
        self._render_pending_action: str | None = None  # "count_in" or "resume"
        self._layers: dict[str, np.ndarray] | None = None

        # -- Count-in state ----------------------------------------------------
        self._count_in_active: bool = False
        self._count_in_start: float = 0.0  # perf_counter timestamp
        self._count_in_total_beats: int = 0
        self._count_in_spb: float = 0.0  # seconds per beat at current tempo
        self._count_in_channel: pygame.mixer.Channel | None = None

        # -- Projection state -------------------------------------------------
        self._proj_size: tuple[int, int] = proj_size
        self._load_projection_calibration()
        self._canonical_surface = make_canonical_surface(*_CANONICAL_SIZE)

        # -- Calibration mode (None when not active) --------------------------
        self._calibration_ui: CalibrationUI | None = None
        self._calibration_font: pygame.font.Font | None = None

    # -- public interface ----------------------------------------------------

    def run(self) -> None:
        """Run the main event loop until the user quits."""
        try:
            while self._running:
                self._process_events()
                self._update_render()
                self._update_count_in()
                tl_state = self._get_timeline_state()
                self._check_chord_change(tl_state)
                self._render_projection()
                self._render_hud(tl_state)
                self._render_chart(tl_state)
                self._clock.tick(_FPS)
        finally:
            pygame.quit()

    # -- event handling ------------------------------------------------------

    def _process_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or event.type == pygame.WINDOWCLOSE:
                self._running = False
                continue
            # While calibrating, the UI consumes all keyboard + mouse input.
            # Its own state machine handles Enter/Esc/etc.; we only watch for
            # it becoming inactive so we can save and return to normal mode.
            if self._calibration_ui is not None:
                self._calibration_ui.handle_event(event)
                if not self._calibration_ui.active:
                    self._finish_calibration()
                continue
            if event.type == pygame.KEYDOWN:
                self._handle_action(key_to_action(event.key, event.mod))

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
            self._invalidate_layers()
            self._stop_playback()
            self._rebuild_timeline()

        elif action is Action.TEMPO_DOWN:
            self._tempo = max(_TEMPO_MIN, self._tempo - _TEMPO_STEP)
            self._invalidate_layers()
            self._stop_playback()
            self._rebuild_timeline()

        elif action is Action.CALIBRATE:
            self._enter_calibration()

        elif action is Action.TOGGLE_METRONOME:
            self._metronome_on = not self._metronome_on
            logger.info("Metronome %s", "ON" if self._metronome_on else "OFF")
            self._remix_and_swap()

        elif action is Action.TOGGLE_COMPING:
            self._backing_mode = _next_backing_mode(self._backing_mode)
            logger.info("Backing: %s", _BACKING_LABELS[self._backing_mode])
            self._remix_and_swap()

        elif action is Action.TOGGLE_ROOT_HIGHLIGHT:
            self._highlight_root = not self._highlight_root
            logger.info("Root highlight %s", "ON" if self._highlight_root else "OFF")

        elif action is Action.TOGGLE_RANGE_MODE:
            self._range_mode = next_range_mode(self._range_mode)
            logger.info("Range: %s", self._range_mode.name)

        elif action is Action.TOGGLE_CHORD_TONES:
            self._chord_tone_mode = next_chord_tone_mode(self._chord_tone_mode)
            logger.info("Chord-tone mode: %s", self._chord_tone_mode.name)

        elif action is Action.TOGGLE_FROZEN:
            self._toggle_frozen_mode()

        elif action is Action.FROZEN_PREV:
            self._frozen_step(-1)

        elif action is Action.FROZEN_NEXT:
            self._frozen_step(1)

        elif action is Action.TOGGLE_GUIDE_TONE_PATH:
            self._cycle_guide_tone_path()

        elif action is Action.GUIDE_TONE_OCTAVE_DOWN:
            self._shift_guide_tone_octave(-1)

        elif action is Action.GUIDE_TONE_OCTAVE_UP:
            self._shift_guide_tone_octave(1)

        elif action is Action.TOGGLE_GUIDE_TONE_NEXT:
            self._show_next_guide_tone = not self._show_next_guide_tone
            logger.info(
                "Next-GT preview %s", "ON" if self._show_next_guide_tone else "OFF"
            )

        elif action is Action.CYCLE_FLOW_PHRASING:
            self._flow_phrasing = next_flow_phrasing(self._flow_phrasing)
            self._regenerate_flow_pattern()
            logger.info("Flow phrasing: %s", self._flow_phrasing.name)

        elif action is Action.CYCLE_PHRASE_LENGTH:
            self._phrase_length = next_phrase_length(self._phrase_length)
            self._regenerate_start_end_pattern()
            logger.info("Phrase length: %s", self._phrase_length.name)

        elif action is Action.REGENERATE_START_END:
            # Bump the seed so identical settings still produce a fresh roll.
            self._start_end_seed += 1
            self._regenerate_start_end_pattern()
            logger.info("Start/End picks regenerated (seed=%d)", self._start_end_seed)

        elif action is Action.CYCLE_WINDOW_WIDTH:
            self._window_width = next_window_width(self._window_width)
            logger.info("Window width: %s", self._window_width.name)

        elif action is Action.CYCLE_CONTOUR_SPEED:
            # Speed change reshapes the arc spacing, so a fresh roll is needed.
            self._contour_speed = next_contour_speed(self._contour_speed)
            self._regenerate_contour_pattern()
            logger.info("Contour speed: %s", self._contour_speed.name)

        elif action is Action.REGENERATE_CONTOUR:
            # Bump the seed so the same lead-sheet/state still rolls a new curve.
            self._contour_seed += 1
            self._regenerate_contour_pattern()
            logger.info("Contour curve regenerated (seed=%d)", self._contour_seed)

        elif action is Action.TOGGLE_LOOP_SELECT:
            self._toggle_loop_select()

        elif action is Action.LOOP_MOVE_LEFT:
            self._loop_move(-1)

        elif action is Action.LOOP_MOVE_RIGHT:
            self._loop_move(1)

        elif action is Action.LOOP_SHRINK:
            self._loop_resize(-1)

        elif action is Action.LOOP_EXPAND:
            self._loop_resize(1)

        elif action is Action.LOOP_CONFIRM:
            self._confirm_loop()

        elif action is Action.LOOP_CANCEL:
            self._cancel_loop()

        elif action.name.startswith("EXERCISE_"):
            idx = int(action.name[-1]) - 1
            if 0 <= idx < len(EXERCISE_NAMES):
                self._exercise_idx = idx

    # -- transport -----------------------------------------------------------

    def _toggle_play_pause(self) -> None:
        if self._timeline is None or self._lead_sheet is None:
            return

        # In frozen mode, SPACE exits frozen and continues into normal play.
        # The frozen-entry path already called _stop_playback(), so the
        # timeline is STOPPED and the fall-through below will trigger a
        # count-in from the start.
        if self._frozen_mode:
            self._frozen_mode = False
            logger.info("Frozen mode OFF (exited via play/pause)")

        # During count-in, treat play/pause as stop
        if self._count_in_active:
            self._stop_count_in()
            return

        # Ignore input while an async render is in flight
        if self._rendering:
            return

        # While a loop is active, play/pause just toggles the loop transport
        # (on the temporary form's timeline) — never fall through to the
        # full-song render/count-in path.
        if self._loop_region_bars is not None and self._loop_timeline is not None:
            if self._loop_timeline.playback_state is PlaybackState.PLAYING:
                self._loop_timeline.pause()
                if self._channel and self._channel.get_busy():
                    self._channel.pause()
            elif self._loop_timeline.playback_state is PlaybackState.PAUSED:
                self._loop_timeline.play()
                if self._channel:
                    self._channel.unpause()
            return

        state = self._timeline.playback_state
        if state is PlaybackState.PLAYING:
            self._timeline.pause()
            if self._channel and self._channel.get_busy():
                self._channel.pause()
        elif state is PlaybackState.PAUSED:
            # Render asynchronously if needed; resume once it completes
            if self._audio_dirty:
                if not self._ensure_soundfont():
                    return
                self._start_render_async("resume")
                return
            self._timeline.play()
            if self._channel:
                self._channel.unpause()
        else:
            # STOPPED → render if needed, then start count-in
            if self._audio_dirty:
                if not self._ensure_soundfont():
                    return
                self._start_render_async("count_in")
                return
            self._start_count_in()

    def _stop_playback(self) -> None:
        self._stop_count_in()
        if self._channel and self._channel.get_busy():
            self._channel.stop()
        if self._timeline:
            self._timeline.stop()
        if self._loop_timeline:
            self._loop_timeline.stop()

        # Tearing down a loop: drop the temporary form and restore the
        # exercise patterns to the original tune (deterministic — the seeds
        # are unchanged, so the pre-loop patterns come back identically).
        leaving_loop = self._loop_lead_sheet is not None
        self._loop_select_active = False
        self._loop_region_bars = None
        self._loop_lead_sheet = None
        self._loop_timeline = None
        self._loop_layers = None
        if leaving_loop:
            self._regenerate_flow_pattern()
            self._regenerate_start_end_pattern()
            self._regenerate_contour_pattern()

        # `_remix_and_swap` may have left `_sound` as a buffer sliced from the
        # middle of the song; rebuild from the full mix so the next play
        # starts at sample 0.
        if self._layers is not None:
            self._sound = pygame.mixer.Sound(buffer=self._mix_active_layers())

    # -- frozen mode -----------------------------------------------------------

    def _toggle_frozen_mode(self) -> None:
        """Enter/exit frozen mode. Entering halts playback and pins the projection
        to a single chord that the user steps through with the arrow keys."""
        if self._lead_sheet is None:
            return
        if self._frozen_mode:
            self._frozen_mode = False
            logger.info("Frozen mode OFF")
            return
        self._stop_playback()
        self._frozen_mode = True
        self._frozen_chord_idx = max(
            0, min(self._frozen_chord_idx, len(self._lead_sheet.chords) - 1)
        )
        chord = self._lead_sheet.chords[self._frozen_chord_idx]
        logger.info(
            "Frozen mode ON — chord %d/%d: %s",
            self._frozen_chord_idx + 1,
            len(self._lead_sheet.chords),
            chord.chord_symbol,
        )

    # -- guide tone path -------------------------------------------------------

    def _cycle_guide_tone_path(self) -> None:
        """Swap which voice-led guide-tone path (3rd-led / 7th-led) is active.

        No-op when no lead sheet is loaded or the analyzer produced fewer
        than two paths. The Guide Tone exercise reads this each frame; the
        cycle is reflected immediately, no audio re-render needed.
        """
        if self._lead_sheet is None:
            return
        n = guide_tone_path_count(self._lead_sheet)
        if n <= 1:
            return
        self._guide_tone_path = (self._guide_tone_path + 1) % n
        logger.info("Guide-tone path: %d/%d", self._guide_tone_path + 1, n)

    def _shift_guide_tone_octave(self, delta: int) -> None:
        """Nudge the Guide Tone exercise's octave offset by ``delta``.

        Clamped to ±3 octaves — beyond that the GT runs off the keyboard
        even in FULL range. In 1/2-OCT range the band-snap normalises any
        offset, so the clamp is purely a guard against accumulating noise.
        """
        self._guide_tone_octave = max(-3, min(3, self._guide_tone_octave + delta))
        logger.info("Guide-tone octave offset: %+d", self._guide_tone_octave)

    def _frozen_step(self, delta: int) -> None:
        if not self._frozen_mode or self._lead_sheet is None:
            return
        n = len(self._lead_sheet.chords)
        if n == 0:
            return
        self._frozen_chord_idx = (self._frozen_chord_idx + delta) % n
        chord = self._lead_sheet.chords[self._frozen_chord_idx]
        logger.info(
            "Frozen chord %d/%d: %s",
            self._frozen_chord_idx + 1,
            n,
            chord.chord_symbol,
        )

    # -- loop selection --------------------------------------------------------

    def _toggle_loop_select(self) -> None:
        """Enter (or leave) the loop-selection editing phase.

        Seeds the band from the active loop if one exists, otherwise a 4-bar
        window starting at the bar under the playhead. No-op while frozen.
        """
        if self._lead_sheet is None or self._frozen_mode:
            return
        if self._loop_select_active:
            self._loop_select_active = False
            logger.info("Loop selection cancelled")
            return

        total_bars = self._lead_sheet.total_bars
        if total_bars <= 0:
            return

        if self._loop_region_bars is not None:
            start, end = self._loop_region_bars
            self._loop_sel_start = start
            self._loop_sel_len = end - start
        else:
            cur_bar = self._current_bar()
            self._loop_sel_len = min(4, total_bars)
            self._loop_sel_start = max(0, min(cur_bar, total_bars - self._loop_sel_len))
        self._loop_select_active = True
        logger.info(
            "Loop select: bars %d-%d",
            self._loop_sel_start + 1,
            self._loop_sel_start + self._loop_sel_len,
        )

    def _current_bar(self) -> int:
        """0-indexed bar under the playhead (0 when stopped)."""
        if self._timeline is None or self._lead_sheet is None:
            return 0
        beats_per_bar = self._lead_sheet.time_signature[0]
        state = self._timeline.get_state()
        return int(state.current_beat // beats_per_bar)

    def _loop_move(self, delta: int) -> None:
        if not self._loop_select_active or self._lead_sheet is None:
            return
        total_bars = self._lead_sheet.total_bars
        self._loop_sel_start = max(
            0, min(self._loop_sel_start + delta, total_bars - self._loop_sel_len)
        )

    def _loop_resize(self, delta: int) -> None:
        if not self._loop_select_active or self._lead_sheet is None:
            return
        total_bars = self._lead_sheet.total_bars
        max_len = total_bars - self._loop_sel_start
        self._loop_sel_len = max(1, min(self._loop_sel_len + delta, max_len))

    # The projection, HUD, and exercises all run against the "active" context,
    # which is the temporary loop form while a loop is active and the original
    # lead sheet / timeline otherwise. (The chart is the exception — it always
    # shows the original tune, translating the loop cursor back onto it.)

    @property
    def _active_lead_sheet(self) -> LeadSheet | None:
        return (
            self._loop_lead_sheet
            if self._loop_lead_sheet is not None
            else self._lead_sheet
        )

    @property
    def _active_timeline(self) -> Timeline | None:
        return (
            self._loop_timeline if self._loop_timeline is not None else self._timeline
        )

    def _confirm_loop(self) -> None:
        """Activate the selected band as a temporary looped form.

        The bars are turned into a mini lead sheet (re-based to beat 0) repeated
        enough to span ~4 minutes, then rendered fresh — so the walking bass /
        comping vary each pass *and* the projection exercises treat the loop as
        one new continuous form (phrases and contours progress across passes
        instead of replaying the same motions).
        """
        if not self._loop_select_active or self._lead_sheet is None:
            return
        if not self._ensure_soundfont():
            return
        start_bar = self._loop_sel_start
        end_bar = start_bar + self._loop_sel_len
        self._loop_region_bars = (start_bar, end_bar)
        self._loop_select_active = False
        logger.info("Loop confirmed: bars %d-%d", start_bar + 1, end_bar)
        self._start_loop(start_bar, end_bar)

    def _cancel_loop(self) -> None:
        """Leave selection mode and clear any active loop (stops playback)."""
        was_selecting = self._loop_select_active
        self._loop_select_active = False
        if self._loop_region_bars is not None:
            self._stop_playback()  # tears down the temp form + restores patterns
            logger.info("Loop cleared")
        elif was_selecting:
            logger.info("Loop selection cancelled")

    def _loop_chords(
        self, start_bar: int, end_bar: int
    ) -> tuple[list[ChordEvent], float]:
        """Clip the chords in ``[start_bar, end_bar)`` and re-base them to 0.

        Returns the re-based chord list (suitable for the backing generators
        and a temporary lead sheet, both of which derive the form length from
        ``chords[-1].end_beat``) and the loop length in beats.
        """
        assert self._lead_sheet is not None
        beats_per_bar = self._lead_sheet.time_signature[0]
        loop_start = start_bar * beats_per_bar
        loop_end = end_bar * beats_per_bar

        out: list[ChordEvent] = []
        for ch in self._lead_sheet.chords:
            if ch.end_beat <= loop_start or ch.start_beat >= loop_end:
                continue
            new_start = max(ch.start_beat, loop_start) - loop_start
            new_end = min(ch.end_beat, loop_end) - loop_start
            out.append(
                replace(
                    ch,
                    start_beat=new_start,
                    end_beat=new_end,
                    duration_beats=new_end - new_start,
                    bar_number=floor(new_start / beats_per_bar) + 1,
                    beat_in_bar=new_start % beats_per_bar,
                )
            )
        return out, float(loop_end - loop_start)

    def _start_loop(self, start_bar: int, end_bar: int) -> None:
        """Build the temporary looped form and kick off its fresh audio render.

        The temp lead sheet + wrap-around timeline + regenerated exercise
        patterns are set up synchronously (cheap); the backing audio renders on
        the worker and starts playing via ``_play_loop_from_layers``.
        """
        if self._lead_sheet is None or self._sf_path is None:
            return
        if self._render_thread is not None and self._render_thread.is_alive():
            return

        loop_chords, loop_beats = self._loop_chords(start_bar, end_bar)
        if not loop_chords or loop_beats <= 0:
            return

        loop_seconds = loop_beats * 60.0 / self._tempo
        repeats = max(1, ceil(_LOOP_TARGET_SECONDS / loop_seconds))
        total_beats = loop_beats * repeats

        # Temporary mini lead sheet: the loop chords as one form, repeated.
        orig = self._lead_sheet
        temp = LeadSheet(
            title=f"{orig.title}  ·  LOOP bars {start_bar + 1}-{end_bar}",
            composer=orig.composer,
            key=orig.key,
            time_signature=orig.time_signature,
            default_tempo=orig.default_tempo,
            form_repeats=repeats,
            chords=loop_chords,
            total_beats=loop_beats,
            total_bars=end_bar - start_bar,
        )
        analyze(temp)
        self._loop_lead_sheet = temp
        self._loop_timeline = Timeline(temp, self._tempo, wrap_around=True)
        # Patterns now regenerate against the active (temp) form, so Flow /
        # Contour / Start-End span the whole looped form.
        self._regenerate_flow_pattern()
        self._regenerate_start_end_pattern()
        self._regenerate_contour_pattern()

        logger.info(
            "Loop form: %d bars × %d repeats = %.0f beats at %d BPM...",
            end_bar - start_bar,
            repeats,
            total_beats,
            self._tempo,
        )
        layer_events: dict[str, list[MidiEvent]] = {
            "bass": generate_walking_bass(
                loop_chords, self._tempo, form_repeats=repeats
            ),
            "drums": generate_drums(total_beats, self._tempo),
            "guitar": generate_comping(loop_chords, self._tempo, form_repeats=repeats),
            "metronome": generate_metronome(total_beats, self._tempo),
        }
        self._launch_render(layer_events, total_beats, "loop")

    def _play_loop_from_layers(self) -> None:
        """Mix the rendered loop layers and play them, starting the temp form."""
        if self._loop_layers is None or self._loop_timeline is None:
            return
        self._stop_count_in()
        buf = self._mix_active_layers(self._loop_layers)
        self._sound = pygame.mixer.Sound(buffer=buf)
        if self._channel is not None and self._channel.get_busy():
            self._channel.stop()
        # loops=-1 so practising past the rendered ~4 min keeps going; the
        # wrap-around timeline likewise wraps at the temp form's end.
        self._channel = self._sound.play(loops=-1)
        self._loop_timeline.stop()  # restart cleanly from the top of the form
        self._loop_timeline.play()

    # -- count-in --------------------------------------------------------------

    def _start_count_in(self) -> None:
        """Render and play a count-in, then transition to real playback."""
        if self._lead_sheet is None or self._sf_path is None:
            return

        beats_per_bar = self._lead_sheet.time_signature[0]
        self._count_in_total_beats = beats_per_bar * 2
        self._count_in_spb = 60.0 / self._tempo

        events = generate_count_in(self._tempo, beats_per_bar, num_bars=2)
        buf = render_backing_track(
            events,
            self._sf_path,
            self._count_in_total_beats,
            self._tempo,
        )
        sound = pygame.mixer.Sound(buffer=buf)
        self._count_in_channel = sound.play()
        # Keep a reference so the Sound isn't garbage-collected
        self._count_in_sound_obj = sound
        self._count_in_start = time.perf_counter()
        self._count_in_active = True

    def _stop_count_in(self) -> None:
        if not self._count_in_active:
            return
        if self._count_in_channel and self._count_in_channel.get_busy():
            self._count_in_channel.stop()
        self._count_in_active = False

    def _update_count_in(self) -> None:
        """Check if the count-in has finished; if so, start real playback."""
        if not self._count_in_active:
            return
        elapsed = time.perf_counter() - self._count_in_start
        beat = elapsed / self._count_in_spb
        if beat >= self._count_in_total_beats:
            self._count_in_active = False
            # Start real playback
            if self._sound is not None:
                self._channel = self._sound.play()
            if self._timeline:
                self._timeline.play()

    def _get_count_in_beat(self) -> float | None:
        """Return current beat within count-in, or None if not counting in."""
        if not self._count_in_active:
            return None
        elapsed = time.perf_counter() - self._count_in_start
        return elapsed / self._count_in_spb

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

    def _start_render_async(self, after_done: str) -> None:
        """Kick off a background thread to render the four backing layers.

        Renders bass, drums, guitar, and metronome as separate int16 buffers
        so toggling backing mode or metronome can remix from the cache without
        another FluidSynth pass.

        *after_done* is the action to trigger once the render finishes:
        ``"count_in"`` (fresh start → play count-in then song) or
        ``"resume"`` (coming back from a tempo change).  The main loop polls
        via :meth:`_update_render`.
        """
        if self._lead_sheet is None or self._sf_path is None:
            return
        if self._render_thread is not None and self._render_thread.is_alive():
            return

        total_beats = self._lead_sheet.total_beats * self._lead_sheet.form_repeats
        logger.info(
            "Rendering backing layers (%.0f beats at %d BPM)...",
            total_beats,
            self._tempo,
        )

        layer_events: dict[str, list[MidiEvent]] = {
            "bass": generate_walking_bass(
                self._lead_sheet.chords,
                self._tempo,
                form_repeats=self._lead_sheet.form_repeats,
            ),
            "drums": generate_drums(total_beats, self._tempo),
            "guitar": generate_comping(
                self._lead_sheet.chords,
                self._tempo,
                form_repeats=self._lead_sheet.form_repeats,
            ),
            "metronome": generate_metronome(total_beats, self._tempo),
        }

        self._launch_render(layer_events, total_beats, after_done)

    def _launch_render(
        self,
        layer_events: dict[str, list[MidiEvent]],
        total_beats: float,
        after_done: str,
    ) -> None:
        """Spawn the parallel layer-render worker and record the follow-up action."""
        if self._sf_path is None:
            return
        self._render_pending_action = after_done
        self._render_result = None
        self._render_thread = threading.Thread(
            target=self._render_worker,
            args=(layer_events, total_beats, self._tempo, self._sf_path),
            daemon=True,
        )
        self._render_thread.start()

    def _render_worker(
        self,
        layer_events: dict[str, list[MidiEvent]],
        total_beats: float,
        tempo: int,
        sf_path: str,
    ) -> None:
        """Render layers in parallel (one thread per layer).

        Each FluidSynth instance is independent (its own SF load, its own
        synth state), so they don't share mutable state. The C-level
        ``get_samples`` calls release the GIL, letting the per-layer renders
        actually overlap on multiple cores.
        """
        from concurrent.futures import ThreadPoolExecutor

        t0 = time.perf_counter()
        try:
            with ThreadPoolExecutor(max_workers=len(layer_events)) as pool:
                futures = {
                    name: pool.submit(render_layer, events, sf_path, total_beats, tempo)
                    for name, events in layer_events.items()
                }
                self._render_result = {name: f.result() for name, f in futures.items()}
        except Exception:
            logger.exception("Backing-layer render failed")
            self._render_result = None
            return
        logger.info("Layer render took %.2fs (parallel)", time.perf_counter() - t0)

    def _update_render(self) -> None:
        """Finalise an async render when the thread completes."""
        if self._render_thread is None:
            return
        if self._render_thread.is_alive():
            return

        self._render_thread.join()
        self._render_thread = None

        layers = self._render_result
        self._render_result = None
        action = self._render_pending_action
        self._render_pending_action = None

        if layers is None:
            return

        # Loop renders are kept separate from the full-song cache so clearing
        # the loop later restores normal playback without a re-render.
        if action == "loop":
            self._loop_layers = layers
            logger.info("Loop render complete.")
            self._play_loop_from_layers()
            return

        self._layers = layers
        self._sound = pygame.mixer.Sound(buffer=self._mix_active_layers())
        self._audio_dirty = False
        logger.info("Render complete.")

        if action == "count_in":
            self._start_count_in()
        elif action == "resume":
            if self._timeline is not None:
                self._timeline.play()
            if self._sound is not None:
                self._channel = self._sound.play()

    # -- layer mixing --------------------------------------------------------

    def _invalidate_layers(self) -> None:
        """Drop cached layers — the next play() will re-render them."""
        self._layers = None
        self._sound = None
        self._audio_dirty = True

    def _mix_active_layers(
        self, layers: dict[str, np.ndarray] | None = None
    ) -> np.ndarray:
        """Sum the currently-enabled layers into a single int16 buffer.

        Defaults to the full-song cache; pass *layers* to mix a different set
        (e.g. the looped-section layers) honouring the same backing/metronome
        toggles.
        """
        layers = layers if layers is not None else self._layers
        assert layers is not None
        active: list[np.ndarray] = []
        if self._backing_mode is not BackingMode.NONE:
            active.append(layers["drums"])
        if self._backing_mode in (BackingMode.DRUMS_BASS, BackingMode.FULL):
            active.append(layers["bass"])
        if self._backing_mode is BackingMode.FULL:
            active.append(layers["guitar"])
        if self._metronome_on:
            active.append(layers["metronome"])
        # All layers share the same length; pass it explicitly so NONE+no-metronome
        # still produces a buffer of the right duration (silence).
        total_samples = layers["drums"].size
        return mix_layers(active, total_samples=total_samples)

    def _remix_and_swap(self) -> None:
        """Rebuild the active mix and, if playing, splice it in mid-stream.

        Cheap (numpy add over int16 arrays) — the whole point of caching layers
        is that this never blocks on FluidSynth.  If the layers haven't been
        rendered yet (no playback has happened), this is a no-op; the next
        play() will render with the new state baked in.
        """
        # A loop is playing from its own rendered layers — remix those and
        # restart the loop from the top (cheap; keeps backing/metronome live).
        if self._loop_region_bars is not None and self._loop_layers is not None:
            self._play_loop_from_layers()
            return

        if self._layers is None:
            return  # nothing to remix from; next play() will pick up new state

        buf = self._mix_active_layers()

        playing = (
            self._channel is not None
            and self._channel.get_busy()
            and not self._count_in_active
        )
        if playing:
            # Slice from the current playhead so audio resumes seamlessly.
            # Stereo interleaved → 2 array entries per audio frame.
            sample_pos = self._current_sample_position()
            offset = sample_pos * 2
            if offset >= buf.size:
                return  # past the end of the song; let it stop naturally
            buf = buf[offset:].copy()  # pygame.mixer keeps a view alive

        self._sound = pygame.mixer.Sound(buffer=buf)
        if playing:
            if self._channel is not None:
                self._channel.stop()
            self._channel = self._sound.play()

    def _current_sample_position(self) -> int:
        """Where in the song buffer the playhead currently sits, in samples."""
        if self._timeline is None or self._lead_sheet is None:
            return 0
        state = self._timeline.get_state()
        total_beats_elapsed = (
            state.form_repeat * self._lead_sheet.total_beats + state.current_beat
        )
        elapsed_seconds = total_beats_elapsed * 60.0 / self._tempo
        return int(elapsed_seconds * _SAMPLE_RATE)

    @property
    def _rendering(self) -> bool:
        """True while the async render thread is running."""
        return self._render_thread is not None and self._render_thread.is_alive()

    def _render_calibration_hud(self) -> None:
        """Mirror the calibration UI on the HUD — the projector text is
        physically too far / too warped to read while editing markers."""
        surface = self._hud_window.get_surface()
        if self._calibration_ui is None:
            return
        render_calibration_hud(surface, self._calibration_ui.snapshot())
        self._hud_window.flip()

    def _render_loading_screen(self, message: str) -> None:
        """Draw an animated 'Rendering audio...' screen while the render thread runs."""
        surface = self._hud_window.get_surface()
        surface.fill((30, 30, 30))
        font = pygame.font.SysFont("consolas", 33)
        n_dots = 1 + (int(time.perf_counter() * 3) % 3)
        text = font.render(f"{message}{'.' * n_dots}", True, (220, 220, 220))
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
            self._frozen_mode = False
            self._frozen_chord_idx = 0
            self._guide_tone_path = 0
            self._guide_tone_octave = 1
            self._show_next_guide_tone = False
            self._regenerate_flow_pattern()
            self._regenerate_start_end_pattern()
            self._regenerate_contour_pattern()
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
        timeline = self._active_timeline
        if timeline is None:
            return None
        return timeline.get_state()

    # -- calibration mode ----------------------------------------------------

    def _enter_calibration(self) -> None:
        """Stop playback and switch the projector window to calibration mode.

        Seeds the UI with the saved calibration when its projector size
        matches, so the user can fine-tune incrementally instead of starting
        from defaults each time.
        """
        if self._calibration_ui is not None:
            return  # already calibrating
        self._stop_playback()

        cal = load_calibration()
        if cal is not None and cal.projector_size == self._proj_size:
            self._calibration_ui = CalibrationUI(
                canonical_size=_CANONICAL_SIZE,
                projector_size=self._proj_size,
                initial_markers=cal.markers,
                black_width_ratio=cal.black_width_ratio,
                black_height_ratio=cal.black_height_ratio,
                black_key_offsets=cal.black_key_offsets,
                midi_full_low=cal.midi_full_low,
                midi_full_high=cal.midi_full_high,
                midi_one_octave_low=cal.midi_one_octave_low,
                midi_one_octave_high=cal.midi_one_octave_high,
                midi_two_octave_low=cal.midi_two_octave_low,
                midi_two_octave_high=cal.midi_two_octave_high,
                audio_delay_ms=cal.audio_delay_ms,
            )
        else:
            self._calibration_ui = CalibrationUI(
                canonical_size=_CANONICAL_SIZE,
                projector_size=self._proj_size,
            )
        if self._calibration_font is None:
            self._calibration_font = pygame.font.SysFont("consolas", 20)
        logger.info("Entered calibration mode")

    def _finish_calibration(self) -> None:
        """Save (or discard) and reload calibration after the UI closes."""
        ui = self._calibration_ui
        self._calibration_ui = None
        if ui is None:
            return
        if ui.confirmed:
            save_calibration(ui.build_calibration())
            logger.info("Saved calibration to %s", DEFAULT_CALIBRATION_PATH)
            self._load_projection_calibration()
        else:
            logger.info("Calibration cancelled — saved calibration unchanged")

    def _load_projection_calibration(self) -> None:
        """Load saved calibration, or fall back to a default identity homography.

        Sets `self._homography`, `self._keyboard_layout`, the per-range MIDI
        bands used by the exercises, and the audio-delay offset. Black-key
        proportion ratios + bands come from the saved calibration when
        present so the canonical layout matches the specific piano;
        otherwise the spec defaults are used.
        """
        cal = load_calibration()
        black_offsets: dict[int, tuple[float, float]] = {}
        if cal is not None and cal.projector_size == self._proj_size:
            self._homography = cal.homography()
            black_w = cal.black_width_ratio
            black_h = cal.black_height_ratio
            black_offsets = cal.black_key_offsets
            self._midi_full_low = cal.midi_full_low
            self._midi_full_high = cal.midi_full_high
            self._midi_one_octave_low = cal.midi_one_octave_low
            self._midi_two_octave_low = cal.midi_two_octave_low
            self._audio_delay_ms = cal.audio_delay_ms
            logger.info(
                "Loaded calibration (black ratios w=%.2f h=%.2f, %d per-key offsets, "
                "full=%d-%d, 1oct low=%d, 2oct low=%d, audio_delay=%+d ms)",
                black_w,
                black_h,
                len(black_offsets),
                self._midi_full_low,
                self._midi_full_high,
                self._midi_one_octave_low,
                self._midi_two_octave_low,
                self._audio_delay_ms,
            )
        else:
            self._homography = make_default_homography(_CANONICAL_SIZE, self._proj_size)
            black_w = DEFAULT_BLACK_WIDTH_RATIO
            black_h = DEFAULT_BLACK_HEIGHT_RATIO
            self._midi_full_low = MIDI_DEFAULT_LOW
            self._midi_full_high = MIDI_DEFAULT_HIGH
            self._midi_one_octave_low = DEFAULT_ONE_OCTAVE_LOW
            self._midi_two_octave_low = DEFAULT_TWO_OCTAVE_LOW
            self._audio_delay_ms = 0
            if cal is None:
                logger.info("No calibration found — using default identity homography")
            else:
                logger.info(
                    "Calibration projector size mismatch (%s vs %s) — using default",
                    cal.projector_size,
                    self._proj_size,
                )

        self._keyboard_layout = build_keyboard_layout(
            *_CANONICAL_SIZE,
            midi_low=self._midi_full_low,
            midi_high=self._midi_full_high,
            black_width_ratio=black_w,
            black_height_ratio=black_h,
            black_key_offsets=black_offsets,
        )

    def _regenerate_flow_pattern(self) -> None:
        """Rebuild the Flow exercise's on/off pattern for the loaded form.

        Called on lead-sheet load and on phrasing change. The pattern spans
        every form repeat so the gate keeps progressing across loops; it is
        measured in beats, so tempo changes don't invalidate it.
        """
        ls = self._active_lead_sheet
        if ls is None:
            self._flow_pattern = None
            return
        total = ls.total_beats * ls.form_repeats
        self._flow_pattern = generate_flow_pattern(total, self._flow_phrasing)

    def _regenerate_contour_pattern(self) -> None:
        """Roll a fresh smoothed-random-walk contour for the loaded form.

        Called on lead-sheet load and on Shift+W. The pattern lives in
        absolute beats across every form repeat, so tempo changes don't
        invalidate it; only the seed (bumped manually) or a different
        lead sheet does. The right-hand-register bounds come from the
        loaded calibration so the curve never leaves the projector's
        physical reach.
        """
        ls = self._active_lead_sheet
        if ls is None:
            self._contour_pattern = None
            return
        total = ls.total_beats * ls.form_repeats
        self._contour_pattern = generate_contour_pattern(
            total,
            midi_full_low=self._midi_full_low,
            midi_full_high=self._midi_full_high,
            beats_per_bar=ls.time_signature[0],
            speed=self._contour_speed,
            seed=self._contour_seed,
        )

    def _regenerate_start_end_pattern(self) -> None:
        """Roll fresh Start/End picks for the active phrase length and range.

        Called on lead-sheet load, phrase-length change, range-mode change,
        and Shift+P. The pattern is keyed on the current ``_start_end_seed``
        so successive Shift+P presses produce a sequence of distinct rolls
        even when nothing else has changed.
        """
        ls = self._active_lead_sheet
        if ls is None:
            self._start_end_pattern = None
            return
        self._start_end_pattern = generate_start_end_pattern(
            ls,
            self._phrase_length,
            midi_full_low=self._midi_full_low,
            midi_full_high=self._midi_full_high,
            seed=self._start_end_seed,
        )

    def _active_band_low(self) -> int | None:
        """Calibrated band-low for the active RangeMode, or None for FULL."""
        if self._range_mode is RangeMode.ONE_OCTAVE:
            return self._midi_one_octave_low
        if self._range_mode is RangeMode.TWO_OCTAVE:
            return self._midi_two_octave_low
        return None

    def _render_projection(self) -> None:
        """Render the projection window: free-mode highlights warped through H.

        While calibrating, hand the entire projector surface over to the
        CalibrationUI — it does its own warping and overlay drawing.
        """
        screen = self._proj_window.get_surface()
        if self._calibration_ui is not None:
            self._calibration_ui.render(screen, font=self._calibration_font)
            self._proj_window.flip()
            return

        screen.fill((0, 0, 0))

        # The projection + exercises run against the active context — the
        # temporary looped form while a loop is active, the original tune
        # otherwise — so the game modes treat a loop as one continuous form.
        active_ls = self._active_lead_sheet
        active_timeline = self._active_timeline

        projected_chord: ChordEvent | None = None
        projected_chord_idx: int | None = None
        # Absolute lead-compensated beat across all form repeats; only set while
        # playing. Used by the Flow exercise to drive its on/off gate.
        projected_abs_beat: float | None = None
        if self._frozen_mode and active_ls is not None:
            chords = active_ls.chords
            if chords:
                idx = max(0, min(self._frozen_chord_idx, len(chords) - 1))
                projected_chord = chords[idx]
                projected_chord_idx = idx
        else:
            timeline = active_timeline
            tl_state = timeline.get_state() if timeline else None
            playing = (
                timeline is not None
                and timeline.playback_state is PlaybackState.PLAYING
            )
            if (
                playing
                and timeline is not None
                and tl_state is not None
                and not self._count_in_active
            ):
                # Positive audio_delay_ms = projection trails audio by N ms →
                # less projection lead than the hardware-tuned default.
                effective_lead_s = (
                    _PROJECTION_LEAD_SECONDS - self._audio_delay_ms / 1000.0
                )
                lead_beats = effective_lead_s * (self._tempo / 60.0)
                projected_chord = timeline.chord_at(tl_state.current_beat + lead_beats)
                if projected_chord is not None and active_ls is not None:
                    # ChordEvent identity is stable (same list used by analyzer + timeline)
                    projected_chord_idx = active_ls.chords.index(projected_chord)
                    projected_abs_beat = (
                        tl_state.form_repeat * active_ls.total_beats
                        + tl_state.current_beat
                        + lead_beats
                    )

        band_low = self._active_band_low()
        if projected_chord is not None:
            if self._chord_tone_mode is ChordToneMode.ONLY:
                highlights = chord_tone_only_highlights(
                    projected_chord,
                    range_mode=self._range_mode,
                    band_low=band_low,
                )
            else:
                highlights = free_mode_highlights(
                    projected_chord,
                    range_mode=self._range_mode,
                    band_low=band_low,
                )
            # Contour exercise: filter the base highlights to a sliding
            # window around the pre-rolled curve's current center. Runs
            # *before* the colour overlays so chord-tone / root / Start
            # & End all paint on whichever scale notes survive. Frozen
            # mode and the stopped/count-in state bypass the filter so
            # the player can still see the full chord-scale.
            if (
                self._exercise_idx == 2
                and self._contour_pattern is not None
                and projected_abs_beat is not None
            ):
                highlights = apply_contour_window(
                    highlights,
                    projected_abs_beat,
                    self._contour_pattern,
                    self._window_width,
                )
            if self._chord_tone_mode is ChordToneMode.OVERLAY:
                highlights = apply_chord_tone_highlight(highlights, projected_chord)
            # Root overlay applied before guide tone so the GT (3rd or 7th)
            # can still beat the root colour when both overlays are on.
            if self._highlight_root:
                highlights = apply_root_highlight(highlights, projected_chord)
            # Guide Tone exercise: red voice-led 3rd/7th on top of everything.
            # Optionally preview the *next* chord's GT in orange first so the
            # player can set up the resolution; the current GT (red) is then
            # applied on top, so a same-MIDI collision still lands on red.
            if (
                self._exercise_idx == 1
                and active_ls is not None
                and projected_chord_idx is not None
            ):
                if self._show_next_guide_tone:
                    next_chord_idx = (projected_chord_idx + 1) % len(active_ls.chords)
                    next_gt_midi = guide_tone_midi(
                        active_ls,
                        next_chord_idx,
                        path_idx=self._guide_tone_path,
                        octave_offset=self._guide_tone_octave,
                        range_mode=self._range_mode,
                        band_low=band_low,
                    )
                    if next_gt_midi is not None:
                        # If the next-chord target isn't in the *current*
                        # chord-scale, playing it now sounds wrong — stripe
                        # it so the player sees the target without being
                        # invited to land on it early.
                        current_scale_pcs = {
                            n % 12 for n in projected_chord.scale_notes
                        }
                        outside_scale = (next_gt_midi % 12) not in current_scale_pcs
                        highlights = apply_guide_tone_highlight(
                            highlights,
                            next_gt_midi,
                            color=NEXT_GUIDE_TONE_COLOR,
                            striped=outside_scale,
                        )
                gt_midi = guide_tone_midi(
                    active_ls,
                    projected_chord_idx,
                    path_idx=self._guide_tone_path,
                    octave_offset=self._guide_tone_octave,
                    range_mode=self._range_mode,
                    band_low=band_low,
                )
                if gt_midi is not None:
                    highlights = apply_guide_tone_highlight(highlights, gt_midi)
            # Flow exercise: gate everything on/off based on the pre-generated
            # pattern. Only applied during real playback (projected_abs_beat is
            # only set then) — frozen mode and the stopped state always show
            # the chord so the player can study it.
            if (
                self._exercise_idx == 3
                and self._flow_pattern is not None
                and projected_abs_beat is not None
                and not self._flow_pattern.is_open(projected_abs_beat)
            ):
                highlights = []
            # Start/End exercise: paint the phrase's start (red) and end
            # (orange) on top of the Free Mode base. Only active during real
            # playback so the picks line up with the absolute-beat schedule.
            if (
                self._exercise_idx == 4
                and self._start_end_pattern is not None
                and projected_abs_beat is not None
            ):
                phrase = self._start_end_pattern.phrase_at(projected_abs_beat)
                if phrase is not None:
                    current_pcs = {n % 12 for n in projected_chord.scale_notes}
                    highlights = apply_start_end_highlight(
                        highlights,
                        phrase,
                        current_pcs,
                    )
            render_canonical(self._canonical_surface, highlights, self._keyboard_layout)
            warped = warp_canonical_to_projector(
                self._canonical_surface,
                self._homography,
                self._proj_size,
            )
            screen.blit(warped, (0, 0))

        self._proj_window.flip()

    def _render_hud(self, tl_state: TimelineState | None) -> None:
        """Render the HUD window."""
        if self._calibration_ui is not None:
            self._render_calibration_hud()
            return
        if self._rendering:
            self._render_loading_screen("Rendering audio")
            return
        surface = self._hud_window.get_surface()
        # Mirror whatever's actually driving playback — the temporary loop form
        # while looping, the original tune otherwise.
        active_ls = self._active_lead_sheet
        active_timeline = self._active_timeline
        pb_state = (
            active_timeline.playback_state if active_timeline else PlaybackState.STOPPED
        )
        gt_path_count = guide_tone_path_count(active_ls) if active_ls else 0
        render_hud(
            surface,
            active_ls,
            tl_state,
            pb_state,
            self._exercise_idx,
            self._tempo,
            self._metronome_on,
            backing_mode=_BACKING_LABELS[self._backing_mode],
            highlight_root=self._highlight_root,
            range_mode=_range_mode_label(self._range_mode),
            chord_tone_mode=self._chord_tone_mode.name,
            count_in_beat=self._get_count_in_beat(),
            count_in_total_beats=self._count_in_total_beats,
            frozen_mode=self._frozen_mode,
            frozen_chord_idx=self._frozen_chord_idx,
            guide_tone_path=self._guide_tone_path,
            guide_tone_path_count=gt_path_count,
            guide_tone_octave=self._guide_tone_octave,
            show_next_guide_tone=self._show_next_guide_tone,
            flow_phrasing=self._flow_phrasing.name,
            phrase_length=_phrase_length_label(self._phrase_length),
            window_width=_window_width_label(self._window_width),
            contour_speed=_contour_speed_label(self._contour_speed),
        )
        self._hud_window.flip()

    def _render_chart(self, tl_state: TimelineState | None) -> None:
        """Render the iReal Pro-style chord chart window."""
        surface = self._chart_window.get_surface()

        # Pick the beat to highlight: the frozen chord's start when frozen, the
        # live playhead while playing/paused, otherwise no cursor (static chart).
        # While looping, `tl_state` is the temp form's cursor — fold it back
        # onto the original tune's bars so the highlight tracks the real chart.
        highlight_beat: float | None = None
        if self._lead_sheet is not None:
            if self._frozen_mode:
                chords = self._lead_sheet.chords
                idx = max(0, min(self._frozen_chord_idx, len(chords) - 1))
                highlight_beat = chords[idx].start_beat
            elif (
                tl_state is not None
                and self._active_timeline is not None
                and self._active_timeline.playback_state
                in (PlaybackState.PLAYING, PlaybackState.PAUSED)
            ):
                if self._loop_region_bars is not None:
                    beats_per_bar = self._lead_sheet.time_signature[0]
                    start_bar, end_bar = self._loop_region_bars
                    loop_beats = (end_bar - start_bar) * beats_per_bar
                    highlight_beat = (
                        start_bar * beats_per_bar + tl_state.current_beat % loop_beats
                    )
                else:
                    highlight_beat = tl_state.current_beat

        # Loop band: the editable selection takes visual priority; once
        # confirmed, the active loop region is shown instead.
        loop_select = None
        loop_active = None
        if self._loop_select_active:
            loop_select = (
                self._loop_sel_start,
                self._loop_sel_start + self._loop_sel_len,
            )
        elif self._loop_region_bars is not None:
            loop_active = self._loop_region_bars

        render_chart(
            surface,
            self._lead_sheet,
            highlight_beat,
            loop_select=loop_select,
            loop_active=loop_active,
        )
        self._chart_window.flip()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    app = App()
    app.run()
