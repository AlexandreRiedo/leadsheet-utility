"""Contour exercise: slide a window of scale notes up and down the keyboard.

A pre-rolled smoothed random walk traces a MIDI "center" across the
whole form. Each frame, only chord-scale notes whose MIDI lies within
``±width`` semitones of the current center stay lit; everything else
goes black. The result is a window of ~5–9 consecutive scale notes that
drifts up and down the keyboard over time, forcing the player to think
about *macro* melodic direction instead of just picking notes from the
full scale set.

Curve generation
----------------

The curve is built from random control points spaced 4–8 bars apart in
absolute beats. Each control point's MIDI is sampled as a bounded random
walk from the previous one (``max_step`` ≈ 60% of the projector range)
so consecutive arcs explore most of the keyboard without leaping wildly.
Between control points the curve uses smoothstep (cubic Hermite with
zero tangent), so the contour has continuous slope and never jerks at
arc boundaries.

The center range is the right-hand register
``[max(C4, midi_full_low), midi_full_high]`` — same band Start & End
targets live in — independent of the active ``RangeMode``. Contour is a
*positioning* exercise: where on the keyboard the window sits is the
whole point, so it shouldn't be clamped to a 1-OCT or 2-OCT band.

Composition
-----------

Contour acts as a pure filter on the base highlight list. It runs
*before* the chord-tone, root, and Start & End overlays, so those keep
recolouring whichever scale notes survive the window. If no scale note
falls inside the window on a given frame (e.g. very narrow window over a
sparse pentatonic), the projection goes black — no auto-widen.
"""

from __future__ import annotations

import random
from bisect import bisect_right
from dataclasses import dataclass
from enum import Enum, auto

from leadsheet_utility.exercises.free import RIGHT_HAND_LOW
from leadsheet_utility.projection import KeyHighlight


class WindowWidth(Enum):
    """How wide the lit window is in semitones either side of the center."""

    NARROW = auto()
    MEDIUM = auto()
    WIDE = auto()


WINDOW_WIDTH_CYCLE: tuple[WindowWidth, ...] = (
    WindowWidth.NARROW,
    WindowWidth.MEDIUM,
    WindowWidth.WIDE,
)


# ±semitones around the contour center. ~5/7/11-semitone diameters land
# 3–9 scale notes inside the window for typical 7-note scales.
_WINDOW_SEMITONES: dict[WindowWidth, int] = {
    WindowWidth.NARROW: 2,
    WindowWidth.MEDIUM: 3,
    WindowWidth.WIDE: 5,
}


def next_window_width(w: WindowWidth) -> WindowWidth:
    """Cycle NARROW -> MEDIUM -> WIDE -> NARROW."""
    i = WINDOW_WIDTH_CYCLE.index(w)
    return WINDOW_WIDTH_CYCLE[(i + 1) % len(WINDOW_WIDTH_CYCLE)]


def window_width_semitones(w: WindowWidth) -> int:
    """Half-width in semitones for a preset (``±N`` around the center)."""
    return _WINDOW_SEMITONES[w]


class ContourSpeed(Enum):
    """How fast the window drifts up and down the keyboard.

    Speed controls only the *spacing* between control points (i.e. how
    long an arc lasts); the random-walk step size stays the same, so
    FAST genuinely covers ground faster than SLOW.
    """

    SLOW = auto()
    MEDIUM = auto()
    FAST = auto()


CONTOUR_SPEED_CYCLE: tuple[ContourSpeed, ...] = (
    ContourSpeed.SLOW,
    ContourSpeed.MEDIUM,
    ContourSpeed.FAST,
)


def next_contour_speed(s: ContourSpeed) -> ContourSpeed:
    """Cycle SLOW -> MEDIUM -> FAST -> SLOW."""
    i = CONTOUR_SPEED_CYCLE.index(s)
    return CONTOUR_SPEED_CYCLE[(i + 1) % len(CONTOUR_SPEED_CYCLE)]


# Bars-per-arc bounds per speed preset. Shifted faster than the original
# 4-8 / 8-16 / 2-4 trio after live testing: even SLOW now drifts visibly
# during a single chorus, MEDIUM gives the original FAST feel, and FAST
# undulates within every bar. Smoothstep interpolation keeps the motion
# kink-free even at the 1-2 bar arc length.
_SPEED_BARS_PER_ARC: dict[ContourSpeed, tuple[float, float]] = {
    ContourSpeed.SLOW: (4.0, 8.0),
    ContourSpeed.MEDIUM: (2.0, 4.0),
    ContourSpeed.FAST: (1.0, 2.0),
}


def contour_speed_bars_per_arc(s: ContourSpeed) -> tuple[float, float]:
    """(min_bars, max_bars) arc length range for a speed preset."""
    return _SPEED_BARS_PER_ARC[s]

# Max step between consecutive control points, expressed as a fraction
# of the projector range. ~60% lets the curve reach the extremes in two
# arcs while keeping each arc visually purposeful.
_MAX_STEP_FRACTION = 0.6


@dataclass(frozen=True)
class ContourPattern:
    """Pre-rolled random-walk curve over absolute beats.

    Stored as a sorted list of ``(beat, midi_center)`` control points;
    :meth:`center_at` interpolates between them with smoothstep. The
    first control point lives at beat 0 and the last lives past
    ``total_beats`` so a query at any in-range beat finds two neighbours.
    """

    control_points: tuple[tuple[float, float], ...]

    def center_at(self, beat: float) -> float:
        """Smoothstep-interpolated MIDI center at ``beat``.

        Clamped to the first / last control-point value outside the
        covered range, so a query past the end of the pattern doesn't
        blow up — it just freezes on the final arc.
        """
        cps = self.control_points
        if not cps:
            return 0.0
        if beat <= cps[0][0]:
            return cps[0][1]
        if beat >= cps[-1][0]:
            return cps[-1][1]
        # Binary search the segment containing ``beat``.
        beats = [b for b, _ in cps]
        i = bisect_right(beats, beat) - 1
        b0, m0 = cps[i]
        b1, m1 = cps[i + 1]
        t = (beat - b0) / (b1 - b0)
        # Smoothstep: cubic Hermite with zero tangents at the endpoints.
        # This guarantees the curve never overshoots and has zero
        # velocity at every control point.
        s = t * t * (3.0 - 2.0 * t)
        return m0 + (m1 - m0) * s


def _range_bounds(midi_full_low: int, midi_full_high: int) -> tuple[int, int]:
    """Inclusive MIDI bounds the contour center is allowed to traverse.

    Fixed to the right-hand register (C4..keyboard ceiling) so the
    window stays where solo improvisation lives, independent of the
    active ``RangeMode``. ``midi_full_low`` only kicks in if the
    projector physically can't reach C4.
    """
    return max(RIGHT_HAND_LOW, midi_full_low), midi_full_high


def generate_contour_pattern(
    total_beats: float,
    *,
    midi_full_low: int,
    midi_full_high: int,
    beats_per_bar: int = 4,
    speed: ContourSpeed = ContourSpeed.MEDIUM,
    seed: int | None = None,
) -> ContourPattern:
    """Generate a smoothed random-walk contour spanning ``total_beats``.

    Control points are placed at random intervals determined by
    ``speed`` (see :data:`_SPEED_BARS_PER_ARC`) and sampled as a bounded
    random walk inside the right-hand register. The first point lives
    at beat 0; one extra point is placed past ``total_beats`` so the
    smoothstep interpolation never runs out of a right-hand neighbour
    while playback is in range.
    """
    midi_low, midi_high = _range_bounds(midi_full_low, midi_full_high)
    if midi_high <= midi_low or total_beats <= 0.0:
        # Degenerate range / empty form — emit a single flat point so
        # callers can still query without special-casing.
        return ContourPattern(
            control_points=((0.0, float((midi_low + midi_high) / 2.0)),),
        )

    rng = random.Random(seed)
    span = midi_high - midi_low
    max_step = span * _MAX_STEP_FRACTION

    # Seed somewhere in the middle 50% of the range so the first arc
    # has room to drift in either direction without immediately hitting
    # a wall and getting biased.
    quarter = span * 0.25
    current = rng.uniform(midi_low + quarter, midi_high - quarter)

    bars_min, bars_max = _SPEED_BARS_PER_ARC[speed]
    points: list[tuple[float, float]] = [(0.0, current)]
    cursor = 0.0
    while cursor < total_beats:
        dt = rng.uniform(
            bars_min * beats_per_bar,
            bars_max * beats_per_bar,
        )
        cursor += dt
        low_bound = max(midi_low, current - max_step)
        high_bound = min(midi_high, current + max_step)
        current = rng.uniform(low_bound, high_bound)
        points.append((cursor, current))
    return ContourPattern(control_points=tuple(points))


def apply_contour_window(
    highlights: list[KeyHighlight],
    beat: float,
    pattern: ContourPattern,
    width: WindowWidth,
) -> list[KeyHighlight]:
    """Drop highlights whose MIDI is outside ``±width`` of the contour center.

    Returns a new list; the order of surviving highlights is preserved
    so the chord-tone / root / Start & End overlays that run after this
    filter still see a consistent ordering.
    """
    center = pattern.center_at(beat)
    half = window_width_semitones(width)
    return [h for h in highlights if abs(h.midi_note - center) <= half]
