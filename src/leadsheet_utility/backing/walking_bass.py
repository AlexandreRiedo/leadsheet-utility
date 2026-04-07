"""Algorithmic walking bass line generator.

Produces one quarter-note bass event per beat.  Direction persists for
1–2 bar *phrases* before flipping, creating long ascending or descending
arcs.  Within each bar, beats 2–3 follow the phrase direction (with an
occasional mid-bar arch for variety) and mix chord-tone leaps with
scale-tone steps.

- **Beat 1**: Root (or 5th/3rd for repeated chords).
- **Beats 2–3**: Phrase-direction mix of chord tones and scale tones.
- **Beat 4**: Diatonic approach note targeting the next chord's root.
- **2-beat chords**: Root + approach note.

Range: MIDI 28 (E1) – 48 (C3).
"""

from __future__ import annotations

import random

from leadsheet_utility.backing.events import MidiEvent
from leadsheet_utility.harmony.constants import NOTE_TO_PC
from leadsheet_utility.leadsheet.models import ChordEvent

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASS_LOW = 28  # E1
BASS_HIGH = 48  # C3
BASS_MID = 38  # approximate centre of range
BASS_CHANNEL = 0
BASS_VELOCITY = 100
LEGATO = 0.95  # fraction of a beat the note rings
_ARCH_CHANCE = 0.1  # probability of mid-bar direction reversal on beat 3


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _notes_with_pc(pc: int, low: int = BASS_LOW, high: int = BASS_HIGH) -> list[int]:
    """All MIDI notes with *pc* in [*low*, *high*]."""
    return [n for n in range(low, high + 1) if n % 12 == pc]


def _in_range(notes: list[int]) -> list[int]:
    """Filter MIDI notes to bass range."""
    return [n for n in notes if BASS_LOW <= n <= BASS_HIGH]


def _closest(target: int, candidates: list[int]) -> int:
    """Return the candidate nearest to *target*."""
    return min(candidates, key=lambda n: abs(n - target))


def _effective_root_pc(chord: ChordEvent) -> int:
    """Pitch class used as the bass root (respects slash-chord bass notes)."""
    if chord.bass_note is not None:
        return NOTE_TO_PC[chord.bass_note]
    return NOTE_TO_PC[chord.root]


# ---------------------------------------------------------------------------
# Note pickers
# ---------------------------------------------------------------------------


def _pick_root(
    roots: list[int], prev_note: int | None, ascending: bool = False,
) -> int:
    """Pick a root note in bass range, direction-aware."""
    if prev_note is None:
        return _closest(BASS_MID, roots)
    if ascending:
        preferred = [n for n in roots if n >= prev_note]
    else:
        preferred = [n for n in roots if n <= prev_note]
    pool = preferred if preferred else roots
    return _closest(prev_note, pool)


def _pick_in_direction(
    pool: list[int], reference: int, go_up: bool, avoid: int | None = None,
) -> int:
    """Nearest note above/below *reference* from *pool*, skipping *avoid*."""
    if go_up:
        cands = sorted(n for n in pool if n > reference)
    else:
        cands = sorted((n for n in pool if n < reference), reverse=True)
    if avoid is not None:
        filtered = [n for n in cands if n != avoid]
        if filtered:
            cands = filtered
    if cands:
        return cands[0]
    # Nothing in preferred direction — nearest different note in pool
    fallback = [n for n in pool if n != reference]
    if avoid is not None:
        pref = [n for n in fallback if n != avoid]
        if pref:
            fallback = pref
    return _closest(reference, fallback) if fallback else reference


def _pick_approach(
    target: int, scale_notes_bass: list[int], ascending: bool,
    avoid: int | None = None,
) -> int:
    """Approach note to *target* — diatonic step or a 4th/5th below.

    ~25 % of the time uses a "dominant approach" (P4 or P5 below the
    target), giving the line a stronger pull into the next root.
    """
    # Dominant approach: P4 below (5 semitones) or P5 above (7 semitones)
    if random.random() < 0.25:
        candidates = [target - 5, target + 7]
        valid = [n for n in candidates if BASS_LOW <= n <= BASS_HIGH and n != avoid]
        if valid:
            return random.choice(valid)

    # Diatonic step approach
    pool = [n for n in scale_notes_bass if n != target]
    if avoid is not None:
        preferred = [n for n in pool if n != avoid]
        if preferred:
            pool = preferred

    if ascending:
        below = [n for n in pool if n < target]
        if below:
            return max(below)
    else:
        above = [n for n in pool if n > target]
        if above:
            return min(above)
    if pool:
        return _closest(target, pool)
    if scale_notes_bass:
        return _closest(target, scale_notes_bass)
    return max(BASS_LOW, min(BASS_HIGH, target))


def _deduplicate(
    notes: list[int], sn_bass: list[int], prev_note: int | None,
) -> list[int]:
    """Replace any consecutive repeated note with the nearest different scale tone."""
    result = list(notes)
    prev = prev_note
    for i in range(len(result)):
        if result[i] == prev and sn_bass:
            alternatives = [n for n in sn_bass if n != result[i]]
            if alternatives:
                result[i] = _closest(result[i], alternatives)
        prev = result[i]
    return result


def _at_boundary(note: int) -> int | None:
    """Return forced direction if *note* is near a range boundary, else None."""
    if note >= BASS_HIGH - 3:
        return False  # must descend
    if note <= BASS_LOW + 3:
        return True  # must ascend
    return None


# ---------------------------------------------------------------------------
# Walking bass for one chord
# ---------------------------------------------------------------------------


def _walk_four(
    roots: list[int],
    ct_bass: list[int],
    sn_bass: list[int],
    next_target: int,
    prev_note: int | None,
    ascending: bool,
    use_alternate_root: bool,
    root_pc: int,
) -> list[int]:
    """Generate 4 walking-bass notes for a single bar.

    Beats 2–3 follow the phrase *ascending* direction.  ~10 % of the
    time beat 3 reverses (an "arch"), adding occasional variety without
    chopping the phrase up.
    """
    # -- Beat 1 ---------------------------------------------------------------
    if use_alternate_root:
        non_root = [n for n in ct_bass if n % 12 != root_pc]
        if non_root:
            beat1 = _closest(prev_note or BASS_MID, non_root)
        else:
            beat1 = _pick_root(roots, prev_note, ascending)
    else:
        beat1 = _pick_root(roots, prev_note, ascending)

    # -- Beats 2–3: follow phrase direction, occasional arch ------------------
    dir2 = ascending
    dir3 = (not ascending) if random.random() < _ARCH_CHANCE else ascending

    # Beat 2: ~30 % chance of a chord-tone leap, otherwise scale step
    if random.random() < 0.3 and ct_bass:
        beat2 = _pick_in_direction(ct_bass, beat1, dir2, avoid=beat1)
    else:
        beat2 = _pick_in_direction(sn_bass, beat1, dir2, avoid=beat1)

    # Beat 3
    if random.random() < 0.35 and ct_bass:
        beat3 = _pick_in_direction(ct_bass, beat2, dir3, avoid=beat2)
    else:
        beat3 = _pick_in_direction(sn_bass, beat2, dir3, avoid=beat2)

    # -- Beat 4: approach next root -------------------------------------------
    beat4 = _pick_approach(next_target, sn_bass, ascending, avoid=beat3)

    return _deduplicate([beat1, beat2, beat3, beat4], sn_bass, prev_note)


def _walk_two(
    roots: list[int],
    sn_bass: list[int],
    next_target: int,
    prev_note: int | None,
    ascending: bool,
) -> list[int]:
    """Generate 2 walking-bass notes (root + approach)."""
    beat1 = _pick_root(roots, prev_note, ascending)
    beat2 = _pick_approach(next_target, sn_bass, ascending, avoid=beat1)
    return _deduplicate([beat1, beat2], sn_bass, prev_note)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_walking_bass(
    chords: list[ChordEvent],
    tempo: int,
    form_repeats: int = 1,
    sample_rate: int = 44100,
) -> list[MidiEvent]:
    """Generate a walking bass line for the full form (× *form_repeats*).

    *chords* must already be harmony-analysed (``chord_tones`` and
    ``scale_notes`` populated).

    Returns :class:`MidiEvent` objects on channel 0 (GM Acoustic Bass).
    """
    if not chords:
        return []

    events: list[MidiEvent] = []
    spb = 60.0 / tempo
    total_beats_one_form = chords[-1].end_beat

    # Flatten chords across form repeats, tracking absolute beat offsets.
    expanded: list[tuple[ChordEvent, float, float]] = []
    for rep in range(form_repeats):
        offset = rep * total_beats_one_form
        for c in chords:
            expanded.append((c, c.start_beat + offset, c.end_beat + offset))

    prev_note: int | None = None
    ascending = True  # start ascending — phrases flip after 1-2 bars
    bars_in_phrase = 0
    phrase_length = random.randint(1, 2)

    def _advance_phrase() -> None:
        """Flip direction at phrase boundaries or range limits."""
        nonlocal ascending, bars_in_phrase, phrase_length
        bars_in_phrase += 1
        forced = _at_boundary(prev_note) if prev_note is not None else None
        if forced is not None:
            ascending = forced
            bars_in_phrase = 0
            phrase_length = random.randint(1, 2)
        elif bars_in_phrase >= phrase_length:
            ascending = not ascending
            bars_in_phrase = 0
            phrase_length = random.randint(1, 2)

    for idx, (chord, abs_start, abs_end) in enumerate(expanded):
        num_beats = int(round(abs_end - abs_start))
        if num_beats < 1:
            continue

        # Chord data filtered to bass range
        ct_bass = _in_range(chord.chord_tones)
        sn_bass = _in_range(chord.scale_notes)
        root_pc = _effective_root_pc(chord)
        roots = _notes_with_pc(root_pc)

        if not roots:
            continue  # defensive — every PC exists in 28-48

        # Next chord's root — used for approach notes
        next_chord = expanded[idx + 1][0] if idx + 1 < len(expanded) else chords[0]
        next_root_pc = _effective_root_pc(next_chord)
        next_roots = _notes_with_pc(next_root_pc)
        next_target = _closest(prev_note or BASS_MID, next_roots) if next_roots else BASS_MID

        # --- Generate notes for this chord -----------------------------------
        notes: list[int] = []
        beats_left = num_beats
        bar_idx = 0

        while beats_left >= 4:
            is_last_bar = beats_left < 8
            if is_last_bar:
                bar_target = next_target
            else:
                non_root = [n for n in ct_bass if n % 12 != root_pc]
                bar_target = _closest(prev_note or BASS_MID, non_root) if non_root else next_target

            bar_notes = _walk_four(
                roots, ct_bass, sn_bass, bar_target,
                prev_note, ascending,
                use_alternate_root=(bar_idx > 0),
                root_pc=root_pc,
            )
            notes.extend(bar_notes)
            prev_note = bar_notes[-1]
            _advance_phrase()
            beats_left -= 4
            bar_idx += 1

        # Remaining beats (1, 2, or 3)
        if beats_left == 2:
            pair = _walk_two(roots, sn_bass, next_target, prev_note, ascending)
            notes.extend(pair)
            prev_note = pair[-1]
        elif beats_left == 3:
            beat1 = _pick_root(roots, prev_note, ascending)
            beat2 = _pick_in_direction(sn_bass, beat1, ascending, avoid=beat1)
            beat3 = _pick_approach(next_target, sn_bass, ascending, avoid=beat2)
            trio = _deduplicate([beat1, beat2, beat3], sn_bass, prev_note)
            notes.extend(trio)
            prev_note = trio[-1]
        elif beats_left == 1:
            beat1 = _pick_root(roots, prev_note, ascending)
            notes.append(beat1)
            prev_note = beat1

        # --- Emit MidiEvents -------------------------------------------------
        for i, note in enumerate(notes):
            beat_pos = abs_start + i
            on_sample = int(beat_pos * spb * sample_rate)
            off_sample = int((beat_pos + LEGATO) * spb * sample_rate)
            events.append(
                MidiEvent(on_sample, BASS_CHANNEL, note, BASS_VELOCITY, True),
            )
            events.append(
                MidiEvent(off_sample, BASS_CHANNEL, note, 0, False),
            )

    return events
