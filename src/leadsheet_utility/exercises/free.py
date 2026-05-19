"""Free Mode: highlight every chord-scale note in white.

The simplest exercise — no guide tones, no contour, no rhythmic gating.
The projector lights up exactly the notes the player can use over the
current chord, leaving the choice of *which* ones to play entirely to
them.
"""

from __future__ import annotations

from leadsheet_utility.leadsheet.models import ChordEvent
from leadsheet_utility.projection import KeyHighlight

# Debug green — same hue used by the calibration overlay, easier to spot on
# the piano than pure white while we're still validating projection alignment.
HIGHLIGHT_COLOR: tuple[int, int, int] = (60, 220, 90)


def free_mode_highlights(chord: ChordEvent) -> list[KeyHighlight]:
    """Return one KeyHighlight per MIDI note in the chord-scale.

    `chord.scale_notes` already contains the full MIDI range (21–108) of
    the resolved scale, so the renderer just needs to draw whichever of
    those land inside the projected keyboard layout — out-of-range notes
    are silently dropped downstream.
    """
    return [KeyHighlight(midi_note=n, color=HIGHLIGHT_COLOR) for n in chord.scale_notes]
