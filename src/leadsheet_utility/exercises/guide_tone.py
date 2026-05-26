"""Guide Tone exercise: highlight the voice-led 3rd or 7th in red.

Uses the pre-computed :attr:`LeadSheet.guide_tone_line` — two voice-led
paths (one MIDI note per chord each) built by the harmony analyzer. The
exercise is implemented as a *post-processing overlay* over whatever base
highlights the projection pass produced, so it composes cleanly with the
Free-Mode sub-toggles:

- ``RangeMode`` — when 1-OCT/2-OCT is active, the voice-led MIDI is
  snapped by octaves into the calibrated band so the guide tone is always
  visible inside the practice region.
- ``ChordToneMode`` — the guide tone is a chord tone by construction, so
  ``ONLY`` and ``OVERLAY`` colour it cyan first; this overlay then
  repaints it red.
- Root overlay — guide tones are 3rds/7ths, never the root, so the two
  overlays don't collide.

The canonical renderer fills highlights in list order with last-write
wins, so appending the guide-tone highlight last guarantees the red
beats any base / chord-tone / root colour at the same MIDI.
"""

from __future__ import annotations

from leadsheet_utility.exercises.free import RangeMode
from leadsheet_utility.leadsheet.models import LeadSheet
from leadsheet_utility.projection import KeyHighlight

# Punchy red — high contrast over the white/cyan/blue base layers.
GUIDE_TONE_COLOR: tuple[int, int, int] = (255, 50, 50)
# Orange preview of the *next* chord's guide tone — sits below red so a
# same-MIDI collision still resolves to the active GT.
NEXT_GUIDE_TONE_COLOR: tuple[int, int, int] = (255, 150, 30)


def guide_tone_path_count(lead_sheet: LeadSheet) -> int:
    """Number of voice-led paths the harmony analyzer produced (0, 1, or 2)."""
    return len(lead_sheet.guide_tone_line)


def _snap_into_band(midi: int, band_low: int, octaves: int) -> int:
    """Octave-transpose *midi* so it lands inside the active practice band.

    The band starts at ``band_low`` and spans ``octaves`` octaves plus the
    final octave-of-root repeat (matching the ``free_mode_highlights``
    layout). We bias toward the lowest matching octave inside the band.
    """
    band_high = band_low + 12 * octaves
    while midi < band_low:
        midi += 12
    while midi > band_high:
        midi -= 12
    return midi


def guide_tone_midi(
    lead_sheet: LeadSheet,
    chord_idx: int,
    *,
    path_idx: int = 0,
    octave_offset: int = 1,
    range_mode: RangeMode = RangeMode.FULL,
    band_low: int | None = None,
) -> int | None:
    """Return the voice-led guide-tone MIDI for chord ``chord_idx``, snapped
    into the active practice band when ``range_mode`` is 1-OCT/2-OCT.

    ``octave_offset`` shifts the voice-led note by N octaves before
    band-snapping. In 1/2-OCT mode the snap normalises octaves, so the
    offset only affects the FULL-range projection — handy for nudging the
    line into a comfortable register without recomputing the analysis.

    Returns ``None`` when no guide-tone line exists (empty lead sheet) or
    the requested path/index is out of range.
    """
    line = lead_sheet.guide_tone_line
    if not line:
        return None
    path = line[path_idx % len(line)]
    if chord_idx < 0 or chord_idx >= len(path):
        return None
    midi = path[chord_idx] + 12 * octave_offset
    if range_mode is RangeMode.FULL or band_low is None:
        return midi
    octaves = 1 if range_mode is RangeMode.ONE_OCTAVE else 2
    return _snap_into_band(midi, band_low, octaves)


def apply_guide_tone_highlight(
    highlights: list[KeyHighlight],
    midi_note: int,
    color: tuple[int, int, int] = GUIDE_TONE_COLOR,
    *,
    striped: bool = False,
) -> list[KeyHighlight]:
    """Return ``highlights`` with *midi_note* forced to ``color`` on top.

    Any existing highlight on the same MIDI is dropped before the new one
    is appended, so the renderer paints the guide tone last regardless of
    what the base highlights contained. If the MIDI wasn't in the base
    list at all (e.g. range-limited Free Mode hid it), it is added so the
    player always sees the guide tone.

    Set ``striped=True`` to render the key with diagonal hashes — used for
    a next-GT preview whose pitch class isn't in the current chord-scale,
    so the player sees the target without being invited to play it yet.
    """
    out = [h for h in highlights if h.midi_note != midi_note]
    out.append(KeyHighlight(midi_note=midi_note, color=color, striped=striped))
    return out
