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


# --- black-key proportion overrides -----------------------------------------


def test_black_width_ratio_scales_black_key_widths():
    base = build_keyboard_layout(width=1920, height=200)
    wider = build_keyboard_layout(width=1920, height=200, black_width_ratio=1.0)
    base_black = next(k for k in base if k.is_black)
    wide_black = next(k for k in wider if k.is_black)
    assert wide_black.width > base_black.width


def test_black_height_ratio_scales_black_key_heights():
    base = build_keyboard_layout(width=1920, height=200)
    longer = build_keyboard_layout(width=1920, height=200, black_height_ratio=0.95)
    base_black = next(k for k in base if k.is_black)
    long_black = next(k for k in longer if k.is_black)
    assert long_black.height > base_black.height


def test_ratio_overrides_do_not_affect_white_keys():
    """Whites tile the full width regardless of black-key ratios."""
    layout = build_keyboard_layout(width=1920, height=200, black_width_ratio=0.9, black_height_ratio=0.8)
    whites = [k for k in layout if not k.is_black]
    assert whites[0].x == 0
    assert whites[-1].x + whites[-1].width == 1920
    for k in whites:
        assert k.height == 200


# --- per-black-key offsets ---------------------------------------------------


def test_black_key_offsets_shift_individual_black_keys():
    base = build_keyboard_layout(width=1920, height=200)
    base_by_midi = {k.midi_note: k for k in base}
    target_midi = next(m for m, k in base_by_midi.items() if k.is_black)
    shifted = build_keyboard_layout(
        width=1920, height=200, black_key_offsets={target_midi: (5.0, 3.0)},
    )
    shifted_by_midi = {k.midi_note: k for k in shifted}
    assert shifted_by_midi[target_midi].x == base_by_midi[target_midi].x + 5
    assert shifted_by_midi[target_midi].y == base_by_midi[target_midi].y + 3
    # Width/height unchanged.
    assert shifted_by_midi[target_midi].width == base_by_midi[target_midi].width
    assert shifted_by_midi[target_midi].height == base_by_midi[target_midi].height


def test_black_key_offsets_do_not_affect_white_keys():
    base = build_keyboard_layout(width=1920, height=200)
    target_midi = next(k.midi_note for k in base if k.is_black)
    shifted = build_keyboard_layout(
        width=1920, height=200, black_key_offsets={target_midi: (10.0, 0.0)},
    )
    base_whites = [k for k in base if not k.is_black]
    shifted_whites = [k for k in shifted if not k.is_black]
    assert base_whites == shifted_whites


def test_black_key_offsets_only_apply_to_listed_keys():
    base = build_keyboard_layout(width=1920, height=200)
    base_blacks = {k.midi_note: k for k in base if k.is_black}
    target = next(iter(base_blacks))
    shifted = build_keyboard_layout(
        width=1920, height=200, black_key_offsets={target: (5.0, 0.0)},
    )
    shifted_blacks = {k.midi_note: k for k in shifted if k.is_black}
    for midi, key in shifted_blacks.items():
        if midi == target:
            continue
        assert key == base_blacks[midi]
