"""Tests for the canonical -> projector homography warp."""

import os

import numpy as np
import pygame
import pytest

from leadsheet_utility.projection.layout import build_keyboard_layout
from leadsheet_utility.projection.renderer import (
    KeyHighlight,
    make_canonical_surface,
    render_canonical,
)
from leadsheet_utility.projection.warp import (
    make_default_homography,
    warp_canonical_to_projector,
)


@pytest.fixture(scope="module", autouse=True)
def _pygame_headless():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    yield
    pygame.quit()


def test_default_homography_shape_and_dtype():
    H = make_default_homography((1920, 200), (1920, 1080))
    assert H.shape == (3, 3)
    assert H.dtype in (np.float32, np.float64)


def _apply(H, x, y):
    """Apply a homography to a 2D point."""
    v = H @ np.array([x, y, 1.0])
    return v[0] / v[2], v[1] / v[2]


def test_default_homography_maps_corners_to_centered_band():
    canonical = (1920, 200)
    projector = (1920, 1080)
    H = make_default_homography(canonical, projector, band_fraction=0.2)

    band_h = int(round(1080 * 0.2))
    y_top = (1080 - band_h) // 2
    y_bot = y_top + band_h

    # Each canonical corner should land on the matching band corner.
    corners = [
        ((0, 0), (0, y_top)),
        ((1920, 0), (1920, y_top)),
        ((1920, 200), (1920, y_bot)),
        ((0, 200), (0, y_bot)),
    ]
    for (sx, sy), (ex, ey) in corners:
        x, y = _apply(H, sx, sy)
        assert x == pytest.approx(ex, abs=0.5)
        assert y == pytest.approx(ey, abs=0.5)


def test_warp_produces_band_with_content_and_black_margins():
    canonical_size = (1920, 200)
    projector_size = (1920, 1080)
    layout = build_keyboard_layout(*canonical_size)
    canonical = make_canonical_surface(*canonical_size)
    render_canonical(
        canonical,
        [KeyHighlight(m, (255, 255, 255)) for m in (60, 62, 64, 65, 67, 69, 71, 72)],
        layout,
    )

    H = make_default_homography(canonical_size, projector_size, band_fraction=0.2)
    warped = warp_canonical_to_projector(canonical, H, projector_size)

    assert warped.get_size() == projector_size

    band_h = int(round(1080 * 0.2))
    y_center = 1080 // 2
    y_above = (1080 - band_h) // 2 - 20
    y_below = (1080 + band_h) // 2 + 20

    # Above and below the band: pure black (no light on the piano).
    assert tuple(warped.get_at((960, y_above)))[:3] == (0, 0, 0)
    assert tuple(warped.get_at((960, y_below)))[:3] == (0, 0, 0)

    # Somewhere on the band there must be a lit pixel (the C-major fills).
    arr = pygame.surfarray.array3d(warped)
    band_slice = arr[:, y_center - band_h // 4 : y_center + band_h // 4, :]
    assert band_slice.max() > 0


def test_warp_writes_into_preallocated_surface():
    canonical_size = (1920, 200)
    projector_size = (1920, 1080)
    layout = build_keyboard_layout(*canonical_size)
    canonical = make_canonical_surface(*canonical_size)
    render_canonical(canonical, [KeyHighlight(60, (255, 255, 255))], layout)

    H = make_default_homography(canonical_size, projector_size)
    out = pygame.Surface(projector_size)
    returned = warp_canonical_to_projector(canonical, H, projector_size, out=out)
    assert returned is out
    # Surface should have *some* non-black pixel after warp.
    assert pygame.surfarray.array3d(out).max() > 0
