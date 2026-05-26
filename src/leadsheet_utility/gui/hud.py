"""Heads-up display rendering on the primary monitor.

Draws song info, current chord, exercise selection, transport controls,
and a progress bar onto the HUD pygame surface each frame.
"""

from __future__ import annotations

import pygame

from leadsheet_utility.calibration.ui import (
    CalibrationPhase,
    CalibrationSnapshot,
    RangeEndpoint,
)
from leadsheet_utility.exercises.free import RangeMode
from leadsheet_utility.leadsheet.models import LeadSheet
from leadsheet_utility.timeline import PlaybackState, TimelineState

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------

_BG = (30, 30, 30)
_TEXT = (220, 220, 220)
_DIM = (130, 130, 130)
_ACCENT = (100, 200, 120)
_BAR_BG = (60, 60, 60)
_BAR_FILL = (80, 180, 100)
_TITLE_BG = (45, 45, 45)
_COUNT_IN_EMPTY = (60, 60, 60)
_COUNT_IN_FILL = (60, 160, 80)
_COUNT_IN_ACCENT = (100, 200, 120)

# ---------------------------------------------------------------------------
# Vertical rhythm
# ---------------------------------------------------------------------------

_LINE_H = 32         # space between consecutive body lines inside a group
_HEADER_GAP = 36     # space between a SECTION title and the first content line
_SECTION_GAP = 36    # extra vertical air between sibling groups

# ---------------------------------------------------------------------------
# Exercise names
# ---------------------------------------------------------------------------

EXERCISE_NAMES: list[str] = [
    "Free",
    "Guide Tone",
    "Contour",
    "Flow",
    "Start/End",
]

# Per-exercise extra keys for the CONTROLS panel. Keyed by exercise index;
# entries are merged after the universal "[1-5] Select" line. Keep entries
# scoped to keys whose binding is only meaningful for that exercise — so
# the panel never advertises a key that does nothing in the current mode.
_EXERCISE_EXTRA_KEYS: dict[int, tuple[str, ...]] = {
    1: ("[H] GT path", "[Up/Dn] GT octave", "[N] Next GT preview"),  # Guide Tone
}

# ---------------------------------------------------------------------------
# Font cache (initialised on first call)
# ---------------------------------------------------------------------------

_fonts: dict[str, pygame.font.Font] = {}


def _get_fonts() -> dict[str, pygame.font.Font]:
    if not _fonts:
        _fonts["title"] = pygame.font.SysFont("consolas", 39, bold=True)
        _fonts["heading"] = pygame.font.SysFont("consolas", 30, bold=True)
        _fonts["section"] = pygame.font.SysFont("consolas", 30, bold=True)
        _fonts["body"] = pygame.font.SysFont("consolas", 27)
        _fonts["small"] = pygame.font.SysFont("consolas", 20)
        _fonts["small_bold"] = pygame.font.SysFont("consolas", 20, bold=True)
    return _fonts


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def render_hud(
    surface: pygame.Surface,
    lead_sheet: LeadSheet | None,
    timeline_state: TimelineState | None,
    playback_state: PlaybackState,
    exercise_idx: int,
    tempo: int,
    metronome_on: bool = False,
    backing_mode: str = "FULL",
    highlight_root: bool = False,
    range_mode: str = "FULL",
    chord_tone_mode: str = "OFF",
    count_in_beat: float | None = None,
    count_in_total_beats: int = 0,
    frozen_mode: bool = False,
    frozen_chord_idx: int = 0,
    guide_tone_path: int = 0,
    guide_tone_path_count: int = 0,
    guide_tone_octave: int = 0,
    show_next_guide_tone: bool = False,
) -> None:
    """Draw the full HUD onto *surface*.  Called once per frame."""
    fonts = _get_fonts()
    surface.fill(_BG)
    w, h = surface.get_size()
    y = 0

    # -- Count-in overlay (covers the whole HUD) -----------------------------
    if count_in_beat is not None and count_in_total_beats > 0:
        _render_count_in(surface, fonts, count_in_beat, count_in_total_beats)
        return

    # -- Title bar -----------------------------------------------------------
    pygame.draw.rect(surface, _TITLE_BG, (0, 0, w, 60))
    _blit(surface, fonts["title"], "leadsheet-utility", 20, 10, _TEXT)
    y = 90

    if lead_sheet is None:
        _blit(surface, fonts["body"], "No lead sheet loaded.", 20, y, _DIM)
        y += 40
        _blit(surface, fonts["body"], 'Press O to open a .tsv file.', 20, y, _DIM)
        y += 75
        _render_shortcuts(surface, fonts, y, exercise_idx)
        return

    # -- Song info -----------------------------------------------------------
    # The song title doubles as the section header (no separate "SONG" label).
    song_line = f"{lead_sheet.title} (by {lead_sheet.composer})".upper()
    _blit(surface, fonts["section"], song_line, 20, y, _TEXT)
    y += _HEADER_GAP

    ts = lead_sheet.time_signature
    info = f"Key: {lead_sheet.key}    Time: {ts[0]}/{ts[1]}    Tempo: {tempo} BPM"
    _blit(surface, fonts["body"], info, 20, y, _DIM)
    y += _LINE_H

    # -- Current / next chord (no extra gap — same SONG block) ---------------
    if frozen_mode:
        chords = lead_sheet.chords
        idx = max(0, min(frozen_chord_idx, len(chords) - 1))
        chord = chords[idx]
        cur_line = (
            f"Current: {chord.chord_symbol}  "
            f"(bar {chord.bar_number}/{lead_sheet.total_bars})  "
            f"[FROZEN {idx + 1}/{len(chords)}]"
        )
        _blit(surface, fonts["body"], cur_line, 20, y, _DIM)
        y += _LINE_H
        nxt = chords[(idx + 1) % len(chords)].chord_symbol if chords else "--"
        _blit(surface, fonts["body"], f"Next:    {nxt}", 20, y, _DIM)
        y += _LINE_H + _SECTION_GAP
    elif timeline_state is not None:
        chord = timeline_state.current_chord
        bar = chord.bar_number
        total_bars = lead_sheet.total_bars
        form_rep = timeline_state.form_repeat + 1
        form_total = lead_sheet.form_repeats

        cur_line = (
            f"Current: {chord.chord_symbol}  "
            f"(bar {bar}/{total_bars})  "
            f"[Form {form_rep}/{form_total}]"
        )
        _blit(surface, fonts["body"], cur_line, 20, y, _DIM)
        y += _LINE_H

        # Next chord
        chords = lead_sheet.chords
        idx = chords.index(chord)
        if idx + 1 < len(chords):
            nxt = chords[idx + 1].chord_symbol
        elif form_rep < form_total:
            nxt = chords[0].chord_symbol
        else:
            nxt = "--"
        _blit(surface, fonts["body"], f"Next:    {nxt}", 20, y, _DIM)
        y += _LINE_H + _SECTION_GAP
    else:
        _blit(surface, fonts["body"], f"Current: {lead_sheet.chords[0].chord_symbol}", 20, y, _DIM)
        y += _LINE_H + _SECTION_GAP

    # -- Exercise selection --------------------------------------------------
    _blit(surface, fonts["section"], "PROJECTION EXERCICES", 20, y, _TEXT)
    y += _HEADER_GAP
    _render_exercises(surface, fonts, exercise_idx, y)
    y += 2 * _LINE_H + _SECTION_GAP

    # -- Transport / progress ------------------------------------------------
    _blit(surface, fonts["section"], "PLAYBACK", 20, y, _TEXT)
    y += _HEADER_GAP
    if frozen_mode:
        status_label = "FROZEN"
    else:
        status_label = {
            PlaybackState.STOPPED: "STOPPED",
            PlaybackState.PLAYING: "PLAYING",
            PlaybackState.PAUSED: "PAUSED",
        }[playback_state]
    met_label = "ON" if metronome_on else "OFF"
    root_label = "ON" if highlight_root else "OFF"
    range_label = range_mode  # FULL / 2 OCT / 1 OCT
    tones_label = chord_tone_mode  # OFF / ONLY / OVERLAY
    status_grid = [
        [("Status", status_label), ("Metronome", met_label), ("Backing", backing_mode)],
        [("Root", root_label), ("Range", range_label), ("Chord tones", tones_label)],
    ]
    if exercise_idx == 1 and guide_tone_path_count > 0:
        gt_label = f"{guide_tone_path + 1}/{guide_tone_path_count}"
        oct_label = f"{guide_tone_octave:+d}"
        next_label = "ON" if show_next_guide_tone else "OFF"
        status_grid.append([
            ("GT path", gt_label),
            ("GT octave", oct_label),
            ("Next GT", next_label),
        ])
    col_x = [20, 310, 600]
    for row in status_grid:
        for (key, val), x in zip(row, col_x):
            _blit(surface, fonts["body"], f"{key}: {val}", x, y, _ACCENT)
        y += 32
    y += 23

    # Progress bar
    if timeline_state is not None and lead_sheet is not None:
        progress = _compute_progress(timeline_state, lead_sheet)
    else:
        progress = 0.0
    _render_progress_bar(surface, 20, y, w - 40, 24, progress)
    y += 24 + _SECTION_GAP

    # -- Keyboard shortcuts --------------------------------------------------
    _blit(surface, fonts["section"], "CONTROLS", 20, y, _TEXT)
    y += _HEADER_GAP
    _render_shortcuts(surface, fonts, y, exercise_idx)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _blit(
    surface: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    x: int,
    y: int,
    color: tuple[int, int, int],
) -> None:
    rendered = font.render(text, True, color)
    surface.blit(rendered, (x, y))


def _render_count_in(
    surface: pygame.Surface,
    fonts: dict[str, pygame.font.Font],
    count_in_beat: float,
    total_count_in_beats: int,
) -> None:
    """Draw a two-row grid of squares that fill in one-by-one during count-in."""
    w, h = surface.get_size()
    filled = min(int(count_in_beat) + 1, total_count_in_beats)  # +1: fill on the beat, not after

    beats_per_bar = total_count_in_beats // 2
    sq_size = 90
    gap = 24

    # Two rows, beats_per_bar squares each
    grid_w = beats_per_bar * sq_size + (beats_per_bar - 1) * gap
    row_h = sq_size * 2 + gap
    x_start = (w - grid_w) // 2
    y_start = (h - row_h) // 2

    # Title
    title = "Get Ready..."
    _blit(surface, fonts["heading"], title, (w - fonts["heading"].size(title)[0]) // 2, y_start - 75, _TEXT)

    for i in range(total_count_in_beats):
        row = i // beats_per_bar
        col = i % beats_per_bar
        x = x_start + col * (sq_size + gap)
        y = y_start + row * (sq_size + gap)
        if i < filled:
            color = _COUNT_IN_ACCENT if col == 0 else _COUNT_IN_FILL
            pygame.draw.rect(surface, color, (x, y, sq_size, sq_size))
        else:
            pygame.draw.rect(surface, _COUNT_IN_EMPTY, (x, y, sq_size, sq_size))
        pygame.draw.rect(surface, _DIM, (x, y, sq_size, sq_size), 2)

    # Beat number below the grid
    beat_label = str(filled) if filled <= total_count_in_beats else ""
    if beat_label:
        _blit(
            surface, fonts["heading"], beat_label,
            (w - fonts["heading"].size(beat_label)[0]) // 2,
            y_start + row_h + 21,
            _ACCENT,
        )


def _render_exercises(
    surface: pygame.Surface,
    fonts: dict[str, pygame.font.Font],
    active_idx: int,
    y: int,
) -> None:
    x = 20
    font = fonts["body"]
    for i, name in enumerate(EXERCISE_NAMES):
        label = f"[{i + 1}] {name}"
        color = _ACCENT if i == active_idx else _DIM
        _blit(surface, font, label, x, y, color)
        x += font.size(label)[0] + 24
        if i == 2:
            # Wrap to second row
            y += 32
            x = 20


def _render_progress_bar(
    surface: pygame.Surface,
    x: int,
    y: int,
    width: int,
    height: int,
    progress: float,
) -> None:
    pygame.draw.rect(surface, _BAR_BG, (x, y, width, height))
    fill_w = int(width * max(0.0, min(1.0, progress)))
    if fill_w > 0:
        pygame.draw.rect(surface, _BAR_FILL, (x, y, fill_w, height))


def _render_shortcuts(
    surface: pygame.Surface,
    fonts: dict[str, pygame.font.Font],
    y: int,
    exercise_idx: int = 0,
) -> None:
    font = fonts["small"]
    line_h = 30

    # Generic select + only this exercise's specific keys, so the panel
    # never advertises a key that does nothing in the current mode.
    exercise_lines = ["[1-5] Select"]
    exercise_lines.extend(_EXERCISE_EXTRA_KEYS.get(exercise_idx, ()))

    columns: list[tuple[str, list[str]]] = [
        (
            "TRANSPORT",
            [
                "[SPACE] Play/Pause",
                "[S] Stop",
                "[+/-] Tempo",
                "[O] Open file",
                "[Q] Quit",
            ],
        ),
        ("CALIBRATION", ["[C] Calibrate"]),
        ("BACKING", ["[M] Metronome", "[G] Cycle backing"]),
        ("DISPLAY", ["[R] Root highlight", "[B] Range", "[T] Chord tones"]),
        ("FROZEN", ["[F] Frozen mode", "[<-/->] Step chord"]),
        ("EXERCISE", exercise_lines),
    ]

    w = surface.get_width()
    margin = 20
    col_w = (w - 2 * margin) // len(columns)

    for i, (title, items) in enumerate(columns):
        x = margin + i * col_w
        cy = y
        _blit(surface, fonts["small_bold"], title, x, cy, _TEXT)
        cy += line_h
        for line in items:
            _blit(surface, font, line, x, cy, _DIM)
            cy += line_h


def _compute_progress(state: TimelineState, lead_sheet: LeadSheet) -> float:
    total = lead_sheet.total_beats * lead_sheet.form_repeats
    current = state.form_repeat * lead_sheet.total_beats + state.current_beat
    return current / total if total > 0 else 0.0


# ---------------------------------------------------------------------------
# Calibration HUD mirror
# ---------------------------------------------------------------------------


_PHASE_LABELS: dict[CalibrationPhase, str] = {
    CalibrationPhase.RANGE_EDIT: "1/5 — FULL range (projector reach)",
    CalibrationPhase.MAIN: "2/5 — Markers & ratios",
    CalibrationPhase.BLACK_KEY_TUNE: "3/5 — Per-key offsets",
    CalibrationPhase.BAND_EDIT: "4/5 — 1-OCT / 2-OCT exercise bands",
    CalibrationPhase.AUDIO_DELAY: "5/5 — Audio delay",
}

_RANGE_LABELS: dict[RangeMode, str] = {
    RangeMode.FULL: "FULL",
    RangeMode.TWO_OCTAVE: "2-OCT",
    RangeMode.ONE_OCTAVE: "1-OCT",
}


def _midi_note_label(midi: int) -> str:
    """Render a MIDI note as 'C4', 'F#3' etc. for HUD readability."""
    names = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
    octave = (midi // 12) - 1
    return f"{names[midi % 12]}{octave}"


def render_calibration_hud(
    surface: pygame.Surface,
    snapshot: CalibrationSnapshot,
) -> None:
    """Mirror the calibration UI state onto the HUD window.

    The projector overlay is hard to read from across the room, so the HUD
    repeats the phase, the value being edited, and the keybind cheat sheet
    here in a comfortable size.
    """
    fonts = _get_fonts()
    surface.fill(_BG)
    w, _ = surface.get_size()

    # -- Title bar -----------------------------------------------------------
    pygame.draw.rect(surface, _TITLE_BG, (0, 0, w, 60))
    _blit(surface, fonts["title"], "Calibrating", 20, 10, _TEXT)
    y = 90

    _blit(surface, fonts["section"], "PHASE", 20, y, _TEXT)
    y += _HEADER_GAP
    _blit(surface, fonts["body"], _PHASE_LABELS[snapshot.phase], 20, y, _ACCENT)
    y += _LINE_H + _SECTION_GAP

    # -- Phase-specific values ----------------------------------------------
    _blit(surface, fonts["section"], "EDITING", 20, y, _TEXT)
    y += _HEADER_GAP
    for line in _calibration_value_lines(snapshot):
        _blit(surface, fonts["body"], line, 20, y, _ACCENT)
        y += _LINE_H
    y += _SECTION_GAP

    # -- Persistent fields (always shown so the user sees current state) ----
    _blit(surface, fonts["section"], "CURRENT VALUES", 20, y, _TEXT)
    y += _HEADER_GAP
    full_low, full_high = snapshot.full_range
    two_low, two_high = snapshot.two_octave_range
    one_low, one_high = snapshot.one_octave_range
    rows = [
        f"FULL    {_midi_note_label(full_low)} - {_midi_note_label(full_high)}"
        f"  (MIDI {full_low}-{full_high})",
        f"2-OCT   {_midi_note_label(two_low)} - {_midi_note_label(two_high)}"
        f"  (MIDI {two_low}-{two_high})",
        f"1-OCT   {_midi_note_label(one_low)} - {_midi_note_label(one_high)}"
        f"  (MIDI {one_low}-{one_high})",
        f"Audio delay: {snapshot.audio_delay_ms:+d} ms",
        f"Black-key ratios: width={snapshot.black_width_ratio:.2f}  "
        f"height={snapshot.black_height_ratio:.2f}",
    ]
    for line in rows:
        _blit(surface, fonts["body"], line, 20, y, _DIM)
        y += _LINE_H
    y += _SECTION_GAP

    # -- Keybind cheat sheet -------------------------------------------------
    _blit(surface, fonts["section"], "KEYS (this phase)", 20, y, _TEXT)
    y += _HEADER_GAP
    _render_calibration_keys(surface, fonts, snapshot.phase, y)


def _calibration_value_lines(snapshot: CalibrationSnapshot) -> list[str]:
    """Per-phase 'what am I editing right now' lines."""
    if snapshot.phase is CalibrationPhase.MAIN:
        mx, my = snapshot.marker_pos
        return [
            f"Marker: {snapshot.active_marker_label} "
            f"({snapshot.active_marker_idx + 1}/{snapshot.marker_count})",
            f"Position: ({mx:.0f}, {my:.0f}) px",
            f"Black-key ratios: width={snapshot.black_width_ratio:.2f}  "
            f"height={snapshot.black_height_ratio:.2f}",
        ]
    if snapshot.phase is CalibrationPhase.RANGE_EDIT:
        low, high = snapshot.full_range
        endpoint = "LOW" if snapshot.active_endpoint is RangeEndpoint.LOW else "HIGH"
        return [
            "Editing FULL range (projector reach)",
            f"Editing endpoint: {endpoint}",
            f"Low:  {_midi_note_label(low)}  (MIDI {low})",
            f"High: {_midi_note_label(high)}  (MIDI {high})",
        ]
    if snapshot.phase is CalibrationPhase.BAND_EDIT:
        mode = snapshot.active_range_mode
        if mode is RangeMode.TWO_OCTAVE:
            low, high = snapshot.two_octave_range
        else:
            low, high = snapshot.one_octave_range
        endpoint = "LOW" if snapshot.active_endpoint is RangeEndpoint.LOW else "HIGH"
        full_low, full_high = snapshot.full_range
        return [
            f"Active band: {_RANGE_LABELS[mode]}",
            f"Editing endpoint: {endpoint}",
            f"Low:  {_midi_note_label(low)}  (MIDI {low})",
            f"High: {_midi_note_label(high)}  (MIDI {high})",
            f"Clipped to FULL: {_midi_note_label(full_low)} - {_midi_note_label(full_high)}",
        ]
    if snapshot.phase is CalibrationPhase.AUDIO_DELAY:
        return [
            f"Audio delay: {snapshot.audio_delay_ms:+d} ms",
            "Positive = projection lags audio.",
        ]
    # BLACK_KEY_TUNE
    if snapshot.active_black_midi is None:
        return ["(no black keys in range)"]
    ox, oy = snapshot.active_black_offset
    return [
        f"Black key {snapshot.active_black_idx + 1}/{snapshot.black_key_count}: "
        f"{_midi_note_label(snapshot.active_black_midi)} "
        f"(MIDI {snapshot.active_black_midi})",
        f"Offset: dx={ox:+.0f} px   dy={oy:+.0f} px",
    ]


def _render_calibration_keys(
    surface: pygame.Surface,
    fonts: dict[str, pygame.font.Font],
    phase: CalibrationPhase,
    y: int,
) -> None:
    columns: list[tuple[str, list[str]]]
    if phase is CalibrationPhase.RANGE_EDIT:
        columns = [
            (
                "FULL RANGE",
                [
                    "[Tab] Switch low/high endpoint",
                    "[Left/Right] Nudge by white key",
                    "[Shift+Arrow] Octave step",
                    "[R] Reset to defaults",
                ],
            ),
            (
                "PHASE",
                ["[Enter] Next (markers)", "[Esc] Cancel"],
            ),
        ]
    elif phase is CalibrationPhase.BAND_EDIT:
        columns = [
            (
                "EXERCISE BANDS",
                [
                    "[B] Switch 1-OCT / 2-OCT",
                    "[Tab] Switch low/high endpoint",
                    "[Left/Right] Nudge by white key",
                    "[Shift+Arrow] Octave step",
                    "[R] Reset active band",
                ],
            ),
            (
                "PHASE",
                ["[Enter] Next (audio delay)", "[Esc] Cancel"],
            ),
        ]
    elif phase is CalibrationPhase.MAIN:
        columns = [
            (
                "MARKERS",
                [
                    "[Drag/Arrows] Move",
                    "[Tab / 1-4] Select",
                    "[Shift+Arrow] x10",
                    "[R] Reset",
                ],
            ),
            (
                "RATIOS",
                [
                    "[Q/W] Width -/+",
                    "[A/S] Height -/+",
                    "[Shift] x5",
                ],
            ),
            (
                "PHASE",
                ["[Enter] Next (per-key)", "[Esc] Cancel"],
            ),
        ]
    elif phase is CalibrationPhase.BLACK_KEY_TUNE:
        columns = [
            (
                "PER-KEY OFFSETS",
                [
                    "[Tab / Shift+Tab] Next / prev key",
                    "[Arrows] Nudge",
                    "[Shift+Arrow] x10",
                    "[R] Reset all offsets",
                ],
            ),
            (
                "PHASE",
                ["[Enter] Next (bands)", "[Esc] Cancel"],
            ),
        ]
    else:  # AUDIO_DELAY
        columns = [
            (
                "AUDIO DELAY",
                [
                    "[Up/Down] +/- 1 ms",
                    "[Shift+Up/Dn] +/- 10 ms",
                    "[R] Reset to 0",
                ],
            ),
            (
                "PHASE",
                ["[Enter] Confirm & save", "[Esc] Cancel"],
            ),
        ]

    font = fonts["small"]
    line_h = 30
    w = surface.get_width()
    margin = 20
    col_w = (w - 2 * margin) // max(1, len(columns))
    for i, (title, items) in enumerate(columns):
        x = margin + i * col_w
        cy = y
        _blit(surface, fonts["small_bold"], title, x, cy, _TEXT)
        cy += line_h
        for line in items:
            _blit(surface, font, line, x, cy, _DIM)
            cy += line_h
