"""Tests for the canonical keyboard renderer."""

import os

import pygame
import pytest

from leadsheet_utility.projection.layout import build_keyboard_layout
from leadsheet_utility.projection.renderer import (
    KeyHighlight,
    make_canonical_surface,
    render_canonical,
)


@pytest.fixture(scope="module", autouse=True)
def _pygame_headless():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    yield
    pygame.quit()


def _center_pixel(surface, rect):
    return tuple(surface.get_at((rect.x + rect.width // 2, rect.y + rect.height // 2)))[:3]


def test_empty_highlights_leaves_surface_black():
    layout = build_keyboard_layout()
    surface = make_canonical_surface()
    surface.fill((123, 45, 67))  # dirty it first to prove render clears
    render_canonical(surface, [], layout)
    # Sample several positions
    for pos in [(0, 0), (960, 100), (1919, 199)]:
        assert tuple(surface.get_at(pos))[:3] == (0, 0, 0)


def test_highlighted_white_key_is_filled():
    layout = build_keyboard_layout()
    surface = make_canonical_surface()
    middle_c = next(k for k in layout if k.midi_note == 60)
    render_canonical(surface, [KeyHighlight(60, (255, 255, 255))], layout)
    assert _center_pixel(surface, middle_c) == (255, 255, 255)


def test_highlighted_black_key_is_filled():
    layout = build_keyboard_layout()
    surface = make_canonical_surface()
    c_sharp = next(k for k in layout if k.midi_note == 61)
    render_canonical(surface, [KeyHighlight(61, (255, 50, 50))], layout)
    # Sample the upper half where only the black key exists.
    px = tuple(surface.get_at((c_sharp.x + c_sharp.width // 2, c_sharp.height // 4)))[:3]
    assert px == (255, 50, 50)


def test_non_highlighted_keys_stay_black():
    layout = build_keyboard_layout()
    surface = make_canonical_surface()
    render_canonical(surface, [KeyHighlight(60, (255, 255, 255))], layout)
    d4 = next(k for k in layout if k.midi_note == 62)
    assert _center_pixel(surface, d4) == (0, 0, 0)


def test_black_key_overlays_adjacent_white():
    """If a white and an overlapping black key are both highlighted, the black
    key's color must win in the overlap region (it sits visually on top)."""
    layout = build_keyboard_layout()
    surface = make_canonical_surface()
    c_sharp = next(k for k in layout if k.midi_note == 61)
    # Order matters here only if the renderer doesn't enforce z-order; pass
    # the black key first to make sure white-then-black ordering is enforced
    # by the renderer, not by argument order.
    render_canonical(
        surface,
        [
            KeyHighlight(61, (255, 0, 0)),  # C#4 black
            KeyHighlight(60, (0, 255, 0)),  # C4 white
            KeyHighlight(62, (0, 255, 0)),  # D4 white
        ],
        layout,
    )
    # Center of the black key should be red, not green.
    px = tuple(surface.get_at((c_sharp.x + c_sharp.width // 2, c_sharp.height // 4)))[:3]
    assert px == (255, 0, 0)


def test_unknown_midi_note_is_silently_ignored():
    layout = build_keyboard_layout()
    surface = make_canonical_surface()
    # Out-of-range notes — must not raise.
    render_canonical(
        surface,
        [KeyHighlight(0, (255, 255, 255)), KeyHighlight(200, (255, 255, 255))],
        layout,
    )
    assert tuple(surface.get_at((960, 100)))[:3] == (0, 0, 0)


def test_white_key_does_not_bleed_into_adjacent_black_zone():
    """A highlighted white key adjacent to an un-highlighted black key must
    not paint pixels inside that black key's rectangle (real piano white
    keys are L-shaped — the upper portion is hidden behind the black key)."""
    layout = build_keyboard_layout()
    surface = make_canonical_surface()
    c4 = next(k for k in layout if k.midi_note == 60)
    c_sharp = next(k for k in layout if k.midi_note == 61)
    render_canonical(surface, [KeyHighlight(60, (255, 255, 255))], layout)

    # Lower part of C4 (below the black-key height) must be white.
    lower_y = c4.height - 5
    assert tuple(surface.get_at((c4.x + c4.width // 2, lower_y)))[:3] == (255, 255, 255)

    # The pixel inside the adjacent C# zone must stay black, even though it
    # falls inside the C4 rectangle's upper-right corner.
    inside_black_zone = (c_sharp.x + c_sharp.width // 2, c_sharp.height // 4)
    assert tuple(surface.get_at(inside_black_zone))[:3] == (0, 0, 0)


def test_render_clears_previous_frame():
    layout = build_keyboard_layout()
    surface = make_canonical_surface()
    render_canonical(surface, [KeyHighlight(60, (255, 255, 255))], layout)
    render_canonical(surface, [KeyHighlight(72, (255, 255, 255))], layout)
    middle_c = next(k for k in layout if k.midi_note == 60)
    c5 = next(k for k in layout if k.midi_note == 72)
    assert _center_pixel(surface, middle_c) == (0, 0, 0)
    assert _center_pixel(surface, c5) == (255, 255, 255)
