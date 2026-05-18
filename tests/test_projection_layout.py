"""Tests for the canonical keyboard layout."""

import pytest

from leadsheet_utility.projection.layout import (
    MIDI_DEFAULT_HIGH,
    MIDI_DEFAULT_LOW,
    MIDI_HIGH,
    MIDI_LOW,
    NUM_KEYS,
    NUM_WHITE_KEYS,
    build_keyboard_layout,
    count_white_keys,
    is_black_key,
)


# --- full 88-key range -------------------------------------------------------


def test_full_range_returns_88_keys():
    layout = build_keyboard_layout(midi_low=MIDI_LOW, midi_high=MIDI_HIGH)
    assert len(layout) == NUM_KEYS == 88


def test_full_range_midi_endpoints():
    layout = build_keyboard_layout(midi_low=MIDI_LOW, midi_high=MIDI_HIGH)
    assert layout[0].midi_note == MIDI_LOW == 21
    assert layout[-1].midi_note == MIDI_HIGH == 108


def test_full_range_white_and_black_counts():
    layout = build_keyboard_layout(midi_low=MIDI_LOW, midi_high=MIDI_HIGH)
    whites = [k for k in layout if not k.is_black]
    blacks = [k for k in layout if k.is_black]
    assert len(whites) == NUM_WHITE_KEYS == 52
    assert len(blacks) == 36


# --- default range (D2..G6) --------------------------------------------------


def test_default_range_is_f2_to_e6():
    layout = build_keyboard_layout()
    assert layout[0].midi_note == MIDI_DEFAULT_LOW == 41  # F2
    assert layout[-1].midi_note == MIDI_DEFAULT_HIGH == 88  # E6


def test_default_range_key_count():
    layout = build_keyboard_layout()
    assert len(layout) == MIDI_DEFAULT_HIGH - MIDI_DEFAULT_LOW + 1
    whites = [k for k in layout if not k.is_black]
    assert len(whites) == count_white_keys(MIDI_DEFAULT_LOW, MIDI_DEFAULT_HIGH)


# --- shared geometric invariants --------------------------------------------


def test_keys_are_in_midi_order():
    layout = build_keyboard_layout()
    midi_notes = [k.midi_note for k in layout]
    assert midi_notes == list(range(MIDI_DEFAULT_LOW, MIDI_DEFAULT_HIGH + 1))


@pytest.mark.parametrize(
    "midi,expected_black",
    [
        (21, False),  # A0
        (22, True),  # A#0
        (23, False),  # B0
        (24, False),  # C1
        (60, False),  # middle C
        (61, True),  # C#4
        (108, False),  # C8
    ],
)
def test_is_black_key(midi, expected_black):
    assert is_black_key(midi) is expected_black


def test_white_keys_tile_width_exactly():
    layout = build_keyboard_layout(width=1920, height=200)
    whites = [k for k in layout if not k.is_black]
    for prev, curr in zip(whites, whites[1:]):
        assert prev.x + prev.width == curr.x


def test_white_keys_span_full_width():
    layout = build_keyboard_layout(width=1920, height=200)
    whites = [k for k in layout if not k.is_black]
    assert whites[0].x == 0
    assert whites[-1].x + whites[-1].width == 1920


def test_white_keys_fill_full_height():
    layout = build_keyboard_layout(width=1920, height=200)
    for key in layout:
        if not key.is_black:
            assert key.y == 0
            assert key.height == 200


def test_black_keys_are_shorter_and_narrower():
    layout = build_keyboard_layout(width=1920, height=200)
    white_w = next(k.width for k in layout if not k.is_black)
    for key in layout:
        if key.is_black:
            assert key.height < 200
            assert key.width < white_w


def test_black_keys_centered_on_white_boundary():
    layout = build_keyboard_layout(width=1920, height=200)
    whites_by_midi = {k.midi_note: k for k in layout if not k.is_black}

    for key in layout:
        if not key.is_black:
            continue
        lower_white = whites_by_midi.get(key.midi_note - 1)
        upper_white = whites_by_midi.get(key.midi_note + 1)
        assert lower_white is not None
        assert upper_white is not None
        seam_x = lower_white.x + lower_white.width
        assert seam_x == upper_white.x
        black_center = key.x + key.width / 2
        assert abs(black_center - seam_x) <= 1


def test_no_two_keys_share_a_midi_note():
    layout = build_keyboard_layout()
    midi_set = {k.midi_note for k in layout}
    assert len(midi_set) == len(layout)


def test_layout_scales_with_width():
    layout_small = build_keyboard_layout(width=960, height=100)
    layout_large = build_keyboard_layout(width=1920, height=200)
    assert len(layout_small) == len(layout_large)
    small_white = next(k for k in layout_small if not k.is_black)
    large_white = next(k for k in layout_large if not k.is_black)
    assert large_white.width == pytest.approx(small_white.width * 2, abs=1)


# --- range configurability ---------------------------------------------------


def test_custom_range_one_octave():
    """C4..C5 = 13 keys (8 whites + 5 blacks)."""
    layout = build_keyboard_layout(midi_low=60, midi_high=72)
    assert [k.midi_note for k in layout] == list(range(60, 73))
    whites = [k for k in layout if not k.is_black]
    assert len(whites) == 8


def test_custom_range_white_keys_span_full_width():
    layout = build_keyboard_layout(width=1000, height=200, midi_low=60, midi_high=72)
    whites = [k for k in layout if not k.is_black]
    assert whites[0].x == 0
    assert whites[-1].x + whites[-1].width == 1000


def test_range_endpoints_must_be_white_keys():
    with pytest.raises(ValueError):
        build_keyboard_layout(midi_low=61, midi_high=72)  # starts on C#
    with pytest.raises(ValueError):
        build_keyboard_layout(midi_low=60, midi_high=70)  # ends on A#
