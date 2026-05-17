"""88-key piano keyboard layout in a canonical (undistorted) image.

Coordinates are pixel positions inside a flat top-down image of the keyboard
(default 1920x200). This image is later warped onto the projector frame via
a homography. The layout itself knows nothing about projection — it is pure
geometry derived from standard piano proportions.
"""

from dataclasses import dataclass

MIDI_LOW = 21  # A0
MIDI_HIGH = 108  # C8
NUM_KEYS = MIDI_HIGH - MIDI_LOW + 1  # 88
NUM_WHITE_KEYS = 52

# Pitch classes that correspond to black keys (C=0).
_BLACK_PCS = frozenset({1, 3, 6, 8, 10})

# Standard acoustic-piano proportions. A black key is roughly 60% the width
# of a white key and about 65% of its length.
_BLACK_WIDTH_RATIO = 0.6
_BLACK_HEIGHT_RATIO = 0.65


@dataclass(frozen=True)
class KeyRect:
    midi_note: int
    is_black: bool
    x: int
    y: int
    width: int
    height: int


def is_black_key(midi_note: int) -> bool:
    return (midi_note % 12) in _BLACK_PCS


def build_keyboard_layout(width: int = 1920, height: int = 200) -> list[KeyRect]:
    """Compute axis-aligned rectangles for all 88 keys.

    White keys tile the full width with no gaps (rounding distributes the
    leftover sub-pixels). Black keys are centered on the boundary between
    their two adjacent white keys.
    """
    white_w = width / NUM_WHITE_KEYS
    black_w = white_w * _BLACK_WIDTH_RATIO
    black_h = int(round(height * _BLACK_HEIGHT_RATIO))

    rects: list[KeyRect] = []
    white_index = 0
    for midi in range(MIDI_LOW, MIDI_HIGH + 1):
        if is_black_key(midi):
            # Black keys sit on top of the boundary between the previous
            # white key (index white_index - 1) and the next (white_index).
            boundary_x = white_index * white_w
            x = boundary_x - black_w / 2
            rects.append(
                KeyRect(
                    midi_note=midi,
                    is_black=True,
                    x=int(round(x)),
                    y=0,
                    width=int(round(black_w)),
                    height=black_h,
                )
            )
        else:
            # Snap left and right edges to integer pixels independently so
            # adjacent white keys share an exact boundary with no 1-px gaps.
            left = int(round(white_index * white_w))
            right = int(round((white_index + 1) * white_w))
            rects.append(
                KeyRect(
                    midi_note=midi,
                    is_black=False,
                    x=left,
                    y=0,
                    width=right - left,
                    height=height,
                )
            )
            white_index += 1

    return rects
