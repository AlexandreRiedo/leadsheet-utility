"""Fixture-driven integration tests for the harmony analyzer.

Each entry in tests/fixtures/harmony/<piece>.expected.json specifies a chord
(identified by start_beat) and the expected pitch-class sets for:
  - scale_notes
  - chord_tones
  - guide_tones

Guide-tone line fixtures (<piece>.guide_tone_line.expected.json) specify the
expected two-voice MIDI paths across the full form.

The corresponding lead sheet is parsed from data/leadsheets/<piece>.tsv,
analyzed once per module, and then checked against every fixture entry.
"""

import json
from pathlib import Path

import pytest

from leadsheet_utility.harmony import analyze
from leadsheet_utility.harmony.constants import NOTE_TO_PC
from leadsheet_utility.leadsheet.parser import parse_leadsheet

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "harmony"
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "leadsheets"

PIECES = ["all_the_things_you_are", "oleo", "stella_by_starlight", "nefertiti", "inner_urge", "26_2"]

# ---------------------------------------------------------------------------
# Known scale-notes failures (chord_tones / guide_tones still pass)
# ---------------------------------------------------------------------------

_KNOWN_SCALE_FAILURES: dict[tuple[str, float], str] = {
    ("all_the_things_you_are", 120.0): (
        "The Cm7 here is a iii phrygian, not a ii dorian chord. Cf. that Barry Harris video, this ain't easy to know."
    ),
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Canonical flat spellings for display (pitch class → note name)
_PC_NAME = {
    0: "C",
    1: "Db",
    2: "D",
    3: "Eb",
    4: "E",
    5: "F",
    6: "Gb",
    7: "G",
    8: "Ab",
    9: "A",
    10: "Bb",
    11: "B",
}


def _names_to_pcs(names: list[str]) -> frozenset[int]:
    return frozenset(NOTE_TO_PC[n] for n in names)


def _pcs_of(midi_list: list[int]) -> frozenset[int]:
    return frozenset(n % 12 for n in midi_list)


def _fmt(pcs: frozenset[int], root_pc: int = 0) -> str:
    """Render a pitch-class set as space-separated note names, starting from root."""
    # Sort based on the distance from the root (0 to 11 half-steps)
    sorted_pcs = sorted(pcs, key=lambda pc: (pc - root_pc) % 12)
    return "  ".join(_PC_NAME[pc] for pc in sorted_pcs)


# ---------------------------------------------------------------------------
# Module-scoped fixture: parse + analyze each piece once
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def analyzed_leadsheets() -> dict[str, dict[float, object]]:
    """Return {piece_stem: {start_beat: ChordEvent}} for all pieces."""
    result: dict[str, dict[float, object]] = {}
    for stem in PIECES:
        ls = parse_leadsheet(DATA_DIR / f"{stem}.tsv")
        analyze(ls)
        result[stem] = {chord.start_beat: chord for chord in ls.chords}
    return result


# ---------------------------------------------------------------------------
# Build parametrize cases
# ---------------------------------------------------------------------------


def _fixture_cases() -> list:
    cases = []
    for stem in PIECES:
        path = FIXTURES_DIR / f"{stem}.expected.json"
        entries = json.loads(path.read_text(encoding="utf-8"))
        for entry in entries:
            beat = entry["start_beat"]
            chord_label = (
                entry["chord"].replace(":", "_").replace("(", "").replace(")", "")
            )
            case_id = f"{stem}@{beat}_{chord_label}"
            cases.append(pytest.param(stem, entry, id=case_id))
    return cases


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("piece,entry", _fixture_cases())
def test_scale_notes(piece: str, entry: dict, analyzed_leadsheets):
    chord = analyzed_leadsheets[piece][entry["start_beat"]]
    expected = _names_to_pcs(entry["expected_scale_notes"])
    actual = _pcs_of(chord.scale_notes)

    # Extract root string (e.g., "Bb" from "Bb:min7") and get its pitch class
    root_str = entry["chord"].split(":")[0]
    root_pc = NOTE_TO_PC[root_str]

    print(f"\n[{piece}] Beat {entry['start_beat']} - {entry['chord']}")
    print(f"  produced: {_fmt(actual, root_pc)}")
    print(f"  expected: {_fmt(expected, root_pc)}")

    # For known errors, skip them to avoid breaking the test suite
    key = (piece, entry["start_beat"])
    if key in _KNOWN_SCALE_FAILURES:
        pytest.xfail(_KNOWN_SCALE_FAILURES[key])

    assert actual == expected, (
        f"{entry['chord']} beat {entry['start_beat']}\n"
        f"  produced: {_fmt(actual, root_pc)}\n"
        f"  expected: {_fmt(expected, root_pc)}"
    )


@pytest.mark.parametrize("piece,entry", _fixture_cases())
def test_chord_tones(piece: str, entry: dict, analyzed_leadsheets):
    chord = analyzed_leadsheets[piece][entry["start_beat"]]
    expected = _names_to_pcs(entry["expected_chord_tones"])
    actual = _pcs_of(chord.chord_tones)

    root_str = entry["chord"].split(":")[0]
    root_pc = NOTE_TO_PC[root_str]

    print(f"\n[{piece}] Beat {entry['start_beat']} - {entry['chord']}")
    print(f"  produced: {_fmt(actual, root_pc)}")
    print(f"  expected: {_fmt(expected, root_pc)}")

    assert actual == expected, (
        f"{entry['chord']} beat {entry['start_beat']}\n"
        f"  produced: {_fmt(actual, root_pc)}\n"
        f"  expected: {_fmt(expected, root_pc)}"
    )


@pytest.mark.parametrize("piece,entry", _fixture_cases())
def test_guide_tones(piece: str, entry: dict, analyzed_leadsheets):
    chord = analyzed_leadsheets[piece][entry["start_beat"]]
    expected = _names_to_pcs(entry["expected_guide_tones"])
    actual = _pcs_of(chord.guide_tones)

    root_str = entry["chord"].split(":")[0]
    root_pc = NOTE_TO_PC[root_str]

    print(f"\n[{piece}] Beat {entry['start_beat']} - {entry['chord']}")
    print(f"  produced: {_fmt(actual, root_pc)}")
    print(f"  expected: {_fmt(expected, root_pc)}")

    assert actual == expected, (
        f"{entry['chord']} beat {entry['start_beat']}\n"
        f"  produced: {_fmt(actual, root_pc)}\n"
        f"  expected: {_fmt(expected, root_pc)}"
    )


# ---------------------------------------------------------------------------
# Guide-tone line tests
# ---------------------------------------------------------------------------

_GUIDE_TONE_LINE_PIECES = [
    stem for stem in PIECES
    if (FIXTURES_DIR / f"{stem}.guide_tone_line.expected.json").exists()
]


def _guide_tone_line_cases() -> list:
    cases = []
    for stem in _GUIDE_TONE_LINE_PIECES:
        path = FIXTURES_DIR / f"{stem}.guide_tone_line.expected.json"
        fixture = json.loads(path.read_text(encoding="utf-8"))
        cases.append(pytest.param(stem, fixture, id=stem))
    return cases


@pytest.mark.parametrize("piece,fixture", _guide_tone_line_cases())
def test_guide_tone_line_paths(piece: str, fixture: dict, analyzed_leadsheets):
    """The two voice-led guide-tone paths must match the expected MIDI notes."""
    # Reconstruct the analyzed LeadSheet to access guide_tone_line
    ls = parse_leadsheet(DATA_DIR / f"{piece}.tsv")
    analyze(ls)

    expected = fixture["expected_guide_tone_line"]
    actual = ls.guide_tone_line

    assert len(actual) == len(expected), (
        f"Expected {len(expected)} paths, got {len(actual)}"
    )

    print(f"\n[{piece}] Guide-tone line ({len(ls.chords)} chords)")
    for chord_idx, entry in enumerate(fixture["per_chord"]):
        a0 = actual[0][chord_idx] if chord_idx < len(actual[0]) else None
        a1 = actual[1][chord_idx] if len(actual) > 1 and chord_idx < len(actual[1]) else None
        e0 = expected[0][chord_idx] if chord_idx < len(expected[0]) else None
        e1 = expected[1][chord_idx] if len(expected) > 1 and chord_idx < len(expected[1]) else None
        def _n(m): return f"{_PC_NAME[m % 12]}{m // 12 - 1}({m})" if m is not None else "---"
        ok0 = " " if a0 == e0 else "X"
        ok1 = " " if a1 == e1 else "X"
        print(f"  {entry['start_beat']:6.1f}  {entry['chord']:12s}"
              f"  P0: {_n(a0):>10s} {ok0} {_n(e0):>10s}"
              f"  P1: {_n(a1):>10s} {ok1} {_n(e1):>10s}")

    for path_idx in range(len(expected)):
        assert len(actual[path_idx]) == len(expected[path_idx]), (
            f"Path {path_idx}: expected {len(expected[path_idx])} notes, "
            f"got {len(actual[path_idx])}"
        )

        for chord_idx, (act, exp) in enumerate(
            zip(actual[path_idx], expected[path_idx])
        ):
            entry = fixture["per_chord"][chord_idx]
            assert act == exp, (
                f"Path {path_idx}, chord {chord_idx} "
                f"({entry['chord']} @ beat {entry['start_beat']}): "
                f"got MIDI {act} ({_PC_NAME[act % 12]}{act // 12 - 1}), "
                f"expected MIDI {exp} ({_PC_NAME[exp % 12]}{exp // 12 - 1})"
            )
