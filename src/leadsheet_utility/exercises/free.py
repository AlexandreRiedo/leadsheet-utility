"""Free Mode: highlight every chord-scale note.

The simplest exercise — no guide tones, no contour, no rhythmic gating.
The projector lights up exactly the notes the player can use over the
current chord, leaving the choice of *which* ones to play entirely to
them.

A "range" sub-toggle collapses the highlight set to a single ascending
1- or 2-octave run of scale degrees so the player can practice the scale
shape in one position instead of seeing it tiled across the whole
keyboard. The two windows are chosen so every chromatic root has a slot:

- 1 octave: Bb3-A5 (root in Bb3..A4, octave above in Bb4..A5)
- 2 octave: Ab3-G6 (root in Ab3..G4, 2-octave above in Ab5..G6)

Other Free-mode emphases (chord-tone overlay, root overlay) are pure
post-processing passes that live in sibling modules — see
:mod:`leadsheet_utility.exercises.chord_tones` and
:mod:`leadsheet_utility.exercises.root`.
"""

from __future__ import annotations

from enum import Enum, auto

from leadsheet_utility.harmony.constants import NOTE_TO_PC
from leadsheet_utility.leadsheet.models import ChordEvent
from leadsheet_utility.projection import KeyHighlight

# Debug green — same hue used by the calibration overlay, easier to spot on
# the piano than pure white while we're still validating projection alignment.
HIGHLIGHT_COLOR: tuple[int, int, int] = (60, 220, 90)
# HIGHLIGHT_COLOR: tuple[int, int, int] = (255, 255, 255)

# 1-octave range: 24 semitones (12 root slots + 12 for the octave above).
ONE_OCTAVE_RANGE_LOW = 58   # Bb3
ONE_OCTAVE_RANGE_HIGH = 81  # A5
# 2-octave range: 36 semitones (12 root slots + 24 for two octaves above).
TWO_OCTAVE_RANGE_LOW = 56   # Ab3
TWO_OCTAVE_RANGE_HIGH = 91  # G6


class RangeMode(Enum):
    FULL = auto()
    TWO_OCTAVE = auto()
    ONE_OCTAVE = auto()


RANGE_CYCLE: tuple[RangeMode, ...] = (
    RangeMode.FULL,
    RangeMode.TWO_OCTAVE,
    RangeMode.ONE_OCTAVE,
)


def next_range_mode(mode: RangeMode) -> RangeMode:
    """Return the next mode in the cycle (FULL -> 2-OCT -> 1-OCT -> FULL)."""
    idx = RANGE_CYCLE.index(mode)
    return RANGE_CYCLE[(idx + 1) % len(RANGE_CYCLE)]


def range_mode_low(mode: RangeMode) -> int:
    """Lowest MIDI note in the *default* band selected by `mode`.

    Callers that have a calibrated band should pass it explicitly via the
    ``band_low`` parameter on the highlight functions instead.
    """
    if mode is RangeMode.ONE_OCTAVE:
        return ONE_OCTAVE_RANGE_LOW
    if mode is RangeMode.TWO_OCTAVE:
        return TWO_OCTAVE_RANGE_LOW
    raise ValueError(f"range_mode_low: not applicable for {mode}")


def _range_midis(chord: ChordEvent, mode: RangeMode, band_low: int) -> list[int]:
    """Scale degrees 1..(8 or 15), one or two octaves, starting at the
    lowest root inside the active band. Empty list if no scale.
    """
    if not chord.scale_notes:
        return []
    octaves = 1 if mode is RangeMode.ONE_OCTAVE else 2
    root_pc = NOTE_TO_PC[chord.root]
    root_midi = band_low + (root_pc - band_low) % 12
    pcs = sorted(
        {n % 12 for n in chord.scale_notes},
        key=lambda pc: (pc - root_pc) % 12,
    )
    midis: list[int] = []
    for o in range(octaves):
        midis.extend(root_midi + (pc - root_pc) % 12 + 12 * o for pc in pcs)
    # Final octave-of-root repeat (the 8th / 15th degree).
    midis.append(root_midi + 12 * octaves)
    return midis


def free_mode_highlights(
    chord: ChordEvent,
    *,
    range_mode: RangeMode = RangeMode.FULL,
    band_low: int | None = None,
) -> list[KeyHighlight]:
    """Return one KeyHighlight per MIDI note in the chord-scale.

    When ``range_mode`` is ``ONE_OCTAVE`` or ``TWO_OCTAVE``, only that many
    ascending octaves of scale degrees inside the corresponding band are
    returned (plus the final octave repeat). ``band_low`` overrides the
    module default — pass the calibrated band low when available.
    """
    if range_mode is RangeMode.FULL:
        midis = chord.scale_notes
    else:
        low = band_low if band_low is not None else range_mode_low(range_mode)
        midis = _range_midis(chord, range_mode, low)
    return [KeyHighlight(midi_note=n, color=HIGHLIGHT_COLOR) for n in midis]
