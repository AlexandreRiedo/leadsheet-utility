"""Swing comping rhythm patterns from Phil DeGreg's ``comping-rhythms`` page.

One-bar patterns (1–12) and two-bar patterns (13–16). Positions are in beats,
0-indexed within the pattern window (0=beat 1, 1=beat 2, ..., "and" = +0.5).

Two-bar pattern ``anticipation_beats`` contain hit positions in bar 1 that are
tied into bar 2 — these hits should play the harmony of bar 2 (anticipation).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass(frozen=True)
class RhythmHit:
    beat: float       # 0-indexed within the pattern window
    duration: float   # how long the chord rings (in beats) before the next hit
    accented: bool = False


@dataclass(frozen=True)
class CompingPattern:
    bars: int                                   # 1 or 2
    hits: tuple[RhythmHit, ...]
    anticipation_beats: frozenset[float] = field(default_factory=frozenset)


# ---------------------------------------------------------------------------
# One-bar swing patterns (1–12)
# ---------------------------------------------------------------------------

_ONE_BAR: list[CompingPattern] = [
    # 1: dotted-quarter, 8th (on and of 2), half rest
    CompingPattern(1, (
        RhythmHit(0.0, 1.5),
        RhythmHit(1.5, 0.5),
    )),
    # 2: two 8ths, rest
    CompingPattern(1, (
        RhythmHit(0.0, 0.5),
        RhythmHit(0.5, 1.0),
    )),
    # 3: three quarters (last accented)
    CompingPattern(1, (
        RhythmHit(0.0, 1.0),
        RhythmHit(1.0, 1.0),
        RhythmHit(2.0, 1.0, accented=True),
    )),
    # 4: 8th + accented quarter + half
    CompingPattern(1, (
        RhythmHit(0.0, 0.5),
        RhythmHit(0.5, 1.5, accented=True),
    )),
    # 5: quarters on 1, 2, 4 (staccato feel on 4)
    CompingPattern(1, (
        RhythmHit(0.0, 1.0),
        RhythmHit(1.0, 1.0),
        RhythmHit(3.0, 0.5),
    )),
    # 6: accented and-of-1 + quarter on 2 + and-of-3
    CompingPattern(1, (
        RhythmHit(0.5, 0.5, accented=True),
        RhythmHit(1.0, 1.0),
        RhythmHit(2.5, 0.5),
    )),
    # 7: and-of-1, beat 2, beat 4
    CompingPattern(1, (
        RhythmHit(0.5, 0.5),
        RhythmHit(1.0, 1.0),
        RhythmHit(3.0, 1.0),
    )),
    # 8: beat 1 (half), and-of-3 (accent), beat 4
    CompingPattern(1, (
        RhythmHit(0.0, 2.0),
        RhythmHit(2.5, 0.5, accented=True),
        RhythmHit(3.0, 1.0),
    )),
    # 9: and-of-1, and-of-2, beat 3
    CompingPattern(1, (
        RhythmHit(0.5, 1.0),
        RhythmHit(1.5, 0.5),
        RhythmHit(2.0, 1.0),
    )),
    # 10: beat 1, and-1, beat 2, beat 3, and-3 (busier)
    CompingPattern(1, (
        RhythmHit(0.0, 0.5),
        RhythmHit(0.5, 0.5),
        RhythmHit(1.0, 1.0),
        RhythmHit(2.0, 0.5),
        RhythmHit(2.5, 0.5),
    )),
    # 11: busy eighth-driven
    CompingPattern(1, (
        RhythmHit(0.0, 0.5),
        RhythmHit(0.5, 0.5),
        RhythmHit(1.0, 0.5),
        RhythmHit(1.5, 0.5),
        RhythmHit(2.0, 0.5),
        RhythmHit(2.5, 0.5),
    )),
    # 12: busy pattern with accent on beat 4
    CompingPattern(1, (
        RhythmHit(0.0, 0.5),
        RhythmHit(0.5, 0.5),
        RhythmHit(1.0, 0.5),
        RhythmHit(1.5, 1.0),
        RhythmHit(2.5, 0.5),
        RhythmHit(3.0, 1.0, accented=True),
    )),
]


# ---------------------------------------------------------------------------
# Two-bar swing patterns (13–16) — anticipations cross the barline.
# Hits at beat 3.5 are anticipations of bar 2 (use bar 2's harmony).
# ---------------------------------------------------------------------------

_TWO_BAR: list[CompingPattern] = [
    # 13: bar1 [beat 1, beat 2, and-3 (accent), and-4 tied] + bar 2 [half whole]
    CompingPattern(2, (
        RhythmHit(0.0, 1.0),
        RhythmHit(1.0, 1.0),
        RhythmHit(2.5, 1.0, accented=True),
        RhythmHit(3.5, 1.5),  # anticipation → bar 2
        RhythmHit(5.0, 1.0),
        RhythmHit(6.0, 2.0),
    ), anticipation_beats=frozenset({3.5})),
    # 14: staccato beat 1, anticipation to bar 2; bar 2 = long hold
    CompingPattern(2, (
        RhythmHit(0.0, 0.5),
        RhythmHit(1.0, 1.0),
        RhythmHit(3.5, 2.5),  # anticipation → bar 2, long hold through bar 2 downbeat
        RhythmHit(6.0, 2.0),
    ), anticipation_beats=frozenset({3.5})),
    # 15: beat 1, and-1, beat 3 accent, anticipation; bar 2 = dotted quarter + 8th
    CompingPattern(2, (
        RhythmHit(0.0, 0.5),
        RhythmHit(0.5, 0.5),
        RhythmHit(2.0, 1.0, accented=True),
        RhythmHit(3.5, 1.5),  # anticipation
        RhythmHit(5.0, 1.5),
        RhythmHit(6.5, 0.5, accented=True),
    ), anticipation_beats=frozenset({3.5})),
    # 16: dotted quarter, 8th, anticipation; bar 2 mirrors
    CompingPattern(2, (
        RhythmHit(0.0, 1.5),
        RhythmHit(1.5, 0.5),
        RhythmHit(3.5, 1.5),  # anticipation
        RhythmHit(5.0, 1.5),
        RhythmHit(6.5, 0.5),
    ), anticipation_beats=frozenset({3.5})),
]


SWING_PATTERNS_1BAR: tuple[CompingPattern, ...] = tuple(_ONE_BAR)
SWING_PATTERNS_2BAR: tuple[CompingPattern, ...] = tuple(_TWO_BAR)


def pick_pattern(rng: random.Random, bars_available: int) -> CompingPattern:
    """Pick a random pattern that fits within *bars_available* bars.

    With 2+ bars available, 50/50 chance to return either a 2-bar pattern or
    a 1-bar pattern. Otherwise returns a 1-bar pattern.
    """
    if bars_available >= 2 and rng.random() < 0.5:
        return rng.choice(SWING_PATTERNS_2BAR)
    return rng.choice(SWING_PATTERNS_1BAR)
