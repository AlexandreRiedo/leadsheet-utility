"""Tests for the CalibrationUI state machine.

Rendering is not tested here — the preview script is the visual harness.

Phase order:
RANGE_EDIT (FULL only) -> MAIN -> BLACK_KEY_TUNE -> BAND_EDIT
(1-OCT/2-OCT bands, clipped to FULL) -> AUDIO_DELAY -> confirmed.
"""

import os

import pygame
import pytest

from leadsheet_utility.calibration import (
    NUM_MARKERS,
    CalibrationPhase,
    CalibrationUI,
)
from leadsheet_utility.calibration.ui import RangeEndpoint
from leadsheet_utility.exercises.free import RangeMode


@pytest.fixture(scope="module", autouse=True)
def _pygame_headless():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    yield
    pygame.quit()


def _ui() -> CalibrationUI:
    return CalibrationUI(canonical_size=(1920, 200), projector_size=(1920, 1080))


def _kd(key: int, mod: int = 0) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, {"key": key, "mod": mod})


def _mb_down(pos: tuple[int, int], button: int = 1) -> pygame.event.Event:
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": button})


def _mb_up(button: int = 1) -> pygame.event.Event:
    return pygame.event.Event(pygame.MOUSEBUTTONUP, {"pos": (0, 0), "button": button})


def _mm(pos: tuple[int, int]) -> pygame.event.Event:
    return pygame.event.Event(pygame.MOUSEMOTION, {"pos": pos, "rel": (0, 0), "buttons": (1, 0, 0)})


def _enter_main_phase(ui: CalibrationUI) -> None:
    ui.handle_event(_kd(pygame.K_RETURN))
    assert ui.phase is CalibrationPhase.MAIN


def _enter_black_key_tune(ui: CalibrationUI) -> None:
    # RANGE_EDIT -> MAIN -> BLACK_KEY_TUNE
    ui.handle_event(_kd(pygame.K_RETURN))
    ui.handle_event(_kd(pygame.K_RETURN))
    assert ui.phase is CalibrationPhase.BLACK_KEY_TUNE


def _enter_band_edit(ui: CalibrationUI) -> None:
    # RANGE_EDIT -> MAIN -> BLACK_KEY_TUNE -> BAND_EDIT
    ui.handle_event(_kd(pygame.K_RETURN))
    ui.handle_event(_kd(pygame.K_RETURN))
    ui.handle_event(_kd(pygame.K_RETURN))
    assert ui.phase is CalibrationPhase.BAND_EDIT


def _enter_audio_delay(ui: CalibrationUI) -> None:
    # RANGE_EDIT -> MAIN -> BLACK_KEY_TUNE -> BAND_EDIT -> AUDIO_DELAY
    ui.handle_event(_kd(pygame.K_RETURN))
    ui.handle_event(_kd(pygame.K_RETURN))
    ui.handle_event(_kd(pygame.K_RETURN))
    ui.handle_event(_kd(pygame.K_RETURN))
    assert ui.phase is CalibrationPhase.AUDIO_DELAY


# --- bootstrap --------------------------------------------------------------


def test_starts_in_range_edit_with_four_markers():
    ui = _ui()
    assert ui.active
    assert ui.phase is CalibrationPhase.RANGE_EDIT
    assert len(ui.markers) == NUM_MARKERS
    assert not ui.confirmed and not ui.cancelled


def test_enter_advances_through_all_phases_then_confirms():
    """Enter advances RANGE_EDIT -> MAIN -> BLACK_KEY_TUNE -> BAND_EDIT
    -> AUDIO_DELAY -> confirmed."""
    ui = _ui()
    ui.handle_event(_kd(pygame.K_RETURN))
    assert ui.phase is CalibrationPhase.MAIN
    ui.handle_event(_kd(pygame.K_RETURN))
    assert ui.phase is CalibrationPhase.BLACK_KEY_TUNE
    ui.handle_event(_kd(pygame.K_RETURN))
    assert ui.phase is CalibrationPhase.BAND_EDIT
    ui.handle_event(_kd(pygame.K_RETURN))
    assert ui.phase is CalibrationPhase.AUDIO_DELAY
    assert ui.active
    ui.handle_event(_kd(pygame.K_RETURN))
    assert ui.confirmed
    assert not ui.active


def test_escape_cancels_from_range_edit():
    ui = _ui()
    ui.handle_event(_kd(pygame.K_ESCAPE))
    assert ui.cancelled
    assert not ui.active


def test_events_ignored_once_inactive():
    ui = _ui()
    # Five Enters: RANGE_EDIT -> MAIN -> BLACK_KEY_TUNE -> BAND_EDIT
    # -> AUDIO_DELAY -> confirmed.
    for _ in range(5):
        ui.handle_event(_kd(pygame.K_RETURN))
    assert ui.confirmed
    original = list(ui.markers)
    ui.handle_event(_kd(pygame.K_RIGHT))
    assert ui.markers == original


# --- phase 1: RANGE_EDIT (FULL range only) ----------------------------------


def test_range_edit_pins_active_range_to_full():
    """B and other range-cycle keys must not change the active range here."""
    ui = _ui()
    assert ui.active_range_mode is RangeMode.FULL
    ui.handle_event(_kd(pygame.K_b))
    # Any keypress runs the pin; explicit assert.
    assert ui.active_range_mode is RangeMode.FULL


def test_range_edit_tab_switches_endpoint():
    ui = _ui()
    assert ui.active_endpoint is RangeEndpoint.LOW
    ui.handle_event(_kd(pygame.K_TAB))
    assert ui.active_endpoint is RangeEndpoint.HIGH
    ui.handle_event(_kd(pygame.K_TAB))
    assert ui.active_endpoint is RangeEndpoint.LOW


def test_range_edit_arrows_nudge_low_endpoint_by_white_key():
    ui = _ui()
    initial_low = ui.midi_full_low
    assert ui.active_endpoint is RangeEndpoint.LOW
    ui.handle_event(_kd(pygame.K_RIGHT))
    assert ui.midi_full_low > initial_low
    assert (ui.midi_full_low % 12) not in {1, 3, 6, 8, 10}  # still white
    ui.handle_event(_kd(pygame.K_LEFT))
    assert ui.midi_full_low == initial_low


def test_range_edit_arrows_nudge_high_endpoint_after_tab():
    ui = _ui()
    ui.handle_event(_kd(pygame.K_TAB))
    assert ui.active_endpoint is RangeEndpoint.HIGH
    initial_high = ui.midi_full_high
    ui.handle_event(_kd(pygame.K_RIGHT))
    assert ui.midi_full_high > initial_high
    ui.handle_event(_kd(pygame.K_LEFT))
    assert ui.midi_full_high == initial_high


def test_range_edit_shift_arrow_moves_by_octave():
    ui = _ui()
    initial_low = ui.midi_full_low
    ui.handle_event(_kd(pygame.K_RIGHT, mod=pygame.KMOD_SHIFT))
    assert ui.midi_full_low == initial_low + 12


def test_range_edit_low_clamped_below_high_by_min_width():
    ui = _ui()
    for _ in range(200):
        ui.handle_event(_kd(pygame.K_RIGHT, mod=pygame.KMOD_SHIFT))
    assert ui.midi_full_high - ui.midi_full_low >= 12


def test_range_edit_r_resets_to_defaults():
    from leadsheet_utility.projection import MIDI_DEFAULT_HIGH, MIDI_DEFAULT_LOW

    ui = _ui()
    ui.handle_event(_kd(pygame.K_RIGHT, mod=pygame.KMOD_SHIFT))
    assert ui.midi_full_low != MIDI_DEFAULT_LOW
    ui.handle_event(_kd(pygame.K_r))
    assert ui.midi_full_low == MIDI_DEFAULT_LOW
    assert ui.midi_full_high == MIDI_DEFAULT_HIGH


def test_range_edit_enter_advances_to_main():
    ui = _ui()
    ui.handle_event(_kd(pygame.K_RETURN))
    assert ui.phase is CalibrationPhase.MAIN


def test_range_edit_does_not_handle_mouse_drag():
    """RANGE_EDIT shouldn't move markers — that's MAIN's job."""
    ui = _ui()
    original_markers = list(ui.markers)
    ui.handle_event(_mb_down((int(ui.markers[0][0]), int(ui.markers[0][1]))))
    ui.handle_event(_mm((500, 600)))
    ui.handle_event(_mb_up())
    assert ui.markers == original_markers


# --- phase 2: MAIN ----------------------------------------------------------


def test_tab_cycles_active_marker():
    ui = _ui()
    _enter_main_phase(ui)
    assert ui.active_idx == 0
    ui.handle_event(_kd(pygame.K_TAB))
    assert ui.active_idx == 1
    ui.handle_event(_kd(pygame.K_TAB))
    ui.handle_event(_kd(pygame.K_TAB))
    ui.handle_event(_kd(pygame.K_TAB))
    assert ui.active_idx == 0  # wraps


def test_shift_tab_cycles_backward():
    ui = _ui()
    _enter_main_phase(ui)
    ui.handle_event(_kd(pygame.K_TAB, mod=pygame.KMOD_SHIFT))
    assert ui.active_idx == NUM_MARKERS - 1


def test_number_keys_select_marker():
    ui = _ui()
    _enter_main_phase(ui)
    ui.handle_event(_kd(pygame.K_3))
    assert ui.active_idx == 2


def test_arrow_keys_nudge_active_marker():
    ui = _ui()
    _enter_main_phase(ui)
    x0, y0 = ui.markers[0]
    ui.handle_event(_kd(pygame.K_RIGHT))
    ui.handle_event(_kd(pygame.K_DOWN))
    assert ui.markers[0] == (x0 + 1, y0 + 1)


def test_shift_arrow_big_step():
    ui = _ui()
    _enter_main_phase(ui)
    x0, y0 = ui.markers[0]
    ui.handle_event(_kd(pygame.K_RIGHT, mod=pygame.KMOD_SHIFT))
    assert ui.markers[0] == (x0 + 10, y0)


def test_mouse_click_selects_nearest_marker_then_drag_moves_it():
    ui = _ui()
    _enter_main_phase(ui)
    target_pos = ui.markers[2]
    ui.handle_event(_mb_down((int(target_pos[0]), int(target_pos[1]))))
    assert ui.active_idx == 2
    ui.handle_event(_mm((500, 600)))
    assert ui.markers[2] == (500.0, 600.0)
    ui.handle_event(_mb_up())
    ui.handle_event(_mm((10, 10)))
    assert ui.markers[2] == (500.0, 600.0)


def test_click_outside_any_marker_does_not_select():
    ui = _ui()
    _enter_main_phase(ui)
    ui.handle_event(_kd(pygame.K_2))
    ui.handle_event(_mb_down((960, 540)))
    assert ui.active_idx == 1


def test_markers_are_clamped_to_projector_bounds():
    ui = _ui()
    _enter_main_phase(ui)
    ui.active_idx = 0
    for _ in range(100):
        ui.handle_event(_kd(pygame.K_LEFT, mod=pygame.KMOD_SHIFT))
        ui.handle_event(_kd(pygame.K_UP, mod=pygame.KMOD_SHIFT))
    assert ui.markers[0] == (0.0, 0.0)


def test_reset_restores_default_markers():
    ui = _ui()
    _enter_main_phase(ui)
    ui.handle_event(_kd(pygame.K_RIGHT, mod=pygame.KMOD_SHIFT))
    original = ui.markers[0]
    ui.handle_event(_kd(pygame.K_r))
    assert ui.markers[0] != original


def test_homography_matches_built_calibration():
    ui = _ui()
    H_ui = ui.homography()
    H_cal = ui.build_calibration().homography()
    assert (H_ui == H_cal).all()


# --- MAIN: black-key proportion live adjustments ----------------------------


def test_qw_keys_adjust_black_width_ratio():
    ui = _ui()
    _enter_main_phase(ui)
    base = ui.black_width_ratio
    ui.handle_event(_kd(pygame.K_w))
    assert ui.black_width_ratio == pytest.approx(base + 0.01)
    ui.handle_event(_kd(pygame.K_q))
    assert ui.black_width_ratio == pytest.approx(base)


def test_as_keys_adjust_black_height_ratio():
    ui = _ui()
    _enter_main_phase(ui)
    base = ui.black_height_ratio
    ui.handle_event(_kd(pygame.K_s))
    assert ui.black_height_ratio == pytest.approx(base + 0.01)
    ui.handle_event(_kd(pygame.K_a))
    assert ui.black_height_ratio == pytest.approx(base)


def test_shift_ratio_keys_use_big_step():
    ui = _ui()
    _enter_main_phase(ui)
    base_w = ui.black_width_ratio
    ui.handle_event(_kd(pygame.K_w, mod=pygame.KMOD_SHIFT))
    assert ui.black_width_ratio == pytest.approx(base_w + 0.05)


def test_black_width_ratio_clamped_to_max():
    ui = _ui()
    _enter_main_phase(ui)
    for _ in range(200):
        ui.handle_event(_kd(pygame.K_w, mod=pygame.KMOD_SHIFT))
    assert ui.black_width_ratio <= 1.20


def test_black_height_ratio_clamped_to_min():
    ui = _ui()
    _enter_main_phase(ui)
    for _ in range(200):
        ui.handle_event(_kd(pygame.K_a, mod=pygame.KMOD_SHIFT))
    assert ui.black_height_ratio >= 0.30


def test_build_calibration_carries_ratios():
    ui = _ui()
    _enter_main_phase(ui)
    ui.handle_event(_kd(pygame.K_w))
    ui.handle_event(_kd(pygame.K_s))
    cal = ui.build_calibration()
    assert cal.black_width_ratio == ui.black_width_ratio
    assert cal.black_height_ratio == ui.black_height_ratio


def test_initial_ratios_can_be_overridden():
    ui = CalibrationUI(
        canonical_size=(1920, 200),
        projector_size=(1920, 1080),
        black_width_ratio=0.75,
        black_height_ratio=0.55,
    )
    assert ui.black_width_ratio == pytest.approx(0.75)
    assert ui.black_height_ratio == pytest.approx(0.55)


# --- phase 3: BLACK_KEY_TUNE ------------------------------------------------


def test_tune_phase_tab_cycles_black_keys():
    ui = _ui()
    _enter_black_key_tune(ui)
    assert ui.active_black_idx == 0
    ui.handle_event(_kd(pygame.K_TAB))
    assert ui.active_black_idx == 1
    ui.handle_event(_kd(pygame.K_TAB, mod=pygame.KMOD_SHIFT))
    assert ui.active_black_idx == 0
    ui.handle_event(_kd(pygame.K_TAB, mod=pygame.KMOD_SHIFT))
    assert ui.active_black_idx == len(ui._black_key_midis) - 1


def test_tune_phase_arrow_nudges_active_black_key_offset():
    ui = _ui()
    _enter_black_key_tune(ui)
    midi = ui._black_key_midis[0]
    ui.handle_event(_kd(pygame.K_RIGHT))
    ui.handle_event(_kd(pygame.K_DOWN))
    assert ui.black_key_offsets[midi] == (1.0, 1.0)
    ui.handle_event(_kd(pygame.K_LEFT, mod=pygame.KMOD_SHIFT))
    assert ui.black_key_offsets[midi] == (-9.0, 1.0)


def test_tune_phase_offsets_are_per_key():
    ui = _ui()
    _enter_black_key_tune(ui)
    first = ui._black_key_midis[0]
    ui.handle_event(_kd(pygame.K_RIGHT))
    ui.handle_event(_kd(pygame.K_TAB))
    second = ui._black_key_midis[1]
    ui.handle_event(_kd(pygame.K_LEFT))
    assert ui.black_key_offsets[first] == (1.0, 0.0)
    assert ui.black_key_offsets[second] == (-1.0, 0.0)


def test_tune_phase_r_resets_offsets():
    ui = _ui()
    _enter_black_key_tune(ui)
    ui.handle_event(_kd(pygame.K_RIGHT))
    assert ui.black_key_offsets
    ui.handle_event(_kd(pygame.K_r))
    assert ui.black_key_offsets == {}


def test_tune_phase_escape_cancels():
    ui = _ui()
    _enter_black_key_tune(ui)
    ui.handle_event(_kd(pygame.K_ESCAPE))
    assert ui.cancelled
    assert not ui.active


def test_tune_phase_ignores_marker_drag():
    """Mouse events shouldn't move markers during black-key tuning."""
    ui = _ui()
    original_markers = list(ui.markers)
    _enter_black_key_tune(ui)
    ui.handle_event(_mb_down((int(ui.markers[0][0]), int(ui.markers[0][1]))))
    ui.handle_event(_mm((500, 600)))
    ui.handle_event(_mb_up())
    assert ui.markers == original_markers


def test_tune_phase_enter_advances_to_band_edit():
    ui = _ui()
    _enter_black_key_tune(ui)
    ui.handle_event(_kd(pygame.K_RETURN))
    assert ui.phase is CalibrationPhase.BAND_EDIT


def test_build_calibration_carries_black_key_offsets():
    ui = _ui()
    _enter_black_key_tune(ui)
    ui.handle_event(_kd(pygame.K_RIGHT, mod=pygame.KMOD_SHIFT))
    cal = ui.build_calibration()
    assert cal.black_key_offsets == ui.black_key_offsets
    assert len(cal.black_key_offsets) == 1


# --- phase 4: BAND_EDIT -----------------------------------------------------


def test_band_edit_defaults_to_two_octave():
    """Entering BAND_EDIT should pin the active range to a band, not FULL."""
    ui = _ui()
    _enter_band_edit(ui)
    assert ui.active_range_mode is RangeMode.TWO_OCTAVE


def test_band_edit_b_cycles_one_two_only():
    """B in BAND_EDIT must not select FULL."""
    ui = _ui()
    _enter_band_edit(ui)
    assert ui.active_range_mode is RangeMode.TWO_OCTAVE
    ui.handle_event(_kd(pygame.K_b))
    assert ui.active_range_mode is RangeMode.ONE_OCTAVE
    ui.handle_event(_kd(pygame.K_b))
    assert ui.active_range_mode is RangeMode.TWO_OCTAVE


def test_band_edit_nudge_low_endpoint():
    ui = _ui()
    _enter_band_edit(ui)
    initial = ui.midi_two_octave_low
    ui.handle_event(_kd(pygame.K_RIGHT))
    assert ui.midi_two_octave_low > initial


def test_band_edit_high_endpoint_clipped_to_full_high():
    """Nudging band high past full_high must not exceed the FULL range."""
    ui = _ui()
    _enter_band_edit(ui)
    ui.handle_event(_kd(pygame.K_TAB))  # active = HIGH
    for _ in range(50):
        ui.handle_event(_kd(pygame.K_RIGHT, mod=pygame.KMOD_SHIFT))
    assert ui.midi_two_octave_high <= ui.midi_full_high


def test_band_edit_low_endpoint_clipped_to_full_low():
    ui = _ui()
    _enter_band_edit(ui)
    # Active = LOW. Push downward (Left) past FULL low — should clip.
    for _ in range(50):
        ui.handle_event(_kd(pygame.K_LEFT, mod=pygame.KMOD_SHIFT))
    assert ui.midi_two_octave_low >= ui.midi_full_low


def test_band_edit_clips_existing_bands_on_entry_when_full_range_shrunk():
    """If FULL is shrunk in phase 1 so that the default 2-OCT band extends
    past it, entering BAND_EDIT must clip the band into the new FULL range."""
    ui = _ui()
    # In RANGE_EDIT: shrink FULL high so the default 2-OCT high (91 = G6)
    # is now outside. Default FULL high is 88 (E6); push it down a few
    # white keys with Left to bring it below 91 (it already is) — instead,
    # use Shift+Left from HIGH to drop FULL by an octave: 88 -> 76.
    ui.handle_event(_kd(pygame.K_TAB))  # active = HIGH
    ui.handle_event(_kd(pygame.K_LEFT, mod=pygame.KMOD_SHIFT))
    assert ui.midi_full_high == 76
    # Default 2-OCT high is 91 (G6), which is now well above 76.
    assert ui.midi_two_octave_high == 91
    _enter_band_edit(ui)
    assert ui.midi_two_octave_high <= ui.midi_full_high
    assert ui.midi_one_octave_high <= ui.midi_full_high


def test_band_edit_enter_advances_to_audio_delay():
    ui = _ui()
    _enter_band_edit(ui)
    ui.handle_event(_kd(pygame.K_RETURN))
    assert ui.phase is CalibrationPhase.AUDIO_DELAY


def test_band_edit_escape_cancels():
    ui = _ui()
    _enter_band_edit(ui)
    ui.handle_event(_kd(pygame.K_ESCAPE))
    assert ui.cancelled
    assert not ui.active


# --- phase 5: AUDIO_DELAY ---------------------------------------------------


def test_audio_delay_up_down_nudges_by_one_ms():
    ui = _ui()
    _enter_audio_delay(ui)
    assert ui.audio_delay_ms == 0
    ui.handle_event(_kd(pygame.K_UP))
    assert ui.audio_delay_ms == 1
    ui.handle_event(_kd(pygame.K_DOWN))
    assert ui.audio_delay_ms == 0


def test_audio_delay_shift_arrow_nudges_by_ten_ms():
    ui = _ui()
    _enter_audio_delay(ui)
    ui.handle_event(_kd(pygame.K_UP, mod=pygame.KMOD_SHIFT))
    assert ui.audio_delay_ms == 10
    ui.handle_event(_kd(pygame.K_DOWN, mod=pygame.KMOD_SHIFT))
    assert ui.audio_delay_ms == 0


def test_audio_delay_r_resets_to_zero():
    ui = _ui()
    _enter_audio_delay(ui)
    ui.handle_event(_kd(pygame.K_UP, mod=pygame.KMOD_SHIFT))
    ui.handle_event(_kd(pygame.K_UP, mod=pygame.KMOD_SHIFT))
    assert ui.audio_delay_ms == 20
    ui.handle_event(_kd(pygame.K_r))
    assert ui.audio_delay_ms == 0


def test_audio_delay_enter_confirms():
    ui = _ui()
    _enter_audio_delay(ui)
    ui.handle_event(_kd(pygame.K_RETURN))
    assert ui.confirmed
    assert not ui.active


def test_audio_delay_escape_cancels():
    ui = _ui()
    _enter_audio_delay(ui)
    ui.handle_event(_kd(pygame.K_ESCAPE))
    assert ui.cancelled
    assert not ui.active


# --- build_calibration & snapshot -------------------------------------------


def test_build_calibration_carries_range_and_audio_fields():
    ui = _ui()
    # Adjust FULL range in phase 1, then a band in phase 4, then audio delay.
    ui.handle_event(_kd(pygame.K_RIGHT))  # FULL low up by one white key
    full_low_after = ui.midi_full_low
    _enter_band_edit(ui)
    ui.handle_event(_kd(pygame.K_RIGHT))  # 2-OCT (default active band) low +1
    two_low_after = ui.midi_two_octave_low
    ui.handle_event(_kd(pygame.K_RETURN))  # -> AUDIO_DELAY
    assert ui.phase is CalibrationPhase.AUDIO_DELAY
    ui.handle_event(_kd(pygame.K_UP, mod=pygame.KMOD_SHIFT))
    cal = ui.build_calibration()
    assert cal.midi_full_low == full_low_after
    assert cal.midi_two_octave_low == two_low_after
    assert cal.audio_delay_ms == 10


def test_snapshot_reflects_initial_phase_and_values():
    ui = _ui()
    snap = ui.snapshot()
    assert snap.phase is CalibrationPhase.RANGE_EDIT
    assert snap.audio_delay_ms == 0
    assert snap.active_range_mode is RangeMode.FULL
    assert snap.active_endpoint is RangeEndpoint.LOW


def test_snapshot_updates_during_range_edit():
    ui = _ui()
    ui.handle_event(_kd(pygame.K_TAB))
    snap = ui.snapshot()
    assert snap.active_endpoint is RangeEndpoint.HIGH


def test_snapshot_reflects_audio_delay_phase():
    ui = _ui()
    _enter_audio_delay(ui)
    ui.handle_event(_kd(pygame.K_UP))
    snap = ui.snapshot()
    assert snap.phase is CalibrationPhase.AUDIO_DELAY
    assert snap.audio_delay_ms == 1


def test_initial_range_fields_can_be_overridden():
    ui = CalibrationUI(
        canonical_size=(1920, 200),
        projector_size=(1920, 1080),
        midi_full_low=36,
        midi_full_high=84,
        midi_one_octave_low=60,
        midi_one_octave_high=83,
        midi_two_octave_low=48,
        midi_two_octave_high=83,
        audio_delay_ms=25,
    )
    assert ui.midi_full_low == 36
    assert ui.midi_full_high == 84
    assert ui.midi_one_octave_low == 60
    assert ui.midi_two_octave_low == 48
    assert ui.audio_delay_ms == 25
