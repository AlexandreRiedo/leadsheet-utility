"""Free Mode: highlight every chord-scale note.

The simplest exercise — no guide tones, no contour, no rhythmic gating.
The projector lights up exactly the notes the player can use over the
current chord, leaving the choice of *which* ones to play entirely to
them.

A "small" sub-toggle collapses the highlight set to a single ascending
1- or 2-octave run of scale degrees so the player can practice the scale
shape in one position instead of seeing it tiled across the whole
keyboard. The two ranges are chosen so every chromatic root has a slot:

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

# Back-compat aliases for callers that imported the originals.
SMALL_RANGE_LOW = ONE_OCTAVE_RANGE_LOW
SMALL_RANGE_HIGH = ONE_OCTAVE_RANGE_HIGH


class SmallMode(Enum):
    OFF = auto()
    ONE_OCTAVE = auto()
    TWO_OCTAVE = auto()


SMALL_CYCLE: tuple[SmallMode, ...] = (
    SmallMode.OFF,
    SmallMode.ONE_OCTAVE,
    SmallMode.TWO_OCTAVE,
)


def next_small_mode(mode: SmallMode) -> SmallMode:
    """Return the next mode in the cycle (OFF -> 1-OCT -> 2-OCT -> OFF)."""
    idx = SMALL_CYCLE.index(mode)
    return SMALL_CYCLE[(idx + 1) % len(SMALL_CYCLE)]


def small_range_low(mode: SmallMode) -> int:
    """Lowest MIDI note in the band selected by `mode`."""
    if mode is SmallMode.ONE_OCTAVE:
        return ONE_OCTAVE_RANGE_LOW
    if mode is SmallMode.TWO_OCTAVE:
        return TWO_OCTAVE_RANGE_LOW
    raise ValueError(f"small_range_low: not applicable for {mode}")


def _small_midis(chord: ChordEvent, mode: SmallMode) -> list[int]:
    """Scale degrees 1..(8 or 15), one or two octaves, starting at the
    lowest root inside the active band. Empty list if no scale.
    """
    if not chord.scale_notes:
        return []
    octaves = 1 if mode is SmallMode.ONE_OCTAVE else 2
    band_low = small_range_low(mode)
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
    small: SmallMode = SmallMode.OFF,
) -> list[KeyHighlight]:
    """Return one KeyHighlight per MIDI note in the chord-scale.

    When ``small`` is ``ONE_OCTAVE`` or ``TWO_OCTAVE``, only that many
    ascending octaves of scale degrees inside the corresponding band are
    returned (plus the final octave repeat).
    """
    if small is SmallMode.OFF:
        midis = chord.scale_notes
    else:
        midis = _small_midis(chord, small)
    return [KeyHighlight(midi_note=n, color=HIGHLIGHT_COLOR) for n in midis]
