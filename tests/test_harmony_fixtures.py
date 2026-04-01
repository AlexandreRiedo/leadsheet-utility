"""Fixture-driven integration tests for the harmony analyzer.

Each entry in tests/fixtures/harmony/<piece>.expected.json specifies a chord
(identified by start_beat) and the expected pitch-class sets for:
  - scale_notes
  - chord_tones
  - guide_tones

The corresponding lead sheet is parsed from data/leadsheets/<piece>.tsv,
analyzed once per module, and then checked against every fixture entry.

Known failures document unimplemented context rules (incremental Layer 2
expansion per SPEC §5 "Context-Aware Resolution").
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

PIECES = ["all_the_things_you_are", "oleo", "stella_by_starlight"]

# ---------------------------------------------------------------------------
# Known scale-notes failures (chord_tones / guide_tones still pass)
#
# These cases require Layer 2 rules not yet in the SPEC:
#
#  all_the_things beat 120 — C:min7 after Gb:7(13).
#    Expected: Dorian b2 (0,1,3,5,7,9,10).  Actual: Dorian (default).
#    Rule needed: minor chord following a tritone-sub dominant (root ±6) may
#    get Dorian b2 when the tritone-sub resolves deceptively to minor.
#    (Dorian b2 is also not yet in SCALES.)
#
#  stella beat 40 — D:min7.
#    Expected: Phrygian (D as iii in Bb major).  Actual: Dorian (default).
#    Rule needed: chain detection fails because the connecting G:min7 (vi in Bb)
#    is absent from this TSV; with it the full iii-vi-ii-V would be recognised.
# ---------------------------------------------------------------------------

_KNOWN_SCALE_FAILURES: dict[tuple[str, float], str] = {
    ("all_the_things_you_are", 120.0): (
        "Is actually a iii phrygian, not a dorian chord."
    ),
    ("stella_by_starlight", 40.0): (
        "D:min7 is iii in Bb major but the intervening G:min7 (vi) is omitted "
        "from this TSV, so the P4-chain back-walk cannot extend to D."
    ),
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _names_to_pcs(names: list[str]) -> frozenset[int]:
    return frozenset(NOTE_TO_PC[n] for n in names)


def _pcs_of(midi_list: list[int]) -> frozenset[int]:
    return frozenset(n % 12 for n in midi_list)


# ---------------------------------------------------------------------------
# Module-scoped fixture: parse + analyze each piece once
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def analyzed_leadsheets() -> dict[str, dict[float, object]]:
    """Return {piece_stem: {start_beat: ChordEvent}} for all three pieces."""
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
            chord_label = entry["chord"].replace(":", "_").replace("(", "").replace(")", "")
            case_id = f"{stem}@{beat}_{chord_label}"
            cases.append(pytest.param(stem, entry, id=case_id))
    return cases


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("piece,entry", _fixture_cases())
def test_scale_notes(piece: str, entry: dict, analyzed_leadsheets):
    key = (piece, entry["start_beat"])
    if key in _KNOWN_SCALE_FAILURES:
        pytest.xfail(_KNOWN_SCALE_FAILURES[key])

    chord = analyzed_leadsheets[piece][entry["start_beat"]]
    expected = _names_to_pcs(entry["expected_scale_notes"])
    actual = _pcs_of(chord.scale_notes)
    assert actual == expected, (
        f"{entry['chord']} (beat {entry['start_beat']}): "
        f"scale {actual} != expected {expected}"
    )


@pytest.mark.parametrize("piece,entry", _fixture_cases())
def test_chord_tones(piece: str, entry: dict, analyzed_leadsheets):
    chord = analyzed_leadsheets[piece][entry["start_beat"]]
    expected = _names_to_pcs(entry["expected_chord_tones"])
    actual = _pcs_of(chord.chord_tones)
    assert actual == expected, (
        f"{entry['chord']} (beat {entry['start_beat']}): "
        f"chord tones {actual} != expected {expected}"
    )


@pytest.mark.parametrize("piece,entry", _fixture_cases())
def test_guide_tones(piece: str, entry: dict, analyzed_leadsheets):
    chord = analyzed_leadsheets[piece][entry["start_beat"]]
    expected = _names_to_pcs(entry["expected_guide_tones"])
    actual = _pcs_of(chord.guide_tones)
    assert actual == expected, (
        f"{entry['chord']} (beat {entry['start_beat']}): "
        f"guide tones {actual} != expected {expected}"
    )
