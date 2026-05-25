"""Load/save calibration to <repo>/data/calibration.json."""

from __future__ import annotations

import json
from pathlib import Path

from leadsheet_utility.calibration.models import (
    DEFAULT_ONE_OCTAVE_HIGH,
    DEFAULT_ONE_OCTAVE_LOW,
    DEFAULT_TWO_OCTAVE_HIGH,
    DEFAULT_TWO_OCTAVE_LOW,
    NUM_MARKERS,
    Calibration,
)
from leadsheet_utility.projection.layout import (
    DEFAULT_BLACK_HEIGHT_RATIO,
    DEFAULT_BLACK_WIDTH_RATIO,
    MIDI_DEFAULT_HIGH,
    MIDI_DEFAULT_LOW,
)

# Repo root = parent of src/. This module sits at
# src/leadsheet_utility/calibration/persistence.py so we go up four levels.
_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_DIR = _REPO_ROOT / "data"
DEFAULT_CALIBRATION_PATH = DEFAULT_CONFIG_DIR / "calibration.json"


def save_calibration(calibration: Calibration, path: Path = DEFAULT_CALIBRATION_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "canonical_size": list(calibration.canonical_size),
        "projector_size": list(calibration.projector_size),
        "markers": [list(m) for m in calibration.markers],
        "black_width_ratio": calibration.black_width_ratio,
        "black_height_ratio": calibration.black_height_ratio,
        # JSON object keys must be strings — convert MIDI notes here, parse back on load.
        "black_key_offsets": {
            str(midi): list(off) for midi, off in calibration.black_key_offsets.items()
        },
        "midi_full_low": calibration.midi_full_low,
        "midi_full_high": calibration.midi_full_high,
        "midi_one_octave_low": calibration.midi_one_octave_low,
        "midi_one_octave_high": calibration.midi_one_octave_high,
        "midi_two_octave_low": calibration.midi_two_octave_low,
        "midi_two_octave_high": calibration.midi_two_octave_high,
        "audio_delay_ms": calibration.audio_delay_ms,
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
        raw_offsets = data.get("black_key_offsets", {})
        offsets: dict[int, tuple[float, float]] = {
            int(k): (float(v[0]), float(v[1])) for k, v in raw_offsets.items()
        }
        return Calibration(
            canonical_size=tuple(data["canonical_size"]),
            projector_size=tuple(data["projector_size"]),
            markers=markers,
            black_width_ratio=float(data.get("black_width_ratio", DEFAULT_BLACK_WIDTH_RATIO)),
            black_height_ratio=float(data.get("black_height_ratio", DEFAULT_BLACK_HEIGHT_RATIO)),
            black_key_offsets=offsets,
            midi_full_low=int(data.get("midi_full_low", MIDI_DEFAULT_LOW)),
            midi_full_high=int(data.get("midi_full_high", MIDI_DEFAULT_HIGH)),
            midi_one_octave_low=int(data.get("midi_one_octave_low", DEFAULT_ONE_OCTAVE_LOW)),
            midi_one_octave_high=int(data.get("midi_one_octave_high", DEFAULT_ONE_OCTAVE_HIGH)),
            midi_two_octave_low=int(data.get("midi_two_octave_low", DEFAULT_TWO_OCTAVE_LOW)),
            midi_two_octave_high=int(data.get("midi_two_octave_high", DEFAULT_TWO_OCTAVE_HIGH)),
            audio_delay_ms=int(data.get("audio_delay_ms", 0)),
        )
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        return None
