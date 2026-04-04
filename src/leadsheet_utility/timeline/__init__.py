"""Timeline module: musical clock synced to audio playback.

Public API::

    from leadsheet_utility.timeline import Timeline, TimelineState, PlaybackState
"""

from leadsheet_utility.timeline.engine import (
    PlaybackState,
    Timeline,
    TimelineState,
)

__all__ = ["PlaybackState", "Timeline", "TimelineState"]
