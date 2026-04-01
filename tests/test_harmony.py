"""Tests for the harmony module.

Covers: scale generation, default quality-to-scale lookup, extension overrides,
context rules (Rules 1–5), chain detection (Rules 3 & 4), analyze(), and
guide-tone voice-leading.
"""

import pytest

from leadsheet_utility.harmony import analyze, get_scale_midi_notes, resolve_scale
from leadsheet_utility.harmony.constants import SCALES
from leadsheet_utility.harmony.core import _assign_chain_overrides
from leadsheet_utility.leadsheet.models import ChordEvent, LeadSheet

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_chord(root: str, quality: str, extensions: list[str] | None = None) -> ChordEvent:
    return ChordEvent(
        chord_symbol=f"{root}:{quality}",
        root=root,
        quality=quality,
        extensions=extensions or [],
    )


# ---------------------------------------------------------------------------
# get_scale_midi_notes
# ---------------------------------------------------------------------------

class TestGetScaleMidiNotes:
    def test_c_ionian_contains_all_c_major_notes(self):
        notes = get_scale_midi_notes(0, SCALES["ionian"])
        # All MIDI notes for C, D, E, F, G, A, B should be present
        assert all(n % 12 in {0, 2, 4, 5, 7, 9, 11} for n in notes)

    def test_c_ionian_excludes_sharps(self):
        notes = get_scale_midi_notes(0, SCALES["ionian"])
        assert all(n % 12 not in {1, 3, 6, 8, 10} for n in notes)

    def test_range_is_21_to_108(self):
        notes = get_scale_midi_notes(0, SCALES["ionian"])
        assert min(notes) >= 21
        assert max(notes) <= 108

    def test_bb_dorian_root(self):
        # Bb = pitch class 10
        notes = get_scale_midi_notes(10, SCALES["dorian"])
        # Dorian intervals: 0,2,3,5,7,9,10 → Bb C Db Eb F G Ab
        expected_pcs = {(10 + i) % 12 for i in (0, 2, 3, 5, 7, 9, 10)}
        assert all(n % 12 in expected_pcs for n in notes)

    def test_whole_tone_has_six_notes_per_octave(self):
        # Whole-tone has 6 distinct pitch classes
        notes = get_scale_midi_notes(0, SCALES["whole_tone"])
        pcs = {n % 12 for n in notes}
        assert len(pcs) == 6

    def test_half_whole_dim_has_eight_notes_per_octave(self):
        notes = get_scale_midi_notes(0, SCALES["half_whole_dim"])
        pcs = {n % 12 for n in notes}
        assert len(pcs) == 8


# ---------------------------------------------------------------------------
# Default quality-to-scale mapping (Layer 1)
# ---------------------------------------------------------------------------

class TestDefaultQualityToScale:
    @pytest.mark.parametrize("quality,expected_scale", [
        ("maj7",    "ionian"),
        ("maj",     "ionian"),
        ("6",       "ionian"),
        ("maj9",    "ionian"),
        ("maj69",   "ionian"),
        ("maj7#11", "lydian"),
        ("7",       "mixolydian"),
        ("9",       "mixolydian"),
        ("sus4",    "mixolydian"),
        ("7sus4",   "mixolydian"),
        ("min7",    "dorian"),
        ("min",     "dorian"),
        ("min6",    "dorian"),
        ("min9",    "dorian"),
        ("minmaj7", "melodic_minor"),
        ("hdim7",   "locrian_nat9"), # Without the context of a following 7, it should use the locrian_nat9
        ("dim7",    "whole_half_dim"),
        ("aug",     "whole_tone"),
    ])
    def test_default_lookup(self, quality: str, expected_scale: str):
        chord = make_chord("C", quality)
        assert resolve_scale(None, chord, None) == expected_scale


# ---------------------------------------------------------------------------
# Extension overrides (Priority 1)
# ---------------------------------------------------------------------------

class TestExtensionOverrides:
    @pytest.mark.parametrize("extensions,expected_scale", [
        (["b9"],          "phrygian_dom"),
        (["b13"],         "phrygian_dom"),
        (["b9", "b13"],   "phrygian_dom"),
        (["b9", "13"],    "half_whole_dim"),
        (["#9"],          "altered"),
        (["b9", "#9"],    "altered"),
        (["#5"],          "whole_tone"),
        (["#11"],         "lydian_dominant"),
        (["b5"],          "lydian_dominant"),
        (["13"],          "mixolydian"),
    ])
    def test_dom7_extension_overrides(self, extensions: list[str], expected_scale: str):
        chord = make_chord("G", "7", extensions)
        assert resolve_scale(None, chord, None) == expected_scale

    def test_extension_does_not_apply_to_non_dominant(self):
        # b9 on a minor chord → no override, default applies
        chord = make_chord("G", "min7", ["b9"])
        assert resolve_scale(None, chord, None) == "dorian"

    def test_sharp9_beats_b9(self):
        # #9 present → altered, even if b9 also present
        chord = make_chord("G", "7", ["b9", "#9"])
        assert resolve_scale(None, chord, None) == "altered"


# ---------------------------------------------------------------------------
# Rule 1: V7 resolving to minor
# ---------------------------------------------------------------------------

class TestRule1V7ToMinor:
    def test_g7_to_cmin7(self):
        dom = make_chord("G", "7")
        tgt = make_chord("C", "min7")
        assert resolve_scale(None, dom, tgt) == "phrygian_dom"

    def test_d7_to_gmin7(self):
        dom = make_chord("D", "7")
        tgt = make_chord("G", "min7")
        assert resolve_scale(None, dom, tgt) == "phrygian_dom"

    def test_g7_to_cmaj7_is_mixolydian(self):
        dom = make_chord("G", "7")
        tgt = make_chord("C", "maj7")
        assert resolve_scale(None, dom, tgt) == "mixolydian"

    def test_g7_to_cmin_triad(self):
        dom = make_chord("G", "7")
        tgt = make_chord("C", "min")
        assert resolve_scale(None, dom, tgt) == "phrygian_dom"

    def test_extension_beats_rule1(self):
        # Explicit #9 extension overrides everything, including Rule 1
        dom = make_chord("G", "7", ["#9"])
        tgt = make_chord("C", "min7")
        assert resolve_scale(None, dom, tgt) == "altered"

    def test_wrong_interval_not_rule1(self):
        # A:7 → C:min7 — interval (9-0)%12 = 9, not 7 → no Rule 1
        dom = make_chord("A", "7")
        tgt = make_chord("C", "min7")
        assert resolve_scale(None, dom, tgt) == "mixolydian"


# ---------------------------------------------------------------------------
# Rule 2: Tritone substitution
# ---------------------------------------------------------------------------

class TestRule2TritoneSub:
    def test_db7_to_cmaj7(self):
        sub = make_chord("Db", "7")
        tgt = make_chord("C", "maj7")
        assert resolve_scale(None, sub, tgt) == "lydian_dominant"

    def test_f7_to_emaj7(self):
        sub = make_chord("F", "7")
        tgt = make_chord("E", "maj7")
        # (5 - 4) % 12 = 1 → tritone sub
        assert resolve_scale(None, sub, tgt) == "lydian_dominant"

    def test_not_tritone_sub_when_interval_is_2(self):
        chord = make_chord("D", "7")
        tgt = make_chord("C", "maj7")
        # (2 - 0) % 12 = 2, not 1
        assert resolve_scale(None, chord, tgt) == "mixolydian"


# ---------------------------------------------------------------------------
# Rule 5: IV chord in major context
# ---------------------------------------------------------------------------

class TestRule5IVInMajor:
    def test_fmaj7_after_cmaj7_gets_lydian(self):
        prev = make_chord("C", "maj7")
        curr = make_chord("F", "maj7")
        # (5 - 0) % 12 = 5 → P4 ascending → IV
        assert resolve_scale(prev, curr, None) == "lydian"

    def test_cmaj7_after_gmaj7_gets_lydian(self):
        prev = make_chord("G", "maj7")
        curr = make_chord("C", "maj7")
        # (0 - 7) % 12 = 5
        assert resolve_scale(prev, curr, None) == "lydian"

    def test_maj7_after_min7_does_not_get_lydian(self):
        prev = make_chord("C", "min7")
        curr = make_chord("F", "maj7")
        assert resolve_scale(prev, curr, None) == "ionian"

    def test_cmaj7_no_context_gets_ionian(self):
        assert resolve_scale(None, make_chord("C", "maj7"), None) == "ionian"


# ---------------------------------------------------------------------------
# Rules 3 & 4: ii-V chain and I-vi-ii-V turnaround
# ---------------------------------------------------------------------------

class TestChainOverrides:
    def test_vi_ii_v_chain_assigns_aeolian_to_vi(self):
        # A:min7 → D:min7 → G:7 in C major
        chords = [
            make_chord("A", "min7"),
            make_chord("D", "min7"),
            make_chord("G", "7"),
        ]
        overrides = _assign_chain_overrides(chords)
        assert overrides[0] == "aeolian"   # vi
        assert overrides[1] == "dorian"    # ii
        # V (index 2) not in overrides — handled by default/Rule 1

    def test_iii_vi_ii_v_chain(self):
        # E:min7 → A:min7 → D:min7 → G:7 in C major
        chords = [
            make_chord("E", "min7"),
            make_chord("A", "min7"),
            make_chord("D", "min7"),
            make_chord("G", "7"),
        ]
        overrides = _assign_chain_overrides(chords)
        assert overrides[0] == "phrygian"  # iii
        assert overrides[1] == "aeolian"   # vi
        assert overrides[2] == "dorian"    # ii

    def test_i_vi_ii_v_turnaround(self):
        # C:maj7 → A:min7 → D:min7 → G:7
        chords = [
            make_chord("C", "maj7"),
            make_chord("A", "min7"),
            make_chord("D", "min7"),
            make_chord("G", "7"),
        ]
        overrides = _assign_chain_overrides(chords)
        assert overrides[0] == "ionian"    # I
        assert overrides[1] == "aeolian"   # vi
        assert overrides[2] == "dorian"    # ii

    def test_isolated_ii_v_no_override_for_plain_dorian(self):
        # D:min7 → G:7 alone — ii stays dorian (its default), no override needed
        chords = [make_chord("D", "min7"), make_chord("G", "7")]
        overrides = _assign_chain_overrides(chords)
        # Dorian override may or may not be set; if set it must equal "dorian"
        if 0 in overrides:
            assert overrides[0] == "dorian"

    def test_chain_overrides_dorian_default_for_vi(self):
        # Full resolve_scale call: A:min7 in a vi-ii-V chain should get aeolian,
        # not the default dorian.
        chords = [
            make_chord("A", "min7"),
            make_chord("D", "min7"),
            make_chord("G", "7"),
        ]
        overrides = _assign_chain_overrides(chords)
        vi = chords[0]
        result = resolve_scale(None, vi, chords[1], chain_override=overrides.get(0))
        assert result == "aeolian"


# ---------------------------------------------------------------------------
# analyze()
# ---------------------------------------------------------------------------

def _make_leadsheet(*chord_specs: tuple[str, str, float, float]) -> LeadSheet:
    """Build a minimal LeadSheet from (root, quality, start_beat, end_beat) tuples."""
    chords = [
        ChordEvent(
            chord_symbol=f"{r}:{q}",
            root=r,
            quality=q,
            start_beat=s,
            end_beat=e,
        )
        for r, q, s, e in chord_specs
    ]
    return LeadSheet(chords=chords)


class TestAnalyze:
    def test_scale_notes_populated(self):
        ls = _make_leadsheet(("C", "maj7", 0, 4))
        analyze(ls)
        assert ls.chords[0].scale_notes != []

    def test_c_ionian_scale_notes_correct(self):
        ls = _make_leadsheet(("C", "maj7", 0, 4))
        analyze(ls)
        pcs = {n % 12 for n in ls.chords[0].scale_notes}
        assert pcs == {0, 2, 4, 5, 7, 9, 11}

    def test_chord_tones_populated(self):
        ls = _make_leadsheet(("C", "maj7", 0, 4))
        analyze(ls)
        pcs = {n % 12 for n in ls.chords[0].chord_tones}
        assert pcs == {0, 4, 7, 11}

    def test_guide_tones_are_subset_of_chord_tones(self):
        ls = _make_leadsheet(("C", "maj7", 0, 4))
        analyze(ls)
        chord = ls.chords[0]
        ct_pcs = {n % 12 for n in chord.chord_tones}
        gt_pcs = {n % 12 for n in chord.guide_tones}
        assert gt_pcs.issubset(ct_pcs)

    def test_guide_tones_are_third_and_seventh(self):
        ls = _make_leadsheet(("C", "maj7", 0, 4))
        analyze(ls)
        # Cmaj7: 3rd = E (pc 4), 7th = B (pc 11)
        pcs = {n % 12 for n in ls.chords[0].guide_tones}
        assert pcs == {4, 11}

    def test_available_tensions_are_not_chord_tones(self):
        ls = _make_leadsheet(("C", "maj7", 0, 4))
        analyze(ls)
        chord = ls.chords[0]
        ct_pcs = {n % 12 for n in chord.chord_tones}
        for n in chord.available_tensions:
            assert n % 12 not in ct_pcs

    def test_available_tensions_are_in_scale(self):
        ls = _make_leadsheet(("C", "maj7", 0, 4))
        analyze(ls)
        chord = ls.chords[0]
        scale_set = set(chord.scale_notes)
        for n in chord.available_tensions:
            assert n in scale_set

    def test_guide_tone_line_length_matches_chords(self):
        ls = _make_leadsheet(
            ("D", "min7", 0, 4),
            ("G", "7",    4, 8),
            ("C", "maj7", 8, 12),
        )
        analyze(ls)
        assert len(ls.guide_tone_line) == 2
        for path in ls.guide_tone_line:
            assert len(path) == 3

    def test_guide_tone_line_midi_in_range(self):
        ls = _make_leadsheet(
            ("D", "min7", 0, 4),
            ("G", "7",    4, 8),
            ("C", "maj7", 8, 12),
        )
        analyze(ls)
        for path in ls.guide_tone_line:
            for note in path:
                assert 21 <= note <= 108

    def test_ii_v_i_rule1_applied(self):
        # G:7 → C:min7: G should get phrygian_dom
        ls = _make_leadsheet(
            ("G", "7",    0, 4),
            ("C", "min7", 4, 8),
        )
        analyze(ls)
        pcs = {n % 12 for n in ls.chords[0].scale_notes}
        # G phrygian_dom: G Ab B C D Eb F = 7,8,11,0,2,3,5
        assert pcs == {(7 + i) % 12 for i in (0, 1, 4, 5, 7, 8, 10)}

    def test_empty_leadsheet(self):
        ls = LeadSheet()
        result = analyze(ls)
        assert result.guide_tone_line == []


# ---------------------------------------------------------------------------
# Guide-tone voice-leading
# ---------------------------------------------------------------------------

class TestGuideToneLine:
    def test_two_paths_returned(self):
        """Two paths are returned, one per guide tone (quality-dependent) of the first chord."""
        ls = _make_leadsheet(
            ("D", "min7", 0, 4),
            ("G", "7",    4, 8),
            ("C", "maj7", 8, 12),
        )
        analyze(ls)
        assert len(ls.guide_tone_line) == 2
        # The two paths must start from different notes
        assert ls.guide_tone_line[0][0] != ls.guide_tone_line[1][0]

    def test_ii_v_i_voice_leading_smooth(self):
        """Both paths should move smoothly (≤ 3 semitones per step)."""
        ls = _make_leadsheet(
            ("D", "min7", 0, 4),
            ("G", "7",    4, 8),
            ("C", "maj7", 8, 12),
        )
        analyze(ls)
        for path in ls.guide_tone_line:
            for i in range(1, len(path)):
                assert abs(path[i] - path[i - 1]) <= 3, (
                    f"Step {i}: {path[i-1]} → {path[i]} is not smooth"
                )

    def test_7sus4_starting_chord_uses_4th_and_7th(self):
        """For 7sus4 the guide tones are the 4th and 7th, not 3rd and 7th."""
        ls = _make_leadsheet(
            ("G", "7sus4", 0, 4),
            ("C", "maj7",  4, 8),
        )
        analyze(ls)
        assert len(ls.guide_tone_line) == 2
        # G7sus4 guide tones: 4th = C (PC 0), 7th = F (PC 5)
        start_pcs = {ls.guide_tone_line[0][0] % 12, ls.guide_tone_line[1][0] % 12}
        assert start_pcs == {0, 5}

    def test_guide_tone_line_notes_are_guide_tones_of_respective_chord(self):
        ls = _make_leadsheet(
            ("D", "min7", 0, 4),
            ("G", "7",    4, 8),
            ("C", "maj7", 8, 12),
        )
        analyze(ls)
        for path in ls.guide_tone_line:
            for i, note in enumerate(path):
                assert note in ls.chords[i].guide_tones


# ---------------------------------------------------------------------------
# Slash-chord 7sus4 detection
# ---------------------------------------------------------------------------

def make_slash_chord(root: str, quality: str, bass: str) -> ChordEvent:
    return ChordEvent(
        chord_symbol=f"{root}:{quality}/{bass}",
        root=root,
        quality=quality,
        bass_note=bass,
    )


class TestSlashSus4:
    # --- resolve_scale returns mixolydian ---

    def test_maj_whole_step_below_bass_is_mixolydian(self):
        # Ab:maj/Bb — Ab is 2 semitones below Bb → Bb7sus4
        chord = make_slash_chord("Ab", "maj", "Bb")
        assert resolve_scale(None, chord, None) == "mixolydian"

    def test_maj7_whole_step_below_bass_is_mixolydian(self):
        # Eb:maj7/F — Eb is 2 semitones below F → F7sus4
        chord = make_slash_chord("Eb", "maj7", "F")
        assert resolve_scale(None, chord, None) == "mixolydian"

    def test_min_p5_above_bass_is_mixolydian(self):
        # E:min/A — E is 7 semitones above A → A7sus4
        chord = make_slash_chord("E", "min", "A")
        assert resolve_scale(None, chord, None) == "mixolydian"

    def test_min7_p5_above_bass_is_mixolydian(self):
        # B:min7/E — B is 7 semitones above E → E7sus4
        chord = make_slash_chord("B", "min7", "E")
        assert resolve_scale(None, chord, None) == "mixolydian"

    def test_no_bass_note_not_affected(self):
        # Plain Ab:maj without slash — stays ionian
        chord = make_chord("Ab", "maj")
        assert resolve_scale(None, chord, None) == "ionian"

    def test_wrong_interval_maj_not_detected(self):
        # Ab:maj/C — (0-8)%12 = 4, not 2 → no slash-7sus4 detection
        chord = make_slash_chord("Ab", "maj", "C")
        assert resolve_scale(None, chord, None) == "ionian"

    def test_wrong_interval_min_not_detected(self):
        # E:min/C — (4-0)%12 = 4, not 7 → no slash-7sus4 detection
        chord = make_slash_chord("E", "min", "C")
        assert resolve_scale(None, chord, None) == "dorian"

    # --- analyze() uses bass note as harmonic root ---

    def test_analyze_scale_rooted_on_bass_maj_slash(self):
        # Ab:maj/Bb → Bb Mixolydian: Bb C D Eb F G Ab = pcs {10,0,2,3,5,7,8}
        chord = make_slash_chord("Ab", "maj", "Bb")
        chord.start_beat, chord.end_beat = 0, 4
        ls = LeadSheet(chords=[chord])
        analyze(ls)
        pcs = {n % 12 for n in ls.chords[0].scale_notes}
        bb_mixolydian = {(10 + i) % 12 for i in (0, 2, 4, 5, 7, 9, 10)}
        assert pcs == bb_mixolydian

    def test_analyze_scale_rooted_on_bass_min_slash(self):
        # E:min/A → A Mixolydian: A B C# D E F# G = pcs {9,11,1,2,4,6,7}
        chord = make_slash_chord("E", "min", "A")
        chord.start_beat, chord.end_beat = 0, 4
        ls = LeadSheet(chords=[chord])
        analyze(ls)
        pcs = {n % 12 for n in ls.chords[0].scale_notes}
        a_mixolydian = {(9 + i) % 12 for i in (0, 2, 4, 5, 7, 9, 10)}
        assert pcs == a_mixolydian

    def test_analyze_chord_tones_rooted_on_bass(self):
        # Ab:maj/Bb → Bb7sus4 chord tones: Bb Eb F Ab = pcs {10,3,5,8}
        chord = make_slash_chord("Ab", "maj", "Bb")
        chord.start_beat, chord.end_beat = 0, 4
        ls = LeadSheet(chords=[chord])
        analyze(ls)
        pcs = {n % 12 for n in ls.chords[0].chord_tones}
        assert pcs == {10, 3, 5, 8}  # Bb=10, Eb=3, F=5, Ab=8

    def test_analyze_guide_tones_rooted_on_bass(self):
        # Ab:maj/Bb → Bb7sus4 guide tones: sus4=Eb (pc 3), b7=Ab (pc 8)
        chord = make_slash_chord("Ab", "maj", "Bb")
        chord.start_beat, chord.end_beat = 0, 4
        ls = LeadSheet(chords=[chord])
        analyze(ls)
        pcs = {n % 12 for n in ls.chords[0].guide_tones}
        assert pcs == {3, 8}  # Eb=3, Ab=8
