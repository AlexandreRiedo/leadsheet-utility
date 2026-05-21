"""Tests for Free Mode highlight computation and the shared root overlay."""

from pathlib import Path

import pytest

from leadsheet_utility.exercises import (
    CHORD_TONE_COLOR,
    ROOT_COLOR,
    apply_chord_tone_highlight,
    apply_root_highlight,
    chord_tone_pitch_classes,
    free_mode_highlights,
)
from leadsheet_utility.exercises.free import (
    HIGHLIGHT_COLOR,
    SMALL_RANGE_HIGH,
    SMALL_RANGE_LOW,
)
from leadsheet_utility.harmony import analyze
from leadsheet_utility.harmony.constants import NOTE_TO_PC
from leadsheet_utility.leadsheet.models import ChordEvent
from leadsheet_utility.leadsheet.parser import parse_leadsheet
from leadsheet_utility.projection import KeyHighlight

# Use a real lead sheet so we exercise the full ChordEvent contract,
# not a hand-crafted dataclass that might drift from harmony output.
_FIXTURE = Path(__file__).resolve().parent.parent / "data" / "leadsheets" / "all_the_things_you_are.tsv"


def _first_chord():
    ls = parse_leadsheet(_FIXTURE)
    analyze(ls)
    return ls.chords[0]


def test_free_mode_highlights_every_scale_note_in_default_color():
    chord = _first_chord()
    highlights = free_mode_highlights(chord)
    assert len(highlights) == len(chord.scale_notes)
    assert {h.midi_note for h in highlights} == set(chord.scale_notes)
    assert all(h.color == HIGHLIGHT_COLOR for h in highlights)


def test_apply_root_highlight_recolors_only_root_pitch_class():
    chord = _first_chord()
    root_pc = NOTE_TO_PC[chord.root]
    base = free_mode_highlights(chord)
    overlayed = apply_root_highlight(base, chord)
    for hl in overlayed:
        expected = ROOT_COLOR if hl.midi_note % 12 == root_pc else HIGHLIGHT_COLOR
        assert hl.color == expected, f"midi {hl.midi_note}: wrong color"


def test_apply_root_highlight_is_pure():
    """Overlay must not mutate the caller's list."""
    chord = _first_chord()
    base = free_mode_highlights(chord)
    snapshot = list(base)
    apply_root_highlight(base, chord)
    assert base == snapshot


def test_apply_root_highlight_works_on_arbitrary_highlights():
    """Future exercises emit non-scale colors — the overlay still recolors roots."""
    chord = _first_chord()
    root_pc = NOTE_TO_PC[chord.root]
    red = (255, 50, 50)
    midi_at_root = next(n for n in chord.scale_notes if n % 12 == root_pc)
    midi_off_root = next(n for n in chord.scale_notes if n % 12 != root_pc)
    fake_exercise_output = [
        KeyHighlight(midi_note=midi_at_root, color=red),
        KeyHighlight(midi_note=midi_off_root, color=red),
    ]
    out = apply_root_highlight(fake_exercise_output, chord)
    assert out[0].color == ROOT_COLOR
    assert out[1].color == red


def test_root_color_differs_from_default():
    """Sanity: a player needs to actually see the difference."""
    assert ROOT_COLOR != HIGHLIGHT_COLOR


# --- small (one-octave) sub-mode ---------------------------------------------


def _g_lydian_chord() -> ChordEvent:
    """Synthesize a ChordEvent with a G Lydian scale across all MIDI octaves."""
    pcs = {7, 9, 11, 1, 2, 4, 6}  # G A B C# D E F#
    scale_notes = [n for n in range(21, 109) if n % 12 in pcs]
    return ChordEvent(
        chord_symbol="G:maj7(#11)",
        root="G",
        quality="maj7",
        extensions=["#11"],
        scale_notes=scale_notes,
    )


def test_small_mode_matches_g_lydian_example():
    """User's example: G Lydian -> G4 A4 B4 C#5 D5 E5 F#5 G5."""
    chord = _g_lydian_chord()
    highlights = free_mode_highlights(chord, small=True)
    midis = [h.midi_note for h in highlights]
    # G4=67, A4=69, B4=71, C#5=73, D5=74, E5=76, F#5=78, G5=79
    assert midis == [67, 69, 71, 73, 74, 76, 78, 79]


def test_small_mode_all_notes_within_range():
    """Every possible root (Bb..A) must fit in [Bb3, A5] with its octave."""
    for root, _root_pc in NOTE_TO_PC.items():
        # Synthetic major scale on this root.
        pcs = {(_root_pc + i) % 12 for i in (0, 2, 4, 5, 7, 9, 11)}
        scale_notes = [n for n in range(21, 109) if n % 12 in pcs]
        chord = ChordEvent(
            chord_symbol=f"{root}:maj7",
            root=root,
            quality="maj7",
            scale_notes=scale_notes,
        )
        midis = [h.midi_note for h in free_mode_highlights(chord, small=True)]
        assert midis, f"{root}: empty"
        assert all(SMALL_RANGE_LOW <= m <= SMALL_RANGE_HIGH for m in midis), (
            f"{root}: out of range — {midis}"
        )


def test_small_mode_emits_eight_notes_for_seven_note_scale():
    chord = _g_lydian_chord()
    midis = [h.midi_note for h in free_mode_highlights(chord, small=True)]
    assert len(midis) == 8
    # First and last share a pitch class (octave).
    assert midis[0] % 12 == midis[-1] % 12


def test_small_mode_starts_on_chord_root():
    chord = _g_lydian_chord()
    midis = [h.midi_note for h in free_mode_highlights(chord, small=True)]
    assert midis[0] % 12 == NOTE_TO_PC[chord.root]


def test_small_mode_octave_is_exactly_twelve_above_root():
    chord = _g_lydian_chord()
    midis = [h.midi_note for h in free_mode_highlights(chord, small=True)]
    assert midis[-1] == midis[0] + 12


def test_small_mode_handles_empty_scale():
    chord = ChordEvent(chord_symbol="N.C.", root="C", quality="", scale_notes=[])
    assert free_mode_highlights(chord, small=True) == []


def test_small_mode_composes_with_root_highlight_overlay():
    chord = _g_lydian_chord()
    base = free_mode_highlights(chord, small=True)
    overlayed = apply_root_highlight(base, chord)
    # In one ascending octave, exactly two notes share the root pitch class
    # (the 1st degree and the 8th).
    blues = [h for h in overlayed if h.color == ROOT_COLOR]
    assert len(blues) == 2
    assert {h.midi_note for h in blues} == {67, 79}  # G4 and G5


# --- chord-tones-only sub-mode ----------------------------------------------


def _resolved_chord(symbol: str) -> ChordEvent:
    """Parse + analyze a single chord symbol into a fully populated ChordEvent."""
    from leadsheet_utility.harmony import analyze
    from leadsheet_utility.leadsheet.models import LeadSheet
    from leadsheet_utility.leadsheet.parser import parse_chord_symbol

    c = parse_chord_symbol(symbol)
    c.start_beat, c.end_beat, c.duration_beats = 0.0, 4.0, 4.0
    ls = LeadSheet(chords=[c], total_beats=4.0)
    analyze(ls)
    return ls.chords[0]


@pytest.mark.parametrize(
    "symbol,expected_pcs",
    [
        # C7 -> C E G Bb
        ("C:7", {0, 4, 7, 10}),
        # Db sus4 (triad) -> Db Gb Ab
        ("Db:sus4", {1, 6, 8}),
        # C7sus4 -> C F G Bb
        ("C:7sus4", {0, 5, 7, 10}),
        # Emaj7#11 -> E G# A# D# (5 -> #11 substitution)
        ("E:maj7(#11)", {4, 8, 10, 3}),
    ],
)
def test_chord_tone_pitch_classes_matches_user_examples(symbol, expected_pcs):
    chord = _resolved_chord(symbol)
    assert chord_tone_pitch_classes(chord) == expected_pcs


def test_chord_tone_overlay_preserves_scale_notes():
    """Overlay does not hide notes — chord tones recolored, others untouched."""
    chord = _resolved_chord("C:7")
    base = free_mode_highlights(chord)
    overlayed = apply_chord_tone_highlight(base, chord)
    assert len(overlayed) == len(base)
    assert {h.midi_note for h in overlayed} == {h.midi_note for h in base}


def test_chord_tone_overlay_recolors_only_chord_tones():
    chord = _resolved_chord("C:7")
    pcs = chord_tone_pitch_classes(chord)
    base = free_mode_highlights(chord)
    overlayed = apply_chord_tone_highlight(base, chord)
    for hl in overlayed:
        if hl.midi_note % 12 in pcs:
            assert hl.color == CHORD_TONE_COLOR
        else:
            assert hl.color == HIGHLIGHT_COLOR


def test_chord_tone_overlay_uses_substitution_for_maj7sharp11():
    """Emaj7#11: A# is recolored (substituted for B); B is NOT."""
    chord = _resolved_chord("E:maj7(#11)")
    base = free_mode_highlights(chord)
    overlayed = apply_chord_tone_highlight(base, chord)
    by_midi = {h.midi_note: h.color for h in overlayed}
    # Pick representative midis in range: A#4 = 70 (chord tone via #11), B4 = 71 (NOT a chord tone).
    if 70 in by_midi:
        assert by_midi[70] == CHORD_TONE_COLOR
    if 71 in by_midi:
        assert by_midi[71] == HIGHLIGHT_COLOR


def test_chord_tone_overlay_is_pure():
    chord = _resolved_chord("C:7")
    base = free_mode_highlights(chord)
    snapshot = list(base)
    apply_chord_tone_highlight(base, chord)
    assert base == snapshot


def test_chord_tone_overlay_composes_with_small():
    """Small + chord-tone overlay: 8 scale notes, 4 chord tones blue, rest green."""
    chord = _resolved_chord("C:7")
    base = free_mode_highlights(chord, small=True)
    overlayed = apply_chord_tone_highlight(base, chord)
    blues = [h for h in overlayed if h.color == CHORD_TONE_COLOR]
    greens = [h for h in overlayed if h.color == HIGHLIGHT_COLOR]
    # C Mixolydian small: C D E F G A Bb C -> chord tones C E G Bb show up at 4 positions
    # (C appears twice in small mode — both root and the 8th).
    assert len(blues) == 5
    assert len(greens) == 3


def test_root_overlay_wins_over_chord_tone_overlay():
    """Compose chord-tone first, root second — root keeps its distinct color."""
    chord = _resolved_chord("C:7")
    base = free_mode_highlights(chord)
    out = apply_chord_tone_highlight(base, chord)
    out = apply_root_highlight(out, chord)
    for hl in out:
        if hl.midi_note % 12 == 0:  # C is root
            assert hl.color == ROOT_COLOR
        elif hl.midi_note % 12 in {4, 7, 10}:  # E G Bb chord tones
            assert hl.color == CHORD_TONE_COLOR
        else:
            assert hl.color == HIGHLIGHT_COLOR


def test_chord_tone_overlay_handles_empty():
    chord = ChordEvent(chord_symbol="N.C.", root="C", quality="", chord_tones=[])
    base = free_mode_highlights(chord)
    out = apply_chord_tone_highlight(base, chord)
    # Both empty (nothing to highlight, nothing to recolor).
    assert base == [] and out == []


def test_chord_tone_color_differs_from_other_colors():
    assert CHORD_TONE_COLOR != HIGHLIGHT_COLOR
    assert CHORD_TONE_COLOR != ROOT_COLOR
