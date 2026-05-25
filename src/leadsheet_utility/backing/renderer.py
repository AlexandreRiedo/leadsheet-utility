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


def render_layer(
    events: list[MidiEvent],
    sf_path: str,
    total_beats: float,
    tempo: int,
    sample_rate: int = 44100,
) -> np.ndarray:
    """Render *events* to a raw stereo float32 buffer.

    Returns an interleaved L/R array shaped ``(total_samples * 2,)``. The
    output is *not* clipped or normalized — a single dense layer (e.g.
    drums on a downbeat) can momentarily exceed |1.0|, and clipping at
    the layer stage would shear off peaks that the final mix can still
    accommodate.  Always pair with :func:`mix_layers` for clipping +
    int16 conversion.
    """
    synth = fluidsynth.Synth(samplerate=float(sample_rate), gain=0.5) # type: ignore
    sfid = synth.sfload(sf_path)
    synth.program_select(0, sfid, 0, 33)   # channel 0 → Acoustic Bass (GM #34)
    synth.program_select(1, sfid, 0, 26)   # channel 1 → Electric Guitar Jazz (GM #27)
    synth.program_select(9, sfid, 128, 0)  # channel 9 → GM drums

    # Per-channel volume balance (MIDI CC7, 0-127).
    synth.cc(0, 7, 110)  # bass: full
    synth.cc(1, 7, 70)   # guitar: backed off — comping shouldn't dominate
    synth.cc(9, 7, 115)  # drums: near full

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

    return buf


def mix_layers(
    layers: list[np.ndarray],
    total_samples: int | None = None,
) -> np.ndarray:
    """Sum float32 layer buffers and convert to a normalized int16 buffer.

    Peaks are only attenuated, never amplified — so a layer's loudness stays
    consistent whether or not other layers are also playing (the original
    full-mix renderer had the same property).
    """
    if total_samples is None:
        total_samples = max((layer.size for layer in layers), default=0)
    acc = np.zeros(total_samples, dtype=np.float32)
    for layer in layers:
        n = min(layer.size, total_samples)
        acc[:n] += layer[:n]

    peak = float(np.max(np.abs(acc))) if acc.size else 0.0
    if peak > 0.95:
        acc = acc * (0.95 / peak)
    return (acc * 32767).astype(np.int16)


def render_backing_track(
    events: list[MidiEvent],
    sf_path: str,
    total_beats: float,
    tempo: int,
    sample_rate: int = 44100,
) -> np.ndarray:
    """Render *events* to a stereo int16 NumPy array using FluidSynth offline.

    Convenience wrapper around :func:`render_layer` + :func:`mix_layers` for
    callers that want a single normalized buffer (e.g. the count-in click).
    """
    layer = render_layer(events, sf_path, total_beats, tempo, sample_rate)
    return mix_layers([layer])
