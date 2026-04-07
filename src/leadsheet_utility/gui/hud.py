"""Heads-up display rendering on the primary monitor.

Draws song info, current chord, exercise selection, transport controls,
and a progress bar onto the HUD pygame surface each frame.
"""

from __future__ import annotations

import pygame

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
# Exercise names
# ---------------------------------------------------------------------------

EXERCISE_NAMES: list[str] = [
    "Free",
    "Guide Tone",
    "Contour",
    "Flow",
    "Start/End",
]

# ---------------------------------------------------------------------------
# Font cache (initialised on first call)
# ---------------------------------------------------------------------------

_fonts: dict[str, pygame.font.Font] = {}


def _get_fonts() -> dict[str, pygame.font.Font]:
    if not _fonts:
        _fonts["title"] = pygame.font.SysFont("consolas", 26, bold=True)
        _fonts["heading"] = pygame.font.SysFont("consolas", 20, bold=True)
        _fonts["body"] = pygame.font.SysFont("consolas", 18)
        _fonts["small"] = pygame.font.SysFont("consolas", 15)
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
    count_in_beat: float | None = None,
    count_in_total_beats: int = 0,
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
    pygame.draw.rect(surface, _TITLE_BG, (0, 0, w, 40))
    _blit(surface, fonts["title"], "leadsheet-utility", 14, 7, _TEXT)
    y = 50

    if lead_sheet is None:
        _blit(surface, fonts["body"], "No lead sheet loaded.", 14, y, _DIM)
        y += 26
        _blit(surface, fonts["body"], 'Press O to open a .tsv file.', 14, y, _DIM)
        y += 50
        _render_shortcuts(surface, fonts, y)
        return

    # -- Song info -----------------------------------------------------------
    song_line = f"{lead_sheet.title}  --  {lead_sheet.composer}"
    _blit(surface, fonts["heading"], song_line, 14, y, _TEXT)
    y += 28

    ts = lead_sheet.time_signature
    info = f"Key: {lead_sheet.key}    Time: {ts[0]}/{ts[1]}    Tempo: {tempo} BPM"
    _blit(surface, fonts["body"], info, 14, y, _DIM)
    y += 34

    # -- Current / next chord ------------------------------------------------
    if timeline_state is not None:
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
        _blit(surface, fonts["heading"], cur_line, 14, y, _TEXT)
        y += 26

        # Next chord
        chords = lead_sheet.chords
        idx = chords.index(chord)
        if idx + 1 < len(chords):
            nxt = chords[idx + 1].chord_symbol
        elif form_rep < form_total:
            nxt = chords[0].chord_symbol
        else:
            nxt = "--"
        _blit(surface, fonts["body"], f"Next:    {nxt}", 14, y, _DIM)
        y += 34
    else:
        _blit(surface, fonts["body"], f"Current: {lead_sheet.chords[0].chord_symbol}", 14, y, _DIM)
        y += 34

    # -- Exercise selection --------------------------------------------------
    _render_exercises(surface, fonts, exercise_idx, y)
    y += 60

    # -- Transport / progress ------------------------------------------------
    status_label = {
        PlaybackState.STOPPED: "STOPPED",
        PlaybackState.PLAYING: "PLAYING",
        PlaybackState.PAUSED: "PAUSED",
    }[playback_state]
    met_label = "ON" if metronome_on else "OFF"
    _blit(surface, fonts["body"], f"Status: {status_label}    Metronome: {met_label}", 14, y, _ACCENT)
    y += 30

    # Progress bar
    if timeline_state is not None and lead_sheet is not None:
        progress = _compute_progress(timeline_state, lead_sheet)
    else:
        progress = 0.0
    _render_progress_bar(surface, 14, y, w - 28, 16, progress)
    y += 34

    # -- Keyboard shortcuts --------------------------------------------------
    _render_shortcuts(surface, fonts, y)


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
    sq_size = 60
    gap = 16

    # Two rows, beats_per_bar squares each
    grid_w = beats_per_bar * sq_size + (beats_per_bar - 1) * gap
    row_h = sq_size * 2 + gap
    x_start = (w - grid_w) // 2
    y_start = (h - row_h) // 2

    # Title
    title = "Get Ready..."
    _blit(surface, fonts["heading"], title, (w - fonts["heading"].size(title)[0]) // 2, y_start - 50, _TEXT)

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
            y_start + row_h + 14,
            _ACCENT,
        )


def _render_exercises(
    surface: pygame.Surface,
    fonts: dict[str, pygame.font.Font],
    active_idx: int,
    y: int,
) -> None:
    x = 14
    font = fonts["body"]
    for i, name in enumerate(EXERCISE_NAMES):
        label = f"[{i + 1}] {name}"
        color = _ACCENT if i == active_idx else _DIM
        _blit(surface, font, label, x, y, color)
        x += font.size(label)[0] + 16
        if i == 2:
            # Wrap to second row
            y += 24
            x = 14


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
) -> None:
    font = fonts["small"]
    shortcuts = [
        "[SPACE] Play/Pause    [S] Stop",
        "[+/-] Tempo           [O] Open file",
        "[M] Metronome         [C] Calibrate",
        "[Q] Quit",
    ]
    for line in shortcuts:
        _blit(surface, font, line, 14, y, _DIM)
        y += 20


def _compute_progress(state: TimelineState, lead_sheet: LeadSheet) -> float:
    total = lead_sheet.total_beats * lead_sheet.form_repeats
    current = state.form_repeat * lead_sheet.total_beats + state.current_beat
    return current / total if total > 0 else 0.0
