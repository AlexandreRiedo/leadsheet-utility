"""Piano keyboard layout in a canonical (undistorted) image.

Coordinates are pixel positions inside a flat top-down image of the keyboard
(default 1920x200). This image is later warped onto the projector frame via
a homography. The layout itself knows nothing about projection — it is pure
geometry derived from standard piano proportions.

The full 88-key range (A0–C8) is exposed as constants, but the default
layout covers only D2–G6 — the band the projector actually lights up on
the test rig. The range is configurable per call while we're still
prototyping.
"""

from dataclasses import dataclass

# Full 88-key reference range (A0..C8).
MIDI_LOW = 21
MIDI_HIGH = 108
NUM_KEYS = MIDI_HIGH - MIDI_LOW + 1  # 88
NUM_WHITE_KEYS = 52

# Default projected range: F2..E6. The band starts at the left edge of F2
# and ends at the right edge of E6 — i.e. both projected edges line up with
# the left edge of an F key on the piano, giving the user a single physical
# landmark to align both corners against during calibration.
MIDI_DEFAULT_LOW = 41  # F2
MIDI_DEFAULT_HIGH = 88  # E6

# Pitch classes that correspond to black keys (C=0).
_BLACK_PCS = frozenset({1, 3, 6, 8, 10})

# Standard acoustic-piano proportions. A black key is roughly 60% the width
# of a white key and about 65% of its length. Real instruments vary, so the
# layout builder accepts overrides — these are just the starting defaults.
DEFAULT_BLACK_WIDTH_RATIO = 0.6
DEFAULT_BLACK_HEIGHT_RATIO = 0.65


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


def count_white_keys(midi_low: int, midi_high: int) -> int:
    return sum(1 for m in range(midi_low, midi_high + 1) if not is_black_key(m))


def build_keyboard_layout(
    width: int = 1920,
    height: int = 200,
    midi_low: int = MIDI_DEFAULT_LOW,
    midi_high: int = MIDI_DEFAULT_HIGH,
    black_width_ratio: float = DEFAULT_BLACK_WIDTH_RATIO,
    black_height_ratio: float = DEFAULT_BLACK_HEIGHT_RATIO,
) -> list[KeyRect]:
    """Compute axis-aligned rectangles for the keys in [midi_low, midi_high].

    White keys tile the full width with no gaps (rounding distributes the
    leftover sub-pixels). Black keys are centered on the boundary between
    their two adjacent white keys, sized by `black_width_ratio` (fraction of
    a white-key's width) and `black_height_ratio` (fraction of canonical
    image height). These default to "standard" piano proportions but can be
    tuned per-instrument since real pianos vary.

    `midi_low` and `midi_high` must both be white keys so the canonical image
    starts and ends on a clean white-key edge.
    """
    if is_black_key(midi_low) or is_black_key(midi_high):
        raise ValueError(
            f"midi_low and midi_high must be white keys; got {midi_low}, {midi_high}"
        )

    num_whites = count_white_keys(midi_low, midi_high)
    white_w = width / num_whites
    black_w = white_w * black_width_ratio
    black_h = int(round(height * black_height_ratio))

    rects: list[KeyRect] = []
    white_index = 0
    for midi in range(midi_low, midi_high + 1):
        if is_black_key(midi):
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
