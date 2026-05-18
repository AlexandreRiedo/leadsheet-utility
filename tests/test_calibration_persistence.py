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
