"""Musical clock that tracks beat position and resolves the current chord.

The timeline is a stateless query object: the main Pygame loop calls
``get_state()`` every frame, which reads elapsed wall-clock time and
computes the current beat.  A :class:`ClockSource` protocol abstracts
the clock for testability.
"""

from __future__ import annotations

import time
from bisect import bisect_right
from enum import Enum, auto
from typing import NamedTuple, Protocol

from leadsheet_utility.leadsheet.models import ChordEvent, LeadSheet


# ---------------------------------------------------------------------------
# Clock abstraction
# ---------------------------------------------------------------------------


class ClockSource(Protocol):
    """Minimal protocol for a monotonic clock returning seconds."""

    def time(self) -> float: ...


class PerfCounterClock:
    """Production clock backed by :func:`time.perf_counter`."""

    def time(self) -> float:
        return time.perf_counter()


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


class PlaybackState(Enum):
    STOPPED = auto()
    PLAYING = auto()
    PAUSED = auto()


class TimelineState(NamedTuple):
    """Snapshot returned by :meth:`Timeline.get_state` each frame."""

    current_beat: float
    """Beat position within the current form (0-indexed, wraps on repeat)."""

    current_chord: ChordEvent
    """The chord active at *current_beat*."""

    prev_chord: ChordEvent | None
    """The preceding chord, or ``None`` at the very start of repeat 0."""

    form_repeat: int
    """0-indexed repeat counter."""



# ---------------------------------------------------------------------------
# Timeline engine
# ---------------------------------------------------------------------------


class Timeline:
    """Musical clock that derives beat position from elapsed wall-clock time.

    Parameters
    ----------
    lead_sheet:
        A parsed (and optionally harmony-analyzed) :class:`LeadSheet`.
    tempo:
        Playback tempo in BPM.
    clock:
        Injectable clock source.  Defaults to :class:`PerfCounterClock`.
    """

    def __init__(
        self,
        lead_sheet: LeadSheet,
        tempo: int,
        clock: ClockSource | None = None,
    ) -> None:
        if not lead_sheet.chords:
            raise ValueError("LeadSheet must contain at least one chord")

        self._lead_sheet = lead_sheet
        self._tempo = tempo
        self._clock: ClockSource = clock or PerfCounterClock()

        self._form_beats: float = lead_sheet.total_beats
        self._form_repeats: int = lead_sheet.form_repeats
        self._total_beats: float = self._form_beats * self._form_repeats

        # Pre-extract start_beat values for binary search.
        self._chord_starts: list[float] = [c.start_beat for c in lead_sheet.chords]

        # Transport state
        self._state: PlaybackState = PlaybackState.STOPPED
        self._play_start_time: float = 0.0
        self._pause_start_time: float = 0.0
        self._accumulated_pause: float = 0.0

    # -- transport controls --------------------------------------------------

    def play(self) -> None:
        """Start or resume playback."""
        if self._state is PlaybackState.STOPPED:
            self._play_start_time = self._clock.time()
            self._accumulated_pause = 0.0
            self._state = PlaybackState.PLAYING
        elif self._state is PlaybackState.PAUSED:
            self._accumulated_pause += self._clock.time() - self._pause_start_time
            self._state = PlaybackState.PLAYING

    def pause(self) -> None:
        """Pause playback (no-op if not playing)."""
        if self._state is PlaybackState.PLAYING:
            self._pause_start_time = self._clock.time()
            self._state = PlaybackState.PAUSED

    def stop(self) -> None:
        """Stop playback and reset to the beginning."""
        self._state = PlaybackState.STOPPED
        self._play_start_time = 0.0
        self._pause_start_time = 0.0
        self._accumulated_pause = 0.0

    # -- query ---------------------------------------------------------------

    def get_state(self) -> TimelineState:
        """Return the current musical position.

        Called once per frame by the main loop; both the projection and
        HUD windows read the same returned value.
        """
        chords = self._lead_sheet.chords

        if self._state is PlaybackState.STOPPED:
            return TimelineState(
                current_beat=0.0,
                current_chord=chords[0],
                prev_chord=None,
                form_repeat=0,
            )

        # Elapsed seconds (paused → frozen at pause instant)
        if self._state is PlaybackState.PAUSED:
            elapsed = (
                self._pause_start_time - self._play_start_time - self._accumulated_pause
            )
        else:
            elapsed = (
                self._clock.time() - self._play_start_time - self._accumulated_pause
            )

        beat_absolute = elapsed * (self._tempo / 60.0)

        # Clamp at the end of all repeats
        if beat_absolute >= self._total_beats:
            beat_absolute = self._total_beats - 1e-9

        form_repeat = int(beat_absolute // self._form_beats)
        beat_in_form = beat_absolute % self._form_beats

        # Binary search for the active chord
        idx = bisect_right(self._chord_starts, beat_in_form) - 1
        idx = max(0, min(idx, len(chords) - 1))

        current_chord = chords[idx]

        # Previous chord
        if idx > 0:
            prev_chord: ChordEvent | None = chords[idx - 1]
        elif form_repeat > 0:
            prev_chord = chords[-1]
        else:
            prev_chord = None

        return TimelineState(
            current_beat=beat_in_form,
            current_chord=current_chord,
            prev_chord=prev_chord,
            form_repeat=form_repeat,
        )

    # -- read-only properties ------------------------------------------------

    @property
    def playback_state(self) -> PlaybackState:
        return self._state

    @property
    def total_beats(self) -> float:
        """Total beats across all form repeats (excluding count-in)."""
        return self._total_beats

    @property
    def total_duration_seconds(self) -> float:
        """Total playback duration in seconds."""
        return self._total_beats / (self._tempo / 60.0)
