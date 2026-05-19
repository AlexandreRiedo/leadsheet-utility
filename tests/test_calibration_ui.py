"""Tests for the CalibrationUI state machine.

Rendering is not tested here — the preview script is the visual harness.
"""

import os

import pygame
import pytest

from leadsheet_utility.calibration import NUM_MARKERS, CalibrationPhase, CalibrationUI


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


def test_starts_active_with_four_markers():
    ui = _ui()
    assert ui.active
    assert len(ui.markers) == NUM_MARKERS
    assert not ui.confirmed and not ui.cancelled


def test_enter_advances_to_black_key_tuning_then_confirms():
    """Enter is a two-step confirm: MAIN -> BLACK_KEY_TUNE -> confirmed."""
    ui = _ui()
    ui.handle_event(_kd(pygame.K_RETURN))
    assert ui.phase is CalibrationPhase.BLACK_KEY_TUNE
    assert ui.active  # not confirmed yet
    ui.handle_event(_kd(pygame.K_RETURN))
    assert ui.confirmed
    assert not ui.active


def test_escape_cancels():
    ui = _ui()
    ui.handle_event(_kd(pygame.K_ESCAPE))
    assert ui.cancelled
    assert not ui.active


def test_events_ignored_once_inactive():
    ui = _ui()
    # Two Enters: advance into tuning, then confirm.
    ui.handle_event(_kd(pygame.K_RETURN))
    ui.handle_event(_kd(pygame.K_RETURN))
    original = list(ui.markers)
    ui.handle_event(_kd(pygame.K_RIGHT))
    assert ui.markers == original


def test_tab_cycles_active_marker():
    ui = _ui()
    assert ui.active_idx == 0
    ui.handle_event(_kd(pygame.K_TAB))
    assert ui.active_idx == 1
    ui.handle_event(_kd(pygame.K_TAB))
    ui.handle_event(_kd(pygame.K_TAB))
    ui.handle_event(_kd(pygame.K_TAB))
    assert ui.active_idx == 0  # wraps


def test_shift_tab_cycles_backward():
    ui = _ui()
    ui.handle_event(_kd(pygame.K_TAB, mod=pygame.KMOD_SHIFT))
    assert ui.active_idx == NUM_MARKERS - 1


def test_number_keys_select_marker():
    ui = _ui()
    ui.handle_event(_kd(pygame.K_3))
    assert ui.active_idx == 2


def test_arrow_keys_nudge_active_marker():
    ui = _ui()
    x0, y0 = ui.markers[0]
    ui.handle_event(_kd(pygame.K_RIGHT))
    ui.handle_event(_kd(pygame.K_DOWN))
    assert ui.markers[0] == (x0 + 1, y0 + 1)


def test_shift_arrow_big_step():
    ui = _ui()
    x0, y0 = ui.markers[0]
    ui.handle_event(_kd(pygame.K_RIGHT, mod=pygame.KMOD_SHIFT))
    assert ui.markers[0] == (x0 + 10, y0)


def test_mouse_click_selects_nearest_marker_then_drag_moves_it():
    ui = _ui()
    target_pos = ui.markers[2]  # bottom-right
    ui.handle_event(_mb_down((int(target_pos[0]), int(target_pos[1]))))
    assert ui.active_idx == 2
    ui.handle_event(_mm((500, 600)))
    assert ui.markers[2] == (500.0, 600.0)
    ui.handle_event(_mb_up())
    # After mouse-up, motion should no longer move the marker.
    ui.handle_event(_mm((10, 10)))
    assert ui.markers[2] == (500.0, 600.0)


def test_click_outside_any_marker_does_not_select():
    ui = _ui()
    ui.handle_event(_kd(pygame.K_2))  # set active to 1
    ui.handle_event(_mb_down((960, 540)))  # middle of the screen — no marker there
    assert ui.active_idx == 1


def test_markers_are_clamped_to_projector_bounds():
    ui = _ui()
    ui.active_idx = 0
    for _ in range(100):
        ui.handle_event(_kd(pygame.K_LEFT, mod=pygame.KMOD_SHIFT))
        ui.handle_event(_kd(pygame.K_UP, mod=pygame.KMOD_SHIFT))
    assert ui.markers[0] == (0.0, 0.0)


def test_reset_restores_default_markers():
    ui = _ui()
    ui.handle_event(_kd(pygame.K_RIGHT, mod=pygame.KMOD_SHIFT))
    original = ui.markers[0]
    ui.handle_event(_kd(pygame.K_r))
    assert ui.markers[0] != original


def test_homography_matches_built_calibration():
    ui = _ui()
    H_ui = ui.homography()
    H_cal = ui.build_calibration().homography()
    assert (H_ui == H_cal).all()


# --- black-key proportion live adjustments ----------------------------------


def test_qw_keys_adjust_black_width_ratio():
    ui = _ui()
    base = ui.black_width_ratio
    ui.handle_event(_kd(pygame.K_w))
    assert ui.black_width_ratio == pytest.approx(base + 0.01)
    ui.handle_event(_kd(pygame.K_q))
    assert ui.black_width_ratio == pytest.approx(base)


def test_as_keys_adjust_black_height_ratio():
    ui = _ui()
    base = ui.black_height_ratio
    ui.handle_event(_kd(pygame.K_s))
    assert ui.black_height_ratio == pytest.approx(base + 0.01)
    ui.handle_event(_kd(pygame.K_a))
    assert ui.black_height_ratio == pytest.approx(base)


def test_shift_ratio_keys_use_big_step():
    ui = _ui()
    base_w = ui.black_width_ratio
    ui.handle_event(_kd(pygame.K_w, mod=pygame.KMOD_SHIFT))
    assert ui.black_width_ratio == pytest.approx(base_w + 0.05)


def test_black_width_ratio_clamped_to_max():
    ui = _ui()
    for _ in range(200):
        ui.handle_event(_kd(pygame.K_w, mod=pygame.KMOD_SHIFT))
    assert ui.black_width_ratio <= 1.20


def test_black_height_ratio_clamped_to_min():
    ui = _ui()
    for _ in range(200):
        ui.handle_event(_kd(pygame.K_a, mod=pygame.KMOD_SHIFT))
    assert ui.black_height_ratio >= 0.30


def test_build_calibration_carries_ratios():
    ui = _ui()
    ui.handle_event(_kd(pygame.K_w))
    ui.handle_event(_kd(pygame.K_s))
    cal = ui.build_calibration()
    assert cal.black_width_ratio == ui.black_width_ratio
    assert cal.black_height_ratio == ui.black_height_ratio


def test_initial_ratios_can_be_overridden():
    from leadsheet_utility.calibration import CalibrationUI
    ui = CalibrationUI(
        canonical_size=(1920, 200),
        projector_size=(1920, 1080),
        black_width_ratio=0.75,
        black_height_ratio=0.55,
    )
    assert ui.black_width_ratio == pytest.approx(0.75)
    assert ui.black_height_ratio == pytest.approx(0.55)


# --- phase 2: per-black-key tuning ------------------------------------------


def _enter_tune_phase(ui: CalibrationUI) -> None:
    ui.handle_event(_kd(pygame.K_RETURN))
    assert ui.phase is CalibrationPhase.BLACK_KEY_TUNE


def test_tune_phase_tab_cycles_black_keys():
    ui = _ui()
    _enter_tune_phase(ui)
    assert ui.active_black_idx == 0
    ui.handle_event(_kd(pygame.K_TAB))
    assert ui.active_black_idx == 1
    ui.handle_event(_kd(pygame.K_TAB, mod=pygame.KMOD_SHIFT))
    assert ui.active_black_idx == 0
    # Shift-Tab from index 0 wraps to the last black key.
    ui.handle_event(_kd(pygame.K_TAB, mod=pygame.KMOD_SHIFT))
    assert ui.active_black_idx == len(ui._black_key_midis) - 1


def test_tune_phase_arrow_nudges_active_black_key_offset():
    ui = _ui()
    _enter_tune_phase(ui)
    midi = ui._black_key_midis[0]
    ui.handle_event(_kd(pygame.K_RIGHT))
    ui.handle_event(_kd(pygame.K_DOWN))
    assert ui.black_key_offsets[midi] == (1.0, 1.0)
    ui.handle_event(_kd(pygame.K_LEFT, mod=pygame.KMOD_SHIFT))
    assert ui.black_key_offsets[midi] == (-9.0, 1.0)


def test_tune_phase_offsets_are_per_key():
    ui = _ui()
    _enter_tune_phase(ui)
    first = ui._black_key_midis[0]
    ui.handle_event(_kd(pygame.K_RIGHT))
    ui.handle_event(_kd(pygame.K_TAB))
    second = ui._black_key_midis[1]
    ui.handle_event(_kd(pygame.K_LEFT))
    assert ui.black_key_offsets[first] == (1.0, 0.0)
    assert ui.black_key_offsets[second] == (-1.0, 0.0)


def test_tune_phase_r_resets_offsets():
    ui = _ui()
    _enter_tune_phase(ui)
    ui.handle_event(_kd(pygame.K_RIGHT))
    assert ui.black_key_offsets
    ui.handle_event(_kd(pygame.K_r))
    assert ui.black_key_offsets == {}


def test_tune_phase_escape_cancels():
    ui = _ui()
    _enter_tune_phase(ui)
    ui.handle_event(_kd(pygame.K_ESCAPE))
    assert ui.cancelled
    assert not ui.active


def test_tune_phase_ignores_marker_drag():
    """Mouse events shouldn't move markers during black-key tuning."""
    ui = _ui()
    original_markers = list(ui.markers)
    _enter_tune_phase(ui)
    ui.handle_event(_mb_down((int(ui.markers[0][0]), int(ui.markers[0][1]))))
    ui.handle_event(_mm((500, 600)))
    ui.handle_event(_mb_up())
    assert ui.markers == original_markers


def test_build_calibration_carries_black_key_offsets():
    ui = _ui()
    _enter_tune_phase(ui)
    ui.handle_event(_kd(pygame.K_RIGHT, mod=pygame.KMOD_SHIFT))
    cal = ui.build_calibration()
    assert cal.black_key_offsets == ui.black_key_offsets
    assert len(cal.black_key_offsets) == 1
