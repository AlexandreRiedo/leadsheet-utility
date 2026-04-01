"""Tests for leadsheet TSV parser.

These tests form the executable specification for the parser module.
They cover: TSV line splitting, root/quality extraction, parenthesized
extensions, slash bass notes, enharmonic normalization, bar/beat derivation,
metadata sidecar loading, and full-file integration against real lead sheets.
"""

import json
import textwrap
from pathlib import Path

import pytest

from leadsheet_utility.leadsheet.models import ChordEvent, LeadSheet
from leadsheet_utility.leadsheet.parser import parse_chord_symbol, parse_leadsheet

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "leadsheets"

# ---------------------------------------------------------------------------
# Note-to-pitch-class mapping (duplicated here for test assertions only)
# ---------------------------------------------------------------------------
NOTE_TO_PC = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
    "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11,
}


# ===================================================================
# 1. TSV LINE SPLITTING — basic three-field parsing
# ===================================================================

class TestTsvLineSplitting:
    """Parser correctly splits start_beat, end_beat, and chord_symbol."""

    def test_basic_line(self, tmp_path):
        tsv = tmp_path / "test.tsv"
        tsv.write_text("0.000\t4.000\tC:maj7\n")
        sheet = parse_leadsheet(tsv)
        assert len(sheet.chords) == 1
        c = sheet.chords[0]
        assert c.start_beat == 0.0
        assert c.end_beat == 4.0
        assert c.chord_symbol == "C:maj7"

    def test_multiple_lines(self, tmp_path):
        tsv = tmp_path / "test.tsv"
        tsv.write_text(
            "0.000\t4.000\tA:min7\n"
            "4.000\t8.000\tD:7\n"
            "8.000\t12.000\tG:maj7\n"
        )
        sheet = parse_leadsheet(tsv)
        assert len(sheet.chords) == 3
        assert sheet.chords[0].chord_symbol == "A:min7"
        assert sheet.chords[1].chord_symbol == "D:7"
        assert sheet.chords[2].chord_symbol == "G:maj7"

    def test_blank_lines_ignored(self, tmp_path):
        tsv = tmp_path / "test.tsv"
        tsv.write_text("0.000\t4.000\tC:maj7\n\n\n4.000\t8.000\tD:7\n")
        sheet = parse_leadsheet(tsv)
        assert len(sheet.chords) == 2

    def test_duration_beats_computed(self, tmp_path):
        tsv = tmp_path / "test.tsv"
        tsv.write_text("0.000\t4.000\tC:maj7\n8.000\t10.000\tD:7\n")
        sheet = parse_leadsheet(tsv)
        assert sheet.chords[0].duration_beats == 4.0
        assert sheet.chords[1].duration_beats == 2.0


# ===================================================================
# 2. ROOT AND QUALITY EXTRACTION
# ===================================================================

class TestRootAndQuality:
    """Parser splits root from quality on the colon delimiter."""

    @pytest.mark.parametrize(
        "symbol, expected_root, expected_quality",
        [
            ("C:maj7", "C", "maj7"),
            ("F:min7", "F", "min7"),
            ("Bb:7", "Bb", "7"),
            ("F#:hdim7", "F#", "hdim7"),
            ("Ab:maj7", "Ab", "maj7"),
            ("D:dim7", "D", "dim7"),
            ("E:aug", "E", "aug"),
            ("G:sus4", "G", "sus4"),
            ("A:min", "A", "min"),
            ("C:maj", "C", "maj"),
            ("Bb:6", "Bb", "6"),
            ("D:min6", "D", "min6"),
            ("Eb:min6", "Eb", "min6"),
            ("G:9", "G", "9"),
            ("C:13", "C", "13"),
            ("A:minmaj7", "A", "minmaj7"),
            ("F:7sus4", "F", "7sus4"),
        ],
    )
    def test_root_quality_split(self, symbol, expected_root, expected_quality):
        event = parse_chord_symbol(symbol)
        assert event.root == expected_root
        assert event.quality == expected_quality


# ===================================================================
# 3. PARENTHESIZED EXTENSIONS
# ===================================================================

class TestExtensions:
    """Parser extracts parenthesized alterations and strips them from quality."""

    def test_single_extension(self):
        event = parse_chord_symbol("C:7(b9)")
        assert event.quality == "7"
        assert event.extensions == ["b9"]

    def test_single_sharp_extension(self):
        event = parse_chord_symbol("E:7(#9)")
        assert event.quality == "7"
        assert event.extensions == ["#9"]

    def test_multiple_extensions(self):
        event = parse_chord_symbol("G:7(b9,b13)")
        assert event.quality == "7"
        assert sorted(event.extensions) == ["b13", "b9"]

    def test_sharp_5_extension(self):
        event = parse_chord_symbol("C:7(#5)")
        assert event.quality == "7"
        assert event.extensions == ["#5"]

    def test_sharp_11_extension(self):
        event = parse_chord_symbol("D:7(#11)")
        assert event.quality == "7"
        assert event.extensions == ["#11"]

    def test_natural_13_extension(self):
        event = parse_chord_symbol("Gb:7(13)")
        assert event.quality == "7"
        assert event.extensions == ["13"]

    def test_b5_extension(self):
        event = parse_chord_symbol("A:7(b5)")
        assert event.quality == "7"
        assert event.extensions == ["b5"]

    def test_no_extensions(self):
        event = parse_chord_symbol("C:maj7")
        assert event.extensions == []

    def test_mixed_sharp_and_flat(self):
        event = parse_chord_symbol("F:7(b9,#9)")
        assert event.quality == "7"
        assert sorted(event.extensions) == ["#9", "b9"]


# ===================================================================
# 4. SLASH BASS NOTES
# ===================================================================

class TestSlashBass:
    """Parser extracts slash bass notes and strips them from quality."""

    def test_slash_natural(self):
        event = parse_chord_symbol("C:maj7/E")
        assert event.root == "C"
        assert event.quality == "maj7"
        assert event.bass_note == "E"

    def test_slash_flat(self):
        event = parse_chord_symbol("Db:7/Cb")
        assert event.root == "Db"
        assert event.quality == "7"
        assert event.bass_note == "Cb"

    def test_slash_sharp(self):
        event = parse_chord_symbol("A:min7/G#")
        assert event.root == "A"
        assert event.quality == "min7"
        assert event.bass_note == "G#"

    def test_no_slash(self):
        event = parse_chord_symbol("C:min7")
        assert event.bass_note is None

    def test_slash_with_extension(self):
        event = parse_chord_symbol("G:7(b9)/F")
        assert event.root == "G"
        assert event.quality == "7"
        assert event.extensions == ["b9"]
        assert event.bass_note == "F"


# ===================================================================
# 5. ENHARMONIC NORMALIZATION
# ===================================================================

class TestEnharmonicNormalization:
    """Enharmonic spellings map to the same pitch class; original preserved."""

    def test_sharp_flat_same_pc(self):
        e1 = parse_chord_symbol("F#:min7")
        e2 = parse_chord_symbol("Gb:min7")
        assert NOTE_TO_PC[e1.root] == NOTE_TO_PC[e2.root] == 6

    def test_original_spelling_preserved(self):
        e1 = parse_chord_symbol("F#:hdim7")
        e2 = parse_chord_symbol("Gb:hdim7")
        assert e1.root == "F#"
        assert e2.root == "Gb"

    @pytest.mark.parametrize(
        "root",
        ["C", "C#", "Db", "D", "D#", "Eb", "E", "F",
         "F#", "Gb", "G", "G#", "Ab", "A", "A#", "Bb", "B"],
    )
    def test_all_roots_accepted(self, root):
        event = parse_chord_symbol(f"{root}:maj7")
        assert event.root == root


# ===================================================================
# 6. BAR NUMBER AND BEAT-IN-BAR DERIVATION
# ===================================================================

class TestBarBeatDerivation:
    """Bar number and beat_in_bar are correctly computed from beat positions."""

    def test_first_bar(self, tmp_path):
        tsv = tmp_path / "test.tsv"
        tsv.write_text("0.000\t4.000\tC:maj7\n")
        sheet = parse_leadsheet(tsv)
        c = sheet.chords[0]
        assert c.bar_number == 1
        assert c.beat_in_bar == 0.0

    def test_second_bar(self, tmp_path):
        tsv = tmp_path / "test.tsv"
        tsv.write_text("4.000\t8.000\tD:7\n")
        sheet = parse_leadsheet(tsv)
        c = sheet.chords[0]
        assert c.bar_number == 2
        assert c.beat_in_bar == 0.0

    def test_mid_bar_chord(self, tmp_path):
        """A chord starting on beat 2 of bar 1."""
        tsv = tmp_path / "test.tsv"
        tsv.write_text("2.000\t4.000\tG:7\n")
        sheet = parse_leadsheet(tsv)
        c = sheet.chords[0]
        assert c.bar_number == 1
        assert c.beat_in_bar == 2.0

    def test_bar_number_sequence(self, tmp_path):
        """Bars are numbered sequentially across a simple ii-V-I."""
        tsv = tmp_path / "test.tsv"
        tsv.write_text(
            "0.000\t4.000\tD:min7\n"
            "4.000\t8.000\tG:7\n"
            "8.000\t16.000\tC:maj7\n"
        )
        sheet = parse_leadsheet(tsv)
        assert [c.bar_number for c in sheet.chords] == [1, 2, 3]

    def test_two_chords_per_bar(self, tmp_path):
        """Two chords in one bar share the same bar_number."""
        tsv = tmp_path / "test.tsv"
        tsv.write_text(
            "0.000\t2.000\tA:min7\n"
            "2.000\t4.000\tD:7\n"
        )
        sheet = parse_leadsheet(tsv)
        assert sheet.chords[0].bar_number == 1
        assert sheet.chords[1].bar_number == 1
        assert sheet.chords[0].beat_in_bar == 0.0
        assert sheet.chords[1].beat_in_bar == 2.0


# ===================================================================
# 7. TOTAL BEATS AND TOTAL BARS
# ===================================================================

class TestLeadSheetTotals:
    """LeadSheet.total_beats and total_bars are derived correctly."""

    def test_total_beats(self, tmp_path):
        tsv = tmp_path / "test.tsv"
        tsv.write_text(
            "0.000\t4.000\tC:maj7\n"
            "4.000\t8.000\tG:7\n"
        )
        sheet = parse_leadsheet(tsv)
        assert sheet.total_beats == 8.0

    def test_total_bars(self, tmp_path):
        tsv = tmp_path / "test.tsv"
        tsv.write_text(
            "0.000\t4.000\tC:maj7\n"
            "4.000\t8.000\tG:7\n"
            "8.000\t16.000\tD:min7\n"
        )
        sheet = parse_leadsheet(tsv)
        assert sheet.total_bars == 4  # 16 beats / 4 beats per bar


# ===================================================================
# 8. METADATA SIDECAR LOADING
# ===================================================================

class TestMetadataSidecar:
    """Parser loads .meta.json sidecar when present, falls back to defaults."""

    def test_loads_metadata(self, tmp_path):
        tsv = tmp_path / "test.tsv"
        tsv.write_text("0.000\t4.000\tC:maj7\n")
        meta = tmp_path / "test.meta.json"
        meta.write_text(json.dumps({
            "title": "Test Tune",
            "composer": "Test Composer",
            "key": "C",
            "time_signature": [4, 4],
            "default_tempo": 160,
            "form_repeats": 2,
        }))
        sheet = parse_leadsheet(tsv)
        assert sheet.title == "Test Tune"
        assert sheet.composer == "Test Composer"
        assert sheet.key == "C"
        assert sheet.time_signature == (4, 4)
        assert sheet.default_tempo == 160
        assert sheet.form_repeats == 2

    def test_defaults_when_no_sidecar(self, tmp_path):
        tsv = tmp_path / "test.tsv"
        tsv.write_text("0.000\t4.000\tC:maj7\n")
        sheet = parse_leadsheet(tsv)
        assert sheet.title == "Unknown"
        assert sheet.composer == "Unknown"
        assert sheet.key == "C"
        assert sheet.time_signature == (4, 4)
        assert sheet.default_tempo == 120
        assert sheet.form_repeats == 1

    def test_partial_metadata_fills_defaults(self, tmp_path):
        """A sidecar with only some fields still fills in defaults for the rest."""
        tsv = tmp_path / "test.tsv"
        tsv.write_text("0.000\t4.000\tC:maj7\n")
        meta = tmp_path / "test.meta.json"
        meta.write_text(json.dumps({"title": "Partial Tune"}))
        sheet = parse_leadsheet(tsv)
        assert sheet.title == "Partial Tune"
        assert sheet.composer == "Unknown"
        assert sheet.default_tempo == 120


# ===================================================================
# 9. PREFIX FAMILY CLASSIFICATION
# ===================================================================

class TestPrefixFamilies:
    """Quality strings are classified into the correct prefix family.

    The parser doesn't do scale mapping, but it must correctly preserve
    the quality string so the harmony module can classify it.
    """

    @pytest.mark.parametrize(
        "quality",
        ["hdim7"],
    )
    def test_half_diminished_family(self, quality):
        event = parse_chord_symbol(f"C:{quality}")
        assert event.quality == quality

    @pytest.mark.parametrize(
        "quality",
        ["min7", "min", "minmaj7", "min6", "min9", "min11", "min13"],
    )
    def test_minor_family(self, quality):
        event = parse_chord_symbol(f"C:{quality}")
        assert event.quality == quality

    @pytest.mark.parametrize(
        "quality",
        ["maj7", "maj", "maj9", "maj13", "maj69", "maj7#11"],
    )
    def test_major_family(self, quality):
        event = parse_chord_symbol(f"C:{quality}")
        assert event.quality == quality

    @pytest.mark.parametrize(
        "quality",
        ["dim7"],
    )
    def test_diminished_family(self, quality):
        event = parse_chord_symbol(f"C:{quality}")
        assert event.quality == quality

    @pytest.mark.parametrize(
        "quality",
        ["aug"],
    )
    def test_augmented_family(self, quality):
        event = parse_chord_symbol(f"C:{quality}")
        assert event.quality == quality

    @pytest.mark.parametrize(
        "quality",
        ["sus4", "sus2", "sus"],
    )
    def test_suspended_family(self, quality):
        event = parse_chord_symbol(f"C:{quality}")
        assert event.quality == quality

    @pytest.mark.parametrize(
        "quality",
        ["7", "9", "7sus4", "13", "6"],
    )
    def test_dominant_and_simple_qualities(self, quality):
        event = parse_chord_symbol(f"C:{quality}")
        assert event.quality == quality


# ===================================================================
# 10. INTEGRATION — real lead sheet files
# ===================================================================

class TestIntegrationRealFiles:
    """Parse real .tsv files from the data directory end-to-end."""

    def test_all_the_things_you_are(self):
        tsv = DATA_DIR / "all_the_things_you_are.tsv"
        if not tsv.exists():
            pytest.skip("Test data not available")
        sheet = parse_leadsheet(tsv)
        assert len(sheet.chords) == 36
        assert sheet.total_beats == 144.0
        assert sheet.total_bars == 36
        # Metadata from sidecar
        assert sheet.title == "All The Things You Are"
        assert sheet.composer == "Jerome Kern"
        assert sheet.key == "Ab"
        assert sheet.default_tempo == 100
        # First chord
        first = sheet.chords[0]
        assert first.root == "F"
        assert first.quality == "min7"
        assert first.start_beat == 0.0
        assert first.end_beat == 4.0
        assert first.bar_number == 1
        # Last chord has b9 extension
        last = sheet.chords[-1]
        assert last.root == "C"
        assert last.quality == "7"
        assert last.extensions == ["b9"]
        assert last.end_beat == 144.0
        # Chord with #5 extension
        c_aug = sheet.chords[22]  # C:7(#5)
        assert c_aug.root == "C"
        assert c_aug.quality == "7"
        assert c_aug.extensions == ["#5"]
        # Chord with sharp root
        fsharp = sheet.chords[19]  # F#:hdim7
        assert fsharp.root == "F#"
        assert fsharp.quality == "hdim7"

    def test_oleo(self):
        tsv = DATA_DIR / "oleo.tsv"
        if not tsv.exists():
            pytest.skip("Test data not available")
        sheet = parse_leadsheet(tsv)
        assert len(sheet.chords) == 54
        assert sheet.total_beats == 128.0
        assert sheet.total_bars == 32
        # Oleo has Bb:6 and Eb:min6
        bb6 = sheet.chords[0]
        assert bb6.root == "Bb"
        assert bb6.quality == "6"

    def test_autumn_leaves(self):
        tsv = DATA_DIR / "autumn_leaves.tsv"
        if not tsv.exists():
            pytest.skip("Test data not available")
        sheet = parse_leadsheet(tsv)
        assert len(sheet.chords) == 29
        # Has both F#:hdim7 and B:7(b9)
        fsharp_chords = [c for c in sheet.chords if c.root == "F#"]
        assert len(fsharp_chords) >= 1
        assert all(c.quality == "hdim7" for c in fsharp_chords)
        b9_chords = [c for c in sheet.chords if c.extensions == ["b9"]]
        assert len(b9_chords) >= 1

    def test_stella_by_starlight(self):
        tsv = DATA_DIR / "stella_by_starlight.tsv"
        if not tsv.exists():
            pytest.skip("Test data not available")
        sheet = parse_leadsheet(tsv)
        assert len(sheet.chords) == 30
        assert sheet.total_beats == 128.0
        # Multiple hdim7 chords
        hdim_chords = [c for c in sheet.chords if c.quality == "hdim7"]
        assert len(hdim_chords) >= 4

    def test_all_chords_have_positive_duration(self):
        """Every chord in every lead sheet has positive duration."""
        for tsv_path in DATA_DIR.glob("*.tsv"):
            sheet = parse_leadsheet(tsv_path)
            for chord in sheet.chords:
                assert chord.duration_beats > 0, (
                    f"{tsv_path.name}: {chord.chord_symbol} at beat "
                    f"{chord.start_beat} has non-positive duration"
                )

    def test_chords_are_contiguous(self):
        """Each chord's start_beat equals the previous chord's end_beat."""
        for tsv_path in DATA_DIR.glob("*.tsv"):
            sheet = parse_leadsheet(tsv_path)
            for i in range(1, len(sheet.chords)):
                prev = sheet.chords[i - 1]
                curr = sheet.chords[i]
                assert curr.start_beat == prev.end_beat, (
                    f"{tsv_path.name}: gap between chord {i - 1} "
                    f"(end={prev.end_beat}) and chord {i} "
                    f"(start={curr.start_beat})"
                )


# ===================================================================
# 11. EDGE CASES
# ===================================================================

class TestEdgeCases:
    """Edge cases and malformed input handling."""

    def test_empty_file(self, tmp_path):
        tsv = tmp_path / "empty.tsv"
        tsv.write_text("")
        sheet = parse_leadsheet(tsv)
        assert len(sheet.chords) == 0
        assert sheet.total_beats == 0.0
        assert sheet.total_bars == 0

    def test_single_chord(self, tmp_path):
        tsv = tmp_path / "single.tsv"
        tsv.write_text("0.000\t4.000\tC:maj7\n")
        sheet = parse_leadsheet(tsv)
        assert len(sheet.chords) == 1
        assert sheet.total_beats == 4.0
        assert sheet.total_bars == 1

    def test_non_integer_beats(self, tmp_path):
        """Fractional beat positions are handled correctly."""
        tsv = tmp_path / "test.tsv"
        tsv.write_text("0.000\t2.500\tC:maj7\n2.500\t4.000\tG:7\n")
        sheet = parse_leadsheet(tsv)
        assert sheet.chords[0].duration_beats == 2.5
        assert sheet.chords[1].start_beat == 2.5

    def test_long_form(self, tmp_path):
        """Parser handles a long form (64 bars / 256 beats)."""
        lines = []
        for i in range(64):
            start = float(i * 4)
            end = float((i + 1) * 4)
            lines.append(f"{start:.3f}\t{end:.3f}\tC:maj7")
        tsv = tmp_path / "long.tsv"
        tsv.write_text("\n".join(lines) + "\n")
        sheet = parse_leadsheet(tsv)
        assert len(sheet.chords) == 64
        assert sheet.total_beats == 256.0
        assert sheet.total_bars == 64
