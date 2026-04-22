"""Drop 2 / Drop 3 voicings with root-as-bass and voice-leading optimisation.

Given a chord's ``chord_tones`` (populated by harmony analysis), we build two
candidate voicing shapes per root octave:

- **Drop 2** (root-bass): ``[R, 5th, 7th, 3rd+12]``
- **Drop 3** (root-bass): ``[R, 7th, 3rd+12, 5th+12]``

For triads (3 chord tones), only the drop-2 analog ``[R, 5th, 3rd+12]`` is used.
The formulas operate on whatever intervals are in ``chord.chord_tones`` — so
7sus4 (``0,5,7,10``) produces a valid sus voicing, and altered/lydian chords
use the same R/3/5/7 shell as their base quality (alterations live in
``available_tensions``, not chord tones).
"""

from __future__ import annotations

from leadsheet_utility.harmony.constants import NOTE_TO_PC
from leadsheet_utility.leadsheet.models import ChordEvent

COMP_ROOT_LOW = 45   # A2
COMP_ROOT_HIGH = 57  # A3
COMP_TOP_MAX = 79    # G5 — don't let top voice exceed this


def _effective_root_pc(chord: ChordEvent) -> int:
    """Return the pitch class to voice as the bass note."""
    if chord.bass_note is not None:
        return NOTE_TO_PC[chord.bass_note]
    return NOTE_TO_PC[chord.root]


def _chord_interval_tuple(chord: ChordEvent) -> tuple[int, ...]:
    """Extract unique chord-tone intervals from root, sorted ascending.

    Returns ``(0, i2, i3)`` for triads or ``(0, i2, i3, i4)`` for 7th chords.
    Operates on ``chord.chord_tones`` (MIDI notes) relative to the effective
    root pitch class.

    Substitutes the natural 5th based on chord context:

    - ``#11`` / ``b5`` extensions or ``maj7#11`` quality → replace 5 with #11 (6)
    - ``b9`` / ``b13`` extensions (phrygian-dominant / harmonic-minor V feel,
      without a natural 13) → replace 5 with b6 (8)
    """
    root_pc = _effective_root_pc(chord)
    seen: set[int] = set()
    intervals: list[int] = []
    for midi in chord.chord_tones:
        interval = (midi - root_pc) % 12
        if interval not in seen:
            seen.add(interval)
            intervals.append(interval)
    intervals.sort()

    if 7 in intervals:
        exts = set(chord.extensions)
        use_sharp11 = "#11" in exts or "b5" in exts or chord.quality == "maj7#11"
        use_flat13 = (
            ("b9" in exts or "b13" in exts)
            and "13" not in exts
            and not use_sharp11
        )
        if use_sharp11:
            intervals = [6 if i == 7 else i for i in intervals]
        elif use_flat13:
            intervals = [8 if i == 7 else i for i in intervals]

    return tuple(intervals)


def build_drop2(root_midi: int, intervals: tuple[int, ...]) -> list[int]:
    """Drop 2 root-bass voicing.

    4-note: ``[R, 5th, 7th, 3rd+12]``.
    3-note triad: ``[R, 5th, 3rd+12]`` — the drop-2 analog for triads.
    """
    if len(intervals) == 4:
        _, i2, i3, i4 = intervals
        return [root_midi, root_midi + i3, root_midi + i4, root_midi + i2 + 12]
    if len(intervals) == 3:
        _, i2, i3 = intervals
        return [root_midi, root_midi + i3, root_midi + i2 + 12]
    raise ValueError(f"Unsupported chord-tone count: {intervals}")


def build_drop3(root_midi: int, intervals: tuple[int, ...]) -> list[int]:
    """Drop 3 root-bass voicing.

    4-note: ``[R, 7th, 3rd+12, 5th+12]``.
    Triads have no distinct drop-3 shape — fall back to drop-2.
    """
    if len(intervals) == 4:
        _, i2, i3, i4 = intervals
        return [root_midi, root_midi + i4, root_midi + i2 + 12, root_midi + i3 + 12]
    return build_drop2(root_midi, intervals)


def candidate_voicings(chord: ChordEvent) -> list[list[int]]:
    """All drop-2 and drop-3 voicings across valid root octaves in register."""
    intervals = _chord_interval_tuple(chord)
    if not intervals:
        return []

    root_pc = _effective_root_pc(chord)
    candidates: list[list[int]] = []
    seen_voicings: set[tuple[int, ...]] = set()

    for root_midi in range(COMP_ROOT_LOW, COMP_ROOT_HIGH + 1):
        if root_midi % 12 != root_pc:
            continue
        for builder in (build_drop2, build_drop3):
            voicing = builder(root_midi, intervals)
            if max(voicing) > COMP_TOP_MAX:
                continue
            key = tuple(voicing)
            if key in seen_voicings:
                continue
            seen_voicings.add(key)
            candidates.append(voicing)

    return candidates


def _movement(a: list[int], b: list[int]) -> int:
    """Total semitone movement between two voicings of equal size."""
    if len(a) != len(b):
        # Triad ↔ 7th: compare common-sized prefix to get a rough cost
        n = min(len(a), len(b))
        return sum(abs(a[i] - b[i]) for i in range(n))
    return sum(abs(a[i] - b[i]) for i in range(len(a)))


def best_voicing(
    chord: ChordEvent,
    prev_voicing: list[int] | None,
) -> list[int]:
    """Pick the drop-2/drop-3 candidate that minimises movement from *prev_voicing*.

    For the first chord (no previous voicing), picks the drop-2 voicing whose
    root is closest to the middle of the valid register.
    """
    candidates = candidate_voicings(chord)
    if not candidates:
        return []

    if prev_voicing is None:
        target_root = (COMP_ROOT_LOW + COMP_ROOT_HIGH) // 2
        return min(candidates, key=lambda v: abs(v[0] - target_root))

    return min(candidates, key=lambda v: _movement(v, prev_voicing))
