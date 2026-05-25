"""Application entry point: two-window Pygame loop with timeline sync.

Creates a fullscreen projection window on the secondary display and a
windowed HUD on the primary display.  Both are updated each frame from
the same :class:`~leadsheet_utility.timeline.Timeline` state.
"""

from __future__ import annotations

import logging
import sys
import threading
import time
from enum import Enum
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
from leadsheet_utility.backing.renderer import mix_layers, render_backing_track, render_layer
from leadsheet_utility.backing.walking_bass import generate_walking_bass
from leadsheet_utility.calibration import (
    DEFAULT_CALIBRATION_PATH,
    CalibrationUI,
    load_calibration,
    save_calibration,
)
from leadsheet_utility.exercises import (
    ChordToneMode,
    SmallMode,
    apply_chord_tone_highlight,
    apply_root_highlight,
    chord_tone_only_highlights,
    free_mode_highlights,
    next_chord_tone_mode,
    next_small_mode,
)
from leadsheet_utility.gui.hud import EXERCISE_NAMES, render_hud
from leadsheet_utility.gui.input import Action, key_to_action
from leadsheet_utility.harmony import analyze, midi_note_name, pc_name
from leadsheet_utility.leadsheet.models import ChordEvent, LeadSheet
from leadsheet_utility.leadsheet.parser import parse_leadsheet
from leadsheet_utility.projection import (
    DEFAULT_BLACK_HEIGHT_RATIO,
    DEFAULT_BLACK_WIDTH_RATIO,
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

_HUD_SIZE = (1200, 820)
_FPS = 60
_TEMPO_STEP = 5
_TEMPO_MIN = 40
_TEMPO_MAX = 320
_DEFAULT_SF_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "soundfonts" / "GeneralUser-GS.sf2"
_CANONICAL_SIZE = (1920, 200)
_SAMPLE_RATE = 44100

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


def _small_mode_label(mode: SmallMode) -> str:
    """Short HUD label for the small-mode cycle."""
    return {
        SmallMode.OFF: "OFF",
        SmallMode.ONE_OCTAVE: "1-OCT",
        SmallMode.TWO_OCTAVE: "2-OCT",
    }[mode]


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
        self._backing_mode: BackingMode = BackingMode.FULL
        self._highlight_root: bool = False
        self._small_mode: SmallMode = SmallMode.OFF
        self._chord_tone_mode: ChordToneMode = ChordToneMode.OFF

        # -- Frozen mode state ------------------------------------------------
        self._frozen_mode: bool = False
        self._frozen_chord_idx: int = 0

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

        elif action is Action.TOGGLE_FREE_SMALL:
            self._small_mode = next_small_mode(self._small_mode)
            logger.info("Small mode: %s", self._small_mode.name)

        elif action is Action.TOGGLE_CHORD_TONES:
            self._chord_tone_mode = next_chord_tone_mode(self._chord_tone_mode)
            logger.info("Chord-tone mode: %s", self._chord_tone_mode.name)

        elif action is Action.TOGGLE_FROZEN:
            self._toggle_frozen_mode()

        elif action is Action.FROZEN_PREV:
            self._frozen_step(-1)

        elif action is Action.FROZEN_NEXT:
            self._frozen_step(1)

        elif action.name.startswith("EXERCISE_"):
            idx = int(action.name[-1]) - 1
            if 0 <= idx < len(EXERCISE_NAMES):
                self._exercise_idx = idx

    # -- transport -----------------------------------------------------------

    def _toggle_play_pause(self) -> None:
        if self._timeline is None or self._lead_sheet is None:
            return

        # Frozen mode owns the projection and does not advance with audio.
        if self._frozen_mode:
            return

        # During count-in, treat play/pause as stop
        if self._count_in_active:
            self._stop_count_in()
            return

        # Ignore input while an async render is in flight
        if self._rendering:
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
            self._frozen_chord_idx + 1, len(self._lead_sheet.chords), chord.chord_symbol,
        )

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
            self._frozen_chord_idx + 1, n, chord.chord_symbol,
        )

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
            events, self._sf_path, self._count_in_total_beats, self._tempo,
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
        logger.info("Rendering backing layers (%.0f beats at %d BPM)...", total_beats, self._tempo)

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
        """Render each layer to its own int16 buffer on a background thread."""
        try:
            self._render_result = {
                name: render_layer(events, sf_path, total_beats, tempo)
                for name, events in layer_events.items()
            }
        except Exception:
            logger.exception("Backing-layer render failed")
            self._render_result = None

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

    def _mix_active_layers(self) -> np.ndarray:
        """Sum the currently-enabled layers into a single int16 buffer."""
        assert self._layers is not None
        active: list[np.ndarray] = []
        if self._backing_mode is not BackingMode.NONE:
            active.append(self._layers["drums"])
        if self._backing_mode in (BackingMode.DRUMS_BASS, BackingMode.FULL):
            active.append(self._layers["bass"])
        if self._backing_mode is BackingMode.FULL:
            active.append(self._layers["guitar"])
        if self._metronome_on:
            active.append(self._layers["metronome"])
        # All layers share the same length; pass it explicitly so NONE+no-metronome
        # still produces a buffer of the right duration (silence).
        total_samples = self._layers["drums"].size
        return mix_layers(active, total_samples=total_samples)

    def _remix_and_swap(self) -> None:
        """Rebuild the active mix and, if playing, splice it in mid-stream.

        Cheap (numpy add over int16 arrays) — the whole point of caching layers
        is that this never blocks on FluidSynth.  If the layers haven't been
        rendered yet (no playback has happened), this is a no-op; the next
        play() will render with the new state baked in.
        """
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
        """Minimal HUD while calibrating — directs the user to the projector."""
        surface = self._hud_window.get_surface()
        surface.fill((30, 30, 30))
        font = pygame.font.SysFont("consolas", 33)
        text = font.render(
            "Calibrating — see projector window", True, (220, 220, 220),
        )
        w, h = surface.get_size()
        surface.blit(text, ((w - text.get_width()) // 2, (h - text.get_height()) // 2))
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

        Sets `self._homography`, `self._keyboard_layout`. Black-key proportion
        ratios come from the saved calibration when present so the canonical
        layout matches the specific piano; otherwise the spec defaults are used.
        """
        cal = load_calibration()
        black_offsets: dict[int, tuple[float, float]] = {}
        if cal is not None and cal.projector_size == self._proj_size:
            self._homography = cal.homography()
            black_w = cal.black_width_ratio
            black_h = cal.black_height_ratio
            black_offsets = cal.black_key_offsets
            logger.info(
                "Loaded calibration (black ratios w=%.2f h=%.2f, %d per-key offsets)",
                black_w, black_h, len(black_offsets),
            )
        else:
            self._homography = make_default_homography(_CANONICAL_SIZE, self._proj_size)
            black_w = DEFAULT_BLACK_WIDTH_RATIO
            black_h = DEFAULT_BLACK_HEIGHT_RATIO
            if cal is None:
                logger.info("No calibration found — using default identity homography")
            else:
                logger.info(
                    "Calibration projector size mismatch (%s vs %s) — using default",
                    cal.projector_size, self._proj_size,
                )

        self._keyboard_layout = build_keyboard_layout(
            *_CANONICAL_SIZE,
            black_width_ratio=black_w,
            black_height_ratio=black_h,
            black_key_offsets=black_offsets,
        )

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

        projected_chord: ChordEvent | None = None
        if self._frozen_mode and self._lead_sheet is not None:
            chords = self._lead_sheet.chords
            if chords:
                idx = max(0, min(self._frozen_chord_idx, len(chords) - 1))
                projected_chord = chords[idx]
        else:
            timeline = self._timeline
            tl_state = timeline.get_state() if timeline else None
            playing = timeline is not None and timeline.playback_state is PlaybackState.PLAYING
            if playing and timeline is not None and tl_state is not None and not self._count_in_active:
                lead_beats = _PROJECTION_LEAD_SECONDS * (self._tempo / 60.0)
                projected_chord = timeline.chord_at(tl_state.current_beat + lead_beats)

        if projected_chord is not None:
            if self._chord_tone_mode is ChordToneMode.ONLY:
                highlights = chord_tone_only_highlights(projected_chord, small=self._small_mode)
            else:
                highlights = free_mode_highlights(projected_chord, small=self._small_mode)
                if self._chord_tone_mode is ChordToneMode.OVERLAY:
                    highlights = apply_chord_tone_highlight(highlights, projected_chord)
            # Root overlay applied last so the root keeps its own color
            # (root is always a chord tone).
            if self._highlight_root:
                highlights = apply_root_highlight(highlights, projected_chord)
            render_canonical(self._canonical_surface, highlights, self._keyboard_layout)
            warped = warp_canonical_to_projector(
                self._canonical_surface, self._homography, self._proj_size,
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
            backing_mode=_BACKING_LABELS[self._backing_mode],
            highlight_root=self._highlight_root,
            small_mode=_small_mode_label(self._small_mode),
            chord_tone_mode=self._chord_tone_mode.name,
            count_in_beat=self._get_count_in_beat(),
            count_in_total_beats=self._count_in_total_beats,
            frozen_mode=self._frozen_mode,
            frozen_chord_idx=self._frozen_chord_idx,
        )
        self._hud_window.flip()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    app = App()
    app.run()
