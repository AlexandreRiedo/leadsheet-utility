"""Tests for calibration load/save round-trip."""

from pathlib import Path

import pytest

from leadsheet_utility.calibration import (
    Calibration,
    load_calibration,
    save_calibration,
)


def _sample() -> Calibration:
    return Calibration(
        canonical_size=(1920, 200),
        projector_size=(1920, 1080),
        markers=[(100, 100), (1800, 110), (1810, 1000), (90, 1010)],
    )


def test_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "calibration.json"
    original = _sample()
    save_calibration(original, path)
    loaded = load_calibration(path)
    assert loaded is not None
    assert loaded.canonical_size == original.canonical_size
    assert loaded.projector_size == original.projector_size
    assert loaded.markers == original.markers


def test_missing_file_returns_none(tmp_path: Path) -> None:
    assert load_calibration(tmp_path / "nope.json") is None


def test_invalid_json_returns_none(tmp_path: Path) -> None:
    path = tmp_path / "calibration.json"
    path.write_text("{not valid json")
    assert load_calibration(path) is None


def test_wrong_marker_count_returns_none(tmp_path: Path) -> None:
    path = tmp_path / "calibration.json"
    path.write_text(
        '{"canonical_size":[1920,200],"projector_size":[1920,1080],"markers":[[0,0],[1,1]]}'
    )
    assert load_calibration(path) is None


def test_construction_validates_marker_count() -> None:
    with pytest.raises(ValueError):
        Calibration(canonical_size=(1920, 200), projector_size=(1920, 1080), markers=[(0, 0)])


def test_homography_matrix_shape() -> None:
    H = _sample().homography()
    assert H.shape == (3, 3)


def test_round_trip_preserves_black_ratios(tmp_path: Path) -> None:
    path = tmp_path / "calibration.json"
    cal = Calibration(
        canonical_size=(1920, 200),
        projector_size=(1920, 1080),
        markers=[(100, 100), (1800, 110), (1810, 1000), (90, 1010)],
        black_width_ratio=0.72,
        black_height_ratio=0.58,
    )
    save_calibration(cal, path)
    loaded = load_calibration(path)
    assert loaded is not None
    assert loaded.black_width_ratio == 0.72
    assert loaded.black_height_ratio == 0.58


def test_legacy_file_without_ratios_uses_defaults(tmp_path: Path) -> None:
    """JSON files predating the ratio fields must still load."""
    path = tmp_path / "calibration.json"
    path.write_text(
        '{"canonical_size":[1920,200],"projector_size":[1920,1080],'
        '"markers":[[0,0],[1920,0],[1920,1080],[0,1080]]}'
    )
    loaded = load_calibration(path)
    assert loaded is not None
    assert loaded.black_width_ratio == pytest.approx(0.6)
    assert loaded.black_height_ratio == pytest.approx(0.65)
    assert loaded.black_key_offsets == {}


def test_round_trip_preserves_black_key_offsets(tmp_path: Path) -> None:
    path = tmp_path / "calibration.json"
    cal = Calibration(
        canonical_size=(1920, 200),
        projector_size=(1920, 1080),
        markers=[(100, 100), (1800, 110), (1810, 1000), (90, 1010)],
        black_key_offsets={61: (3.5, -1.0), 63: (-2.0, 0.0)},
    )
    save_calibration(cal, path)
    loaded = load_calibration(path)
    assert loaded is not None
    assert loaded.black_key_offsets == {61: (3.5, -1.0), 63: (-2.0, 0.0)}


def test_legacy_file_without_offsets_uses_empty_dict(tmp_path: Path) -> None:
    path = tmp_path / "calibration.json"
    path.write_text(
        '{"canonical_size":[1920,200],"projector_size":[1920,1080],'
        '"markers":[[0,0],[1920,0],[1920,1080],[0,1080]],'
        '"black_width_ratio":0.6,"black_height_ratio":0.65}'
    )
    loaded = load_calibration(path)
    assert loaded is not None
    assert loaded.black_key_offsets == {}


def test_round_trip_preserves_range_and_audio_delay(tmp_path: Path) -> None:
    path = tmp_path / "calibration.json"
    cal = Calibration(
        canonical_size=(1920, 200),
        projector_size=(1920, 1080),
        markers=[(100, 100), (1800, 110), (1810, 1000), (90, 1010)],
        midi_full_low=36,
        midi_full_high=84,
        midi_one_octave_low=60,
        midi_one_octave_high=83,
        midi_two_octave_low=48,
        midi_two_octave_high=83,
        audio_delay_ms=25,
    )
    save_calibration(cal, path)
    loaded = load_calibration(path)
    assert loaded is not None
    assert loaded.midi_full_low == 36
    assert loaded.midi_full_high == 84
    assert loaded.midi_one_octave_low == 60
    assert loaded.midi_one_octave_high == 83
    assert loaded.midi_two_octave_low == 48
    assert loaded.midi_two_octave_high == 83
    assert loaded.audio_delay_ms == 25


def test_legacy_file_without_range_fields_uses_defaults(tmp_path: Path) -> None:
    """Pre-range/audio-delay JSON files must still load with defaults."""
    from leadsheet_utility.calibration import (
        DEFAULT_ONE_OCTAVE_HIGH,
        DEFAULT_ONE_OCTAVE_LOW,
        DEFAULT_TWO_OCTAVE_HIGH,
        DEFAULT_TWO_OCTAVE_LOW,
    )
    from leadsheet_utility.projection import MIDI_DEFAULT_HIGH, MIDI_DEFAULT_LOW

    path = tmp_path / "calibration.json"
    path.write_text(
        '{"canonical_size":[1920,200],"projector_size":[1920,1080],'
        '"markers":[[0,0],[1920,0],[1920,1080],[0,1080]],'
        '"black_width_ratio":0.6,"black_height_ratio":0.65}'
    )
    loaded = load_calibration(path)
    assert loaded is not None
    assert loaded.midi_full_low == MIDI_DEFAULT_LOW
    assert loaded.midi_full_high == MIDI_DEFAULT_HIGH
    assert loaded.midi_one_octave_low == DEFAULT_ONE_OCTAVE_LOW
    assert loaded.midi_one_octave_high == DEFAULT_ONE_OCTAVE_HIGH
    assert loaded.midi_two_octave_low == DEFAULT_TWO_OCTAVE_LOW
    assert loaded.midi_two_octave_high == DEFAULT_TWO_OCTAVE_HIGH
    assert loaded.audio_delay_ms == 0
