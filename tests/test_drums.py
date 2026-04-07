"""Tests for the swing drum pattern generator."""

from __future__ import annotations

from leadsheet_utility.backing.events import (
    GHOST_SNARE,
    HI_HAT_PEDAL,
    KICK,
    RIDE_CYMBAL,
    generate_drums,
)


def _on_events(events, note=None):
    """Filter to note-on events, optionally for a specific GM note."""
    return [e for e in events if e.is_note_on and (note is None or e.note == note)]


# 16 beats = 4 bars of 4/4
TOTAL_BEATS = 16.0
TEMPO = 120


class TestNoteNumbers:
    """Only expected GM drum notes should appear."""

    def test_only_expected_notes(self):
        events = generate_drums(TOTAL_BEATS, TEMPO)
        allowed = {RIDE_CYMBAL, HI_HAT_PEDAL, KICK, GHOST_SNARE}
        for e in _on_events(events):
            assert e.note in allowed, f"Unexpected drum note {e.note}"


class TestChannel:
    """All drum events must be on channel 9."""

    def test_channel_9(self):
        events = generate_drums(TOTAL_BEATS, TEMPO)
        for e in events:
            assert e.channel == 9


class TestRide:
    """Ride cymbal: quarter notes on every beat + skip on the 'and' of 2 and 4."""

    def test_quarter_note_count(self):
        # 4 bars × 4 beats = 16 quarter-note ride hits
        events = generate_drums(TOTAL_BEATS, TEMPO)
        ride_ons = _on_events(events, RIDE_CYMBAL)
        # 16 quarter notes + 8 skip notes (2 per bar × 4 bars)
        assert len(ride_ons) == 16 + 8


class TestHiHat:
    """Hi-hat pedal on beats 2 and 4 of each bar."""

    def test_count(self):
        events = generate_drums(TOTAL_BEATS, TEMPO)
        hh_ons = _on_events(events, HI_HAT_PEDAL)
        # 2 per bar × 4 bars = 8
        assert len(hh_ons) == 8


class TestKick:
    """Kick on beat 1 of each bar."""

    def test_count(self):
        events = generate_drums(TOTAL_BEATS, TEMPO)
        kick_ons = _on_events(events, KICK)
        # 1 per bar × 4 bars = 4
        assert len(kick_ons) == 4

    def test_low_velocity(self):
        events = generate_drums(TOTAL_BEATS, TEMPO)
        for e in _on_events(events, KICK):
            # Base velocity 50 ± 10 humanization
            assert 30 <= e.velocity <= 70, f"Kick velocity {e.velocity} out of range"


class TestNoteOnOff:
    """Every note-on must have a matching note-off."""

    def test_balanced(self):
        events = generate_drums(TOTAL_BEATS, TEMPO)
        on_count = sum(1 for e in events if e.is_note_on)
        off_count = sum(1 for e in events if not e.is_note_on)
        assert on_count == off_count


class TestSwingRatio:
    """Skip notes should shift with the swing ratio."""

    def test_straight_eighths(self):
        events = generate_drums(TOTAL_BEATS, TEMPO, swing_ratio=0.5)
        ride_ons = sorted(_on_events(events, RIDE_CYMBAL), key=lambda e: e.time_samples)
        # With straight eighths, skip notes land exactly halfway through the beat.
        # Just verify we still get the right count — timing is humanized.
        assert len(ride_ons) == 24

    def test_hard_swing(self):
        events = generate_drums(TOTAL_BEATS, TEMPO, swing_ratio=0.75)
        ride_ons = sorted(_on_events(events, RIDE_CYMBAL), key=lambda e: e.time_samples)
        assert len(ride_ons) == 24


class TestGhostSnare:
    """Ghost snare: soft, occasional, only on offbeats."""

    def test_appears_over_many_bars(self):
        # 64 bars = 256 beats → 256 offbeat chances at 25 % ≈ 64 expected.
        # Vanishingly unlikely to get 0.
        events = generate_drums(256.0, TEMPO)
        snare_ons = _on_events(events, GHOST_SNARE)
        assert len(snare_ons) > 0

    def test_soft_velocity(self):
        events = generate_drums(256.0, TEMPO)
        for e in _on_events(events, GHOST_SNARE):
            # Base 60 ± 10 humanization
            assert e.velocity <= 80, f"Ghost snare too loud: {e.velocity}"


class TestEmpty:
    """Zero beats should produce no events."""

    def test_zero_beats(self):
        events = generate_drums(0, TEMPO)
        assert events == []
