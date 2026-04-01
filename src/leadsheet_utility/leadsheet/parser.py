"""Parse MIR-style TSV chord annotation files into LeadSheet / ChordEvent IR."""

import json
import re
from math import floor
from pathlib import Path

from leadsheet_utility.leadsheet.models import ChordEvent, LeadSheet

_EXT_RE = re.compile(r"\(([^)]+)\)")
_BASS_RE = re.compile(r"/([A-G][#b]?)$")


def parse_chord_symbol(symbol: str) -> ChordEvent:
    """Parse a chord symbol string like ``'Bb:min7'`` or ``'G:7(b9)/F'``."""
    root, rest = symbol.split(":", maxsplit=1)

    # Extract parenthesized extensions first (before slash, so the regex
    # doesn't confuse extension content with a bass note).
    extensions: list[str] = []
    ext_match = _EXT_RE.search(rest)
    if ext_match:
        extensions = [e.strip() for e in ext_match.group(1).split(",")]
        rest = rest[: ext_match.start()] + rest[ext_match.end() :]

    # Extract slash bass note from what remains.
    bass_note: str | None = None
    bass_match = _BASS_RE.search(rest)
    if bass_match:
        bass_note = bass_match.group(1)
        rest = rest[: bass_match.start()]

    quality = rest

    return ChordEvent(
        chord_symbol=symbol,
        root=root,
        quality=quality,
        extensions=extensions,
        bass_note=bass_note,
    )


def parse_leadsheet(path: Path) -> LeadSheet:
    """Parse a ``.tsv`` lead-sheet file (+ optional ``.meta.json`` sidecar)."""
    text = path.read_text(encoding="utf-8")

    # --- Load metadata sidecar (if present) --------------------------------
    meta_path = path.with_suffix(".meta.json")
    if meta_path.exists():
        raw = json.loads(meta_path.read_text(encoding="utf-8-sig"))
    else:
        raw = {}

    title = raw.get("title", "Unknown")
    composer = raw.get("composer", "Unknown")
    key = raw.get("key", "C")
    ts = raw.get("time_signature", [4, 4])
    time_signature = (ts[0], ts[1])
    default_tempo = raw.get("default_tempo", 120)
    form_repeats = raw.get("form_repeats", 1)

    beats_per_bar = time_signature[0]  # numerator

    # --- Parse TSV lines ---------------------------------------------------
    chords: list[ChordEvent] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        start_s, end_s, symbol = line.split("\t")
        start_beat = float(start_s)
        end_beat = float(end_s)

        event = parse_chord_symbol(symbol)
        event.start_beat = start_beat
        event.end_beat = end_beat
        event.duration_beats = end_beat - start_beat
        event.bar_number = floor(start_beat / beats_per_bar) + 1
        event.beat_in_bar = start_beat % beats_per_bar
        chords.append(event)

    # --- Derive totals -----------------------------------------------------
    total_beats = chords[-1].end_beat if chords else 0.0
    total_bars = int(total_beats / beats_per_bar) if chords else 0

    return LeadSheet(
        title=title,
        composer=composer,
        key=key,
        time_signature=time_signature,
        default_tempo=default_tempo,
        form_repeats=form_repeats,
        chords=chords,
        total_beats=total_beats,
        total_bars=total_bars,
    )
