"""End-to-end projection preview.

Opens a fullscreen window on the secondary display (the projector), renders
the C-minor scale into a canonical 1920x200 keyboard image over the default
projected range (D2..G6), warps it with a placeholder homography to a
horizontal band on the 1920x1080 projector frame, and displays it. If no
secondary display is detected, falls back to a windowed preview on the
primary display.

Range can be overridden via PROJ_MIDI_LOW / PROJ_MIDI_HIGH env vars (both
must be white-key MIDI numbers).

Press Esc or close the window to quit.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# On Windows, opt into per-monitor DPI awareness so display sizes are reported
# in real pixels (e.g. 1920x1080) instead of the scaled logical size that
# Windows hands to non-DPI-aware apps (1536x864 under 125% scaling).
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

import pygame

from leadsheet_utility.projection import (
    KeyHighlight,
    MIDI_DEFAULT_HIGH,
    MIDI_DEFAULT_LOW,
    build_keyboard_layout,
    make_canonical_surface,
    make_default_homography,
    render_canonical,
    warp_canonical_to_projector,
)


CANONICAL_SIZE = (1920, 200)


def main() -> None:
    pygame.init()

    desktop_sizes = pygame.display.get_desktop_sizes()
    print(f"Detected displays: {desktop_sizes}")

    # Choose display index: env var PROJ_DISPLAY=N overrides, else last display.
    chosen = int(os.environ.get("PROJ_DISPLAY", len(desktop_sizes) - 1))
    if chosen < 0 or chosen >= len(desktop_sizes):
        print(f"PROJ_DISPLAY={chosen} out of range; using 0.")
        chosen = 0
    proj_size = desktop_sizes[chosen]
    # x-position = sum of widths of all displays to the left of `chosen`.
    # This assumes a horizontal arrangement, which is the typical case.
    x_offset = sum(w for w, _ in desktop_sizes[:chosen])
    print(f"Targeting display index {chosen} at size {proj_size}, x_offset={x_offset}")

    window = pygame.Window(
        title=f"Projector preview (display {chosen})",
        size=proj_size,
        position=(x_offset, 0),
        fullscreen_desktop=(len(desktop_sizes) > 1),
    )
    # Re-query actual size in case the OS placed the window on a different
    # monitor than we asked for.
    actual_size = window.size
    print(f"Window opened, actual size = {actual_size}")
    if actual_size != proj_size:
        print("WARNING: window size differs from target — the OS may have placed it on the wrong monitor.")
        proj_size = actual_size

    midi_low = int(os.environ.get("PROJ_MIDI_LOW", MIDI_DEFAULT_LOW))
    midi_high = int(os.environ.get("PROJ_MIDI_HIGH", MIDI_DEFAULT_HIGH))
    print(f"Keyboard range: MIDI {midi_low}..{midi_high}")

    layout = build_keyboard_layout(*CANONICAL_SIZE, midi_low=midi_low, midi_high=midi_high)
    canonical = make_canonical_surface(*CANONICAL_SIZE)
    # C natural minor pitch classes: C D Eb F G Ab Bb
    c_minor_pcs = {0, 2, 3, 5, 7, 8, 10}
    highlights = [
        KeyHighlight(k.midi_note, (255, 255, 255))
        for k in layout
        if (k.midi_note % 12) in c_minor_pcs
    ]
    render_canonical(canonical, highlights, layout)

    homography = make_default_homography(CANONICAL_SIZE, proj_size)
    warped_buffer = pygame.Surface(proj_size)

    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type in (pygame.QUIT, pygame.WINDOWCLOSE):
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        warp_canonical_to_projector(canonical, homography, proj_size, out=warped_buffer)
        screen = window.get_surface()
        screen.fill((0, 0, 0))
        screen.blit(warped_buffer, (0, 0))
        window.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
