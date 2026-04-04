"""MidiEvent dataclass and metronome event generator."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MidiEvent:
    """A single MIDI note-on or note-off at an absolute sample offset."""

    time_samples: int  # absolute sample offset from start of buffer
    channel: int  # 0 = bass, 9 = drums (GM)
    note: int  # MIDI note number
    velocity: int  # 0–127
    is_note_on: bool  # True = noteon, False = noteoff


# GM drum note numbers
RIDE_CYMBAL = 51
HI_HAT_PEDAL = 44
SIDE_STICK = 37

_DRUM_CHANNEL = 9


def generate_metronome(
    total_beats: float,
    tempo: int,
    sample_rate: int = 44100,
) -> list[MidiEvent]:
    """Generate a simple metronome click on every beat.

    Uses the side-stick (GM 37) on the drum channel.  Beat 1 of each bar
    is accented (higher velocity).
    """
    events: list[MidiEvent] = []
    seconds_per_beat = 60.0 / tempo
    click_duration_samples = int(0.05 * sample_rate)  # 50 ms click

    beat = 0
    while beat < total_beats:
        sample_offset = int(beat * seconds_per_beat * sample_rate)
        # Accent beat 1 of each bar (every 4 beats)
        velocity = 110 if beat % 4 == 0 else 80
        events.append(MidiEvent(
            time_samples=sample_offset,
            channel=_DRUM_CHANNEL,
            note=SIDE_STICK,
            velocity=velocity,
            is_note_on=True,
        ))
        events.append(MidiEvent(
            time_samples=sample_offset + click_duration_samples,
            channel=_DRUM_CHANNEL,
            note=SIDE_STICK,
            velocity=0,
            is_note_on=False,
        ))
        beat += 1

    return events
