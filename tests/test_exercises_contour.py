"""Tests for the Contour exercise's pattern generation and window filter."""

from leadsheet_utility.exercises import (
    ContourPattern,
    ContourSpeed,
    WindowWidth,
    apply_contour_window,
    contour_speed_bars_per_arc,
    generate_contour_pattern,
    next_contour_speed,
    next_window_width,
    window_width_semitones,
)
from leadsheet_utility.projection import KeyHighlight


def _hl(midi: int) -> KeyHighlight:
    return KeyHighlight(midi_note=midi, color=(255, 255, 255))


# ---------------------------------------------------------------------------
# Cycle / preset helpers
# ---------------------------------------------------------------------------


def test_window_width_cycle_order():
    """W key cycles NARROW -> MEDIUM -> WIDE -> NARROW."""
    assert next_window_width(WindowWidth.NARROW) is WindowWidth.MEDIUM
    assert next_window_width(WindowWidth.MEDIUM) is WindowWidth.WIDE
    assert next_window_width(WindowWidth.WIDE) is WindowWidth.NARROW


def test_window_width_semitones_match_spec():
    """User-chosen presets: NARROW=±2, MEDIUM=±3, WIDE=±5 semitones."""
    assert window_width_semitones(WindowWidth.NARROW) == 2
    assert window_width_semitones(WindowWidth.MEDIUM) == 3
    assert window_width_semitones(WindowWidth.WIDE) == 5


def test_contour_speed_cycle_order():
    """X key cycles SLOW -> MEDIUM -> FAST -> SLOW."""
    assert next_contour_speed(ContourSpeed.SLOW) is ContourSpeed.MEDIUM
    assert next_contour_speed(ContourSpeed.MEDIUM) is ContourSpeed.FAST
    assert next_contour_speed(ContourSpeed.FAST) is ContourSpeed.SLOW


def test_contour_speed_bars_per_arc_strictly_monotone():
    """SLOW arcs are strictly longer than MEDIUM, MEDIUM longer than FAST."""
    slow = contour_speed_bars_per_arc(ContourSpeed.SLOW)
    med = contour_speed_bars_per_arc(ContourSpeed.MEDIUM)
    fast = contour_speed_bars_per_arc(ContourSpeed.FAST)
    # min and max both shift monotonically — no overlap that would let
    # a single seed produce identical arc lengths across two presets.
    assert slow[0] > med[0] > fast[0]
    assert slow[1] > med[1] > fast[1]


# ---------------------------------------------------------------------------
# Curve generation
# ---------------------------------------------------------------------------


def test_pattern_starts_at_beat_zero_and_covers_total():
    """First control point is at beat 0; last is at or past total_beats."""
    pattern = generate_contour_pattern(
        200.0, midi_full_low=36, midi_full_high=88, seed=0,
    )
    assert pattern.control_points[0][0] == 0.0
    assert pattern.control_points[-1][0] >= 200.0


def test_control_points_stay_inside_right_hand_register():
    """Centers never wander below C4 or above the calibrated ceiling."""
    pattern = generate_contour_pattern(
        500.0, midi_full_low=36, midi_full_high=88, seed=3,
    )
    for _, midi in pattern.control_points:
        # C4 = 60 is the right-hand floor; midi_full_high = 88 the ceiling.
        assert 60.0 <= midi <= 88.0


def test_low_calibration_floor_wins_over_c4():
    """If the projector can't reach C4, the higher floor wins."""
    pattern = generate_contour_pattern(
        200.0, midi_full_low=65, midi_full_high=88, seed=4,
    )
    for _, midi in pattern.control_points:
        assert 65.0 <= midi <= 88.0


def test_control_point_spacing_inside_bars_per_arc_range():
    """Consecutive control points fall inside the active speed's arc range."""
    beats_per_bar = 4
    for speed in ContourSpeed:
        bars_min, bars_max = contour_speed_bars_per_arc(speed)
        pattern = generate_contour_pattern(
            1000.0,
            midi_full_low=36,
            midi_full_high=88,
            beats_per_bar=beats_per_bar,
            speed=speed,
            seed=5,
        )
        for (b0, _), (b1, _) in zip(pattern.control_points, pattern.control_points[1:]):
            dt = b1 - b0
            assert bars_min * beats_per_bar <= dt <= bars_max * beats_per_bar, (
                f"{speed.name}: arc {dt} beats outside [{bars_min}, {bars_max}] bars"
            )


def test_pattern_is_seeded_deterministic():
    a = generate_contour_pattern(100.0, midi_full_low=36, midi_full_high=88, seed=42)
    b = generate_contour_pattern(100.0, midi_full_low=36, midi_full_high=88, seed=42)
    assert a.control_points == b.control_points


def test_different_seeds_produce_different_patterns():
    a = generate_contour_pattern(100.0, midi_full_low=36, midi_full_high=88, seed=1)
    b = generate_contour_pattern(100.0, midi_full_low=36, midi_full_high=88, seed=2)
    assert a.control_points != b.control_points


def test_degenerate_range_yields_single_flat_point():
    """When low >= high (impossible calibration), emit a flat curve."""
    pattern = generate_contour_pattern(
        100.0, midi_full_low=88, midi_full_high=88, seed=0,
    )
    # Single point — center is flat.
    assert len(pattern.control_points) == 1


def test_empty_form_yields_safe_pattern():
    """total_beats=0 must still be queryable without raising."""
    pattern = generate_contour_pattern(
        0.0, midi_full_low=36, midi_full_high=88, seed=0,
    )
    # Caller still does pattern.center_at(0.0) at startup — it must not blow up.
    assert pattern.center_at(0.0) >= 0.0


# ---------------------------------------------------------------------------
# center_at interpolation
# ---------------------------------------------------------------------------


def test_center_at_control_point_returns_exact_value():
    """Smoothstep is exact at t=0 and t=1, so control points read back unchanged."""
    pattern = ContourPattern(control_points=((0.0, 60.0), (10.0, 72.0), (20.0, 64.0)))
    assert pattern.center_at(0.0) == 60.0
    assert pattern.center_at(10.0) == 72.0
    assert pattern.center_at(20.0) == 64.0


def test_center_at_midpoint_is_halfway_under_smoothstep():
    """smoothstep(0.5) = 0.5 → exact midpoint between consecutive controls."""
    pattern = ContourPattern(control_points=((0.0, 60.0), (10.0, 80.0)))
    assert pattern.center_at(5.0) == 70.0


def test_center_at_clamps_outside_pattern_range():
    """Queries before / after the pattern freeze on the boundary value."""
    pattern = ContourPattern(control_points=((0.0, 60.0), (10.0, 80.0)))
    assert pattern.center_at(-5.0) == 60.0
    assert pattern.center_at(20.0) == 80.0


def test_center_at_is_continuous_no_jumps():
    """Smoothstep guarantees small per-beat motion (no chord-boundary leaps)."""
    pattern = generate_contour_pattern(
        300.0, midi_full_low=36, midi_full_high=88, seed=6,
    )
    prev = pattern.center_at(0.0)
    # Sampling every 0.25 beat — even on the fastest arc (4 bars = 16 beats
    # of arc with up to ~17 semitones of swing) per-step motion is bounded.
    for i in range(1, 800):
        beat = i * 0.25
        cur = pattern.center_at(beat)
        # 1 semitone per 0.25 beat is plenty of headroom — the actual
        # peak velocity of a smoothstep arc is 1.5 * span / arc_length,
        # which is well under that bound for our parameters.
        assert abs(cur - prev) < 1.0
        prev = cur


# ---------------------------------------------------------------------------
# Window filter
# ---------------------------------------------------------------------------


def test_window_keeps_only_notes_within_half_width():
    """±3 semitones around C5 (midi 72) keeps midi 69..75 inclusive."""
    highlights = [_hl(m) for m in range(60, 85)]
    pattern = ContourPattern(control_points=((0.0, 72.0),))
    out = apply_contour_window(highlights, 0.0, pattern, WindowWidth.MEDIUM)
    survived_midis = [h.midi_note for h in out]
    assert survived_midis == [69, 70, 71, 72, 73, 74, 75]


def test_window_uses_continuous_center():
    """Mid-arc center is a float; ±N filter must round on absolute distance."""
    # Center 70.5 with ±2 → keeps midi 69, 70, 71, 72 (|m - 70.5| <= 2).
    highlights = [_hl(m) for m in range(60, 80)]
    pattern = ContourPattern(control_points=((0.0, 69.0), (10.0, 72.0)))
    out = apply_contour_window(highlights, 5.0, pattern, WindowWidth.NARROW)
    survived = sorted(h.midi_note for h in out)
    # smoothstep(0.5) = 0.5 → center = 70.5; ±2 includes 69..72.
    assert survived == [69, 70, 71, 72]


def test_empty_window_returns_empty_list():
    """If no highlight falls in the window, the projection goes black."""
    highlights = [_hl(60), _hl(61), _hl(62)]
    # Center is way above the highlights → nothing survives.
    pattern = ContourPattern(control_points=((0.0, 80.0),))
    out = apply_contour_window(highlights, 0.0, pattern, WindowWidth.NARROW)
    assert out == []


def test_window_preserves_order_of_surviving_highlights():
    """Order matters for later overlays — survivors stay in input order."""
    highlights = [_hl(72), _hl(70), _hl(74), _hl(68), _hl(76)]
    pattern = ContourPattern(control_points=((0.0, 72.0),))
    out = apply_contour_window(highlights, 0.0, pattern, WindowWidth.MEDIUM)
    # ±3 around 72 keeps 69..75 — 68 and 76 are dropped, order preserved.
    assert [h.midi_note for h in out] == [72, 70, 74]


def test_window_returns_new_list_does_not_mutate_input():
    """Filter is non-destructive — Free Mode reuses the highlight list."""
    highlights = [_hl(60), _hl(72), _hl(84)]
    pattern = ContourPattern(control_points=((0.0, 72.0),))
    out = apply_contour_window(highlights, 0.0, pattern, WindowWidth.NARROW)
    assert out is not highlights
    assert [h.midi_note for h in highlights] == [60, 72, 84]
