"""Start & End Note exercise: paint an entry point and a target.

Each *phrase* (a fixed-bar window cycled with the ``P`` key) gets two
pre-picked chord tones:

- ``start_midi`` — a random chord tone of the phrase's *first* chord,
  rendered in red.
- ``end_midi`` — a random chord tone of the phrase's *last* chord,
  rendered in orange.

Both lights stay on for the full phrase. The picks live in MIDI space
(not just pitch class) so the player sees a specific *octave* to land on,
not just a key class. The pick range is fixed to the right-hand register
(C4 up to the calibrated keyboard ceiling) regardless of which
``RangeMode`` the Free Mode base is in — the start/end targets always
sit where solo lines are normally played.

When a phrase spans more than one chord, the anchored MIDIs may not be
in the *currently sounding* chord-scale. To signal "this is your target,
but it isn't safe right now" the overlay applies the same hatched stripe
used by the Guide Tone next-chord preview.

Each successive phrase's ``start_midi`` is biased toward the previous
phrase's ``end_midi`` (within a perfect fifth) so the line voice-leads
between phrases instead of leaping randomly. End notes themselves stay
fully random — it's the next phrase's start that has to land near them.

The pattern is pre-generated and indexed by absolute beat (across every
form repeat), so each form gets independently randomised picks just by
playing through.
"""

from __future__ import annotations

import random
from bisect import bisect_right
from dataclasses import dataclass
from enum import Enum, auto

from leadsheet_utility.exercises.chord_tones import chord_tone_pitch_classes
from leadsheet_utility.exercises.free import RIGHT_HAND_LOW
from leadsheet_utility.leadsheet.models import LeadSheet
from leadsheet_utility.projection import KeyHighlight

# Punchy red for the entry note. Matches the Guide Tone palette — the two
# exercises are never active at once so the shared hue is intentional.
START_COLOR: tuple[int, int, int] = (255, 50, 50)
# Warm orange landing target. Distinct from cyan chord-tone overlay and
# blue root overlay so all four layers read cleanly together.
END_COLOR: tuple[int, int, int] = (255, 140, 40)


class PhraseLength(Enum):
    """How many bars one start/end pair covers (cycled with ``P``)."""

    TWO_BARS = auto()
    FOUR_BARS = auto()
    EIGHT_BARS = auto()


PHRASE_LENGTH_CYCLE: tuple[PhraseLength, ...] = (
    PhraseLength.TWO_BARS,
    PhraseLength.FOUR_BARS,
    PhraseLength.EIGHT_BARS,
)


_PHRASE_BARS: dict[PhraseLength, int] = {
    PhraseLength.TWO_BARS: 2,
    PhraseLength.FOUR_BARS: 4,
    PhraseLength.EIGHT_BARS: 8,
}


def next_phrase_length(p: PhraseLength) -> PhraseLength:
    """Cycle TWO -> FOUR -> EIGHT -> TWO."""
    i = PHRASE_LENGTH_CYCLE.index(p)
    return PHRASE_LENGTH_CYCLE[(i + 1) % len(PHRASE_LENGTH_CYCLE)]


def phrase_length_bars(p: PhraseLength) -> int:
    """Bar count for a phrase-length preset."""
    return _PHRASE_BARS[p]


@dataclass(frozen=True)
class StartEndPhrase:
    """One pre-rolled (start, end) pair covering an absolute beat window."""

    start_beat: float
    end_beat: float
    start_midi: int
    end_midi: int


@dataclass(frozen=True)
class StartEndPattern:
    """Sorted, non-overlapping phrase windows across the whole form span."""

    phrases: tuple[StartEndPhrase, ...]

    def phrase_at(self, beat: float) -> StartEndPhrase | None:
        """Return the phrase covering ``beat``, or ``None`` past the end."""
        if not self.phrases:
            return None
        starts = [p.start_beat for p in self.phrases]
        i = bisect_right(starts, beat) - 1
        if i < 0:
            return None
        ph = self.phrases[i]
        if ph.start_beat <= beat < ph.end_beat:
            return ph
        return None


def _range_bounds(midi_full_low: int, midi_full_high: int) -> tuple[int, int]:
    """Inclusive MIDI bounds the start/end pick must fall inside.

    Fixed to the right-hand register (C4..keyboard ceiling) so targets
    always sit where solo improvisation lives, regardless of which
    ``RangeMode`` the Free Mode base is currently displaying.
    ``midi_full_low`` only kicks in if the projector physically can't
    reach C4 — a calibrated low above C4 wins.
    """
    return max(RIGHT_HAND_LOW, midi_full_low), midi_full_high


def _chord_idx_at(lead_sheet: LeadSheet, beat_in_form: float) -> int:
    """Index of the chord covering ``beat_in_form`` (modulo the form length).

    Linear scan — chord lists are short (tens, not thousands) and this is
    only called O(phrases) times at pattern generation, not per frame.
    """
    if not lead_sheet.chords:
        return -1
    total = lead_sheet.total_beats
    if total <= 0:
        return 0
    b = beat_in_form % total
    for i, c in enumerate(lead_sheet.chords):
        if c.start_beat <= b < c.end_beat:
            return i
    return len(lead_sheet.chords) - 1


_VOICE_LEADING_WINDOW = 7  # semitones — a perfect fifth either side of the
                           # previous end. Wide enough to leave 2-4 chord-tone
                           # candidates per chord, tight enough that the line
                           # always feels stepwise rather than leapy.


def _pick_chord_tone_midi(
    lead_sheet: LeadSheet,
    chord_idx: int,
    midi_low: int,
    midi_high: int,
    rng: random.Random,
    *,
    near: int | None = None,
) -> int | None:
    """Random chord-tone MIDI inside ``[midi_low, midi_high]``.

    Honours the same ``#11`` / ``b6`` substitutions as the comping
    voicings via :func:`chord_tone_pitch_classes`. Returns ``None`` when
    the chord has no chord tones or no candidate MIDIs fit the range
    (e.g. an extremely narrow band that doesn't contain any chord tone —
    vanishingly unlikely but defensive).

    When ``near`` is given, the pick is biased toward MIDIs within
    ``_VOICE_LEADING_WINDOW`` semitones of it so consecutive phrases
    voice-lead instead of leaping. If no chord tone falls in that window
    the constraint is dropped — better a small leap than no target at
    all.
    """
    if chord_idx < 0 or chord_idx >= len(lead_sheet.chords):
        return None
    pcs = chord_tone_pitch_classes(lead_sheet.chords[chord_idx])
    if not pcs:
        return None
    candidates = [n for n in range(midi_low, midi_high + 1) if n % 12 in pcs]
    if not candidates:
        return None
    if near is not None:
        near_candidates = [
            n for n in candidates if abs(n - near) <= _VOICE_LEADING_WINDOW
        ]
        if near_candidates:
            candidates = near_candidates
    return rng.choice(candidates)


def generate_start_end_pattern(
    lead_sheet: LeadSheet,
    phrase_length: PhraseLength,
    *,
    midi_full_low: int,
    midi_full_high: int,
    seed: int | None = None,
) -> StartEndPattern:
    """Pre-roll start/end picks across every form repeat.

    Phrases start at beat 0 and tile the full span; the final phrase is
    clipped to ``total_beats * form_repeats`` so a partial phrase still
    shows targets. Picks are random chord tones in the right-hand
    register (C4..``midi_full_high``) — no voice-leading optimisation
    between consecutive phrases, and no dependency on the user's current
    ``RangeMode`` choice.
    """
    if not lead_sheet.chords:
        return StartEndPattern(phrases=())

    beats_per_bar = lead_sheet.time_signature[0]
    phrase_beats = float(phrase_length_bars(phrase_length) * beats_per_bar)
    if phrase_beats <= 0:
        return StartEndPattern(phrases=())

    total = lead_sheet.total_beats * lead_sheet.form_repeats
    if total <= 0:
        return StartEndPattern(phrases=())

    rng = random.Random(seed)
    midi_low, midi_high = _range_bounds(midi_full_low, midi_full_high)

    phrases: list[StartEndPhrase] = []
    cursor = 0.0
    prev_end_midi: int | None = None
    while cursor < total:
        end = min(cursor + phrase_beats, total)
        start_idx = _chord_idx_at(lead_sheet, cursor)
        # Land just before `end` so the anchor is the chord still sounding
        # at the phrase's tail, not the next phrase's first chord.
        end_idx = _chord_idx_at(lead_sheet, max(cursor, end - 1e-6))
        # Bias the start toward the previous end so consecutive phrases
        # voice-lead. The end itself is left fully random — it's the
        # *next* phrase's start that has to land near it.
        start_midi = _pick_chord_tone_midi(
            lead_sheet, start_idx, midi_low, midi_high, rng,
            near=prev_end_midi,
        )
        end_midi = _pick_chord_tone_midi(
            lead_sheet, end_idx, midi_low, midi_high, rng,
        )
        if start_midi is not None and end_midi is not None:
            phrases.append(
                StartEndPhrase(
                    start_beat=cursor,
                    end_beat=end,
                    start_midi=start_midi,
                    end_midi=end_midi,
                )
            )
            prev_end_midi = end_midi
        cursor = end
    return StartEndPattern(phrases=tuple(phrases))


def apply_start_end_highlight(
    highlights: list[KeyHighlight],
    phrase: StartEndPhrase,
    current_scale_pcs: set[int],
    *,
    start_color: tuple[int, int, int] = START_COLOR,
    end_color: tuple[int, int, int] = END_COLOR,
) -> list[KeyHighlight]:
    """Return ``highlights`` with the phrase's start (red) and end (orange) on top.

    The hatched-stripe flag follows the Guide Tone next-chord preview
    convention: a target whose pitch class isn't in the *current*
    chord-scale is painted with diagonal hashes so the player sees the
    target without being invited to play it right now.

    If start and end happen to be the same MIDI, the end colour wins
    (last-write wins in the renderer) — the resolution target is the
    one the player needs to see.
    """
    targets = {phrase.start_midi, phrase.end_midi}
    out = [h for h in highlights if h.midi_note not in targets]
    out.append(
        KeyHighlight(
            midi_note=phrase.start_midi,
            color=start_color,
            striped=(phrase.start_midi % 12) not in current_scale_pcs,
        )
    )
    if phrase.end_midi != phrase.start_midi:
        out.append(
            KeyHighlight(
                midi_note=phrase.end_midi,
                color=end_color,
                striped=(phrase.end_midi % 12) not in current_scale_pcs,
            )
        )
    else:
        # Same MIDI for both: paint the end colour on top so the
        # resolution target reads through.
        out.append(
            KeyHighlight(
                midi_note=phrase.end_midi,
                color=end_color,
                striped=(phrase.end_midi % 12) not in current_scale_pcs,
            )
        )
    return out
