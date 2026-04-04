"""Tests for the timeline module."""

import pytest

from leadsheet_utility.leadsheet.models import ChordEvent, LeadSheet
from leadsheet_utility.timeline import PlaybackState, Timeline, TimelineState


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class FakeClock:
    """Deterministic clock for testing.  Satisfies ClockSource protocol."""

    def __init__(self, start: float = 0.0) -> None:
        self._now = start

    def time(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += seconds


def _chord(root: str, quality: str, start: float, end: float) -> ChordEvent:
    return ChordEvent(
        chord_symbol=f"{root}:{quality}",
        root=root,
        quality=quality,
        start_beat=start,
        end_beat=end,
        duration_beats=end - start,
    )


def _lead_sheet(
    chords: list[ChordEvent],
    tempo: int = 120,
    form_repeats: int = 1,
) -> LeadSheet:
    return LeadSheet(
        chords=chords,
        total_beats=chords[-1].end_beat,
        total_bars=int(chords[-1].end_beat / 4),
        default_tempo=tempo,
        form_repeats=form_repeats,
    )


# A typical 8-bar mini-form (4 chords, 4 beats each = 16 beats total)
CHORDS_4 = [
    _chord("C", "maj7", 0.0, 4.0),
    _chord("A", "min7", 4.0, 8.0),
    _chord("D", "min7", 8.0, 12.0),
    _chord("G", "7", 12.0, 16.0),
]


# ---------------------------------------------------------------------------
# TestTimelineInit
# ---------------------------------------------------------------------------


class TestTimelineInit:
    def test_defaults_to_stopped(self):
        tl = Timeline(_lead_sheet(CHORDS_4), tempo=120, clock=FakeClock())
        assert tl.playback_state is PlaybackState.STOPPED

    def test_total_beats_single_form(self):
        tl = Timeline(_lead_sheet(CHORDS_4), tempo=120, clock=FakeClock())
        assert tl.total_beats == 16.0

    def test_total_beats_with_repeats(self):
        ls = _lead_sheet(CHORDS_4, form_repeats=3)
        tl = Timeline(ls, tempo=120, clock=FakeClock())
        assert tl.total_beats == 48.0

    def test_total_duration_seconds(self):
        # 16 beats at 120 BPM = 8 seconds
        tl = Timeline(_lead_sheet(CHORDS_4), tempo=120, clock=FakeClock())
        assert tl.total_duration_seconds == pytest.approx(8.0)

    def test_accepts_custom_clock(self):
        clock = FakeClock(100.0)
        tl = Timeline(_lead_sheet(CHORDS_4), tempo=120, clock=clock)
        assert tl.playback_state is PlaybackState.STOPPED

    def test_empty_chords_raises(self):
        ls = LeadSheet(chords=[], total_beats=0.0)
        with pytest.raises(ValueError, match="at least one chord"):
            Timeline(ls, tempo=120)


# ---------------------------------------------------------------------------
# TestGetStateStopped
# ---------------------------------------------------------------------------


class TestGetStateStopped:
    def test_beat_is_zero(self):
        tl = Timeline(_lead_sheet(CHORDS_4), tempo=120, clock=FakeClock())
        assert tl.get_state().current_beat == 0.0

    def test_returns_first_chord(self):
        tl = Timeline(_lead_sheet(CHORDS_4), tempo=120, clock=FakeClock())
        assert tl.get_state().current_chord is CHORDS_4[0]

    def test_no_prev_chord(self):
        tl = Timeline(_lead_sheet(CHORDS_4), tempo=120, clock=FakeClock())
        assert tl.get_state().prev_chord is None

    def test_repeat_is_zero(self):
        tl = Timeline(_lead_sheet(CHORDS_4), tempo=120, clock=FakeClock())
        assert tl.get_state().form_repeat == 0

    def test_returns_namedtuple(self):
        tl = Timeline(_lead_sheet(CHORDS_4), tempo=120, clock=FakeClock())
        state = tl.get_state()
        assert isinstance(state, TimelineState)
        beat, chord, prev, repeat = state  # unpacking works
        assert beat == 0.0
        assert chord is CHORDS_4[0]
        assert prev is None
        assert repeat == 0


# ---------------------------------------------------------------------------
# TestGetStatePlaying
# ---------------------------------------------------------------------------


class TestGetStatePlaying:
    def test_beat_at_start(self):
        clock = FakeClock()
        tl = Timeline(_lead_sheet(CHORDS_4), tempo=120, clock=clock)
        tl.play()
        assert tl.get_state().current_beat == pytest.approx(0.0)

    def test_beat_advances(self):
        clock = FakeClock()
        tl = Timeline(_lead_sheet(CHORDS_4), tempo=120, clock=clock)
        tl.play()
        clock.advance(0.5)  # 0.5s at 120 BPM = 1 beat
        assert tl.get_state().current_beat == pytest.approx(1.0)

    def test_beat_position_at_2_seconds(self):
        clock = FakeClock()
        tl = Timeline(_lead_sheet(CHORDS_4), tempo=120, clock=clock)
        tl.play()
        clock.advance(2.0)  # 2s at 120 BPM = 4 beats
        assert tl.get_state().current_beat == pytest.approx(4.0)

    def test_chord_lookup_first(self):
        clock = FakeClock()
        tl = Timeline(_lead_sheet(CHORDS_4), tempo=120, clock=clock)
        tl.play()
        clock.advance(0.5)  # beat 1.0 → still first chord (0–4)
        assert tl.get_state().current_chord is CHORDS_4[0]

    def test_chord_lookup_second(self):
        clock = FakeClock()
        tl = Timeline(_lead_sheet(CHORDS_4), tempo=120, clock=clock)
        tl.play()
        clock.advance(2.5)  # beat 5.0 → second chord (4–8)
        assert tl.get_state().current_chord is CHORDS_4[1]

    def test_chord_lookup_last(self):
        clock = FakeClock()
        tl = Timeline(_lead_sheet(CHORDS_4), tempo=120, clock=clock)
        tl.play()
        clock.advance(7.0)  # beat 14.0 → last chord (12–16)
        assert tl.get_state().current_chord is CHORDS_4[3]

    def test_chord_boundary_returns_new_chord(self):
        """Exactly at a chord's start_beat, it should be the active chord."""
        clock = FakeClock()
        tl = Timeline(_lead_sheet(CHORDS_4), tempo=120, clock=clock)
        tl.play()
        clock.advance(2.0)  # beat 4.0 exactly → second chord
        assert tl.get_state().current_chord is CHORDS_4[1]

    def test_prev_chord_at_first(self):
        clock = FakeClock()
        tl = Timeline(_lead_sheet(CHORDS_4), tempo=120, clock=clock)
        tl.play()
        assert tl.get_state().prev_chord is None

    def test_prev_chord_at_second(self):
        clock = FakeClock()
        tl = Timeline(_lead_sheet(CHORDS_4), tempo=120, clock=clock)
        tl.play()
        clock.advance(2.5)  # beat 5.0 → second chord
        assert tl.get_state().prev_chord is CHORDS_4[0]

    def test_prev_chord_at_last(self):
        clock = FakeClock()
        tl = Timeline(_lead_sheet(CHORDS_4), tempo=120, clock=clock)
        tl.play()
        clock.advance(7.0)  # beat 14.0 → last chord
        assert tl.get_state().prev_chord is CHORDS_4[2]


# ---------------------------------------------------------------------------
# TestFormLooping
# ---------------------------------------------------------------------------


class TestFormLooping:
    def test_repeat_increments(self):
        clock = FakeClock()
        ls = _lead_sheet(CHORDS_4, form_repeats=3)
        tl = Timeline(ls, tempo=120, clock=clock)
        tl.play()
        clock.advance(8.5)  # 17 beats → past first form (16 beats)
        assert tl.get_state().form_repeat == 1

    def test_beat_wraps(self):
        clock = FakeClock()
        ls = _lead_sheet(CHORDS_4, form_repeats=3)
        tl = Timeline(ls, tempo=120, clock=clock)
        tl.play()
        clock.advance(8.5)  # 17 beats → beat_in_form = 1.0
        assert tl.get_state().current_beat == pytest.approx(1.0)

    def test_chord_restarts(self):
        clock = FakeClock()
        ls = _lead_sheet(CHORDS_4, form_repeats=3)
        tl = Timeline(ls, tempo=120, clock=clock)
        tl.play()
        clock.advance(8.5)  # beat_in_form = 1.0 → first chord
        assert tl.get_state().current_chord is CHORDS_4[0]

    def test_prev_chord_at_form_wrap(self):
        """At the first chord of repeat > 0, prev_chord is the last chord."""
        clock = FakeClock()
        ls = _lead_sheet(CHORDS_4, form_repeats=3)
        tl = Timeline(ls, tempo=120, clock=clock)
        tl.play()
        clock.advance(8.1)  # beat 16.2 → form 1, beat_in_form ~0.2
        state = tl.get_state()
        assert state.form_repeat == 1
        assert state.current_chord is CHORDS_4[0]
        assert state.prev_chord is CHORDS_4[-1]

    def test_third_repeat(self):
        clock = FakeClock()
        ls = _lead_sheet(CHORDS_4, form_repeats=4)
        tl = Timeline(ls, tempo=120, clock=clock)
        tl.play()
        clock.advance(17.0)  # 34 beats → repeat 2
        assert tl.get_state().form_repeat == 2


# ---------------------------------------------------------------------------
# TestTransportControls
# ---------------------------------------------------------------------------


class TestTransportControls:
    def test_play_sets_playing(self):
        tl = Timeline(_lead_sheet(CHORDS_4), tempo=120, clock=FakeClock())
        tl.play()
        assert tl.playback_state is PlaybackState.PLAYING

    def test_pause_sets_paused(self):
        tl = Timeline(_lead_sheet(CHORDS_4), tempo=120, clock=FakeClock())
        tl.play()
        tl.pause()
        assert tl.playback_state is PlaybackState.PAUSED

    def test_stop_sets_stopped(self):
        tl = Timeline(_lead_sheet(CHORDS_4), tempo=120, clock=FakeClock())
        tl.play()
        tl.stop()
        assert tl.playback_state is PlaybackState.STOPPED

    def test_pause_freezes_beat(self):
        clock = FakeClock()
        tl = Timeline(_lead_sheet(CHORDS_4), tempo=120, clock=clock)
        tl.play()
        clock.advance(1.0)  # beat 2.0
        tl.pause()
        clock.advance(5.0)  # 5 more seconds pass while paused
        assert tl.get_state().current_beat == pytest.approx(2.0)

    def test_unpause_resumes(self):
        clock = FakeClock()
        tl = Timeline(_lead_sheet(CHORDS_4), tempo=120, clock=clock)
        tl.play()
        clock.advance(1.0)  # beat 2.0
        tl.pause()
        clock.advance(5.0)  # paused for 5s
        tl.play()  # resume
        clock.advance(1.0)  # 1 more second of playing → beat 4.0
        assert tl.get_state().current_beat == pytest.approx(4.0)

    def test_multiple_pause_resume_cycles(self):
        clock = FakeClock()
        tl = Timeline(_lead_sheet(CHORDS_4), tempo=120, clock=clock)
        tl.play()
        clock.advance(0.5)  # 1 beat
        tl.pause()
        clock.advance(10.0)
        tl.play()
        clock.advance(0.5)  # 1 beat
        tl.pause()
        clock.advance(10.0)
        tl.play()
        clock.advance(0.5)  # 1 beat → total 3 beats
        assert tl.get_state().current_beat == pytest.approx(3.0)

    def test_stop_resets(self):
        clock = FakeClock()
        tl = Timeline(_lead_sheet(CHORDS_4), tempo=120, clock=clock)
        tl.play()
        clock.advance(3.0)
        tl.stop()
        assert tl.get_state().current_beat == 0.0
        assert tl.get_state().current_chord is CHORDS_4[0]

    def test_play_after_stop_starts_fresh(self):
        clock = FakeClock()
        tl = Timeline(_lead_sheet(CHORDS_4), tempo=120, clock=clock)
        tl.play()
        clock.advance(3.0)  # beat 6
        tl.stop()
        clock.advance(1.0)  # 1s passes while stopped
        tl.play()
        clock.advance(0.5)  # 1 beat from new start
        assert tl.get_state().current_beat == pytest.approx(1.0)

    def test_pause_while_stopped_is_noop(self):
        tl = Timeline(_lead_sheet(CHORDS_4), tempo=120, clock=FakeClock())
        tl.pause()
        assert tl.playback_state is PlaybackState.STOPPED

    def test_play_while_playing_is_noop(self):
        clock = FakeClock()
        tl = Timeline(_lead_sheet(CHORDS_4), tempo=120, clock=clock)
        tl.play()
        clock.advance(1.0)  # beat 2
        tl.play()  # should not reset start time
        assert tl.get_state().current_beat == pytest.approx(2.0)


# ---------------------------------------------------------------------------
# TestEndOfPlayback
# ---------------------------------------------------------------------------


class TestEndOfPlayback:
    def test_clamps_at_end(self):
        clock = FakeClock()
        tl = Timeline(_lead_sheet(CHORDS_4), tempo=120, clock=clock)
        tl.play()
        clock.advance(100.0)  # way past the end (8s total)
        state = tl.get_state()
        assert state.current_beat < 16.0

    def test_last_chord_visible(self):
        clock = FakeClock()
        tl = Timeline(_lead_sheet(CHORDS_4), tempo=120, clock=clock)
        tl.play()
        clock.advance(100.0)
        assert tl.get_state().current_chord is CHORDS_4[-1]

    def test_form_repeat_at_end(self):
        clock = FakeClock()
        ls = _lead_sheet(CHORDS_4, form_repeats=3)
        tl = Timeline(ls, tempo=120, clock=clock)
        tl.play()
        clock.advance(100.0)  # way past 24s total
        assert tl.get_state().form_repeat == 2  # 0-indexed last repeat


# ---------------------------------------------------------------------------
# TestEdgeCases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_single_chord_form(self):
        chords = [_chord("C", "maj7", 0.0, 4.0)]
        clock = FakeClock()
        tl = Timeline(_lead_sheet(chords), tempo=120, clock=clock)
        tl.play()
        clock.advance(0.5)
        state = tl.get_state()
        assert state.current_chord.root == "C"
        assert state.prev_chord is None

    def test_fast_tempo(self):
        clock = FakeClock()
        tl = Timeline(_lead_sheet(CHORDS_4), tempo=300, clock=clock)
        tl.play()
        clock.advance(0.2)  # 0.2s at 300 BPM = 1 beat
        assert tl.get_state().current_beat == pytest.approx(1.0)

    def test_fractional_beat_chords(self):
        chords = [
            _chord("C", "maj7", 0.0, 2.5),
            _chord("D", "min7", 2.5, 4.0),
        ]
        clock = FakeClock()
        tl = Timeline(_lead_sheet(chords), tempo=120, clock=clock)
        tl.play()
        clock.advance(1.0)  # beat 2.0 → still first chord
        assert tl.get_state().current_chord.root == "C"
        clock.advance(0.5)  # beat 3.0 → second chord
        assert tl.get_state().current_chord.root == "D"

    def test_two_beat_chord_boundary(self):
        """Exactly at beat 2.5 should resolve to the second chord."""
        chords = [
            _chord("C", "maj7", 0.0, 2.5),
            _chord("D", "min7", 2.5, 4.0),
        ]
        clock = FakeClock()
        tl = Timeline(_lead_sheet(chords), tempo=120, clock=clock)
        tl.play()
        clock.advance(1.25)  # beat 2.5 exactly
        assert tl.get_state().current_chord.root == "D"
