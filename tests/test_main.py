"""Tests for the main application module and GUI components."""

from __future__ import annotations

import pygame
import pytest

from leadsheet_utility.gui.hud import EXERCISE_NAMES, _compute_progress
from leadsheet_utility.gui.input import Action, key_to_action
from leadsheet_utility.leadsheet.models import ChordEvent, LeadSheet
from leadsheet_utility.timeline import TimelineState


# ---------------------------------------------------------------------------
# Input handling tests
# ---------------------------------------------------------------------------


class TestKeyToAction:
    def test_quit_q(self):
        assert key_to_action(pygame.K_q) is Action.QUIT

    def test_quit_escape(self):
        assert key_to_action(pygame.K_ESCAPE) is Action.QUIT

    def test_play_pause(self):
        assert key_to_action(pygame.K_SPACE) is Action.TOGGLE_PLAY_PAUSE

    def test_stop(self):
        assert key_to_action(pygame.K_s) is Action.STOP

    def test_open_file(self):
        assert key_to_action(pygame.K_o) is Action.OPEN_FILE

    def test_tempo_up_plus(self):
        assert key_to_action(pygame.K_PLUS) is Action.TEMPO_UP

    def test_tempo_up_equals(self):
        assert key_to_action(pygame.K_EQUALS) is Action.TEMPO_UP

    def test_tempo_down(self):
        assert key_to_action(pygame.K_MINUS) is Action.TEMPO_DOWN

    def test_calibrate(self):
        assert key_to_action(pygame.K_c) is Action.CALIBRATE

    def test_exercises(self):
        assert key_to_action(pygame.K_1) is Action.EXERCISE_1
        assert key_to_action(pygame.K_2) is Action.EXERCISE_2
        assert key_to_action(pygame.K_3) is Action.EXERCISE_3
        assert key_to_action(pygame.K_4) is Action.EXERCISE_4
        assert key_to_action(pygame.K_5) is Action.EXERCISE_5

    def test_unmapped_key_returns_none(self):
        assert key_to_action(pygame.K_z) is Action.NONE

    def test_exercise_names_count(self):
        assert len(EXERCISE_NAMES) == 5


# ---------------------------------------------------------------------------
# Progress computation tests
# ---------------------------------------------------------------------------


def _make_chord(start: float = 0.0, end: float = 4.0) -> ChordEvent:
    return ChordEvent(
        chord_symbol="C:maj7",
        root="C",
        quality="maj7",
        start_beat=start,
        end_beat=end,
        duration_beats=end - start,
    )


def _make_lead_sheet(total_beats: float = 32.0, form_repeats: int = 2) -> LeadSheet:
    return LeadSheet(
        title="Test",
        composer="Test",
        total_beats=total_beats,
        form_repeats=form_repeats,
        chords=[_make_chord(0.0, total_beats)],
    )


class TestComputeProgress:
    def test_start_of_form(self):
        ls = _make_lead_sheet(32.0, 2)
        state = TimelineState(
            current_beat=0.0,
            current_chord=ls.chords[0],
            prev_chord=None,
            form_repeat=0,
        )
        assert _compute_progress(state, ls) == pytest.approx(0.0)

    def test_mid_first_form(self):
        ls = _make_lead_sheet(32.0, 2)
        state = TimelineState(
            current_beat=16.0,
            current_chord=ls.chords[0],
            prev_chord=None,
            form_repeat=0,
        )
        # 16 / 64 = 0.25
        assert _compute_progress(state, ls) == pytest.approx(0.25)

    def test_start_of_second_form(self):
        ls = _make_lead_sheet(32.0, 2)
        state = TimelineState(
            current_beat=0.0,
            current_chord=ls.chords[0],
            prev_chord=None,
            form_repeat=1,
        )
        # 32 / 64 = 0.5
        assert _compute_progress(state, ls) == pytest.approx(0.5)

    def test_near_end(self):
        ls = _make_lead_sheet(32.0, 2)
        state = TimelineState(
            current_beat=31.0,
            current_chord=ls.chords[0],
            prev_chord=None,
            form_repeat=1,
        )
        # 63 / 64
        assert _compute_progress(state, ls) == pytest.approx(63.0 / 64.0)

    def test_single_repeat(self):
        ls = _make_lead_sheet(32.0, 1)
        state = TimelineState(
            current_beat=16.0,
            current_chord=ls.chords[0],
            prev_chord=None,
            form_repeat=0,
        )
        assert _compute_progress(state, ls) == pytest.approx(0.5)
