"""Keyboard shortcut handling for the main application loop.

Translates pygame key events into application actions.
"""

from __future__ import annotations

from enum import Enum, auto

import pygame


class Action(Enum):
    """Discrete actions that the main loop can react to."""

    NONE = auto()
    QUIT = auto()
    TOGGLE_PLAY_PAUSE = auto()
    STOP = auto()
    OPEN_FILE = auto()
    TEMPO_UP = auto()
    TEMPO_DOWN = auto()
    CALIBRATE = auto()
    EXERCISE_1 = auto()
    EXERCISE_2 = auto()
    EXERCISE_3 = auto()
    EXERCISE_4 = auto()
    EXERCISE_5 = auto()
    TOGGLE_METRONOME = auto()
    TOGGLE_COMPING = auto()


_KEY_MAP: dict[int, Action] = {
    pygame.K_q: Action.QUIT,
    pygame.K_ESCAPE: Action.QUIT,
    pygame.K_SPACE: Action.TOGGLE_PLAY_PAUSE,
    pygame.K_s: Action.STOP,
    pygame.K_o: Action.OPEN_FILE,
    pygame.K_PLUS: Action.TEMPO_UP,
    pygame.K_EQUALS: Action.TEMPO_UP,  # unshifted + on US layout
    pygame.K_KP_PLUS: Action.TEMPO_UP,
    pygame.K_MINUS: Action.TEMPO_DOWN,
    pygame.K_KP_MINUS: Action.TEMPO_DOWN,
    pygame.K_c: Action.CALIBRATE,
    pygame.K_m: Action.TOGGLE_METRONOME,
    pygame.K_g: Action.TOGGLE_COMPING,
    pygame.K_1: Action.EXERCISE_1,
    pygame.K_2: Action.EXERCISE_2,
    pygame.K_3: Action.EXERCISE_3,
    pygame.K_4: Action.EXERCISE_4,
    pygame.K_5: Action.EXERCISE_5,
}


def key_to_action(key: int) -> Action:
    """Map a ``pygame.KEYDOWN`` key code to an :class:`Action`."""
    return _KEY_MAP.get(key, Action.NONE)
