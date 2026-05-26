"""Tests for the Flow exercise's pattern generation and gate."""

from leadsheet_utility.exercises import (
    FlowPattern,
    FlowPhrasing,
    generate_flow_pattern,
    next_flow_phrasing,
)
from leadsheet_utility.exercises.flow import _PHRASING_PARAMS


def test_phrasing_cycle_order():
    """D key cycles SHORT -> MEDIUM -> LONG -> SHORT."""
    assert next_flow_phrasing(FlowPhrasing.SHORT) is FlowPhrasing.MEDIUM
    assert next_flow_phrasing(FlowPhrasing.MEDIUM) is FlowPhrasing.LONG
    assert next_flow_phrasing(FlowPhrasing.LONG) is FlowPhrasing.SHORT


def test_pattern_covers_form_without_overshoot():
    """Windows stay inside [0, total_beats] and are well-ordered."""
    pattern = generate_flow_pattern(200.0, FlowPhrasing.MEDIUM, seed=0)
    assert pattern.open_windows
    prev_end = 0.0
    for start, end in pattern.open_windows:
        assert 0.0 <= start < end <= 200.0
        # Strictly increasing — no overlap, no zero-length windows.
        assert start >= prev_end
        prev_end = end


def test_empty_form_yields_empty_pattern():
    assert generate_flow_pattern(0.0).open_windows == ()
    assert generate_flow_pattern(-1.0).open_windows == ()


def test_pattern_is_seeded_deterministic():
    """Same seed and phrasing reproduce the same pattern."""
    a = generate_flow_pattern(100.0, FlowPhrasing.SHORT, seed=42)
    b = generate_flow_pattern(100.0, FlowPhrasing.SHORT, seed=42)
    assert a.open_windows == b.open_windows


def test_different_seeds_produce_different_patterns():
    a = generate_flow_pattern(100.0, FlowPhrasing.SHORT, seed=1)
    b = generate_flow_pattern(100.0, FlowPhrasing.SHORT, seed=2)
    assert a.open_windows != b.open_windows


def test_is_open_inside_and_outside_window():
    pattern = FlowPattern(open_windows=((2.0, 5.0), (10.0, 12.0)))
    assert not pattern.is_open(0.0)
    assert not pattern.is_open(1.99)
    assert pattern.is_open(2.0)
    assert pattern.is_open(4.99)
    assert not pattern.is_open(5.0)  # exclusive end
    assert not pattern.is_open(7.0)
    assert pattern.is_open(10.5)
    assert not pattern.is_open(100.0)


def test_is_open_handles_empty_pattern():
    assert FlowPattern(open_windows=()).is_open(0.0) is False
    assert FlowPattern(open_windows=()).is_open(50.0) is False


def test_play_time_dominates_rest_time_for_every_phrasing():
    """User constraint: playing windows must be longer than rest on average."""
    for phrasing in FlowPhrasing:
        pattern = generate_flow_pattern(2000.0, phrasing, seed=7)
        play_total = sum(end - start for start, end in pattern.open_windows)
        rest_total = 2000.0 - play_total
        assert play_total > rest_total, f"{phrasing.name}: play={play_total} rest={rest_total}"


def test_long_has_longer_phrases_than_short():
    """LONG distinguishes itself by longer playing windows than SHORT.

    Total play time is roughly comparable across phrasings (all keep play
    > rest), but LONG stretches the phrases — the player gets long uninterrupted
    runs punctuated by long rests, while SHORT chops the form into shorter chunks.
    """
    total = 2000.0
    short = generate_flow_pattern(total, FlowPhrasing.SHORT, seed=3).open_windows
    long_ = generate_flow_pattern(total, FlowPhrasing.LONG, seed=3).open_windows
    avg_short = sum(e - s for s, e in short) / len(short)
    avg_long = sum(e - s for s, e in long_) / len(long_)
    assert avg_long > avg_short


def test_durations_fall_inside_phrasing_ranges():
    """Each generated window obeys its phrasing's (min_play, max_play) bound."""
    for phrasing in FlowPhrasing:
        min_p, max_p, _, _ = _PHRASING_PARAMS[phrasing]
        pattern = generate_flow_pattern(500.0, phrasing, seed=11)
        for i, (start, end) in enumerate(pattern.open_windows):
            dur = end - start
            # The final window can be clipped short by the total-beats cap.
            is_last = i == len(pattern.open_windows) - 1
            if is_last and end == 500.0:
                assert 0.0 < dur <= max_p
            else:
                assert min_p <= dur <= max_p, f"{phrasing.name} window {i}: {dur=}"
