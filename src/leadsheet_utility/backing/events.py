"""MidiEvent dataclass, metronome, and swing drum pattern generators."""

from __future__ import annotations

import random
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
KICK = 36
GHOST_SNARE = 38
SIDE_STICK = 37

_DRUM_CHANNEL = 9
_HUMANIZE_SAMPLES = 220  # ±5 ms at 44.1 kHz
_HUMANIZE_VELOCITY = 10


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _hit(
    beat: float,
    note: int,
    velocity: int,
    seconds_per_beat: float,
    sample_rate: int,
    duration: float = 0.05,
    humanize: bool = False,
) -> list[MidiEvent]:
    """Return a note-on / note-off pair for a single drum hit."""
    on_sample = int(beat * seconds_per_beat * sample_rate)
    if humanize:
        on_sample += random.randint(-_HUMANIZE_SAMPLES, _HUMANIZE_SAMPLES)
        velocity = max(1, min(127, velocity + random.randint(-_HUMANIZE_VELOCITY, _HUMANIZE_VELOCITY)))
    on_sample = max(0, on_sample)
    off_sample = on_sample + int(duration * sample_rate)
    return [
        MidiEvent(on_sample, _DRUM_CHANNEL, note, velocity, True),
        MidiEvent(off_sample, _DRUM_CHANNEL, note, 0, False),
    ]


# ---------------------------------------------------------------------------
# Metronome
# ---------------------------------------------------------------------------


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
    spb = 60.0 / tempo

    beat = 0
    while beat < total_beats:
        velocity = 110 if beat % 4 == 0 else 80
        events.extend(_hit(beat, SIDE_STICK, velocity, spb, sample_rate))
        beat += 1

    return events


# ---------------------------------------------------------------------------
# Swing drum pattern
# ---------------------------------------------------------------------------


def generate_drums(
    total_beats: float,
    tempo: int,
    swing_ratio: float = 0.67,
    sample_rate: int = 44100,
) -> list[MidiEvent]:
    """Generate a swing ride + hi-hat + kick pattern.

    Per bar (4 beats):

    - **Ride**: quarter notes on 1, 2, 3, 4 + swing-eighth skip note on
      the "and" of 2 and 4.
    - **Hi-hat pedal**: beats 2 and 4.
    - **Kick**: beat 1 (soft).
    - **Ghost snare**: ~25 % chance on each swung offbeat (very soft).
    - Minor humanization on all hits (±5 ms, ±10 velocity).

    *swing_ratio* controls the placement of skip notes:
    0.50 = straight eighths, 0.67 = triplet feel (default), 0.75 = hard swing.
    """
    events: list[MidiEvent] = []
    spb = 60.0 / tempo

    beat = 0
    while beat < total_beats:
        beat_in_bar = beat % 4

        # -- Ride: quarter note on every beat ---------------------------------
        ride_vel = 100 if beat_in_bar == 0 else 90
        events.extend(
            _hit(beat, RIDE_CYMBAL, ride_vel, spb, sample_rate, humanize=True),
        )

        # -- Ride skip on the "and" of 2 and 4 --------------------------------
        if beat_in_bar in (1, 3):
            skip_beat = beat + swing_ratio  # shifted later by swing
            if skip_beat < total_beats:
                events.extend(
                    _hit(skip_beat, RIDE_CYMBAL, 75, spb, sample_rate, humanize=True),
                )

        # -- Hi-hat pedal on 2 and 4 ------------------------------------------
        if beat_in_bar in (1, 3):
            events.extend(
                _hit(beat, HI_HAT_PEDAL, 80, spb, sample_rate, humanize=True),
            )

        # -- Kick on beat 1 ---------------------------------------------------
        if beat_in_bar == 0:
            events.extend(
                _hit(beat, KICK, 50, spb, sample_rate, humanize=True),
            )

        # -- Ghost snare on random offbeats (~25 % chance) --------------------
        ghost_beat = beat + swing_ratio  # same swung position as ride skip
        if random.random() < 0.25 and ghost_beat < total_beats:
            events.extend(
                _hit(ghost_beat, GHOST_SNARE, 60, spb, sample_rate, humanize=True),
            )

        beat += 1

    return events
