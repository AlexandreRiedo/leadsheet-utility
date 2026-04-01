"""Harmony analysis: chord-scale resolution and annotation."""

from __future__ import annotations

from leadsheet_utility.harmony.constants import (
    CHORD_TONES,
    DOMINANT_SCALES,
    NOTE_TO_PC,
    QUALITY_TO_SCALE,
    SCALES,
)
from leadsheet_utility.leadsheet.models import ChordEvent, LeadSheet

# ---------------------------------------------------------------------------
# Public helper
# ---------------------------------------------------------------------------

def get_scale_midi_notes(
    root_pc: int,
    intervals: tuple[int, ...],
    low: int = 21,
    high: int = 108,
) -> list[int]:
    """Return all MIDI notes in *low*–*high* whose pitch class is in *intervals*."""
    return [m for m in range(low, high + 1) if (m - root_pc) % 12 in intervals]


# ---------------------------------------------------------------------------
# Slash-chord 7sus4 detection
# ---------------------------------------------------------------------------

def _slash_sus4_effective(chord: ChordEvent) -> tuple[int, str] | None:
    """If *chord* is a slash-chord spelling of a 7sus4, return (bass_pc, '7sus4').

    Two patterns are recognised:
    - **Major upper structure a whole step below the bass** (2 semitones):
      e.g. ``Ab:maj/Bb`` → ``Bb7sus4`` (Ab is the b7, C is the 9, Eb is the sus4)
    - **Minor upper structure a perfect fifth above the bass** (7 semitones):
      e.g. ``E:min/A`` → ``A7sus4`` (E is the 5th, G is the b7, B is the 9)

    Returns *None* when the chord has no bass note or does not match either pattern.
    """
    if chord.bass_note is None:
        return None
    root_pc = NOTE_TO_PC[chord.root]
    bass_pc = NOTE_TO_PC[chord.bass_note]
    if not (chord.quality.startswith("7")) and (bass_pc - root_pc) % 12 == 2: # "7" rule to catch that wacky E7/F# in 26-2
        return (bass_pc, "7sus4")
    if chord.quality.startswith("min") and (root_pc - bass_pc) % 12 == 7:
        return (bass_pc, "7sus4")
    return None


# ---------------------------------------------------------------------------
# Extension override (Priority 1)
# ---------------------------------------------------------------------------

def _resolve_extension_scale(quality: str, extensions: list[str]) -> str | None:
    """Return a scale name when parenthesized extensions override the default.
    
    Also overrides the ii chord if it's actually a minmaj7 (Nefertiti).
    Only applies to dominant ``7`` chords. Returns *None* if no override.
    """
    if quality == "minmaj7":
        return "melodic_minor"
    if quality != "7" or not extensions:
        return None
    ext = set(extensions)
    if "#9" in ext:
        return "altered"
    if "#5" in ext:
        return "whole_tone"
    if "#11" in ext or "b5" in ext:
        return "lydian_dominant"
    if "b9" in ext and "13" in ext:
        return "half_whole_dim"
    if "b9" in ext or "b13" in ext:
        return "phrygian_dom"
    if "13" in ext:
        return "mixolydian"
    return None


# ---------------------------------------------------------------------------
# Chain override pre-pass (Rules 3 & 4)
# ---------------------------------------------------------------------------

def _assign_chain_overrides(chords: list[ChordEvent]) -> dict[int, str]:
    """Detect ii-V chains (and I-vi-ii-V turnarounds) and return a dict of
    index → scale_name overrides for minor chords whose diatonic mode differs
    from the Layer 1 default.

    Rule 3: iii-vi-ii-V — roots ascend by P4 (5 semitones); minor chords get
    Phrygian (iii), Aeolian (vi), or Dorian (ii) based on degree in the key.

    Rule 4: I-vi-ii-V — maj chord a minor 3rd above the first minor in the chain
    confirms the key center; same diatonic assignments.
    """
    overrides: dict[int, str] = {}
    n = len(chords)

    for i in range(n - 1):
        curr = chords[i]
        nxt = chords[i + 1]
        curr_root_pc = NOTE_TO_PC[curr.root]
        nxt_root_pc = NOTE_TO_PC[nxt.root]

        # Identify a ii-V pair: min* → 7* with ascending P4 (5 semitones)
        if not (curr.quality.startswith("min") and nxt.quality.startswith("7")):
            continue
        if (nxt_root_pc - curr_root_pc) % 12 != 5:
            continue

        # Key center: P4 above the V root (= the I root)
        key_center_pc = (nxt_root_pc + 5) % 12

        # Walk backwards to extend the chain
        chain = [i, i + 1]
        j = i - 1
        while j >= 0:
            prev_c = chords[j]
            chain_head = chords[chain[0]]
            if ((NOTE_TO_PC[chain_head.root] - NOTE_TO_PC[prev_c.root]) % 12 == 5
                    and (prev_c.quality.startswith("min") or prev_c.quality.startswith("7"))):
                chain.insert(0, j)
                j -= 1
            else:
                break

        # Rule 4: check for a I chord (maj*) just before the chain
        if chain[0] > 0:
            prev_c = chords[chain[0] - 1]
            chain_head = chords[chain[0]]
            if (prev_c.quality.startswith("maj")
                    and (NOTE_TO_PC[prev_c.root] - NOTE_TO_PC[chain_head.root]) % 12 == 3):
                chain.insert(0, chain[0] - 1)

        # Assign diatonic modes to minor (and I maj) chords in the chain.
        # Dominant 7 chords in the chain are handled by Rule 1 in resolve_scale.
        for idx in chain:
            chord = chords[idx]
            degree = (NOTE_TO_PC[chord.root] - key_center_pc) % 12
            if chord.quality.startswith("min"):
                if degree == 2:    # ii → Dorian (same as default; explicit for clarity)
                    overrides[idx] = "dorian"
                elif degree == 4:  # iii → Phrygian (overrides Dorian default)
                    overrides[idx] = "phrygian"
                elif degree == 9:  # vi → Aeolian (overrides Dorian default)
                    overrides[idx] = "aeolian"
            elif chord.quality.startswith("maj"):
                if degree == 0:    # I → Ionian (same as default; explicit for clarity)
                    overrides[idx] = "ionian"

    return overrides


# ---------------------------------------------------------------------------
# Main scale resolver
# ---------------------------------------------------------------------------

def resolve_scale(
    prev_chord: ChordEvent | None,
    current_chord: ChordEvent,
    next_chord: ChordEvent | None,
    chain_override: str | None = None,
) -> str:
    """Return the scale name for *current_chord* given its context.

    Resolution priority:
    1. Extension overrides (b9, #9, #11, …)
    2. Context rules: Rule 1 (V7→minor), Rule 2 (tritone sub),
       Rule 3/4 chain override, Rule 5 (IV in major)
    3. Default quality lookup
    """
    root_pc = NOTE_TO_PC[current_chord.root]

    # Priority 1: extension overrides
    ext_scale = _resolve_extension_scale(current_chord.quality, current_chord.extensions)
    if ext_scale:
        return ext_scale

    # Slash-chord 7sus4 (e.g. Ab:maj/Bb → Bb Mixolydian)
    if _slash_sus4_effective(current_chord):
        return "mixolydian"

    # Priority 2: Rule based overrides (usually based on the before/after chord context)
    # Rule 1: V7 resolving to minor  (e.g. G:7 → C:min7 → phrygian_dom)
    if (current_chord.quality == "7"
            and next_chord is not None
            and (root_pc - NOTE_TO_PC[next_chord.root]) % 12 == 7
            and next_chord.quality.startswith("min")):
        return "phrygian_dom"

    # Rule 2: tritone substitution  (e.g. Db:7 → C:maj7 → lydian_dominant)
    if (current_chord.quality == "7"
            and next_chord is not None
            and (root_pc - NOTE_TO_PC[next_chord.root]) % 12 == 1):
        return "lydian_dominant"

    # Rule 3/4: chain override (iii/vi/ii/V and I-vi-ii-V)
    if chain_override is not None:
        return chain_override

    # Rule 5: IV chord in major context  (e.g. Cmaj7 → Fmaj7 → Fmaj7 gets lydian)
    if (current_chord.quality.startswith("maj")
            and prev_chord is not None
            and prev_chord.quality.startswith("maj")
            and (root_pc - NOTE_TO_PC[prev_chord.root]) % 12 == 5):
        return "lydian"

    # Rule 6: hdim7 not followed by a dominant 7 → locrian_nat9 (not ii°7 in ii°-V context)
    if (current_chord.quality.startswith("hdim")
            and not (next_chord is not None
                 and QUALITY_TO_SCALE.get(next_chord.quality) in DOMINANT_SCALES)):
        return "locrian_nat9"

    # Priority 3: default quality lookup
    return QUALITY_TO_SCALE.get(current_chord.quality, "ionian")


# ---------------------------------------------------------------------------
# Guide tones and guide-tone line
# ---------------------------------------------------------------------------

def _guide_tone_intervals(quality: str) -> tuple[int, ...]:
    """Return the semitone intervals (from root) that are guide tones.

    For most chords: 3rd and 7th. For triads without a 7th: just the 3rd.
    Falls back by prefix family when the exact quality is unknown.
    """
    tones = CHORD_TONES.get(quality)
    if tones is None:
        # Prefix-family fallback
        if quality.startswith("maj"):
            tones = CHORD_TONES["maj7"]
        elif quality.startswith("min"):
            tones = CHORD_TONES["min7"]
        elif quality.startswith("hdim"):
            tones = CHORD_TONES["hdim7"]
        elif quality.startswith("dim"):
            tones = CHORD_TONES["dim7"]
        else:
            tones = CHORD_TONES["7"]

    # 3rd is always index 1; 7th (or 6th sub) is index 3 when present
    intervals: list[int] = [tones[1]]
    if len(tones) > 3:
        intervals.append(tones[3])
    return tuple(intervals)


def _compute_guide_tone_line(chords: list[ChordEvent]) -> list[int]:
    """Return one MIDI note per chord: the voice-led guide tone.

    Starts in the middle register (around C4) and at each step picks whichever
    available guide-tone MIDI note is closest to the previous choice.
    """
    if not chords:
        return []

    line: list[int] = []
    prev_note: int | None = None

    for chord in chords:
        candidates = chord.guide_tones
        if not candidates:
            chosen = prev_note if prev_note is not None else 60
            line.append(chosen)
            prev_note = chosen
            continue

        if prev_note is None:
            # Start in the middle register (MIDI 48–72, roughly C3–C5)
            mid = [n for n in candidates if 48 <= n <= 72]
            pool = mid if mid else candidates
            chosen = pool[len(pool) // 2]
        else:
            chosen = min(candidates, key=lambda n: abs(n - prev_note)) # type: ignore

        line.append(chosen)
        prev_note = chosen

    return line


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def analyze(lead_sheet: LeadSheet) -> LeadSheet:
    """Populate harmony fields on every ChordEvent and compute the guide-tone line.

    Mutates *lead_sheet* in place and returns it.

    Populated per ChordEvent:
    - ``scale_notes``       — MIDI 21-108 for the resolved chord-scale
    - ``chord_tones``       — MIDI 21-108 for R/3/5/7
    - ``guide_tones``       — MIDI 21-108 for the 3rd (and 7th when present)
    - ``available_tensions``— MIDI 21-108 for scale tones that are not chord tones

    Populated on LeadSheet:
    - ``guide_tone_line``   — one MIDI note per chord, voice-led across the form
    """
    chords = lead_sheet.chords
    if not chords:
        return lead_sheet

    chain_overrides = _assign_chain_overrides(chords)

    for i, chord in enumerate(chords):
        root_pc = NOTE_TO_PC[chord.root]
        prev_chord = chords[i - 1] if i > 0 else None
        next_chord = chords[i + 1] if i < len(chords) - 1 else None

        # Slash-chord 7sus4: use bass note as the harmonic root for all MIDI generation
        slash_sus4 = _slash_sus4_effective(chord)
        if slash_sus4:
            effective_root_pc, effective_quality = slash_sus4
        else:
            effective_root_pc, effective_quality = root_pc, chord.quality

        # Resolve scale
        scale_name = resolve_scale(prev_chord, chord, next_chord, chain_overrides.get(i))
        scale_intervals = SCALES[scale_name]
        chord.scale_notes = get_scale_midi_notes(effective_root_pc, scale_intervals)

        # Chord tones
        ct_intervals = CHORD_TONES.get(effective_quality)
        if ct_intervals is None:
            if effective_quality.startswith("maj"):
                ct_intervals = CHORD_TONES["maj7"]
            elif effective_quality.startswith("min"):
                ct_intervals = CHORD_TONES["min7"]
            elif effective_quality.startswith("hdim"):
                ct_intervals = CHORD_TONES["hdim7"]
            elif effective_quality.startswith("dim"):
                ct_intervals = CHORD_TONES["dim7"]
            else:
                ct_intervals = CHORD_TONES["7"]
        chord.chord_tones = get_scale_midi_notes(effective_root_pc, ct_intervals)

        # Guide tones (3rd and 7th)
        gt_intervals = _guide_tone_intervals(effective_quality)
        chord.guide_tones = get_scale_midi_notes(effective_root_pc, gt_intervals)

        # Available tensions: scale notes whose PC is not a chord tone
        ct_pcs = {(effective_root_pc + iv) % 12 for iv in ct_intervals}
        chord.available_tensions = [n for n in chord.scale_notes if n % 12 not in ct_pcs]

    lead_sheet.guide_tone_line = _compute_guide_tone_line(chords)
    return lead_sheet
