"""Jazz guitar comping: drop-2/drop-3 voicings over swing rhythm patterns."""

from __future__ import annotations

import random

from leadsheet_utility.backing.comping_rhythms import (
    CompingPattern,
    RhythmHit,
    pick_pattern,
)
from leadsheet_utility.backing.comping_voicings import best_voicing
from leadsheet_utility.backing.events import MidiEvent
from leadsheet_utility.leadsheet.models import ChordEvent

COMP_CHANNEL = 1
COMP_VELOCITY_BASE = 75
COMP_VELOCITY_ACCENT = 95
COMP_HUMANIZE_VEL = 8
COMP_HUMANIZE_SAMPLES = 180
COMP_LEGATO = 0.85  # fraction of hit duration before note-off
COMP_SKIP_PROBABILITY = 0.2  # chance a given pattern hit is dropped for sparseness
_SWING_RATIO = 0.67


def _flatten(chords: list[ChordEvent], form_repeats: int) -> list[ChordEvent]:
    """Clone chord events across *form_repeats*, shifting beat offsets.

    We copy only the fields needed by the comping generator (start/end beat
    and the harmony analysis output). The originals are not mutated.
    """
    if not chords:
        return []
    form_length = max(c.end_beat for c in chords)
    flat: list[ChordEvent] = []
    for rep in range(form_repeats):
        offset = rep * form_length
        for c in chords:
            clone = ChordEvent(
                chord_symbol=c.chord_symbol,
                root=c.root,
                quality=c.quality,
                extensions=list(c.extensions),
                bass_note=c.bass_note,
                start_beat=c.start_beat + offset,
                end_beat=c.end_beat + offset,
                duration_beats=c.duration_beats,
                bar_number=c.bar_number,
                beat_in_bar=c.beat_in_bar,
                scale_notes=c.scale_notes,
                chord_tones=c.chord_tones,
                guide_tones=c.guide_tones,
                available_tensions=c.available_tensions,
            )
            flat.append(clone)
    return flat


def _chord_at(chords: list[ChordEvent], beat: float) -> ChordEvent | None:
    """Linear scan for the chord active at *beat*. Clamped to last chord."""
    if not chords:
        return None
    for c in chords:
        if c.start_beat <= beat < c.end_beat:
            return c
    # Beat may sit exactly at total_beats; fall back to the last chord
    return chords[-1] if beat >= chords[-1].end_beat else None


def _apply_swing(beat: float) -> float:
    """Shift offbeat 8ths to the swung position (triplet feel)."""
    frac = beat - int(beat)
    if abs(frac - 0.5) < 1e-6:
        return int(beat) + _SWING_RATIO
    return beat


def _emit_hit(
    voicing: list[int],
    abs_beat: float,
    duration_beats: float,
    accented: bool,
    spb: float,
    sample_rate: int,
    rng: random.Random,
) -> list[MidiEvent]:
    """Emit one note-on + note-off pair per voice in *voicing*."""
    on_sample = int(_apply_swing(abs_beat) * spb * sample_rate)
    on_sample += rng.randint(-COMP_HUMANIZE_SAMPLES, COMP_HUMANIZE_SAMPLES)
    on_sample = max(0, on_sample)

    off_sample = on_sample + int(duration_beats * COMP_LEGATO * spb * sample_rate)
    off_sample = max(on_sample + 1, off_sample)

    base_vel = COMP_VELOCITY_ACCENT if accented else COMP_VELOCITY_BASE
    velocity = max(1, min(127, base_vel + rng.randint(-COMP_HUMANIZE_VEL, COMP_HUMANIZE_VEL)))

    events: list[MidiEvent] = []
    for note in voicing:
        events.append(MidiEvent(on_sample, COMP_CHANNEL, note, velocity, True))
        events.append(MidiEvent(off_sample, COMP_CHANNEL, note, 0, False))
    return events


def _hit_chord(
    hit: RhythmHit,
    pattern: CompingPattern,
    window_start: float,
    bar_beats: int,
    chords: list[ChordEvent],
) -> ChordEvent | None:
    """Resolve which chord voicing a hit should use (handles anticipations)."""
    if pattern.bars == 2 and hit.beat in pattern.anticipation_beats:
        # Anticipation: use bar 2's chord (the downbeat after the barline)
        lookup_beat = window_start + bar_beats
    else:
        lookup_beat = window_start + hit.beat
    return _chord_at(chords, lookup_beat)


def generate_comping(
    chords: list[ChordEvent],
    tempo: int,
    form_repeats: int = 1,
    sample_rate: int = 44100,
    beats_per_bar: int = 4,
    seed: int | None = None,
) -> list[MidiEvent]:
    """Generate jazz guitar comping events across the full form.

    Walks the timeline in 2-bar windows, picking rhythm patterns from the
    Phil DeGreg swing pool. Each hit is voiced as a drop-2 or drop-3 voicing
    (root as bass) chosen to minimise voice movement from the previous hit.
    Anticipations in 2-bar patterns use the upcoming bar's harmony.
    """
    if not chords:
        return []

    flat = _flatten(chords, form_repeats)
    total_beats = flat[-1].end_beat
    spb = 60.0 / tempo
    rng = random.Random(seed)

    events: list[MidiEvent] = []
    prev_voicing: list[int] | None = None
    window_start = 0.0

    while window_start < total_beats:
        bars_left = int((total_beats - window_start) / beats_per_bar)
        if bars_left <= 0:
            break
        pattern = pick_pattern(rng, bars_left)
        window_len = pattern.bars * beats_per_bar

        for hit in pattern.hits:
            abs_beat = window_start + hit.beat
            if abs_beat >= total_beats:
                continue

            if rng.random() < COMP_SKIP_PROBABILITY:
                continue

            chord = _hit_chord(hit, pattern, window_start, beats_per_bar, flat)
            if chord is None:
                continue

            voicing = best_voicing(chord, prev_voicing)
            if not voicing:
                continue

            # Clamp duration so the note-off doesn't run past the form end
            duration = min(hit.duration, total_beats - abs_beat)
            if duration <= 0:
                continue

            events.extend(
                _emit_hit(voicing, abs_beat, duration, hit.accented, spb, sample_rate, rng),
            )
            prev_voicing = voicing

        window_start += window_len

    return events
