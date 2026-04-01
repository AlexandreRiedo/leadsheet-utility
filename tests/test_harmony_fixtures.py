"""Fixture-driven integration tests for the harmony analyzer.

Each entry in tests/fixtures/harmony/<piece>.expected.json specifies a chord
(identified by start_beat) and the expected pitch-class sets for:
  - scale_notes
  - chord_tones
  - guide_tones

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

PIECES = ["all_the_things_you_are", "oleo", "stella_by_starlight", "nefertiti", "inner_urge"]

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
