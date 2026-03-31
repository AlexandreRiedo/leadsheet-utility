---
name: jazz-music-theory
description: Use whenever dealing with anything requiring jazz music theory or harmony. Covers pitch class arithmetic, chord-scale theory, chord tones/guide tones/tensions, context-aware scale resolution (V7 to minor, tritone subs, ii-V), voice-leading, walking bass construction, and swing timing. Essential for the harmony, exercises, and backing modules.
---

# Jazz Music Theory for leadsheet-utility

Reference for the jazz theory concepts used throughout the codebase. Apply this knowledge when implementing or modifying the harmony analyzer, exercise engine, walking bass generator, or any module that reasons about chords, scales, or voice-leading.

## When to Use This Skill

- Implementing or modifying chord-scale mappings in the harmony module
- Writing or debugging walking bass line generation
- Working on exercise logic (guide tones, contour, start/end notes)
- Adding context-aware scale resolution rules
- Computing chord tones, guide tones, or available tensions
- Reasoning about voice-leading across chord changes
- Handling enharmonic equivalence or pitch class arithmetic
- Implementing swing timing or rhythmic patterns

## 1. Pitch Classes and Modulo-12 Arithmetic

All pitch reasoning in this project uses **pitch classes** (integers 0-11) and modulo-12 arithmetic. No music21 or heavy theory libraries.

### Pitch Class Assignment

```
C=0  C#/Db=1  D=2  D#/Eb=3  E=4  F=5  F#/Gb=6  G=7  G#/Ab=8  A=9  A#/Bb=10  B=11
```

Enharmonic equivalents map to the same integer: `F#` and `Gb` are both `6`.

### MIDI Note to Pitch Class

```python
pitch_class = midi_note % 12
# MIDI 60 (middle C) → 60 % 12 = 0 → C
# MIDI 64 (E4)       → 64 % 12 = 4 → E
```

### Interval = Difference Mod 12

```python
interval = (note_pc - root_pc) % 12
# From C (0) to E (4): (4 - 0) % 12 = 4 → major 3rd
# From A (9) to C (0): (0 - 9) % 12 = 3 → minor 3rd
```

### Generating Scale Notes Across the Piano

To find all MIDI notes belonging to a scale, iterate MIDI 21-108 and check membership:

```python
def get_scale_midi_notes(root_pc: int, intervals: tuple[int, ...],
                         low: int = 21, high: int = 108) -> list[int]:
    return [m for m in range(low, high + 1) if (m - root_pc) % 12 in intervals]
```

## 2. Scale Definitions

Each scale is a tuple of semitone intervals from the root. These are the scales used in the project:

| Scale | Intervals | Degrees | Notes (from C) |
|-------|-----------|---------|-----------------|
| Ionian (major) | `(0,2,4,5,7,9,11)` | 1 2 3 4 5 6 7 | C D E F G A B |
| Dorian | `(0,2,3,5,7,9,10)` | 1 2 b3 4 5 6 b7 | C D Eb F G A Bb |
| Phrygian | `(0,1,3,5,7,8,10)` | 1 b2 b3 4 5 b6 b7 | C Db Eb F G Ab Bb |
| Lydian | `(0,2,4,6,7,9,11)` | 1 2 3 #4 5 6 7 | C D E F# G A B |
| Mixolydian | `(0,2,4,5,7,9,10)` | 1 2 3 4 5 6 b7 | C D E F G A Bb |
| Aeolian (natural minor) | `(0,2,3,5,7,8,10)` | 1 2 b3 4 5 b6 b7 | C D Eb F G Ab Bb |
| Locrian | `(0,1,3,5,6,8,10)` | 1 b2 b3 4 b5 b6 b7 | C Db Eb F Gb Ab Bb |
| Melodic minor | `(0,2,3,5,7,9,11)` | 1 2 b3 4 5 6 7 | C D Eb F G A B |
| Phrygian dominant | `(0,1,4,5,7,8,10)` | 1 b2 3 4 5 b6 b7 | C Db E F G Ab Bb |
| Lydian dominant | `(0,2,4,6,7,9,10)` | 1 2 3 #4 5 6 b7 | C D E F# G A Bb |
| Altered | `(0,1,3,4,6,8,10)` | 1 b2 #2 3 #4 b6 b7 | C Db D# E F# Ab Bb |
| Half-whole diminished | `(0,1,3,4,6,7,9,10)` | 1 b2 #2 3 #4 5 6 b7 | C Db D# E F# G A Bb |
| Whole-half diminished | `(0,2,3,5,6,8,9,11)` | 1 2 b3 4 b5 b6 6 7 | C D Eb F Gb Ab A B |
| Whole-tone | `(0,2,4,6,8,10)` | 1 2 3 #4 #5 b7 | C D E F# G# Bb |

**Symmetric scales** (diminished, whole-tone) have 6 or 8 notes instead of 7. The half-whole and whole-half diminished scales are inversions of each other: half-whole starts with a half step (used over dominant chords), whole-half starts with a whole step (used over diminished chords).

### Modes of Melodic Minor

Several important jazz scales are modes of the melodic minor scale:

| Mode | Parent Relationship | Used Over |
|------|-------------------|-----------|
| Melodic minor | 1st mode | minmaj7 |
| Phrygian dominant | 5th mode of harmonic minor | V7 → minor |
| Lydian dominant | 4th mode of melodic minor | Tritone subs, 7(#11) |
| Altered | 7th mode of melodic minor | V7(#9), V7(b9,b13) |
| Locrian natural 2 | 6th mode of melodic minor | hdim7 (alternative to Locrian) |

## 3. Chord-Scale Theory

### Default Quality-to-Scale Mapping

This is Layer 1 of the harmony analyzer — the fallback when no context rule applies:

| Quality | Default Scale | Reasoning |
|---------|--------------|-----------|
| `maj7` | Ionian | Standard major sound |
| `7` | Mixolydian | Plain dominant |
| `min7` | Dorian | Default minor color in jazz (brighter than Aeolian due to natural 6) |
| `hdim7` | Locrian | Half-diminished = m7b5 |
| `dim7` | Whole-half diminished | Symmetric, each chord tone can be a root |
| `maj` | Ionian | Major triad |
| `min` | Dorian | Minor triad |
| `aug` | Whole-tone | Augmented triad is a whole-tone subset |
| `minmaj7` | Melodic minor | The natural 7 over minor = melodic minor |
| `sus4` | Mixolydian | Sus4 functions as a dominant suspension |
| `sus2` | Mixolydian | Same family as sus4 |
| `6` | Ionian | Major with added 6th |
| `min6` | Dorian | Minor with natural 6 = Dorian |
| `9` | Mixolydian | Dominant 9th |
| `min9` | Dorian | Minor 9th |
| `maj9` | Ionian | Major 9th |

### Extension Overrides

When a chord has parenthesized extensions, they override the default scale:

| Quality + Extension | Scale | Why |
|--------------------|-------|-----|
| `7(b9)` | Half-whole diminished | b9 is characteristic of HW dim; also compatible with Phrygian dominant |
| `7(#9)` | Altered | #9 signals altered dominant |
| `7(#5)` | Whole-tone | #5 = augmented dominant, whole-tone contains #5 |
| `7(#11)` | Lydian dominant | #11 is the defining note of Lydian dominant |
| `7(13)` | Mixolydian | Natural 13 confirms standard Mixolydian |
| `7(b13)` | Altered | b13 with dominant = altered sound |
| `7(b9,b13)` | Phrygian dominant | Both b9 and b13 = harmonic minor V |

## 4. Chord Tones, Guide Tones, and Tensions

### Chord Tones

The essential notes that define the chord (root, 3rd, 5th, 7th), expressed as semitone intervals from the root:

| Quality | Root | 3rd | 5th | 7th | Intervals |
|---------|------|-----|-----|-----|-----------|
| `maj7` | 0 | 4 | 7 | 11 | `(0, 4, 7, 11)` |
| `7` | 0 | 4 | 7 | 10 | `(0, 4, 7, 10)` |
| `min7` | 0 | 3 | 7 | 10 | `(0, 3, 7, 10)` |
| `hdim7` | 0 | 3 | 6 | 10 | `(0, 3, 6, 10)` |
| `dim7` | 0 | 3 | 6 | 9 | `(0, 3, 6, 9)` |
| `minmaj7` | 0 | 3 | 7 | 11 | `(0, 3, 7, 11)` |
| `maj` | 0 | 4 | 7 | — | `(0, 4, 7)` |
| `min` | 0 | 3 | 7 | — | `(0, 3, 7)` |
| `aug` | 0 | 4 | 8 | — | `(0, 4, 8)` |
| `6` | 0 | 4 | 7 | 9 | `(0, 4, 7, 9)` (6th replaces 7th) |
| `min6` | 0 | 3 | 7 | 9 | `(0, 3, 7, 9)` |

### Guide Tones

The **3rd and 7th** of each chord. These two notes:
- Define the chord quality (major vs minor vs dominant)
- Move by small intervals (half step or whole step) across chord changes
- Are the primary target notes in the Guide Tone exercise

```python
def get_guide_tones(root_pc: int, quality: str) -> tuple[int, int]:
    """Return (3rd_pc, 7th_pc) for the chord."""
    third = (root_pc + CHORD_TONES[quality][1]) % 12  # 3 or 4 semitones
    seventh = (root_pc + CHORD_TONES[quality][3]) % 12  # 9, 10, or 11 semitones
    return (third, seventh)
```

For triads without a 7th (`maj`, `min`, `aug`), the guide tone is just the 3rd.

### Available Tensions

Scale tones that are NOT chord tones. These add color without clashing:

| Quality | Tensions | Intervals |
|---------|----------|-----------|
| `maj7` (Ionian) | 9, 13 | 2, 9 (avoid 4/11 — half step above 3rd) |
| `7` (Mixolydian) | 9, 13 | 2, 9 |
| `min7` (Dorian) | 9, 11, 13 | 2, 5, 9 |
| `hdim7` (Locrian) | 11, b13 | 5, 8 (avoid b2/b9 — half step above root) |

**Avoid notes**: Scale tones a half step above a chord tone create dissonance when sustained. In Ionian, the 4th (F over Cmaj7) is an avoid note because it's a half step above the 3rd (E). The projection doesn't distinguish avoid notes — all scale tones are shown — but this matters for the walking bass and exercise target note selection.

## 5. Context-Aware Resolution (Layer 2)

These rules override the default scale when the harmonic context is clear. Each rule examines `(prev_chord, current_chord, next_chord)`.

### Rule 1: V7 Resolving to Minor

**Pattern**: `X:7` → `Y:min7` (or `Y:minmaj7`) where X is a 5th above Y.

**Scale**: Phrygian dominant (5th mode of harmonic minor)

**Why**: The b9 and b13 of Phrygian dominant are the characteristic tones of a V7 in minor. Mixolydian (the default) has a natural 9 and 13, which sound like a major-key dominant.

```
G:7 → C:min7   →  G Phrygian dominant (G Ab B C D Eb F)
                   = C harmonic minor starting on G
```

**Detection**: `next_chord.root` is a 5th below (7 semitones) `current_chord.root`, AND `next_chord.quality` is `min7` or `minmaj7` or `min`.

### Rule 2: Tritone Substitution

**Pattern**: `X:7` → `Y` where X is a half step above Y (root moves down by 1 semitone).

**Scale**: Lydian dominant

**Why**: A tritone sub replaces a V7 with a dominant chord a tritone away. Lydian dominant has a #11, which is the enharmonic equivalent of the original dominant's root — it connects the two keys smoothly.

```
Db:7 → C:maj7  →  Db Lydian dominant (Db Eb F G Ab Bb Cb)
                   The G (= #11 of Db) is the 5th of C, linking the resolution
```

**Detection**: `(current_root - next_root) % 12 == 1` AND `current_quality == "7"`.

### Rule 3: ii-V Pair

**Pattern**: `X:min7` → `Y:7` where Y root is a 4th above X (or equivalently, a 5th below).

**Scale**: Both chords share the key center of the V7's resolution target.

**Why**: In a ii-V-I, the ii and V belong to the same key. The min7 is Dorian (which is the default anyway), but recognizing the pair helps when the V7 needs a non-default scale (e.g., if it resolves to minor).

```
D:min7 → G:7 → C:maj7   →  All in C major
A:min7 → D:7 → G:min7   →  D:7 gets Phrygian dominant (ii-V in G minor)
```

**Detection**: `(next_root - current_root) % 12 == 5` AND `current_quality == "min7"` AND `next_quality == "7"`.

### Rule 4: Diminished Passing Chord

**Pattern**: `X:dim7` appears between two chords whose roots are a whole step apart.

**Scale**: Whole-half diminished (the default for dim7 anyway)

**Why**: Diminished chords often function as chromatic connectors. The whole-half diminished scale works because dim7 is symmetric — every note is 3 semitones apart, so any of the 4 chord tones can be heard as the root.

### Rule 5: IV Chord in Major Context

**Pattern**: `X:maj7` where the previous chord or key context suggests X is the IV degree.

**Scale**: Lydian (instead of default Ionian)

**Why**: The #4 of Lydian avoids the clash between the natural 4 and the major 3rd of the chord. When a maj7 chord is clearly functioning as a IV chord, Lydian is the idiomatic jazz choice.

**Detection**: If `prev_chord` root is a 5th below (i.e., current root minus prev root = 5 semitones), and both are maj7, the current chord is likely IV.

### Resolution Priority

When multiple rules could apply, use this priority:
1. Extension overrides (explicit `b9`, `#9`, etc.) — always win
2. Context rules (V→minor, tritone sub, ii-V)
3. Default quality lookup

## 6. Voice-Leading Principles

### Guide-Tone Voice-Leading

The harmony analyzer pre-computes a **guide-tone line** across the entire form. At each chord transition, pick the guide tone (3rd or 7th) that is closest in pitch to the previous guide tone.

```
Dm7    → G7     → Cmaj7
3rd=F    3rd=B     3rd=E
7th=C    7th=F     7th=B

Guide-tone line: F → F → E  (7th of G7 = F, same as 3rd of Dm7; then 3rd of Cmaj7 = E, half step down)
```

Key voice-leading connections in jazz:
- **3rd of ii → 7th of V** (same note or half step): e.g., Dm7 3rd (F) = G7 7th (F)
- **7th of V → 3rd of I** (half step down): e.g., G7 7th (F) → Cmaj7 3rd (E)
- **7th of ii → 3rd of V** (half step down): e.g., Dm7 7th (C) → G7 3rd (B)

This is what makes ii-V-I progressions sound smooth — the guide tones descend by half step.

### Implementation

```python
def compute_guide_tone_line(chords: list[ChordEvent]) -> list[int]:
    """Return one MIDI note per chord: the voice-led guide tone."""
    line = []
    prev_note = None
    for chord in chords:
        third_pc, seventh_pc = get_guide_tones(chord.root_pc, chord.quality)
        # Find closest octave placement of each candidate to prev_note
        candidates = find_nearest_midi(third_pc, prev_note) + find_nearest_midi(seventh_pc, prev_note)
        if prev_note is None:
            chosen = pick_from_middle_register(candidates)  # start in a comfortable range
        else:
            chosen = min(candidates, key=lambda n: abs(n - prev_note))
        line.append(chosen)
        prev_note = chosen
    return line
```

## 7. Walking Bass Construction

### Principles

A walking bass line plays one note per beat (quarter notes) and outlines the harmony while creating melodic motion.

**Strong beats (1 and 3)**: Chord tones — root, 3rd, 5th, 7th. Beat 1 strongly prefers the root.

**Weak beats (2 and 4)**: Scale tones, chromatic approach notes, or passing tones connecting the strong beats.

**Beat 4 → Beat 1 (next chord)**: The most important connection. Beat 4 should approach the root of the next chord by:
- Half step above or below (chromatic approach) — strongest
- Whole step (diatonic approach)
- The 5th of the next chord (dominant approach)

### Range

Bass range: **MIDI 28 (E1) to MIDI 48 (C3)**. This matches the range of an upright bass. Notes should generally move by step or small skip (2nds or 3rds), with occasional larger leaps (4ths, 5ths) for variety.

### Step-by-Step Algorithm

For each bar with chord `X`:

1. **Beat 1**: Root of X (in bass range). If repeating the same chord as previous bar, may use 5th or 3rd for variety.
2. **Beat 2**: Scale tone between beat 1 and beat 3 (stepwise motion).
3. **Beat 3**: 5th of X, or another chord tone (3rd, 7th). Should differ from beat 1.
4. **Beat 4**: Approach note targeting beat 1 of the next bar's chord — chromatic half step above/below the next root.

### Direction and Contour

- Alternate ascending and descending motion across bars to stay within range.
- If approaching the range ceiling (MIDI 48), walk downward. If approaching the floor (MIDI 28), walk upward.
- Avoid staying on the same note for consecutive beats (walking = motion).

### Two-Beat Chords

When a chord lasts only 2 beats:
- Beat 1: Root
- Beat 2: Approach note to the next chord's root

## 8. Swing Timing

### What Swing Is

In swing feel, each beat is divided into two unequal parts instead of two equal eighth notes. The first eighth is longer, the second is shorter — like a triplet with the first two notes tied:

```
Straight: |-----|-----|  (50/50 split)
Swing:    |-------|---|  (67/33 split, triplet feel)
```

### Swing Ratio

The `swing_ratio` parameter controls the split:
- `0.50` = straight (no swing) — each eighth note is exactly 50% of a beat
- `0.67` = triplet swing (default) — the downbeat eighth is 67% of a beat, the upbeat is 33%
- `0.75` = hard swing — exaggerated shuffle feel

### Application

Swing is applied during **event generation**, not during playback. The timeline stays in straight time (chord changes happen on beat boundaries). Only the backing track events (bass notes, drum hits on the "and" of beats) get their timing shifted:

```python
def apply_swing(beat_position: float, swing_ratio: float = 0.67) -> float:
    """Shift offbeat eighth notes forward in time."""
    beat_fraction = beat_position % 1.0
    if abs(beat_fraction - 0.5) < 0.01:  # this is an offbeat ("and")
        beat_int = int(beat_position)
        return beat_int + swing_ratio  # shift the "and" later
    return beat_position
```

### What Gets Swung

- **Ride cymbal** "skip" notes (the "and" of 2 and 4)
- **Walking bass** — if any notes fall on offbeats (rare in standard walking, but possible in rhythmic variations)
- **Ghost snare** notes if placed on offbeats

### What Does NOT Get Swung

- Quarter-note hits (beats 1, 2, 3, 4) — these stay on the grid
- Hi-hat pedal on 2 and 4 — these are on the beat
- Chord changes — always on beat boundaries
- The timeline clock — stays in straight time for chord lookup

## 9. Chord Symbol Parsing

### Grammar

```
SYMBOL = ROOT ":" QUALITY [EXTENSION] [BASS]
ROOT = C | C# | Db | D | D# | Eb | E | F | F# | Gb | G | G# | Ab | A | A# | Bb | B
QUALITY = maj7 | min7 | 7 | hdim7 | dim7 | maj | min | aug | sus4 | sus2
        | min9 | maj9 | 9 | min6 | 6 | minmaj7
EXTENSION = "(" ALTERATION {"," ALTERATION} ")"
ALTERATION = b5 | #5 | b9 | #9 | #11 | b13 | 13
BASS = "/" ROOT
```

### Parsing Strategy

1. Split on `:` to separate root from the rest
2. Extract parenthesized extensions with regex: `\(([^)]+)\)`
3. Extract slash bass note: `/[A-G][#b]?$`
4. What remains is the quality string

### Enharmonic Normalization

The parser must handle both sharp and flat spellings. Both `F#:min7` and `Gb:min7` refer to the same pitch class (6). Normalize to a canonical spelling when computing pitch classes, but preserve the original spelling for display.

## 10. Common Jazz Progressions (Reference)

These patterns appear frequently in the lead sheet corpus and inform context-aware resolution:

| Progression | Example | Key Insight |
|-------------|---------|-------------|
| ii-V-I major | Dm7 → G7 → Cmaj7 | G7 gets Mixolydian |
| ii-V-i minor | Dm7b5 → G7 → Cm7 | G7 gets Phrygian dominant |
| I-vi-ii-V | Cmaj7 → Am7 → Dm7 → G7 | All in C major |
| Tritone sub | Dm7 → Db7 → Cmaj7 | Db7 gets Lydian dominant |
| Backdoor ii-V | Fm7 → Bb7 → Cmaj7 | bVII7 resolving up to I |
| Rhythm changes bridge | D7 → G7 → C7 → F7 | Circle of dominants, each Mixolydian |
| Minor blues | Cm7 → Fm7 → G7 → Cm7 | G7 gets Phrygian dominant |
| Diminished passing | Cmaj7 → C#dim7 → Dm7 | C#dim7 is chromatic connector |

## Related Skills

- [python-design-patterns](../python-design-patterns/SKILL.md) — Architecture and separation of concerns for the harmony module
- [python-testing-patterns](../python-testing-patterns/SKILL.md) — TDD approach for harmony and walking bass correctness
