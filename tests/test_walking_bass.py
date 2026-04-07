"""Tests for the walking bass generator."""

from __future__ import annotations

from leadsheet_utility.backing.walking_bass import (
    BASS_CHANNEL,
    BASS_HIGH,
    BASS_LOW,
    generate_walking_bass,
)
from leadsheet_utility.harmony import analyze
from leadsheet_utility.harmony.constants import NOTE_TO_PC
from leadsheet_utility.leadsheet.models import ChordEvent, LeadSheet


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _chord(root: str, quality: str, start: float, end: float) -> ChordEvent:
    return ChordEvent(
        chord_symbol=f"{root}:{quality}",
        root=root,
        quality=quality,
        start_beat=start,
        end_beat=end,
        duration_beats=end - start,
    )


def _analyzed_sheet(chords: list[ChordEvent], form_repeats: int = 1) -> LeadSheet:
    """Build a LeadSheet and run harmony analysis so chord_tones/scale_notes are populated."""
    ls = LeadSheet(
        chords=chords,
        total_beats=chords[-1].end_beat,
        total_bars=int(chords[-1].end_beat / 4),
        form_repeats=form_repeats,
    )
    analyze(ls)
    return ls


def _note_on_events(events):
    """Filter to note-on events only."""
    return [e for e in events if e.is_note_on]


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

# I-vi-ii-V in C, 4 beats each (16 beats total)
CHORDS_II_V = [
    _chord("C", "maj7", 0.0, 4.0),
    _chord("A", "min7", 4.0, 8.0),
    _chord("D", "min7", 8.0, 12.0),
    _chord("G", "7", 12.0, 16.0),
]

# Two-beat chord changes (8 beats = 2 bars)
CHORDS_TWO_BEAT = [
    _chord("D", "min7", 0.0, 2.0),
    _chord("G", "7", 2.0, 4.0),
    _chord("C", "maj7", 4.0, 6.0),
    _chord("A", "min7", 6.0, 8.0),
]

# Single chord, 8 beats (two bars)
CHORDS_LONG = [
    _chord("F", "min7", 0.0, 8.0),
]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAllNotesInRange:
    """Every generated note must be within MIDI 28–48."""

    def test_four_beat_chords(self):
        ls = _analyzed_sheet(CHORDS_II_V)
        events = generate_walking_bass(ls.chords, tempo=120)
        for e in _note_on_events(events):
            assert BASS_LOW <= e.note <= BASS_HIGH, f"Note {e.note} out of range"

    def test_two_beat_chords(self):
        ls = _analyzed_sheet(CHORDS_TWO_BEAT)
        events = generate_walking_bass(ls.chords, tempo=120)
        for e in _note_on_events(events):
            assert BASS_LOW <= e.note <= BASS_HIGH, f"Note {e.note} out of range"

    def test_long_chord(self):
        ls = _analyzed_sheet(CHORDS_LONG)
        events = generate_walking_bass(ls.chords, tempo=120)
        for e in _note_on_events(events):
            assert BASS_LOW <= e.note <= BASS_HIGH, f"Note {e.note} out of range"


class TestNoteCount:
    """One note-on per beat."""

    def test_four_beat_chords(self):
        ls = _analyzed_sheet(CHORDS_II_V)
        events = generate_walking_bass(ls.chords, tempo=120)
        assert len(_note_on_events(events)) == 16  # 4 chords × 4 beats

    def test_two_beat_chords(self):
        ls = _analyzed_sheet(CHORDS_TWO_BEAT)
        events = generate_walking_bass(ls.chords, tempo=120)
        assert len(_note_on_events(events)) == 8  # 4 chords × 2 beats

    def test_long_chord(self):
        ls = _analyzed_sheet(CHORDS_LONG)
        events = generate_walking_bass(ls.chords, tempo=120)
        assert len(_note_on_events(events)) == 8  # 8 beats

    def test_form_repeats(self):
        ls = _analyzed_sheet(CHORDS_II_V, form_repeats=3)
        events = generate_walking_bass(ls.chords, tempo=120, form_repeats=3)
        assert len(_note_on_events(events)) == 16 * 3

    def test_empty_chords(self):
        events = generate_walking_bass([], tempo=120)
        assert events == []


class TestBeat1IsRoot:
    """Beat 1 of each chord should use the root pitch class."""

    def test_four_beat_first_chord(self):
        ls = _analyzed_sheet(CHORDS_II_V)
        events = generate_walking_bass(ls.chords, tempo=120)
        on_events = _note_on_events(events)
        # First note should be C (root of Cmaj7)
        assert on_events[0].note % 12 == NOTE_TO_PC["C"]

    def test_each_chord_root(self):
        ls = _analyzed_sheet(CHORDS_II_V)
        events = generate_walking_bass(ls.chords, tempo=120)
        on_events = _note_on_events(events)
        roots = ["C", "A", "D", "G"]
        for i, root in enumerate(roots):
            note = on_events[i * 4]  # beat 1 of each 4-beat chord
            assert note.note % 12 == NOTE_TO_PC[root], (
                f"Beat 1 of {root} chord: expected PC {NOTE_TO_PC[root]}, "
                f"got {note.note % 12} (MIDI {note.note})"
            )

    def test_two_beat_roots(self):
        ls = _analyzed_sheet(CHORDS_TWO_BEAT)
        events = generate_walking_bass(ls.chords, tempo=120)
        on_events = _note_on_events(events)
        roots = ["D", "G", "C", "A"]
        for i, root in enumerate(roots):
            note = on_events[i * 2]  # beat 1 of each 2-beat chord
            assert note.note % 12 == NOTE_TO_PC[root]


class TestApproachNotes:
    """Beat 4 (last beat before chord change) should be a scale tone near the next root."""

    def test_approach_is_scale_tone(self):
        ls = _analyzed_sheet(CHORDS_II_V)
        events = generate_walking_bass(ls.chords, tempo=120)
        on_events = _note_on_events(events)
        for i, chord in enumerate(ls.chords):
            approach = on_events[i * 4 + 3]  # beat 4 of each chord
            scale_pcs = {n % 12 for n in chord.scale_notes}
            assert approach.note % 12 in scale_pcs, (
                f"Approach note {approach.note} (PC {approach.note % 12}) "
                f"not in scale of {chord.chord_symbol}"
            )

    def test_approach_near_next_root(self):
        ls = _analyzed_sheet(CHORDS_II_V)
        events = generate_walking_bass(ls.chords, tempo=120)
        on_events = _note_on_events(events)
        roots = ["A", "D", "G", "C"]  # next chord roots (wraps to first)
        for i, next_root in enumerate(roots):
            approach = on_events[i * 4 + 3]  # beat 4 of each chord
            next_root_pc = NOTE_TO_PC[next_root]
            next_root_midi = min(
                [n for n in range(BASS_LOW, BASS_HIGH + 1) if n % 12 == next_root_pc],
                key=lambda n: abs(n - approach.note),
            )
            distance = abs(approach.note - next_root_midi)
            # Diatonic step ≤ 4, dominant approach (P4/P5) ≤ 7
            assert distance <= 7, (
                f"Approach note {approach.note} too far from next root "
                f"{next_root} ({next_root_midi}): distance={distance}"
            )


class TestNoConsecutiveRepeats:
    """No two consecutive beats should play the same MIDI note."""

    def test_four_beat_chords(self):
        ls = _analyzed_sheet(CHORDS_II_V)
        events = generate_walking_bass(ls.chords, tempo=120)
        on_events = _note_on_events(events)
        for i in range(1, len(on_events)):
            assert on_events[i].note != on_events[i - 1].note, (
                f"Repeated note {on_events[i].note} at beats {i - 1} and {i}"
            )

    def test_two_beat_chords(self):
        ls = _analyzed_sheet(CHORDS_TWO_BEAT)
        events = generate_walking_bass(ls.chords, tempo=120)
        on_events = _note_on_events(events)
        for i in range(1, len(on_events)):
            assert on_events[i].note != on_events[i - 1].note, (
                f"Repeated note {on_events[i].note} at beats {i - 1} and {i}"
            )

    def test_long_chord(self):
        ls = _analyzed_sheet(CHORDS_LONG)
        events = generate_walking_bass(ls.chords, tempo=120)
        on_events = _note_on_events(events)
        for i in range(1, len(on_events)):
            assert on_events[i].note != on_events[i - 1].note, (
                f"Repeated note {on_events[i].note} at beats {i - 1} and {i}"
            )

    def test_across_form_repeats(self):
        ls = _analyzed_sheet(CHORDS_II_V, form_repeats=2)
        events = generate_walking_bass(ls.chords, tempo=120, form_repeats=2)
        on_events = _note_on_events(events)
        for i in range(1, len(on_events)):
            assert on_events[i].note != on_events[i - 1].note, (
                f"Repeated note {on_events[i].note} at beats {i - 1} and {i}"
            )


class TestChannel:
    """All events must be on bass channel 0."""

    def test_correct_channel(self):
        ls = _analyzed_sheet(CHORDS_II_V)
        events = generate_walking_bass(ls.chords, tempo=120)
        for e in events:
            assert e.channel == BASS_CHANNEL


class TestNoteOnOff:
    """Every note-on must have a matching note-off."""

    def test_balanced_on_off(self):
        ls = _analyzed_sheet(CHORDS_II_V)
        events = generate_walking_bass(ls.chords, tempo=120)
        on_count = sum(1 for e in events if e.is_note_on)
        off_count = sum(1 for e in events if not e.is_note_on)
        assert on_count == off_count

    def test_off_after_on(self):
        ls = _analyzed_sheet(CHORDS_II_V)
        events = generate_walking_bass(ls.chords, tempo=120)
        sorted_events = sorted(events, key=lambda e: (e.time_samples, not e.is_note_on))
        active: dict[int, int] = {}  # note -> on_time
        for e in sorted_events:
            if e.is_note_on:
                active[e.note] = e.time_samples
            else:
                assert e.note in active, f"Note-off {e.note} without prior note-on"
                assert e.time_samples > active[e.note]
                del active[e.note]


class TestTimingMonotonic:
    """Note-on sample offsets must increase monotonically."""

    def test_monotonic_timing(self):
        ls = _analyzed_sheet(CHORDS_II_V)
        events = generate_walking_bass(ls.chords, tempo=120)
        on_events = _note_on_events(events)
        for i in range(1, len(on_events)):
            assert on_events[i].time_samples > on_events[i - 1].time_samples


class TestSlashChord:
    """Slash chord bass note should be used as root on beat 1."""

    def test_slash_bass_note(self):
        chord = ChordEvent(
            chord_symbol="C:maj7/E",
            root="C",
            quality="maj7",
            bass_note="E",
            start_beat=0.0,
            end_beat=4.0,
            duration_beats=4.0,
        )
        ls = _analyzed_sheet([chord])
        events = generate_walking_bass(ls.chords, tempo=120)
        on_events = _note_on_events(events)
        # Beat 1 should use E (the bass note), not C
        assert on_events[0].note % 12 == NOTE_TO_PC["E"]
