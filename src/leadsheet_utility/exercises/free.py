"""Free Mode: highlight every chord-scale note.

The simplest exercise — no guide tones, no contour, no rhythmic gating.
The projector lights up exactly the notes the player can use over the
current chord, leaving the choice of *which* ones to play entirely to
them.

A "small" sub-mode collapses the highlight set to a single ascending
octave of scale degrees (1-2-3-4-5-6-7-8) inside Bb3-A5, so the player
can practice the scale shape in one position instead of seeing it
tiled across the whole keyboard.
"""

from __future__ import annotations

from leadsheet_utility.harmony.constants import NOTE_TO_PC
from leadsheet_utility.leadsheet.models import ChordEvent
from leadsheet_utility.projection import KeyHighlight

# Debug green — same hue used by the calibration overlay, easier to spot on
# the piano than pure white while we're still validating projection alignment.
HIGHLIGHT_COLOR: tuple[int, int, int] = (60, 220, 90)
# HIGHLIGHT_COLOR: tuple[int, int, int] = (255, 255, 255)

# Small-mode range. Chosen so every possible chord root has its own MIDI
# slot in [58, 69] (Bb3..A4) with the octave-above slot in [70, 81]
# (Bb4..A5) — i.e. one chromatic octave of roots, each with room for the
# scale's 8th degree to fit inside the band.
SMALL_RANGE_LOW = 58   # Bb3
SMALL_RANGE_HIGH = 81  # A5


def _small_octave_midis(chord: ChordEvent) -> list[int]:
    """Return MIDI notes for scale degrees 1..8 in one octave starting at
    the lowest root ≥ Bb3. Empty list if the scale couldn't be resolved.
    """
    if not chord.scale_notes:
        return []
    root_pc = NOTE_TO_PC[chord.root]
    # Lowest MIDI >= SMALL_RANGE_LOW with the root pitch class.
    root_offset = (root_pc - SMALL_RANGE_LOW) % 12
    root_midi = SMALL_RANGE_LOW + root_offset
    # Scale pitch classes ordered by distance up from the root.
    pcs = sorted(
        {n % 12 for n in chord.scale_notes},
        key=lambda pc: (pc - root_pc) % 12,
    )
    midis = [root_midi + (pc - root_pc) % 12 for pc in pcs]
    midis.append(root_midi + 12)  # 8th degree = root one octave up
    return midis


def free_mode_highlights(
    chord: ChordEvent,
    *,
    small: bool = False,
) -> list[KeyHighlight]:
    """Return one KeyHighlight per MIDI note in the chord-scale.

    `chord.scale_notes` already contains the full MIDI range (21–108) of
    the resolved scale, so the renderer just needs to draw whichever of
    those land inside the projected keyboard layout — out-of-range notes
    are silently dropped downstream.

    When ``small`` is True, only one ascending octave's worth of scale
    degrees inside Bb3-A5 is returned.
    """
    midis = _small_octave_midis(chord) if small else chord.scale_notes
    return [KeyHighlight(midi_note=n, color=HIGHLIGHT_COLOR) for n in midis]
