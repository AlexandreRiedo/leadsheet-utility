"""Root-highlight overlay shared by all exercises.

Recolours every highlight that shares a pitch class with the current chord's
root. Applied as a post-processing pass over whatever the active exercise
produced, so each exercise stays oblivious to the toggle and inherits the
behaviour for free.
"""

from __future__ import annotations

from leadsheet_utility.harmony.constants import NOTE_TO_PC
from leadsheet_utility.leadsheet.models import ChordEvent
from leadsheet_utility.projection import KeyHighlight

ROOT_COLOR: tuple[int, int, int] = (60, 130, 255)  # saturated blue


def apply_root_highlight(
    highlights: list[KeyHighlight],
    chord: ChordEvent,
    color: tuple[int, int, int] = ROOT_COLOR,
) -> list[KeyHighlight]:
    """Return a new list with root-pitch-class highlights recolored.

    Notes that don't match the root pitch class are passed through
    unchanged. The original list is not mutated.
    """
    root_pc = NOTE_TO_PC[chord.root]
    return [
        KeyHighlight(midi_note=h.midi_note, color=color)
        if h.midi_note % 12 == root_pc
        else h
        for h in highlights
    ]
