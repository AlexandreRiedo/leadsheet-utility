"""Backing track module: event generation and offline FluidSynth rendering."""

from leadsheet_utility.backing.comping import generate_comping
from leadsheet_utility.backing.events import (
    MidiEvent,
    generate_count_in,
    generate_drums,
    generate_metronome,
)
from leadsheet_utility.backing.renderer import render_backing_track
from leadsheet_utility.backing.walking_bass import generate_walking_bass

__all__ = [
    "MidiEvent",
    "generate_comping",
    "generate_count_in",
    "generate_drums",
    "generate_metronome",
    "generate_walking_bass",
    "render_backing_track",
]
