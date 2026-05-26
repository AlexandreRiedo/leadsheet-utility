"""Flow exercise: gate the projection on/off with phrases that slip across barlines.

When the pattern is "open", the projection shows whatever the base
exercise (currently Free Mode + sub-toggles) would have shown. When
"closed", the projection goes black and the player is forced to rest.

Switches do not align to bar or chord boundaries — a typical run starts
mid-bar, plays for a few bars, and stops mid-bar in a later chord. The
intent is to force the player to think in melodic phrases rather than
chord-by-chord. Playing windows are longer than resting windows so the
player has room to breathe.

The pattern is pre-generated for the whole form (across every repeat)
once per phrasing change, so the same phrasing replays the same gate
sequence — useful for building muscle memory.
"""

from __future__ import annotations

import random
from bisect import bisect_right
from dataclasses import dataclass
from enum import Enum, auto


class FlowPhrasing(Enum):
    """How long the play / rest windows are.

    Three preset bands cycled with the ``D`` key. The play/rest beat ranges
    behind each preset live in ``_PHRASING_PARAMS`` and are tuned so playing
    always dominates resting on average. The total *play fraction* is roughly
    the same across all three modes — what differs is phrase length: SHORT
    chops the form into many small runs, LONG spreads long uninterrupted
    phrases across long rests.
    """

    SHORT = auto()
    MEDIUM = auto()
    LONG = auto()


PHRASING_CYCLE: tuple[FlowPhrasing, ...] = (
    FlowPhrasing.SHORT,
    FlowPhrasing.MEDIUM,
    FlowPhrasing.LONG,
)


# (min_play, max_play, min_rest, max_rest) in beats. Play is always > rest
# on average so the player gets room to phrase.
_PHRASING_PARAMS: dict[FlowPhrasing, tuple[float, float, float, float]] = {
    FlowPhrasing.SHORT: (4.0, 8.0, 3.0, 5.0),
    FlowPhrasing.MEDIUM: (6.0, 12.0, 2.0, 4.0),
    FlowPhrasing.LONG: (10.0, 16.0, 6.0, 12.0),
}


def next_flow_phrasing(p: FlowPhrasing) -> FlowPhrasing:
    """Cycle SHORT -> MEDIUM -> LONG -> SHORT."""
    i = PHRASING_CYCLE.index(p)
    return PHRASING_CYCLE[(i + 1) % len(PHRASING_CYCLE)]


@dataclass(frozen=True)
class FlowPattern:
    """Pre-generated on/off pattern across the whole form.

    ``open_windows`` is a sorted list of (start_beat, end_beat) ranges in
    which the projection is on. Outside any window the projection is off.
    Both endpoints are in absolute beats from the start of playback so the
    pattern spans every form repeat.
    """

    open_windows: tuple[tuple[float, float], ...]

    def is_open(self, beat: float) -> bool:
        """True if ``beat`` falls inside any open window.

        Binary search over the (sorted, non-overlapping) starts: find the
        last window whose start is <= beat and check whether it also ends
        after beat.
        """
        if not self.open_windows:
            return False
        starts = [s for s, _ in self.open_windows]
        i = bisect_right(starts, beat) - 1
        if i < 0:
            return False
        start, end = self.open_windows[i]
        return start <= beat < end


def generate_flow_pattern(
    total_beats: float,
    phrasing: FlowPhrasing = FlowPhrasing.MEDIUM,
    seed: int | None = None,
) -> FlowPattern:
    """Generate a flow pattern spanning ``total_beats`` from beat 0.

    The first window starts at a random offset in ``[0, max_rest]`` beats
    so playback doesn't always open on the downbeat. Windows alternate
    play / rest / play / ... with durations sampled uniformly from the
    phrasing's (min_play, max_play, min_rest, max_rest) ranges. The final
    window is clipped to ``total_beats`` and dropped if it would be empty.
    """
    if total_beats <= 0.0:
        return FlowPattern(open_windows=())

    rng = random.Random(seed)
    min_p, max_p, min_r, max_r = _PHRASING_PARAMS[phrasing]

    windows: list[tuple[float, float]] = []
    cursor = rng.uniform(0.0, max_r)
    while cursor < total_beats:
        play_end = min(cursor + rng.uniform(min_p, max_p), total_beats)
        if play_end > cursor:
            windows.append((cursor, play_end))
        cursor = play_end + rng.uniform(min_r, max_r)
    return FlowPattern(open_windows=tuple(windows))
