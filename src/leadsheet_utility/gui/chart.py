"""iReal Pro-style chord chart window.

Renders the whole form as a bar grid — four bars per row — auto-scaled so a
typical 32-bar form (or longer) always fits one screen with no scrolling.
Chords are quantized to quarter-note slots inside each bar, so a measure can
hold up to four chords at maximum tightness. The chord cell currently being
played is highlighted; the highlight advances bar-by-bar through measures that
hold a chord sustained across barlines.

The lead sheets here carry no section data (no rehearsal letters, repeat
brackets, or endings — see ``.meta.json``), so this is a clean chord grid
rather than a full iReal Pro reproduction.
"""

from __future__ import annotations

import math

import pygame

from leadsheet_utility.leadsheet.models import ChordEvent, LeadSheet

# ---------------------------------------------------------------------------
# Colours (dark theme, matching the HUD window)
# ---------------------------------------------------------------------------

_BG = (30, 30, 30)
_INK = (190, 190, 190)
_BARLINE = (110, 110, 110)
_DIVIDER = (70, 70, 70)
_HIGHLIGHT = (100, 200, 120)  # matches the HUD accent green
_HIGHLIGHT_INK = (20, 28, 22)  # dark text for contrast on the bright fill
_TITLE = (220, 220, 220)
_TITLE_BG = (45, 45, 45)
_DIM = (130, 130, 130)
_LOOP_SELECT = (230, 180, 70)  # amber band while editing the selection
_LOOP_ACTIVE = (90, 170, 230)  # blue band once the loop is confirmed

BARS_PER_ROW = 4

# ---------------------------------------------------------------------------
# Font cache (keyed by point size + weight)
# ---------------------------------------------------------------------------

_fonts: dict[tuple[int, bool], pygame.font.Font] = {}


def _font(size: int, bold: bool = False) -> pygame.font.Font:
    key = (size, bold)
    cached = _fonts.get(key)
    if cached is None:
        cached = pygame.font.SysFont("consolas", size, bold=bold)
        _fonts[key] = cached
    return cached


# ---------------------------------------------------------------------------
# Chord symbol formatting
# ---------------------------------------------------------------------------

# Jazz glyphs (all present in Consolas).
_DELTA_SYM = "Δ"  # Δ  major 7
_HALFDIM_SYM = "ø"  # ø  half-diminished
_DIM_SYM = "°"  # °  diminished

# Quality-token substitutions, applied in order so compound qualities like
# "minmaj7" → "mΔ7" and "maj7#11" → "Δ7#11" fold correctly. The more specific
# tokens (hdim7, dim7) must come before their shorter prefixes.
_QUALITY_SUBS: tuple[tuple[str, str], ...] = (
    ("hdim7", _HALFDIM_SYM + "7"),
    ("dim7", _DIM_SYM + "7"),
    ("dim", _DIM_SYM),
    ("min", "m"),
    ("maj7", _DELTA_SYM + "7"),
    ("maj", ""),  # bare major triad → just the root
    ("aug", "+"),
)


def _format_chord(symbol: str) -> str:
    """Turn a raw ``Root:quality(ext)/bass`` symbol into a compact chart label."""
    if ":" not in symbol:
        return symbol
    root, rest = symbol.split(":", 1)

    bass = ""
    if "/" in rest:
        rest, tail = rest.split("/", 1)
        bass = "/" + tail

    ext = ""
    if "(" in rest:
        qi = rest.index("(")
        ext = rest[qi:]
        rest = rest[:qi]

    quality = rest
    for token, glyph in _QUALITY_SUBS:
        quality = quality.replace(token, glyph)

    return f"{root}{quality}{ext}{bass}"


# ---------------------------------------------------------------------------
# Per-bar cell tiling
# ---------------------------------------------------------------------------

# A cell is a horizontal slice of one bar: (frac_start, frac_end, chord_or_None).
# ``chord is None`` marks a continuation region where a chord sustained from an
# earlier bar/slot is still sounding but no symbol is printed.
_Cell = tuple[float, float, ChordEvent | None]


def _bar_cells(lead_sheet: LeadSheet, bar_idx: int, beats_per_bar: int) -> list[_Cell]:
    """Tile one bar into quarter-note-quantized chord cells covering [0, 1)."""
    bar_start = bar_idx * beats_per_bar
    bar_end = bar_start + beats_per_bar

    # Collect chords that *start* inside this bar, quantized to quarter slots.
    starts: list[tuple[int, ChordEvent]] = []
    prev_slot = -1
    for ch in lead_sheet.chords:
        if bar_start <= ch.start_beat < bar_end:
            slot = round(ch.start_beat - bar_start)
            slot = max(0, min(slot, beats_per_bar - 1))
            if slot <= prev_slot:  # keep slots strictly increasing → positive width
                slot = min(prev_slot + 1, beats_per_bar - 1)
            starts.append((slot, ch))
            prev_slot = slot

    if not starts:
        # Whole bar is a continuation of a chord held over from an earlier bar.
        return [(0.0, 1.0, None)]

    cells: list[_Cell] = []
    # Region before the first chord-start belongs to the held-over chord.
    if starts[0][0] > 0:
        cells.append((0.0, starts[0][0] / beats_per_bar, None))
    for i, (slot, ch) in enumerate(starts):
        frac_start = slot / beats_per_bar
        frac_end = starts[i + 1][0] / beats_per_bar if i + 1 < len(starts) else 1.0
        cells.append((frac_start, frac_end, ch))
    return cells


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def render_chart(
    surface: pygame.Surface,
    lead_sheet: LeadSheet | None,
    highlight_beat: float | None,
    *,
    loop_select: tuple[int, int] | None = None,
    loop_active: tuple[int, int] | None = None,
) -> None:
    """Draw the full chord chart onto *surface*.

    Parameters
    ----------
    surface:
        Target surface (the chart window's surface).
    lead_sheet:
        Parsed lead sheet, or ``None`` when nothing is loaded.
    highlight_beat:
        Absolute beat position within one form (0 .. total_beats) to highlight,
        or ``None`` to draw the static chart with no playback cursor.
    loop_select:
        ``(start_bar, end_bar_exclusive)`` of the loop band currently being
        edited, drawn in amber, or ``None``.
    loop_active:
        ``(start_bar, end_bar_exclusive)`` of a confirmed/running loop, drawn
        in blue, or ``None``. Ignored when *loop_select* is set.
    """
    surface.fill(_BG)
    w, h = surface.get_size()

    margin = 24
    band_h = 56

    # -- Title band (mirrors the HUD's grey header strip) --------------------
    pygame.draw.rect(surface, _TITLE_BG, (0, 0, w, band_h))

    if lead_sheet is None or not lead_sheet.chords:
        surface.blit(_font(30, bold=True).render("Chart", True, _TITLE), (margin, 11))
        surface.blit(
            _font(24).render("No lead sheet loaded.", True, _DIM),
            (margin, band_h + 24),
        )
        return

    beats_per_bar = lead_sheet.time_signature[0]
    total_bars = lead_sheet.total_bars
    if total_bars <= 0:
        return
    rows = math.ceil(total_bars / BARS_PER_ROW)

    header_h = band_h + 8

    # -- Title ---------------------------------------------------------------
    title = f"{lead_sheet.title}  —  {lead_sheet.key}"
    surface.blit(_font(30, bold=True).render(title, True, _TITLE), (margin, 11))

    # -- Grid geometry (auto-scaled to fit) ----------------------------------
    grid_x = margin
    grid_y = header_h
    grid_w = w - 2 * margin
    grid_h = h - header_h - margin
    bar_w = grid_w / BARS_PER_ROW
    row_h = grid_h / rows

    # Chord font scales with the row height but is capped so four chords still
    # fit side by side in one bar; per-cell shrink below handles long symbols.
    chord_size = max(12, min(int(row_h * 0.40), int(bar_w * 0.24), 46))

    # -- Resolve the highlighted bar / fraction ------------------------------
    hl_bar: int | None = None
    hl_frac = 0.0
    if highlight_beat is not None:
        hb = int(highlight_beat // beats_per_bar)
        if 0 <= hb < total_bars:
            hl_bar = hb
            hl_frac = (highlight_beat - hb * beats_per_bar) / beats_per_bar

    # -- Draw bars -----------------------------------------------------------
    for bar_idx in range(total_bars):
        row = bar_idx // BARS_PER_ROW
        col = bar_idx % BARS_PER_ROW
        x = grid_x + col * bar_w
        y = grid_y + row * row_h
        cells = _bar_cells(lead_sheet, bar_idx, beats_per_bar)

        # Index of the active cell in this bar (the one under the playhead).
        active_cell = -1
        if hl_bar == bar_idx:
            for ci, (frac_start, frac_end, _ch) in enumerate(cells):
                if frac_start <= hl_frac < frac_end:
                    active_cell = ci
                    hx = int(x + frac_start * bar_w) + 2
                    hw = int((frac_end - frac_start) * bar_w) - 3
                    pygame.draw.rect(
                        surface, _HIGHLIGHT, (hx, int(y) + 2, hw, int(row_h) - 4)
                    )
                    break

        # Cell dividers + chord labels.
        for ci, (frac_start, frac_end, ch) in enumerate(cells):
            cx = x + frac_start * bar_w
            if ci > 0:
                pygame.draw.line(
                    surface,
                    _DIVIDER,
                    (int(cx), int(y) + 6),
                    (int(cx), int(y + row_h) - 6),
                    1,
                )
            if ch is None:
                continue
            label = _format_chord(ch.chord_symbol)
            cell_w = (frac_end - frac_start) * bar_w
            font = _font(chord_size)
            if font.size(label)[0] > cell_w - 8:
                s = chord_size
                while s > 11 and _font(s).size(label)[0] > cell_w - 8:
                    s -= 2
                font = _font(s)
            ink = _HIGHLIGHT_INK if ci == active_cell else _INK
            txt = font.render(label, True, ink)
            surface.blit(txt, (int(cx) + 6, int(y + (row_h - txt.get_height()) / 2)))

        # Left barline of this bar.
        pygame.draw.line(
            surface, _BARLINE, (int(x), int(y) + 4), (int(x), int(y + row_h) - 4), 2
        )

    # -- Closing barline at the end of each row ------------------------------
    for row in range(rows):
        bars_in_row = min(BARS_PER_ROW, total_bars - row * BARS_PER_ROW)
        rx = grid_x + bars_in_row * bar_w
        ry = grid_y + row * row_h
        pygame.draw.line(
            surface, _BARLINE, (int(rx), int(ry) + 4), (int(rx), int(ry + row_h) - 4), 2
        )

    # -- Loop band (selection in amber, active loop in blue) -----------------
    band = loop_select if loop_select is not None else loop_active
    if band is not None:
        color = _LOOP_SELECT if loop_select is not None else _LOOP_ACTIVE
        start_bar, end_bar = band
        start_bar = max(0, min(start_bar, total_bars - 1))
        end_bar = max(start_bar + 1, min(end_bar, total_bars))
        _draw_loop_band(
            surface,
            grid_x=grid_x,
            grid_y=grid_y,
            bar_w=bar_w,
            row_h=row_h,
            start_bar=start_bar,
            end_bar=end_bar,
            color=color,
        )
        # Status line in the title band, right-aligned.
        if loop_select is not None:
            status = f"SELECT LOOP  bars {start_bar + 1}-{end_bar}   [Enter] confirm  [K] cancel"
        else:
            status = f"LOOP  bars {start_bar + 1}-{end_bar}   [K] clear"
        st = _font(22, bold=True).render(status, True, color)
        surface.blit(st, (w - margin - st.get_width(), 17))


def _draw_loop_band(
    surface: pygame.Surface,
    *,
    grid_x: float,
    grid_y: float,
    bar_w: float,
    row_h: float,
    start_bar: int,
    end_bar: int,
    color: tuple[int, int, int],
) -> None:
    """Tint the looped bars and bracket the range start/end (iReal-style)."""
    fill = pygame.Surface((max(1, int(bar_w)), max(1, int(row_h))), pygame.SRCALPHA)
    fill.fill((*color, 55))
    for bar_idx in range(start_bar, end_bar):
        row = bar_idx // BARS_PER_ROW
        col = bar_idx % BARS_PER_ROW
        x = grid_x + col * bar_w
        y = grid_y + row * row_h
        surface.blit(fill, (int(x), int(y)))
        # Top / bottom edges → the tint reads as a continuous band per row.
        pygame.draw.line(
            surface, color, (int(x), int(y) + 2), (int(x + bar_w), int(y) + 2), 2
        )
        pygame.draw.line(
            surface,
            color,
            (int(x), int(y + row_h) - 2),
            (int(x + bar_w), int(y + row_h) - 2),
            2,
        )

    # Heavy bracket at the very start and very end of the range.
    sx = grid_x + (start_bar % BARS_PER_ROW) * bar_w
    sy = grid_y + (start_bar // BARS_PER_ROW) * row_h
    pygame.draw.rect(surface, color, (int(sx), int(sy) + 2, 5, int(row_h) - 4))
    last = end_bar - 1
    ex = grid_x + ((last % BARS_PER_ROW) + 1) * bar_w
    ey = grid_y + (last // BARS_PER_ROW) * row_h
    pygame.draw.rect(surface, color, (int(ex) - 5, int(ey) + 2, 5, int(row_h) - 4))
