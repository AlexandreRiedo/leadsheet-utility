"""Calibration data model.

A :class:`Calibration` is everything needed to warp the canonical keyboard
image onto the real piano: the four canonical-corner targets (in projector
pixels) and the derived 3x3 homography matrix. The canonical and projector
sizes are stored alongside the matrix so that loaded calibrations can be
invalidated cleanly if those change.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import cv2
import numpy as np

from leadsheet_utility.projection.layout import (
    DEFAULT_BLACK_HEIGHT_RATIO,
    DEFAULT_BLACK_WIDTH_RATIO,
)

# Marker order: top-left, top-right, bottom-right, bottom-left.
# Matches the canonical-image corner ordering used by the homography.
MARKER_LABELS = ("Top-Left", "Top-Right", "Bottom-Right", "Bottom-Left")
NUM_MARKERS = 4


@dataclass
class Calibration:
    """Four marker positions in projector pixels + the canonical→projector homography.

    `markers` is ordered TL, TR, BR, BL. `canonical_size` and `projector_size`
    are stored so the matrix can be invalidated when either changes.

    `black_width_ratio` / `black_height_ratio` are per-instrument tunings of
    the canonical keyboard layout — real pianos deviate from the "standard"
    0.60 / 0.65 proportions, so they're persisted with the calibration.
    """

    canonical_size: tuple[int, int]
    projector_size: tuple[int, int]
    markers: list[tuple[float, float]] = field(default_factory=list)
    black_width_ratio: float = DEFAULT_BLACK_WIDTH_RATIO
    black_height_ratio: float = DEFAULT_BLACK_HEIGHT_RATIO
    # Per-black-key canonical-pixel offsets (MIDI note -> (dx, dy)). Empty
    # dict means every black key uses the default placement.
    black_key_offsets: dict[int, tuple[float, float]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if len(self.markers) != NUM_MARKERS:
            raise ValueError(
                f"Calibration needs exactly {NUM_MARKERS} markers; got {len(self.markers)}"
            )

    def homography(self) -> np.ndarray:
        """Compute the canonical→projector homography from the current markers."""
        cw, ch = self.canonical_size
        src = np.array(
            [[0, 0], [cw, 0], [cw, ch], [0, ch]],
            dtype=np.float32,
        )
        dst = np.array(self.markers, dtype=np.float32)
        return cv2.getPerspectiveTransform(src, dst)


def default_markers(projector_size: tuple[int, int], inset: int = 50) -> list[tuple[float, float]]:
    """Initial marker positions: a generous rectangle inside the projector frame.

    The starting box is inset by `inset` pixels on each side so that all four
    handles are visible and grabbable on first launch.
    """
    pw, ph = projector_size
    return [
        (float(inset), float(inset)),
        (float(pw - inset), float(inset)),
        (float(pw - inset), float(ph - inset)),
        (float(inset), float(ph - inset)),
    ]
