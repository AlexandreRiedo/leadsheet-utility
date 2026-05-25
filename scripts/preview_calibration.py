"""Standalone calibration preview.

Opens the projector window in fullscreen and runs the 4-point calibration
UI. On Enter, saves the calibration to <repo>/data/calibration.json
and then enters a verification mode: a static C-minor highlight is rendered
through the saved homography so you can eyeball alignment on the real keys.

Press Esc at any time to quit without saving.

Controls (during calibration):
  Drag, or Tab / 1-4 to pick a marker
  Arrows to nudge (Shift = x10)
  R to reset markers
  Enter to confirm and save
  Esc to cancel
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

import pygame

from leadsheet_utility.calibration import (
    CalibrationUI,
    DEFAULT_CALIBRATION_PATH,
    load_calibration,
    save_calibration,
)
from leadsheet_utility.projection import (
    KeyHighlight,
    build_keyboard_layout,
    make_canonical_surface,
    render_canonical,
    warp_canonical_to_projector,
)

CANONICAL_SIZE = (1920, 200)


def _open_projection_window() -> tuple[pygame.Window, tuple[int, int]]:
    pygame.init()
    desktop_sizes = pygame.display.get_desktop_sizes()
    print(f"Detected displays: {desktop_sizes}")

    chosen = int(os.environ.get("PROJ_DISPLAY", len(desktop_sizes) - 1))
    if not 0 <= chosen < len(desktop_sizes):
        chosen = 0
    proj_size = desktop_sizes[chosen]
    x_offset = sum(w for w, _ in desktop_sizes[:chosen])
    print(f"Targeting display {chosen} at {proj_size}, x_offset={x_offset}")

    window = pygame.Window(
        title=f"Calibration (display {chosen})",
        size=proj_size,
        position=(x_offset, 0),
        fullscreen_desktop=(len(desktop_sizes) > 1),
    )
    if window.size != proj_size:
        print(f"Window size adjusted to {window.size}")
        proj_size = window.size
    return window, proj_size


def _run_calibration(window: pygame.Window, proj_size: tuple[int, int]) -> bool:
    """Run the calibration UI. Returns True if confirmed (and saved), False otherwise."""
    existing = load_calibration()
    initial_markers = None
    initial_bw = None
    initial_bh = None
    if existing is not None and existing.projector_size == proj_size:
        initial_markers = existing.markers
        initial_bw = existing.black_width_ratio
        initial_bh = existing.black_height_ratio
        print(
            f"Loaded existing calibration from {DEFAULT_CALIBRATION_PATH} "
            f"(black ratios w={initial_bw:.2f} h={initial_bh:.2f})"
        )

    ui_kwargs: dict = {
        "canonical_size": CANONICAL_SIZE,
        "projector_size": proj_size,
        "initial_markers": initial_markers,
    }
    if initial_bw is not None:
        ui_kwargs["black_width_ratio"] = initial_bw
    if initial_bh is not None:
        ui_kwargs["black_height_ratio"] = initial_bh
    if existing is not None:
        ui_kwargs["black_key_offsets"] = existing.black_key_offsets
        ui_kwargs["midi_full_low"] = existing.midi_full_low
        ui_kwargs["midi_full_high"] = existing.midi_full_high
        ui_kwargs["midi_one_octave_low"] = existing.midi_one_octave_low
        ui_kwargs["midi_one_octave_high"] = existing.midi_one_octave_high
        ui_kwargs["midi_two_octave_low"] = existing.midi_two_octave_low
        ui_kwargs["midi_two_octave_high"] = existing.midi_two_octave_high
        ui_kwargs["audio_delay_ms"] = existing.audio_delay_ms
    ui = CalibrationUI(**ui_kwargs)
    font = pygame.font.SysFont("consolas", 20)
    clock = pygame.time.Clock()

    while ui.active:
        for event in pygame.event.get():
            if event.type in (pygame.QUIT, pygame.WINDOWCLOSE):
                ui.cancelled = True
            else:
                ui.handle_event(event)

        ui.render(window.get_surface(), font=font)
        window.flip()
        clock.tick(60)

    if ui.confirmed:
        cal = ui.build_calibration()
        save_calibration(cal)
        print(f"Saved calibration to {DEFAULT_CALIBRATION_PATH}")
        return True
    print("Cancelled — no changes saved.")
    return False


def _run_verification(window: pygame.Window, proj_size: tuple[int, int]) -> None:
    """Render a static C-minor highlight through the saved homography."""
    cal = load_calibration()
    if cal is None:
        return
    H = cal.homography()

    layout = build_keyboard_layout(
        *CANONICAL_SIZE,
        midi_low=cal.midi_full_low,
        midi_high=cal.midi_full_high,
        black_width_ratio=cal.black_width_ratio,
        black_height_ratio=cal.black_height_ratio,
        black_key_offsets=cal.black_key_offsets,
    )
    canonical = make_canonical_surface(*CANONICAL_SIZE)
    c_minor_pcs = {0, 2, 3, 5, 7, 8, 10}
    highlights = [
        KeyHighlight(k.midi_note, (255, 255, 255))
        for k in layout
        if (k.midi_note % 12) in c_minor_pcs
    ]
    render_canonical(canonical, highlights, layout)

    warped_buf = pygame.Surface(proj_size)
    font = pygame.font.SysFont("consolas", 18)
    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type in (pygame.QUIT, pygame.WINDOWCLOSE):
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        warp_canonical_to_projector(canonical, H, proj_size, out=warped_buf)
        screen = window.get_surface()
        screen.fill((0, 0, 0))
        screen.blit(warped_buf, (0, 0))
        hint = font.render("Verification — Esc to exit", True, (120, 120, 120))
        screen.blit(hint, (20, 20))
        window.flip()
        clock.tick(60)


def main() -> None:
    window, proj_size = _open_projection_window()
    try:
        if _run_calibration(window, proj_size):
            _run_verification(window, proj_size)
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
