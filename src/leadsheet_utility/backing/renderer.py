"""Offline FluidSynth rendering: MIDI events to NumPy audio buffer.

The synth runs without an audio driver — events are fed via
``noteon()``/``noteoff()`` and audio is pulled with ``get_samples()``.
"""

from __future__ import annotations

import logging

import fluidsynth
import numpy as np

from leadsheet_utility.backing.events import MidiEvent

logger = logging.getLogger(__name__)


def render_backing_track(
    events: list[MidiEvent],
    sf_path: str,
    total_beats: float,
    tempo: int,
    sample_rate: int = 44100,
) -> np.ndarray:
    """Render *events* to a stereo int16 NumPy array using FluidSynth offline.

    Returns an array shaped ``(total_samples * 2,)`` with interleaved L/R
    samples, ready for ``pygame.mixer.Sound``.
    """
    synth = fluidsynth.Synth(samplerate=float(sample_rate), gain=0.2)
    sfid = synth.sfload(sf_path)
    synth.program_select(0, sfid, 0, 33)   # channel 0 → Acoustic Bass (GM #34)
    synth.program_select(9, sfid, 128, 0)  # channel 9 → GM drums

    total_samples = int((total_beats * 60.0 / tempo) * sample_rate)
    buf = np.zeros(total_samples * 2, dtype=np.float32)
    cursor = 0

    sorted_events = sorted(events, key=lambda e: e.time_samples)

    for event in sorted_events:
        gap = event.time_samples - cursor
        if gap > 0:
            chunk = synth.get_samples(gap)
            buf[cursor * 2:(cursor + gap) * 2] = chunk
            cursor += gap

        if event.is_note_on:
            synth.noteon(event.channel, event.note, event.velocity)
        else:
            synth.noteoff(event.channel, event.note)

    # Render the tail (reverb/release decay)
    remaining = total_samples - cursor
    if remaining > 0:
        buf[cursor * 2:] = synth.get_samples(remaining)

    synth.delete()

    # Normalize to ~80% of int16 range to avoid clipping
    peak = np.max(np.abs(buf))
    if peak > 0:
        buf = buf / peak * 0.8
    return (buf * 32767).astype(np.int16)
