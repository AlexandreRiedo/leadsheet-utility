"""Load/save calibration to ~/.leadsheet-utility/calibration.json."""

from __future__ import annotations

import json
from pathlib import Path

from leadsheet_utility.calibration.models import NUM_MARKERS, Calibration

DEFAULT_CONFIG_DIR = Path.home() / ".leadsheet-utility"
DEFAULT_CALIBRATION_PATH = DEFAULT_CONFIG_DIR / "calibration.json"


def save_calibration(calibration: Calibration, path: Path = DEFAULT_CALIBRATION_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "canonical_size": list(calibration.canonical_size),
        "projector_size": list(calibration.projector_size),
        "markers": [list(m) for m in calibration.markers],
    }
    path.write_text(json.dumps(payload, indent=2))


def load_calibration(path: Path = DEFAULT_CALIBRATION_PATH) -> Calibration | None:
    """Load calibration from disk, or None if the file is missing/invalid."""
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        markers = [tuple(m) for m in data["markers"]]
        if len(markers) != NUM_MARKERS:
            return None
        return Calibration(
            canonical_size=tuple(data["canonical_size"]),
            projector_size=tuple(data["projector_size"]),
            markers=markers,
        )
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        return None
