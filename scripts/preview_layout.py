"""Quick visual sanity check of the canonical keyboard layout.

Opens a window with the C-minor scale highlighted in white (C D Eb F G Ab Bb C),
so both white and black keys are exercised. Close the window or press Esc to quit.
"""

import pygame

from leadsheet_utility.projection import (
    KeyHighlight,
    build_keyboard_layout,
    make_canonical_surface,
    render_canonical,
)


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((1920, 200))
    pygame.display.set_caption("Canonical keyboard preview — C minor")

    layout = build_keyboard_layout()
    surf = make_canonical_surface()
    # C natural minor: C D Eb F G Ab Bb C (60, 62, 63, 65, 67, 68, 70, 72)
    # Three of those (Eb, Ab, Bb) are black keys.
    highlights = [
        KeyHighlight(m, (255, 255, 255)) for m in (60, 62, 63, 65, 67, 68, 70, 72)
    ]
    render_canonical(surf, highlights, layout)

    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
        screen.blit(surf, (0, 0))
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
