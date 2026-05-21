"""Chord-tone highlighting (shared by all exercises).

Three rendering modes (cycled by the `T` keybinding):

- ``OFF``  — no chord-tone treatment.
- ``ONLY`` — replace the chord-scale with just the chord tones (R, 3, 5/#11/b6, 7).
- ``OVERLAY`` — keep the full chord-scale, recolor chord-tone pitch classes.

Pitch classes use the same 5th-substitution rule as the comping voicings:

- ``#11`` / ``b5`` extensions or ``maj7#11`` quality → 5 becomes #11 (6)
- ``b9`` / ``b13`` without natural ``13`` (and not already taking #11) →
  5 becomes b6 (8)
"""

from __future__ import annotations

from enum import Enum, auto

from leadsheet_utility.exercises.free import SmallMode, small_range_low
from leadsheet_utility.harmony.constants import NOTE_TO_PC
from leadsheet_utility.leadsheet.models import ChordEvent
from leadsheet_utility.projection import KeyHighlight

# Lighter, more cyan-leaning blue — distinguishable from the saturated
# root blue when both overlays are active.
CHORD_TONE_COLOR: tuple[int, int, int] = (100, 200, 255)


class ChordToneMode(Enum):
    OFF = auto()
    ONLY = auto()
    OVERLAY = auto()


# Stable cycle order used by the `T` keybinding.
CHORD_TONE_CYCLE: tuple[ChordToneMode, ...] = (
    ChordToneMode.OFF,
    ChordToneMode.ONLY,
    ChordToneMode.OVERLAY,
)


def next_chord_tone_mode(mode: ChordToneMode) -> ChordToneMode:
    """Return the next mode in the cycle (OFF -> ONLY -> OVERLAY -> OFF)."""
    idx = CHORD_TONE_CYCLE.index(mode)
    return CHORD_TONE_CYCLE[(idx + 1) % len(CHORD_TONE_CYCLE)]


def chord_tone_pitch_classes(chord: ChordEvent) -> set[int]:
    """Return the pitch classes of the chord's 7-chord (or triad) tones."""
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


def chord_tone_only_highlights(
    chord: ChordEvent,
    *,
    small: SmallMode = SmallMode.OFF,
    color: tuple[int, int, int] = CHORD_TONE_COLOR,
) -> list[KeyHighlight]:
    """Return only the chord-tone highlights, hiding the rest of the scale.

    When ``small`` is ``ONE_OCTAVE``/``TWO_OCTAVE`` emits the chord tones
    within the corresponding band, starting at the lowest root in the band.
    For ``ONE_OCTAVE`` of C7 → C4 E4 G4 Bb4. For ``TWO_OCTAVE`` → C4 E4 G4
    Bb4 C5 E5 G5 Bb5. No octave-of-root repeat is added — the chord-tone
    set is already a complete voicing.
    """
    pcs = chord_tone_pitch_classes(chord)
    if not pcs:
        return []
    if small is SmallMode.OFF:
        midis = [n for n in range(21, 109) if n % 12 in pcs]
    else:
        octaves = 1 if small is SmallMode.ONE_OCTAVE else 2
        band_low = small_range_low(small)
        root_pc = NOTE_TO_PC[chord.root]
        root_midi = band_low + (root_pc - band_low) % 12
        ordered = sorted(pcs, key=lambda pc: (pc - root_pc) % 12)
        midis = []
        for o in range(octaves):
            midis.extend(root_midi + (pc - root_pc) % 12 + 12 * o for pc in ordered)
    return [KeyHighlight(midi_note=n, color=color) for n in midis]


def apply_chord_tone_highlight(
    highlights: list[KeyHighlight],
    chord: ChordEvent,
    color: tuple[int, int, int] = CHORD_TONE_COLOR,
) -> list[KeyHighlight]:
    """Recolor every highlight whose pitch class is a chord tone (OVERLAY mode).

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
