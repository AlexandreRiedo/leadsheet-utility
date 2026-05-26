"""Tests for the Start & End Note exercise."""

from pathlib import Path

import pytest

from leadsheet_utility.exercises import (
    END_COLOR,
    START_COLOR,
    PhraseLength,
    StartEndPattern,
    StartEndPhrase,
    apply_start_end_highlight,
    chord_tone_pitch_classes,
    generate_start_end_pattern,
    next_phrase_length,
    phrase_length_bars,
)
from leadsheet_utility.exercises.free import RIGHT_HAND_LOW
from leadsheet_utility.harmony import analyze
from leadsheet_utility.leadsheet.parser import parse_leadsheet
from leadsheet_utility.projection import KeyHighlight

_FIXTURE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "leadsheets"
    / "all_the_things_you_are.tsv"
)


@pytest.fixture
def lead_sheet():
    ls = parse_leadsheet(_FIXTURE)
    analyze(ls)
    return ls


# ---------------------------------------------------------------------------
# PhraseLength enum
# ---------------------------------------------------------------------------


def test_phrase_length_cycle_order():
    """P cycles 2 -> 4 -> 8 -> 2."""
    assert next_phrase_length(PhraseLength.TWO_BARS) is PhraseLength.FOUR_BARS
    assert next_phrase_length(PhraseLength.FOUR_BARS) is PhraseLength.EIGHT_BARS
    assert next_phrase_length(PhraseLength.EIGHT_BARS) is PhraseLength.TWO_BARS


def test_phrase_length_bars_values():
    assert phrase_length_bars(PhraseLength.TWO_BARS) == 2
    assert phrase_length_bars(PhraseLength.FOUR_BARS) == 4
    assert phrase_length_bars(PhraseLength.EIGHT_BARS) == 8


# ---------------------------------------------------------------------------
# generate_start_end_pattern
# ---------------------------------------------------------------------------


def test_pattern_tiles_the_full_span(lead_sheet):
    """Phrases start at beat 0 and tile to the end of every form repeat."""
    pattern = generate_start_end_pattern(
        lead_sheet,
        PhraseLength.FOUR_BARS,
        midi_full_low=29,
        midi_full_high=88,
        seed=0,
    )
    assert pattern.phrases
    assert pattern.phrases[0].start_beat == 0.0
    # Each phrase ends exactly where the next begins.
    for a, b in zip(pattern.phrases, pattern.phrases[1:]):
        assert a.end_beat == b.start_beat
    total = lead_sheet.total_beats * lead_sheet.form_repeats
    assert pattern.phrases[-1].end_beat == pytest.approx(total)


def test_picks_are_chord_tones_of_anchor_chords(lead_sheet):
    """Start = chord tone of first chord in phrase; end = chord tone of last."""
    pattern = generate_start_end_pattern(
        lead_sheet,
        PhraseLength.TWO_BARS,
        midi_full_low=29,
        midi_full_high=88,
        seed=42,
    )
    for phrase in pattern.phrases:
        # Find the anchor chords by mapping beat -> chord_idx via the
        # same wrap-around the pattern generator uses.
        total = lead_sheet.total_beats
        start_chord = _chord_at(lead_sheet, phrase.start_beat % total)
        end_chord = _chord_at(lead_sheet, max(phrase.start_beat, phrase.end_beat - 1e-6) % total)
        assert phrase.start_midi % 12 in chord_tone_pitch_classes(start_chord)
        assert phrase.end_midi % 12 in chord_tone_pitch_classes(end_chord)


def test_picks_land_in_right_hand_register(lead_sheet):
    """All picks fall in [C4, midi_full_high] regardless of RangeMode."""
    pattern = generate_start_end_pattern(
        lead_sheet,
        PhraseLength.FOUR_BARS,
        midi_full_low=29,
        midi_full_high=88,
        seed=3,
    )
    for phrase in pattern.phrases:
        assert phrase.start_midi >= RIGHT_HAND_LOW
        assert phrase.end_midi >= RIGHT_HAND_LOW
        assert phrase.start_midi <= 88
        assert phrase.end_midi <= 88


def test_consecutive_phrases_voice_lead(lead_sheet):
    """Each start lands within a fifth of the previous end whenever a
    chord tone in that window exists. Anchor chords always offer at least
    one chord tone within a fifth of any pitch (chord-tone PCs are spaced
    at most ~5 semitones apart), so the constraint should hold for every
    boundary in a real lead sheet."""
    from leadsheet_utility.exercises.start_end import _VOICE_LEADING_WINDOW

    pattern = generate_start_end_pattern(
        lead_sheet,
        PhraseLength.TWO_BARS,
        midi_full_low=29,
        midi_full_high=88,
        seed=11,
    )
    assert len(pattern.phrases) >= 2
    for prev, curr in zip(pattern.phrases, pattern.phrases[1:]):
        gap = abs(curr.start_midi - prev.end_midi)
        assert gap <= _VOICE_LEADING_WINDOW, (
            f"start {curr.start_midi} too far from prev end {prev.end_midi}"
        )


def test_picks_respect_keyboard_low_above_c4(lead_sheet):
    """When the calibrated low sits above C4, picks must stay above it."""
    pattern = generate_start_end_pattern(
        lead_sheet,
        PhraseLength.FOUR_BARS,
        midi_full_low=65,  # F4 — above C4
        midi_full_high=88,
        seed=4,
    )
    for phrase in pattern.phrases:
        assert phrase.start_midi >= 65
        assert phrase.end_midi >= 65


def test_pattern_is_seeded_deterministic(lead_sheet):
    a = generate_start_end_pattern(
        lead_sheet, PhraseLength.TWO_BARS,
        midi_full_low=29, midi_full_high=88, seed=7,
    )
    b = generate_start_end_pattern(
        lead_sheet, PhraseLength.TWO_BARS,
        midi_full_low=29, midi_full_high=88, seed=7,
    )
    assert a.phrases == b.phrases


def test_different_seeds_produce_different_picks(lead_sheet):
    a = generate_start_end_pattern(
        lead_sheet, PhraseLength.FOUR_BARS,
        midi_full_low=29, midi_full_high=88, seed=1,
    )
    b = generate_start_end_pattern(
        lead_sheet, PhraseLength.FOUR_BARS,
        midi_full_low=29, midi_full_high=88, seed=2,
    )
    assert a.phrases != b.phrases


def test_empty_lead_sheet_yields_empty_pattern():
    from leadsheet_utility.leadsheet.models import LeadSheet

    empty = LeadSheet()
    pattern = generate_start_end_pattern(
        empty, PhraseLength.FOUR_BARS,
        midi_full_low=29, midi_full_high=88,
    )
    assert pattern.phrases == ()


# ---------------------------------------------------------------------------
# StartEndPattern.phrase_at
# ---------------------------------------------------------------------------


def test_phrase_at_locates_correct_window():
    pattern = StartEndPattern(
        phrases=(
            StartEndPhrase(0.0, 8.0, 60, 64),
            StartEndPhrase(8.0, 16.0, 67, 70),
        )
    )
    assert pattern.phrase_at(0.0).start_midi == 60
    assert pattern.phrase_at(7.99).start_midi == 60
    assert pattern.phrase_at(8.0).start_midi == 67
    assert pattern.phrase_at(15.99).start_midi == 67
    # Past the end of the last phrase.
    assert pattern.phrase_at(16.0) is None
    assert pattern.phrase_at(100.0) is None


def test_phrase_at_handles_empty_pattern():
    assert StartEndPattern(phrases=()).phrase_at(0.0) is None


# ---------------------------------------------------------------------------
# apply_start_end_highlight
# ---------------------------------------------------------------------------


def test_apply_highlight_paints_red_start_and_orange_end():
    base = [KeyHighlight(midi_note=60, color=(255, 255, 255))]
    phrase = StartEndPhrase(0.0, 4.0, 64, 67)
    out = apply_start_end_highlight(base, phrase, current_scale_pcs={0, 4, 7})
    by_midi = {h.midi_note: h for h in out}
    assert by_midi[64].color == START_COLOR
    assert by_midi[67].color == END_COLOR
    # Pre-existing base highlight survives.
    assert by_midi[60].color == (255, 255, 255)


def test_apply_highlight_drops_pre_existing_target_highlights():
    """If a target MIDI already had a colour, the overlay wins."""
    base = [
        KeyHighlight(midi_note=64, color=(0, 0, 255)),
        KeyHighlight(midi_note=67, color=(0, 0, 255)),
    ]
    phrase = StartEndPhrase(0.0, 4.0, 64, 67)
    out = apply_start_end_highlight(base, phrase, current_scale_pcs={0, 4, 7})
    by_midi = {h.midi_note: h for h in out}
    assert by_midi[64].color == START_COLOR
    assert by_midi[67].color == END_COLOR
    # No duplicates left behind.
    assert len(out) == 2


def test_target_outside_current_scale_is_striped():
    """Hashes signal 'target visible but not safe to land on now'."""
    phrase = StartEndPhrase(0.0, 4.0, 60, 61)  # 60=C in scale, 61=Db not in scale
    out = apply_start_end_highlight([], phrase, current_scale_pcs={0, 2, 4, 5, 7, 9, 11})
    by_midi = {h.midi_note: h for h in out}
    assert by_midi[60].striped is False
    assert by_midi[61].striped is True


def test_apply_highlight_is_pure():
    """Overlay must not mutate the caller's list."""
    base = [KeyHighlight(midi_note=60, color=(255, 255, 255))]
    snapshot = list(base)
    phrase = StartEndPhrase(0.0, 4.0, 64, 67)
    apply_start_end_highlight(base, phrase, current_scale_pcs={0, 4, 7})
    assert base == snapshot


def test_same_midi_for_start_and_end_paints_end_color():
    """If start == end MIDI, the resolution target wins so the player sees orange."""
    phrase = StartEndPhrase(0.0, 4.0, 64, 64)
    out = apply_start_end_highlight([], phrase, current_scale_pcs={4})
    # Find the *last* highlight on midi 64 — that's what the renderer paints.
    target = [h for h in out if h.midi_note == 64][-1]
    assert target.color == END_COLOR


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _chord_at(lead_sheet, beat_in_form):
    for c in lead_sheet.chords:
        if c.start_beat <= beat_in_form < c.end_beat:
            return c
    return lead_sheet.chords[-1]
