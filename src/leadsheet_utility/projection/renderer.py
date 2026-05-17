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


def make_canonical_surface(width: int = 1920, height: int = 200) -> pygame.Surface:
    """Create the canonical keyboard surface, filled black."""
    surface = pygame.Surface((width, height))
    surface.fill(BLACK)
    return surface


def render_canonical(
    surface: pygame.Surface,
    highlights: list[KeyHighlight],
    layout: list[KeyRect],
) -> None:
    """Clear `surface` to black and fill each highlighted key's rectangle.

    Three-pass fill so the result matches the physical L-shape of piano keys:
    1. Fill highlighted white keys as full-height rectangles.
    2. Punch out *every* black-key zone to black — this clips white fills
       into their real L-shape, so light projected onto a real piano lands
       only on the visible top surface of each white key.
    3. Fill highlighted black keys on top of the punched zones.

    Keys not present in `highlights` stay black (no projector light).
    Highlights for MIDI notes outside the layout are silently ignored.
    """
    surface.fill(BLACK)

    rect_by_midi = {k.midi_note: k for k in layout}

    pending_black: list[tuple[KeyRect, RGB]] = []
    for hl in highlights:
        rect = rect_by_midi.get(hl.midi_note)
        if rect is None:
            continue
        if rect.is_black:
            pending_black.append((rect, hl.color))
        else:
            surface.fill(hl.color, (rect.x, rect.y, rect.width, rect.height))

    # Punch out all black-key zones so white fills become L-shaped.
    for rect in layout:
        if rect.is_black:
            surface.fill(BLACK, (rect.x, rect.y, rect.width, rect.height))

    for rect, color in pending_black:
        surface.fill(color, (rect.x, rect.y, rect.width, rect.height))
