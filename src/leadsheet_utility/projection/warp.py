"""Homography warp from the canonical keyboard image to the projector frame.

This module owns the geometric mapping between two coordinate spaces:

- **Canonical** (1920x200 by default): the flat, top-down keyboard image
  produced by `renderer.render_canonical`. All exercise/highlight logic
  draws here.
- **Projector** (typically 1920x1080): the fullscreen surface that lights
  up the real piano.

The mapping is a 3x3 perspective transform `H`. Eventually `H` comes from
4-point calibration where the user drags markers onto the physical corners
of the keyboard. Until then, `make_default_homography` returns a placeholder
that lands the keyboard as a full-width, vertically-centred band on the
projector frame — useful for plumbing tests before the projector is mounted.
"""

from __future__ import annotations

import cv2
import numpy as np
import pygame

Homography = np.ndarray  # shape (3, 3), float32

# Fraction of projector height occupied by the keyboard band in the placeholder
# homography. A real overhead-mounted projector hits ~15-25% of frame height;
# 0.20 keeps the preview close to that without being so thin it's hard to see.
_DEFAULT_BAND_FRACTION = 0.20


def make_default_homography(
    canonical_size: tuple[int, int],
    projector_size: tuple[int, int],
    band_fraction: float = _DEFAULT_BAND_FRACTION,
) -> Homography:
    """Compute a placeholder homography mapping the canonical strip to a
    full-width band centred vertically on the projector frame.

    No perspective tilt — purely an affine scale+translate. Real calibration
    will replace this with a matrix that accounts for the projector's actual
    angle relative to the piano.
    """
    cw, ch = canonical_size
    pw, ph = projector_size
    band_h = int(round(ph * band_fraction))
    y_top = (ph - band_h) // 2
    y_bot = y_top + band_h

    src = np.array(
        [[0, 0], [cw, 0], [cw, ch], [0, ch]],
        dtype=np.float32,
    )
    dst = np.array(
        [[0, y_top], [pw, y_top], [pw, y_bot], [0, y_bot]],
        dtype=np.float32,
    )
    return cv2.getPerspectiveTransform(src, dst)


def warp_canonical_to_projector(
    canonical: pygame.Surface,
    homography: Homography,
    projector_size: tuple[int, int],
    out: pygame.Surface | None = None,
) -> pygame.Surface:
    """Warp the canonical keyboard surface onto a projector-sized surface.

    If `out` is provided, the warped pixels are written into it in place
    (avoids reallocating a surface every frame). Otherwise a new surface
    is created.
    """
    pw, ph = projector_size

    # pygame.surfarray uses (x, y, c) ordering; cv2 expects (y, x, c).
    src = np.transpose(pygame.surfarray.array3d(canonical), (1, 0, 2))
    warped = cv2.warpPerspective(src, homography, (pw, ph))
    warped_xy = np.transpose(warped, (1, 0, 2))

    if out is None:
        return pygame.surfarray.make_surface(warped_xy)

    pygame.surfarray.blit_array(out, warped_xy)
    return out
