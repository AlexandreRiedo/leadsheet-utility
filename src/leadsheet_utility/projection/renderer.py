"""Canonical-image renderer.

Draws `KeyHighlight`s as filled rectangles into a flat, axis-aligned image of
the 88-key keyboard. The resulting surface is later warped by a homography
onto the projector frame, but this module knows nothing about projection
geometry — it just fills rectangles on a black background.
"""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from leadsheet_utility.projection.layout import KeyRect

RGB = tuple[int, int, int]

BLACK: RGB = (0, 0, 0)


@dataclass(frozen=True)
class KeyHighlight:
    midi_note: int
    color: RGB
    # When True the key is filled with `color` and then overlaid with
    # diagonal black hashes — used to flag "this is the right note but
    # don't play it *yet*" (e.g. a next-chord guide tone that's chromatic
    # against the current scale).
    striped: bool = False


# Stripe geometry chosen so a ~22 px white key (canonical 1920×200) shows
# ~3 hashes and a ~14 px black key still shows ~2 — visually distinct
# from a solid fill after the homography warp.
_STRIPE_SPACING = 14
_STRIPE_THICKNESS = 3


def make_canonical_surface(width: int = 1920, height: int = 200) -> pygame.Surface:
    """Create the canonical keyboard surface, filled black."""
    surface = pygame.Surface((width, height))
    surface.fill(BLACK)
    return surface


def _draw_stripes(surface: pygame.Surface, rect: KeyRect) -> None:
    """Overlay 45° black hashes inside `rect`, clipped to the rectangle.

    Drawn after the solid colour fill so the colour reads through the gaps
    — the key still glows in the highlight colour, just visibly broken up.
    """
    old_clip = surface.get_clip()
    surface.set_clip((rect.x, rect.y, rect.width, rect.height))
    # Diagonals slanting down-right; start far enough left so every line
    # crosses the rect even at its top-right corner.
    x_start = rect.x - rect.height
    x_end = rect.x + rect.width
    for x0 in range(x_start, x_end + 1, _STRIPE_SPACING):
        pygame.draw.line(
            surface,
            BLACK,
            (x0, rect.y),
            (x0 + rect.height, rect.y + rect.height),
            _STRIPE_THICKNESS,
        )
    surface.set_clip(old_clip)


def render_canonical(
    surface: pygame.Surface,
    highlights: list[KeyHighlight],
    layout: list[KeyRect],
) -> None:
    """Clear `surface` to black and fill each highlighted key's rectangle.

    Three-pass fill so the result matches the physical L-shape of piano keys:
    1. Fill highlighted white keys as full-height rectangles (+ stripes
       overlay for striped highlights).
    2. Punch out *every* black-key zone to black — this clips white fills
       into their real L-shape, so light projected onto a real piano lands
       only on the visible top surface of each white key.
    3. Fill highlighted black keys on top of the punched zones (+ stripes).

    Keys not present in `highlights` stay black (no projector light).
    Highlights for MIDI notes outside the layout are silently ignored.
    """
    surface.fill(BLACK)

    rect_by_midi = {k.midi_note: k for k in layout}

    pending_black: list[tuple[KeyRect, RGB, bool]] = []
    for hl in highlights:
        rect = rect_by_midi.get(hl.midi_note)
        if rect is None:
            continue
        if rect.is_black:
            pending_black.append((rect, hl.color, hl.striped))
        else:
            surface.fill(hl.color, (rect.x, rect.y, rect.width, rect.height))
            if hl.striped:
                _draw_stripes(surface, rect)

    # Punch out all black-key zones so white fills become L-shaped.
    for rect in layout:
        if rect.is_black:
            surface.fill(BLACK, (rect.x, rect.y, rect.width, rect.height))

    for rect, color, striped in pending_black:
        surface.fill(color, (rect.x, rect.y, rect.width, rect.height))
        if striped:
            _draw_stripes(surface, rect)
