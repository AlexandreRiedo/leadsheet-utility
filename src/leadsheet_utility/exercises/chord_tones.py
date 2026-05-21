"""Chord-tone overlay shared by all exercises.

Recolours every highlight that shares a pitch class with the current
chord's 7-chord (or triad) tones — R, 3, 5/#11/b6, 7 — using the same
5th-substitution rule as the comping voicings:

- ``#11`` / ``b5`` extensions or ``maj7#11`` quality → 5 becomes #11 (6)
- ``b9`` / ``b13`` without natural ``13`` (and not already taking #11) →
  5 becomes b6 (8)

Like the root overlay, this is a pure post-processing pass — exercises
emit their highlights, and the App layer composes overlays on top.
Chord tones that aren't part of the underlying highlight set are not
added; the overlay only recolors what is already lit.
"""

from __future__ import annotations

from leadsheet_utility.harmony.constants import NOTE_TO_PC
from leadsheet_utility.leadsheet.models import ChordEvent
from leadsheet_utility.projection import KeyHighlight

# Lighter, more cyan-leaning blue — distinguishable from the saturated
# root blue when both overlays are active.
CHORD_TONE_COLOR: tuple[int, int, int] = (100, 200, 255)


def chord_tone_pitch_classes(chord: ChordEvent) -> set[int]:
    """Return the pitch classes of the chord's 7-chord (or triad) tones.

    Applies the #11/b5/b6 substitution rules used elsewhere for voicings.
    """
    if not chord.chord_tones:
        return set()
    root_pc = NOTE_TO_PC[chord.root]
    intervals = {(n - root_pc) % 12 for n in chord.chord_tones}
    if 7 in intervals:
        exts = set(chord.extensions)
        use_sharp11 = "#11" in exts or "b5" in exts or chord.quality == "maj7#11"
        use_flat13 = (
            ("b9" in exts or "b13" in exts)
            and "13" not in exts
            and not use_sharp11
        )
        if use_sharp11:
            intervals = {6 if i == 7 else i for i in intervals}
        elif use_flat13:
            intervals = {8 if i == 7 else i for i in intervals}
    return {(root_pc + i) % 12 for i in intervals}


def apply_chord_tone_highlight(
    highlights: list[KeyHighlight],
    chord: ChordEvent,
    color: tuple[int, int, int] = CHORD_TONE_COLOR,
) -> list[KeyHighlight]:
    """Return a new list with chord-tone pitch classes recolored.

    Notes whose pitch class isn't a chord tone pass through unchanged.
    The original list is not mutated.
    """
    pcs = chord_tone_pitch_classes(chord)
    if not pcs:
        return list(highlights)
    return [
        KeyHighlight(midi_note=h.midi_note, color=color)
        if h.midi_note % 12 in pcs
        else h
        for h in highlights
    ]
