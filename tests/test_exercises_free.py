"""Tests for Free Mode highlight computation and the shared root overlay."""

from pathlib import Path

import pytest

from leadsheet_utility.exercises import (
    CHORD_TONE_COLOR,
    ROOT_COLOR,
    ChordToneMode,
    RangeMode,
    apply_chord_tone_highlight,
    apply_root_highlight,
    chord_tone_only_highlights,
    chord_tone_pitch_classes,
    free_mode_highlights,
    next_chord_tone_mode,
    next_range_mode,
)
from leadsheet_utility.exercises.free import (
    HIGHLIGHT_COLOR,
    ONE_OCTAVE_RANGE_HIGH,
    ONE_OCTAVE_RANGE_LOW,
    TWO_OCTAVE_RANGE_HIGH,
    TWO_OCTAVE_RANGE_LOW,
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
    highlights = free_mode_highlights(chord, range_mode=RangeMode.ONE_OCTAVE)
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
        midis = [h.midi_note for h in free_mode_highlights(chord, range_mode=RangeMode.ONE_OCTAVE)]
        assert midis, f"{root}: empty"
        assert all(ONE_OCTAVE_RANGE_LOW <= m <= ONE_OCTAVE_RANGE_HIGH for m in midis), (
            f"{root}: out of range — {midis}"
        )


def test_small_mode_emits_eight_notes_for_seven_note_scale():
    chord = _g_lydian_chord()
    midis = [h.midi_note for h in free_mode_highlights(chord, range_mode=RangeMode.ONE_OCTAVE)]
    assert len(midis) == 8
    # First and last share a pitch class (octave).
    assert midis[0] % 12 == midis[-1] % 12


def test_small_mode_starts_on_chord_root():
    chord = _g_lydian_chord()
    midis = [h.midi_note for h in free_mode_highlights(chord, range_mode=RangeMode.ONE_OCTAVE)]
    assert midis[0] % 12 == NOTE_TO_PC[chord.root]


def test_small_mode_octave_is_exactly_twelve_above_root():
    chord = _g_lydian_chord()
    midis = [h.midi_note for h in free_mode_highlights(chord, range_mode=RangeMode.ONE_OCTAVE)]
    assert midis[-1] == midis[0] + 12


def test_small_mode_handles_empty_scale():
    chord = ChordEvent(chord_symbol="N.C.", root="C", quality="", scale_notes=[])
    assert free_mode_highlights(chord, range_mode=RangeMode.ONE_OCTAVE) == []


def test_small_mode_composes_with_root_highlight_overlay():
    chord = _g_lydian_chord()
    base = free_mode_highlights(chord, range_mode=RangeMode.ONE_OCTAVE)
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
        # B7b9 (hm5 dominant) -> B D# F# A: natural 5 kept, no 5 -> b6 substitution
        ("B:7(b9)", {11, 3, 6, 9}),
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
    base = free_mode_highlights(chord, range_mode=RangeMode.ONE_OCTAVE)
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


# --- ONLY mode (filter, not overlay) ----------------------------------------


def test_chord_tone_only_highlights_returns_chord_tones_only():
    chord = _resolved_chord("C:7")
    highlights = chord_tone_only_highlights(chord)
    pcs = {h.midi_note % 12 for h in highlights}
    assert pcs == {0, 4, 7, 10}  # C E G Bb only
    assert all(h.color == CHORD_TONE_COLOR for h in highlights)


def test_chord_tone_only_small_emits_no_octave_repeat():
    """C7 small + chord-tone-only: C4 E4 G4 Bb4 (no C5 octave repeat)."""
    chord = _resolved_chord("C:7")
    midis = sorted(h.midi_note for h in chord_tone_only_highlights(chord, range_mode=RangeMode.ONE_OCTAVE))
    assert midis == [60, 64, 67, 70]


def test_chord_tone_only_small_with_substitution():
    """Emaj7#11 small + chord-tone-only: E4 G#4 A#4 D#5 (A# via #11)."""
    chord = _resolved_chord("E:maj7(#11)")
    midis = sorted(h.midi_note for h in chord_tone_only_highlights(chord, range_mode=RangeMode.ONE_OCTAVE))
    assert midis == [64, 68, 70, 75]


def test_chord_tone_only_empty_chord_returns_empty():
    chord = ChordEvent(chord_symbol="N.C.", root="C", quality="", chord_tones=[])
    assert chord_tone_only_highlights(chord) == []


# --- mode cycle --------------------------------------------------------------


def test_chord_tone_mode_cycle_order():
    """T key cycles OFF -> ONLY -> OVERLAY -> OFF."""
    assert next_chord_tone_mode(ChordToneMode.OFF) is ChordToneMode.ONLY
    assert next_chord_tone_mode(ChordToneMode.ONLY) is ChordToneMode.OVERLAY
    assert next_chord_tone_mode(ChordToneMode.OVERLAY) is ChordToneMode.OFF


# --- 2-octave range mode -----------------------------------------------------


def test_range_mode_cycle_order():
    """B key cycles FULL -> R.HAND -> 2-OCT -> 1-OCT -> FULL."""
    assert next_range_mode(RangeMode.FULL) is RangeMode.RIGHT_HAND
    assert next_range_mode(RangeMode.RIGHT_HAND) is RangeMode.TWO_OCTAVE
    assert next_range_mode(RangeMode.TWO_OCTAVE) is RangeMode.ONE_OCTAVE
    assert next_range_mode(RangeMode.ONE_OCTAVE) is RangeMode.FULL


def test_two_octave_mode_g_lydian():
    """G Lydian over 2 octaves: G4..G6, 15 notes total (1..15)."""
    chord = _g_lydian_chord()
    midis = [h.midi_note for h in free_mode_highlights(chord, range_mode=RangeMode.TWO_OCTAVE)]
    # 1st octave: G4 A4 B4 C#5 D5 E5 F#5 = 67, 69, 71, 73, 74, 76, 78
    # 2nd octave: G5 A5 B5 C#6 D6 E6 F#6 = 79, 81, 83, 85, 86, 88, 90
    # 15th degree: G6 = 91
    assert midis == [67, 69, 71, 73, 74, 76, 78, 79, 81, 83, 85, 86, 88, 90, 91]


def test_two_octave_mode_all_roots_fit_in_range():
    """Every chromatic root must place its 2-octave run inside Ab3..G6."""
    for root, root_pc in NOTE_TO_PC.items():
        pcs = {(root_pc + i) % 12 for i in (0, 2, 4, 5, 7, 9, 11)}
        scale_notes = [n for n in range(21, 109) if n % 12 in pcs]
        chord = ChordEvent(
            chord_symbol=f"{root}:maj7",
            root=root,
            quality="maj7",
            scale_notes=scale_notes,
        )
        midis = [h.midi_note for h in free_mode_highlights(chord, range_mode=RangeMode.TWO_OCTAVE)]
        assert midis, f"{root}: empty"
        assert all(TWO_OCTAVE_RANGE_LOW <= m <= TWO_OCTAVE_RANGE_HIGH for m in midis), (
            f"{root}: out of range — min={min(midis)} max={max(midis)} range=[{TWO_OCTAVE_RANGE_LOW},{TWO_OCTAVE_RANGE_HIGH}]"
        )


def test_two_octave_mode_first_and_last_are_root():
    chord = _g_lydian_chord()
    midis = [h.midi_note for h in free_mode_highlights(chord, range_mode=RangeMode.TWO_OCTAVE)]
    assert midis[0] % 12 == NOTE_TO_PC[chord.root]
    assert midis[-1] == midis[0] + 24


def test_two_octave_chord_tones_only_no_octave_repeat():
    """C7 + 2-octave + chord-tones-only: 8 chord tones, no octave repeat."""
    chord = _resolved_chord("C:7")
    midis = sorted(h.midi_note for h in chord_tone_only_highlights(chord, range_mode=RangeMode.TWO_OCTAVE))
    # C4=60, E4=64, G4=67, Bb4=70, C5=72, E5=76, G5=79, Bb5=82
    assert midis == [60, 64, 67, 70, 72, 76, 79, 82]


# --- right-hand range mode ---------------------------------------------------


def test_right_hand_mode_filters_scale_notes_to_c4_and_above():
    """RIGHT_HAND keeps the FULL-style spread but clamped from middle C up."""
    chord = _g_lydian_chord()
    midis = [h.midi_note for h in free_mode_highlights(chord, range_mode=RangeMode.RIGHT_HAND)]
    assert midis  # non-empty
    assert all(m >= 60 for m in midis)
    # Every scale note >= 60 should be present.
    expected = [n for n in chord.scale_notes if n >= 60]
    assert midis == expected


def test_right_hand_chord_tones_only_filters_to_c4_and_above():
    """C7 + RIGHT_HAND + chord-tones-only: every chord tone from C4 to top of MIDI."""
    chord = _resolved_chord("C:7")
    midis = sorted(h.midi_note for h in chord_tone_only_highlights(chord, range_mode=RangeMode.RIGHT_HAND))
    assert midis
    assert all(m >= 60 for m in midis)
    assert {m % 12 for m in midis} == {0, 4, 7, 10}


def test_two_octave_composes_with_root_overlay():
    """2-octave + root highlight: exactly 3 root-colored notes (1, 8, 15)."""
    chord = _g_lydian_chord()
    base = free_mode_highlights(chord, range_mode=RangeMode.TWO_OCTAVE)
    overlayed = apply_root_highlight(base, chord)
    blues = [h for h in overlayed if h.color == ROOT_COLOR]
    assert len(blues) == 3
    assert {h.midi_note for h in blues} == {67, 79, 91}  # G4, G5, G6
