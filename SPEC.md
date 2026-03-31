# SPEC.md — leadsheet-utility: Augmented Piano for Jazz Improvisation

## 1. Project Overview

**leadsheet-utility** is a Python application that augments a physical piano with projected light to help users learn and practice jazz improvisation. A projector mounted above the keyboard highlights scale tones, guide tones, and exercise-specific notes in real time, synchronized with an auto-generated backing track (walking bass + drums). The system reads a lead sheet file describing chord changes and timing, analyzes the harmony to compute chord-scales, and drives both the projection and the accompaniment from a shared musical timeline.

### Core Value Proposition

Jazz improvisation is hard because the harmonic context changes rapidly and the player must simultaneously think about scales, voice-leading, phrasing, and rhythmic placement. leadsheet-utility offloads the "which notes are correct right now?" question to the projector, freeing the player to focus on *creative* melodic decisions. On top of that, five structured exercises use color-coded projection to train specific improvisation skills drawn from established jazz pedagogy.

---

## 2. Concrete User Flow

### First-Time Setup (once)

1. The user physically mounts the projector above the piano (e.g., on a mic stand, tripod, or shelf). It points down at the keys. **The projector stays fixed from this point on.**
2. The user downloads a GM SoundFont file (e.g., FluidR3_GM.sf2) and places it somewhere on disk.
3. The user connects the projector as a secondary display and launches the app: `python -m leadsheet_utility`.
4. On first launch, no `~/.leadsheet-utility/config.json` exists. The app prompts for the SoundFont path via a file dialog.
5. No `~/.leadsheet-utility/calibration.json` exists either, so the app automatically enters **calibration mode** on the projector display. Four bright markers appear on a black background.
6. On the primary display (laptop/monitor), the app shows instructions: "Drag each marker to the corresponding corner of your piano keyboard."
7. The user drags the 4 markers (via mouse on the projector window) until they sit on the physical corners of the keyboard. They press Enter to confirm.
8. The app computes the homography, draws a preview of all 88 key outlines on the piano. If alignment looks good, the user presses Enter again. If not, they re-drag and retry.
9. Config and calibration are saved to `~/.leadsheet-utility/`. **These steps never need to be repeated** unless the projector is physically moved or the SoundFont changes.
10. The app transitions to the main screen.

### Normal Usage (every session)

1. User launches the app. It loads config + calibration from `~/.leadsheet-utility/`.
2. The projector display goes fullscreen black (no light on the piano yet). The primary display shows the HUD.
3. User presses `O` to open a `.tsv` lead sheet file (or the app loads the last-used file).
4. The HUD shows: title, chord chart, tempo, exercise selection.
5. User selects an exercise with keys `1`–`5` (default: Free Mode) and adjusts tempo with `+`/`-`.
6. User presses `Space` to play:
   - The backing track is pre-rendered via FluidSynth (~0.5–1s for a 32-bar form). A brief "Rendering..." indicator shows on the HUD.
   - Once ready, `pygame.mixer` starts playing the audio buffer.
   - The projector lights up the appropriate keys on the piano, updating in sync with the audio.
   - The HUD shows the current chord, bar number, and a progress bar.
7. The user improvises on the piano, guided by the colored lights.
8. When the form ends (or loops), the user presses `Space` to pause or `S` to stop.
9. The user can switch exercises, change the tune, or adjust tempo at any time while stopped. Changing tempo triggers a re-render on next play.
10. Press `Q` to quit.

### Re-Calibration (rare)

If the projector or piano gets bumped, the user presses `C` from the main screen to re-enter calibration mode. The existing marker positions are loaded as a starting point so they only need small adjustments.

---

## 3. High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Pygame Application (single process)        │
│                                                         │
│  ┌────────────────────┐    ┌──────────────────────────┐ │
│  │  Control UI        │    │  Projection Window       │ │
│  │  (Pygame overlay   │    │  (fullscreen on          │ │
│  │   or keyboard      │    │   projector display)     │ │
│  │   shortcuts)       │    │                          │ │
│  └────────┬───────────┘    └──────────▲───────────────┘ │
│           │ user actions              │ key highlights  │
│           ▼                           │                 │
│  ┌────────────────────┐    ┌──────────┴───────────────┐ │
│  │  Timeline Engine   │───▶│  Exercise Engine         │ │
│  │  (beat clock,      │    │  (chord + beat →         │ │
│  │   current chord)   │    │   colored keys)          │ │
│  └────────┬───────────┘    └─────────────────────────┘  │
│           │ beat position                               │
│           ▼                                             │
│  ┌────────────────────┐                                 │
│  │  Audio Playback    │    ← pre-rendered audio buffer  │
│  │  (pygame.mixer)    │       generated before playback │
│  └────────────────────┘                                 │
└─────────────────────────────────────────────────────────┘
            ▲
            │ parsed at startup
┌───────────┴──────────┐     ┌─────────────────────────┐
│  Lead Sheet Parser   │     │  Harmony Analyzer       │
│  (.tsv → ChordEvent) │────▶│  (chord → scale, guide  │
└──────────────────────┘     │   tones, chord tones)   │
                             └─────────────────────────┘
            ▲
            │
┌───────────┴──────────┐
│  Backing Track       │
│  Pre-Renderer        │  ← runs once before playback
│  (walking bass +     │     FluidSynth offline → NumPy buffer
│   drums → audio)     │
└──────────────────────┘
```

### Key Architectural Decisions

1. **Single framework (Pygame)** — no PyQt6. The GUI needs are minimal (load file, pick exercise, set tempo, play/stop). Pygame handles both the projection rendering and the control UI. One event loop, zero thread conflicts, minimal latency.

2. **Pre-rendered backing track** — the chord chart and tempo are fully known before playback, so the walking bass and drum audio are synthesized into a NumPy array *before* pressing play using FluidSynth in offline mode (no audio driver attached). Playback uses `pygame.mixer`. This eliminates all real-time MIDI timing concerns. The only real-time task during playback is updating the projection, which is just drawing colored rectangles — trivially fast for Pygame.

3. **Pure Python harmony** — no music21. Chord-to-scale mapping is a dictionary of interval patterns plus basic pitch math (~100 lines). Instant import, zero heavy dependencies.

4. **FluidSynth for audio synthesis** — a GM SoundFont provides high-quality, multi-sampled, velocity-layered instruments out of the box. No need to source or record audio samples. Adding new instruments (piano comping, etc.) is just more MidiEvents on a new channel. FluidSynth runs in offline mode during pre-rendering (no audio driver), keeping the architecture simple.

### Module Summary

| Module | Responsibility | Key Libraries |
|---|---|---|
| `leadsheet` | Parse MIR-style `.tsv` chord files into IR | — (pure Python) |
| `harmony` | Chord symbol → scale pitches, chord tones, guide tones | — (pure Python, lookup tables) |
| `timeline` | Musical clock: track beat position, current chord | `time` (perf_counter) |
| `projection` | Render canonical keyboard image, warp with homography, display | `pygame-ce`, `opencv-python` |
| `backing` | Generate walking bass + drum MIDI events, render to audio via FluidSynth | `pyfluidsynth`, `numpy` |
| `exercises` | 5 exercise modes: compute which keys to highlight per beat | — (pure Python) |
| `calibration` | 4-point marker drag UI + `cv2.getPerspectiveTransform()` | `opencv-python`, `pygame-ce` |
| `gui` | HUD window: chord display, exercise selection, transport | `pygame-ce` |

### Application States

The app is a simple state machine with three modes:

```
                  ┌──────────────┐
   first launch   │  CALIBRATION │  user presses C
   (no config) ──▶│  MODE        │◀── from main screen
                  └──────┬───────┘
                         │ user confirms alignment
                         ▼
                  ┌──────────────┐
                  │  MAIN SCREEN │  load file, select exercise,
   app launch ──▶ │  (STOPPED)   │  adjust tempo
   (config exists)└──────┬───────┘
                         │ Space
                         ▼
                  ┌──────────────┐
                  │  PLAYING     │  backing track plays,
                  │              │  projection active
                  └──────────────┘
```

- **Calibration mode**: projection window shows markers on black; HUD window shows instructions. Only entered on first launch or when user presses `C`.
- **Main screen (stopped)**: projection window is black (no light); HUD window shows file info, exercise selection, tempo. The user loads files and configures here.
- **Playing**: backing track audio plays via `pygame.mixer`; projection window shows colored key highlights updated every frame; HUD window shows current chord and progress. Both windows are updated in the same loop iteration from the same timeline state.

---

## 4. Lead Sheet Format (Input)

The system reads a **MIR-style TSV chord annotation file** (tab-separated values). This is a standard format used in music information retrieval research. The file extension is `.tsv` (or `.lab` / `.txt`).

### Format Specification

Each line contains three tab-separated fields:

```
START_BEAT\tEND_BEAT\tCHORD_SYMBOL
```

- `START_BEAT` — float, the beat position where this chord begins (0-indexed).
- `END_BEAT` — float, the beat position where this chord ends.
- `CHORD_SYMBOL` — in `ROOT:QUALITY` notation, with optional extensions in parentheses.

Beats are absolute positions within the form. In 4/4 time, beat 0.0–4.0 is bar 1, beat 4.0–8.0 is bar 2, etc. The bar number can be derived as `floor(start_beat / beats_per_bar) + 1`.

**Example** — "All The Things You Are":

```tsv
0.000	4.000	F:min7
4.000	8.000	Bb:min7
8.000	12.000	Eb:7
12.000	16.000	Ab:maj7
16.000	20.000	Db:maj7
20.000	24.000	G:7
24.000	32.000	C:maj7
32.000	36.000	C:min7
36.000	40.000	F:min7
40.000	44.000	Bb:7
44.000	48.000	Eb:maj7
48.000	52.000	Ab:maj7
52.000	54.000	A:hdim7
54.000	56.000	D:7
56.000	62.000	G:maj7
62.000	64.000	E:7(#9)
64.000	68.000	A:min7
68.000	72.000	D:7
72.000	80.000	G:maj7
80.000	84.000	F#:hdim7
84.000	88.000	B:7
88.000	92.000	E:maj7
92.000	96.000	C:7(#5)
96.000	100.000	F:min7
100.000	104.000	Bb:min7
104.000	108.000	Eb:7
108.000	112.000	Ab:maj7
112.000	116.000	Db:maj7
116.000	120.000	Gb:7(13)
120.000	124.000	C:min7
124.000	128.000	B:dim7
128.000	132.000	Bb:min7
132.000	136.000	Eb:7
136.000	140.000	Ab:maj7
140.000	142.000	G:hdim7
142.000	144.000	C:7(b9)
```

### Chord Symbol Grammar

```
ROOT      = C | C# | Db | D | D# | Eb | E | F | F# | Gb | G | G# | Ab | A | A# | Bb | B
QUALITY   = maj7 | min7 | 7 | hdim7 | dim7 | maj | min | aug | sus4 | sus2
            | min9 | maj9 | 9 | min6 | 6 | minmaj7
EXTENSION = ( ALTERATION )    ← optional, parenthesized
ALTERATION = b5 | #5 | b9 | #9 | #11 | b13 | 13 | ...
BASS       = / ROOT           ← optional slash bass note
SYMBOL     = ROOT : QUALITY [EXTENSION] [BASS]
```

Key quality mappings:
- `min7` → minor 7th (Dorian default)
- `maj7` → major 7th (Ionian default)
- `7` → dominant 7th (Mixolydian default)
- `hdim7` → half-diminished / m7b5 (Locrian default)
- `dim7` → fully diminished
- `7(b9)` → dominant with flat 9 (half-whole diminished or Phrygian dominant)
- `7(#9)` → dominant with sharp 9 (altered or half-whole diminished)
- `7(#5)` → augmented dominant (whole-tone or Lydian dominant)
- `7(13)` → dominant with natural 13 (Mixolydian / Lydian dominant)

The parser splits on `:` to separate root from quality, then extracts any parenthesized extensions.

### Metadata Sidecar (Optional)

Since the TSV format contains only chord data, metadata is stored in a companion `.meta.json` file with the same base name:

```json
{
    "title": "All The Things You Are",
    "composer": "Jerome Kern",
    "key": "Ab",
    "time_signature": [4, 4],
    "default_tempo": 140,
    "form_repeats": 3
}
```

If no `.meta.json` exists, the system uses defaults (4/4, tempo 120, unknown title) and the user sets metadata in the GUI.

### Internal Representation (IR)

```python
@dataclass
class ChordEvent:
    chord_symbol: str        # raw from file, e.g. "F:min7"
    root: str                # "F"
    quality: str             # "min7"
    extensions: list[str]    # e.g. ["b9"], ["#9"], [] if none
    bass_note: str | None    # slash chord bass, or None
    start_beat: float        # absolute beat position (0-indexed)
    end_beat: float          # absolute beat position where chord ends
    duration_beats: float    # end_beat - start_beat
    bar_number: int          # derived: floor(start_beat / beats_per_bar) + 1
    beat_in_bar: float       # derived: start_beat % beats_per_bar
    scale_notes: list[int]   # MIDI note numbers for the chord-scale (full 88-key range, MIDI 21–108)
    chord_tones: list[int]   # MIDI note numbers of chord tones (R, 3, 5, 7)
    guide_tones: list[int]   # typically 3rd and 7th

@dataclass
class LeadSheet:
    title: str
    composer: str
    key: str
    time_signature: tuple[int, int]   # (4, 4)
    default_tempo: int
    form_repeats: int
    chords: list[ChordEvent]
    total_beats: float               # end_beat of the last chord
    total_bars: int                  # derived from total_beats / beats_per_bar
```

---

## 5. Harmony Analyzer

### Chord-Scale Mapping

The analyzer determines the chord-scale for each chord using two layers:

1. **Default lookup** — a dictionary mapping chord quality (+ extensions) to a default scale. This handles the common case and is always available as a fallback.
2. **Context-aware resolution** — examines the surrounding chords (previous and next) to refine the scale choice. This produces more musically accurate results, especially for dominant chords whose function depends heavily on what they resolve to.

The context-aware logic will be implemented incrementally. The default lookup is the MVP; context rules are added on top as the musical logic is developed.

#### Layer 1: Default Lookup

Each scale is stored as a tuple of semitone intervals from the root:

```python
# Example: scale definitions as semitone intervals from root
SCALES = {
    "ionian":          (0, 2, 4, 5, 7, 9, 11),
    "dorian":          (0, 2, 3, 5, 7, 9, 10),
    "mixolydian":      (0, 2, 4, 5, 7, 9, 10),
    "phrygian_dom":    (0, 1, 4, 5, 7, 8, 10),
    "locrian":         (0, 1, 3, 5, 6, 8, 10),
    "altered":         (0, 1, 3, 4, 6, 8, 10),
    "half_whole_dim":  (0, 1, 3, 4, 6, 7, 9, 10),
    "whole_half_dim":  (0, 2, 3, 5, 6, 8, 9, 11),
    "whole_tone":      (0, 2, 4, 6, 8, 10),
    "melodic_minor":   (0, 2, 3, 5, 7, 9, 11),
    "lydian_dominant": (0, 2, 4, 6, 7, 9, 10),
    "lydian":          (0, 2, 4, 6, 7, 9, 11),
}

# Root name → pitch class (C=0, Db=1, D=2, ...)
NOTE_TO_PC = {"C": 0, "Db": 1, "D": 2, "Eb": 3, "E": 4, "F": 5,
              "F#": 6, "Gb": 6, "G": 7, "Ab": 8, "A": 9, "Bb": 10, "B": 11}

# Quality → default scale name (fallback when context is unavailable)
QUALITY_TO_SCALE = {
    "maj7": "ionian",
    "7":    "mixolydian",
    "min7": "dorian",
    "hdim7": "locrian",
    "dim7": "whole_half_dim",
    # ... etc
}

def get_scale_midi_notes(root: str, quality: str, extensions: list[str],
                         low: int = 21, high: int = 108) -> list[int]:
    """Return all MIDI notes of the chord-scale across the full 88-key piano range."""
    pc = NOTE_TO_PC[root]
    scale_name = resolve_scale(quality, extensions)  # handles extension overrides
    intervals = SCALES[scale_name]
    notes = []
    for midi in range(low, high + 1):
        if (midi - pc) % 12 in intervals:
            notes.append(midi)
    return notes
```

Chord quality → default scale mapping:

| Quality | Default Scale | Notes |
|---|---|---|
| `maj7` | Ionian (or Lydian if IV chord) | Context-dependent; default to Ionian |
| `7` | Mixolydian | Plain dominant |
| `min7` | Dorian | Default minor color in jazz |
| `hdim7` | Locrian | Half-diminished = m7b5 |
| `dim7` | Diminished (whole-half) | Symmetric |
| `maj` | Ionian | Triad, treat as major |
| `min` | Dorian | Minor triad |
| `aug` | Whole-tone | |
| `7` + `(b9)` | Half-whole diminished | Or Phrygian dominant |
| `7` + `(#9)` | Altered (melodic minor VII) | Or half-whole diminished |
| `7` + `(#5)` | Whole-tone | Or Lydian dominant |
| `7` + `(#11)` | Lydian dominant | |
| `7` + `(13)` | Mixolydian | Natural 13 confirms Mixolydian |
| `7` + `(b13)` | Altered or Mixolydian b13 | |
| `minmaj7` | Melodic minor | |
| `sus4` | Mixolydian sus | |
| `6` | Major pentatonic / Ionian | |
| `min6` | Dorian | |

#### Layer 2: Context-Aware Resolution

The default lookup is often insufficient because a chord's function — and therefore its correct scale — depends on where it resolves. The analyzer examines the previous and/or next chord to override the default. The `resolve_scale()` function receives the full context: `(prev_chord, current_chord, next_chord)`.

Examples of context-dependent rules:

- **Dominant → minor resolution** (e.g., `G:7 → C:min7` or `G:7 → C:minmaj7`): the dominant is functioning as a V7 in a minor key. The scale should be **Phrygian dominant** (5th mode of harmonic minor), not plain Mixolydian. Phrygian dominant has a b9 and b13, which are the characteristic tensions of a V7 resolving to minor.
- **Dominant → major resolution** (e.g., `G:7 → C:maj7`): standard V7→I in major. **Mixolydian** is correct (the default).
- **Secondary dominants**: if a `7` chord resolves down a fifth to another chord, it's likely a secondary dominant and its scale depends on the target chord's quality.
- **Tritone substitutions**: a `7` chord resolving down a half step (e.g., `Db:7 → C:maj7`) is likely a tritone sub. **Lydian dominant** is the typical scale choice.
- **ii-V relationships**: if `X:min7` is followed by `Y:7` a fourth above, they form a ii-V pair and should share a key center — the min7 is Dorian and the dominant inherits the same key.
- **Diminished passing chords**: `B:dim7` between `C:min7` and `Bb:min7` functions as a chromatic passing chord; whole-half diminished is correct.

These rules will be implemented incrementally as the musical logic is developed. The architecture supports this cleanly: `resolve_scale()` is a single function that takes context and can grow in sophistication without changing any other module. The default lookup always serves as the fallback when no context rule matches.

### Outputs per Chord

For each `ChordEvent`, the analyzer populates:
- `scale_notes` — all 7 (or 8) pitches of the chord-scale, across the full 88-key piano range (MIDI 21–108, A0–C8).
- `chord_tones` — R, 3, 5, 7.
- `guide_tones` — 3rd and 7th (used by the guide-tone exercise).
- `available_tensions` — 9, 11, 13 where applicable.

### Voice-Leading for Guide Tones

The analyzer also pre-computes a **guide-tone line** across the entire form: for each chord transition, pick the guide tone (3rd or 7th) that is closest by half-step to the previous guide tone. Store this as a list parallel to `chords`.

---

## 6. Exercises (Projection Modes)

All exercises share a common interface:

```python
class Exercise(ABC):
    name: str
    description: str
    category: int  # 1-6 from the pedagogical classification

    @abstractmethod
    def get_highlights(
        self,
        chord: ChordEvent,
        beat_position: float,
        form_position: float,   # 0.0–1.0 across the whole form
        prev_chord: ChordEvent | None,
    ) -> list[KeyHighlight]:
        """Return which keys to highlight and in what color."""
        ...

@dataclass
class KeyHighlight:
    midi_note: int
    color: tuple[int, int, int]   # RGB
```

### 5.1 Free Mode (Mode Libre) — Category 1

- **Projection**: All chord-scale notes in **white**.
- **Purpose**: Introductory mode; the player sees which notes are "safe" and improvises freely.
- **Logic**: Simply return all `scale_notes` in white.

### 5.2 Guide Tone Game — Category 2

- **Projection**: Chord-scale in **white** + one guide tone in **red**.
- **Purpose**: Train the player to build lines that clearly outline the harmony by targeting the 3rd or 7th.
- **Logic**: Use the pre-computed voice-led guide-tone line. Highlight the chosen guide tone in red. The player should gravitate toward this note in their improvisation.

### 5.3 Contour Game — Category 6

- **Projection**: A *window* of ~5–7 consecutive chord-scale notes in **white**, moving up or down the keyboard over time.
- **Purpose**: Force the player to think about melodic direction at a macro level (across the whole form), not just note-by-note.
- **Logic**:
  - Pre-generate a contour curve (e.g., a slow sine wave, or a random walk) that maps `form_position → register (MIDI note center)`.
  - At each moment, highlight only the chord-scale notes within ±3 semitones of the contour center.
  - The illuminated window drifts left/right on the keyboard, guiding the player's register.

### 5.4 Flow Game (Jeu du Flux) — Category 6

- **Projection**: Chord-scale in **white** when "open", **nothing** when "closed".
- **Purpose**: Train rhythmic phrasing by forcing silence. Continuous eighth-note flow is interrupted by blackout windows, teaching the player to phrase with rests.
- **Logic**:
  - Pre-generate an on/off pattern (e.g., 2 bars on, 1 bar off, or a random pattern with configurable density).
  - When "on": highlight all scale notes in white.
  - When "off": highlight nothing (blackout). The player must stop playing.
  - Configurable parameter: `flow_density` (0.0–1.0), controlling the ratio of on-time vs off-time.

### 5.5 Start & End Note Game — Category 6

- **Projection**: Chord-scale in **white** + one note in **green** (start) + one note in **red** (end/target).
- **Purpose**: Give the player an entry point and a target, helping those who freeze up when improvising. Also trains the concept of "target notes."
- **Logic**:
  - For each chord (or every 2 chords), randomly pick a start note and an end note from the chord tones or scale tones.
  - The end note of one phrase should ideally become (or be near) the start note of the next, to encourage continuity.
  - Display start note in green, end note in red.

### Color Palette Summary

| Element | Color | RGB | Projector behavior |
|---|---|---|---|
| Chord-scale notes (base) | White | `(255, 255, 255)` | Bright white light on key |
| Guide tone / target / end note | Red | `(255, 50, 50)` | Red light on key |
| Start note | Green | `(50, 255, 50)` | Green light on key |
| All other keys | Black | `(0, 0, 0)` | **No light** (invisible) |
| Blackout (flow "off" phase) | Black | `(0, 0, 0)` | **No light** on any key |

The black background is critical: the projector emits no light for black pixels, so only highlighted keys are visible on the physical piano. This is what makes the augmentation work — colored light appears to "paint" the real piano keys.

Colors must be configurable in `~/.leadsheet-utility/config.json`.

---

## 7. Projection Engine

### Rendering Principle

The projector is mounted above the piano, pointing down at the keys. The Pygame window runs fullscreen on the projector display with a **pure black background**. Black = no light = the projector emits nothing. Only the keys that should be highlighted receive color:

- **Chord-scale notes** → white light (the "safe" notes to play)
- **Exercise-specific notes** → colored light (red, green — see exercise definitions)
- **All other keys** → black (no light, invisible on the physical piano)

The player sees colored light appearing and disappearing on their real piano keys. There is no rendered "keyboard image" — only colored rectangles on a black canvas, positioned to land precisely on the physical keys.

### Piano Range

Full **88-key piano**: MIDI 21 (A0) to MIDI 108 (C8). The projection covers all 88 keys. The calibration maps the projector's pixel space onto the physical key positions.

### Key Geometry

Each piano key has a known shape and relative position. The system stores a model of the 88-key layout in a **canonical (undistorted) coordinate space**:

```python
@dataclass
class KeyRect:
    midi_note: int
    is_black: bool
    x: int          # pixel x position in canonical image
    y: int          # pixel y position in canonical image
    width: int      # pixel width in canonical image
    height: int     # pixel height in canonical image
```

The canonical image is a fixed-size buffer (e.g., 1920×200 pixels) containing a flat, top-down, undistorted keyboard layout. White keys are full-height rectangles. Black keys are narrower, shorter, and offset between white keys, following standard piano geometry. This canonical image never changes — it's computed once at startup from known piano proportions.

### Rendering Pipeline: Render Flat, Then Warp

Rather than transforming individual key polygons, the system renders into the canonical flat image and then applies **`cv2.warpPerspective()`** to the entire frame in one shot. This is simpler and handles all perspective distortion automatically:

```python
import cv2
import numpy as np
import pygame

def render_frame(
    canonical_size: tuple[int, int],   # e.g. (1920, 200)
    projector_size: tuple[int, int],   # e.g. (1920, 1080)
    highlights: list[KeyHighlight],
    key_rects: list[KeyRect],
    H: np.ndarray,                     # 3x3 homography matrix
    screen: pygame.Surface,
):
    # 1. Render into canonical (flat, undistorted) image
    canonical = np.zeros((*canonical_size[::-1], 3), dtype=np.uint8)  # black
    for kh in highlights:
        kr = key_rects[kh.midi_note - 21]
        cv2.rectangle(canonical, (kr.x, kr.y), (kr.x + kr.width, kr.y + kr.height), kh.color, -1)

    # 2. Warp the entire image to projector space in one call
    warped = cv2.warpPerspective(canonical, H, projector_size, borderValue=(0, 0, 0))

    # 3. Convert to Pygame surface and blit to the projection window
    #    cv2 uses BGR, pygame uses RGB — swap channels
    warped_rgb = cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)
    surface = pygame.surfarray.make_surface(warped_rgb.swapaxes(0, 1))
    screen.blit(surface, (0, 0))
```

This approach has several advantages: keys stay as simple axis-aligned rectangles in the canonical space (easy to reason about), the homography handles all perspective correction, and `cv2.warpPerspective()` is GPU-accelerated on most systems.

### Calibration with OpenCV

Calibration is a **mode within the main app**, not a separate script. The app enters calibration mode in two cases:

- **First launch**: no `~/.leadsheet-utility/calibration.json` found → calibration mode starts automatically.
- **User presses `C`** from the main screen → re-enters calibration mode, with the existing marker positions loaded as starting points for fine adjustment.

The calibration computes the 3×3 homography matrix that maps from the canonical keyboard image to the projector's output, correcting for the projector's angle and position relative to the piano.

#### Calibration Mode Flow

1. **The system displays 4 bright colored marker circles** on the projector, initially placed at the corners of the screen. Each marker corresponds to a known corner in the canonical keyboard image:
   - Top-left of leftmost white key (A0)
   - Top-right of rightmost white key (C8)
   - Bottom-left of leftmost white key (A0)
   - Bottom-right of rightmost white key (C8)

2. **The user drags each marker with the mouse** until it sits exactly on the corresponding corner of the physical piano keyboard. Since the projector is live, the user sees the markers moving on the real piano surface. Arrow keys can nudge the selected marker for pixel-perfect placement. Tab cycles between markers.

3. **The system computes the homography** with a single OpenCV call:

```python
import cv2
import numpy as np

# Source: corners in the canonical image (known, fixed)
src = np.array([
    [0, 0],                             # top-left of A0
    [CANONICAL_WIDTH, 0],               # top-right of C8
    [0, CANONICAL_HEIGHT],              # bottom-left of A0
    [CANONICAL_WIDTH, CANONICAL_HEIGHT] # bottom-right of C8
], dtype=np.float32)

# Destination: where the user placed the markers (in projector pixel coords)
dst = np.array([
    [marker_1_x, marker_1_y],
    [marker_2_x, marker_2_y],
    [marker_3_x, marker_3_y],
    [marker_4_x, marker_4_y],
], dtype=np.float32)

H = cv2.getPerspectiveTransform(src, dst)
```

4. **Preview**: the system renders all 88 key outlines through the homography so the user can visually verify alignment. If it looks off, they re-drag markers and recompute.

5. **Saved to** `~/.leadsheet-utility/calibration.json`:

```json
{
    "projector_resolution": [1920, 1080],
    "canonical_size": [1920, 200],
    "marker_positions_px": [[45, 62], [1875, 58], [42, 890], [1878, 895]],
    "homography_matrix": [[1.02, -0.01, 45.0], [0.003, 0.98, 62.0], [0.0, 0.0, 1.0]]
}
```

Calibration only needs to be done **once per physical setup** — the projector is fixed and static, so the homography doesn't change between sessions. On subsequent launches, the app loads the saved matrix and goes straight to the main screen (see Section 2: Concrete User Flow). If the projector or piano gets bumped, the user presses `C` to re-calibrate; the saved marker positions are loaded as starting points so only small adjustments are needed.

### Refresh Rate

Target **60 FPS**. The per-frame work is: draw ~7–15 filled rectangles into a small canonical image, one `cv2.warpPerspective()` call, and a surface blit. Well within budget.

### Multi-Display Architecture

The app needs two simultaneous outputs on two different displays: the projection (fullscreen on the projector) and the HUD (windowed on the primary monitor). This requires two windows.

**Problem**: standard `pygame` (2.6.x) supports only a single display surface per process. Calling `pygame.display.set_mode()` a second time destroys the first surface. It cannot drive two windows simultaneously.

**Solution**: use **`pygame-ce`** (pygame Community Edition) instead of standard `pygame`. Since version 2.5.2, pygame-ce exposes a proper `pygame.Window` class that supports multiple windows in a single process, each with its own renderer. This is a drop-in replacement: `pip install pygame-ce` instead of `pip install pygame`. The API is identical for everything else.

```python
import pygame

pygame.init()

# Determine display layout
desktop_sizes = pygame.display.get_desktop_sizes()
primary_w, primary_h = desktop_sizes[0]

# Window 1: Projection (fullscreen on the projector / secondary display)
# Position it on the secondary monitor by offsetting past the primary
proj_window = pygame.Window(
    title="Projection",
    size=desktop_sizes[1] if len(desktop_sizes) > 1 else (1920, 1080),
    position=(primary_w, 0),  # top-left of secondary display
    fullscreen_desktop=True,
)
proj_surface = proj_window.get_surface()

# Window 2: HUD (windowed on the primary monitor)
hud_window = pygame.Window(
    title="leadsheet-utility",
    size=(800, 500),
    position=pygame.WINDOWPOS_CENTERED,  # centered on primary
)
hud_surface = hud_window.get_surface()
```

Both windows share the same event loop and the same `pygame.mixer` audio output. The timeline reads the audio playback position, and both windows use it in the same frame — no synchronization needed. The main loop looks like:

```python
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.WINDOWCLOSE:
            running = False
        handle_input(event)  # keyboard shortcuts

    state = timeline.get_state()  # one read, used by both windows

    # Update projection window
    proj_surface.fill((0, 0, 0))
    render_projection(proj_surface, state, highlights, H)
    proj_window.flip()

    # Update HUD window
    hud_surface.fill((30, 30, 30))
    render_hud(hud_surface, state, lead_sheet, current_exercise)
    hud_window.flip()

    clock.tick(60)
```

**Note on multi-monitor positioning**: the `Window.position` property uses absolute screen coordinates where (0, 0) is the top-left of the primary display. To place a window on the secondary monitor, offset the x-coordinate by the primary display's width. Use `pygame.display.get_desktop_sizes()` to query monitor dimensions at startup.

**No shared clock problem**: both windows are rendered in the same thread, in the same frame, reading the same `timeline.get_state()` value. They are inherently synchronized.

---

## 8. Backing Track Engine

### Goal

Generate a backing track (walking bass + swing drums) that sounds like a jazz rhythm section, similar to iReal Pro. The entire track is **pre-rendered to an audio buffer before playback starts** using FluidSynth in offline mode, so there are zero real-time timing concerns. The result is high-quality, multi-sampled audio from a GM SoundFont.

### Architecture: Generate Events → Offline FluidSynth Render → Play

The pipeline has three stages:

1. **Event generation** (pure Python): the walking bass and drum algorithms produce a list of MIDI-like events: `(time_samples, channel, note, velocity, type)`.
2. **Offline rendering** (FluidSynth): a `fluidsynth.Synth` object — not connected to any audio driver — processes the events and outputs raw audio samples into a NumPy buffer via `synth.get_samples()`. No `.mid` files, no `.wav` files, no disk I/O. Everything stays in memory.
3. **Playback** (`pygame.mixer`): the buffer is loaded as a `pygame.mixer.Sound` and played. The timeline reads the playback position from the mixer channel to keep projection in sync.

```python
import fluidsynth
import numpy as np

@dataclass
class MidiEvent:
    time_samples: int       # absolute sample offset from start
    channel: int            # 0 = bass, 9 = drums (GM)
    note: int               # MIDI note number
    velocity: int           # 0–127
    is_note_on: bool        # True = noteon, False = noteoff

def render_backing_track(
    events: list[MidiEvent],
    sf_path: str,
    total_beats: float,
    tempo: int,
    sample_rate: int = 44100,
) -> np.ndarray:
    """Render MIDI events to audio using FluidSynth in offline mode."""
    synth = fluidsynth.Synth(samplerate=float(sample_rate))
    sfid = synth.sfload(sf_path)
    synth.program_select(0, sfid, 0, 33)    # channel 0 → Acoustic Bass (GM #34)
    synth.program_select(9, sfid, 128, 0)   # channel 9 → GM drums

    total_samples = int((total_beats * 60.0 / tempo) * sample_rate)
    buffer = np.zeros(total_samples * 2, dtype=np.int16)  # stereo interleaved
    cursor = 0

    sorted_events = sorted(events, key=lambda e: e.time_samples)

    for event in sorted_events:
        # Advance the synth's internal clock to this event's timestamp
        gap = event.time_samples - cursor
        if gap > 0:
            chunk = synth.get_samples(gap)  # returns (gap * 2,) int16 array
            buffer[cursor * 2 : (cursor + gap) * 2] = chunk
            cursor += gap

        # Trigger the MIDI event
        if event.is_note_on:
            synth.noteon(event.channel, event.note, event.velocity)
        else:
            synth.noteoff(event.channel, event.note)

    # Render the tail (reverb/release decay after last event)
    remaining = total_samples - cursor
    if remaining > 0:
        buffer[cursor * 2 :] = synth.get_samples(remaining)

    synth.delete()
    return buffer
```

Key points:
- **No audio driver** is attached to the `Synth`. It runs purely as an offline sample generator.
- **`synth.get_samples(n)`** advances the synth's internal clock by `n` samples and returns the rendered audio. Between calls, `noteon()` / `noteoff()` modify the synth's state.
- The result is a stereo int16 NumPy array, ready to be loaded into `pygame.mixer.Sound`.
- For a 32-bar form at 140 BPM, this takes <1 second on modern hardware.

### SoundFont

The system requires a General MIDI SoundFont file (`.sf2`). Recommended options:

- **FluidR3_GM.sf2** (~150 MB) — good quality, widely available, free.
- **MuseScore_General.sf2** (~200 MB) — higher quality, CC0 license.
- Any GM-compatible SoundFont the user prefers.

The SoundFont path is configured in `~/.leadsheet-utility/config.json`. On first launch, if no SoundFont is found, the app prompts the user to provide one. Stretch goal: auto-download a free SoundFont.

```json
{
    "soundfont_path": "/path/to/FluidR3_GM.sf2"
}
```

### Walking Bass Generator

Algorithmic walking bass: for each bar, generate a 4-note (quarter-note) bass line as `MidiEvent` objects on channel 0.

Algorithm outline:
1. Beat 1: root of the chord (or a chord tone).
2. Beat 3: 5th or another chord tone.
3. Beats 2 & 4: scale tones or chromatic approach notes targeting the next strong-beat note.
4. Beat 4 of the bar should approach beat 1 of the *next* bar's chord by half step or whole step.
5. Bass range: MIDI 28 (E1) to MIDI 48 (C3).
6. Each note is a quarter-note duration (legato, slight overlap is fine for acoustic bass).

### Drum Pattern Generator

Simple swing ride pattern per bar, as `MidiEvent` objects on channel 9 (GM drums).

GM drum note mapping:
- Ride cymbal: MIDI 51 (Ride Cymbal 1)
- Hi-hat pedal: MIDI 44 (Pedal Hi-Hat)
- Kick: MIDI 36 (Bass Drum 1)
- Optional ghost snare: MIDI 38 (Acoustic Snare) at low velocity

Pattern per bar:
- Ride: quarter notes on 1, 2, 3, 4 + swing eighth "skip" on the and of 2 and 4.
- Hi-hat pedal: beats 2 and 4.
- Kick: beat 1 (light, velocity ~50).
- Minor humanization: velocity ±10, timing offset ±5ms (in samples: ±220 at 44.1kHz).

### Swing Timing

Swing is applied during event generation, not during rendering. For each beat, the "and" (offbeat eighth note) is shifted later:

```python
def swing_offset(beat_fraction: float, swing_ratio: float = 0.67) -> float:
    """Shift the 'and' of each beat. swing_ratio=0.67 is triplet swing."""
    if beat_fraction % 1.0 == 0.5:  # offbeat
        return (swing_ratio - 0.5)  # shift forward
    return 0.0
```

Default swing ratio: 0.67 (triplet feel). Configurable from 0.5 (straight) to 0.75 (hard swing).

### Tempo Change Handling

If the user changes tempo, the backing track is re-rendered. For a 32-bar form this takes <1 second. Re-rendering happens in a background thread; playback restarts once the new buffer is ready.

---

## 9. Timeline Engine

The timeline tracks the current musical position and determines which chord is active. It derives its position from the audio playback clock, ensuring perfect sync.

### Responsibilities

- Derive current beat position from `pygame.mixer` playback position (sample offset → beat number).
- Look up the current `ChordEvent` from the lead sheet based on beat position.
- Provide a `get_state()` method returning `(current_beat, current_chord, prev_chord, form_repeat)` — polled each frame by the projection engine.
- Handle form looping: when the form ends, wrap the beat position back to 0 and increment the repeat counter.
- Support **play**, **stop**, **pause**.

### Implementation

- **No dedicated thread**. The timeline is a stateless query object: the main Pygame loop calls `timeline.get_state()` every frame, which reads the audio channel's playback position and computes the current beat.
- Beat position = `(playback_sample_offset / sample_rate) * (tempo / 60.0)`.
- This guarantees the projection is always in sync with the audio — they share the same clock source.
- For looping: the pre-rendered audio buffer includes `form_repeats` copies of the form. The timeline computes `beat_in_form = current_beat % total_beats_per_form`.

### Swing

Swing is handled in the backing track pre-renderer (offsets the "and" of each beat). The timeline itself stays in straight time — it only needs to know "which beat are we on?" to look up the current chord, and chord changes happen on beat boundaries.

---

## 10. GUI

### Framework: pygame-ce (same as projection)

The HUD runs in a second `pygame.Window` on the **primary display**, while the projection runs fullscreen on the **secondary display** (projector). Both windows are managed in the same event loop (see Section 7: Multi-Display Architecture). No threading, no synchronization — both read the same `timeline.get_state()` each frame.

### Approach: Keyboard Shortcuts + Minimal HUD

For MVP, the control interface is primarily keyboard-driven with a simple heads-up display rendered in Pygame:

```
┌──────────────────────────────────────────────┐
│  leadsheet-utility                                      │
│                                              │
│  ♫ All The Things You Are — Jerome Kern      │
│  Key: Ab    Time: 4/4    Tempo: 140 BPM      │
│                                              │
│  Current: Bb:min7  (bar 2/36)  [Form 1/3]   │
│  Next:    Eb:7                               │
│                                              │
│  Exercise: [1] Free  [2] Guide  [3] Contour  │
│            [4] Flow  [5] Start/End            │
│  Active: ▶ Guide Tone                        │
│                                              │
│  [SPACE] Play/Pause   [S] Stop   [L] Loop    │
│  [+/-] Tempo          [O] Open file          │
│  [C] Calibrate        [Q] Quit               │
│                                              │
│  ████████████░░░░░░░░░░░░░░░  progress bar   │
└──────────────────────────────────────────────┘
```

### Keyboard Shortcuts

| Key | Action |
|---|---|
| `Space` | Play / Pause |
| `S` | Stop (reset to beginning) |
| `L` | Toggle loop mode |
| `O` | Open file dialog (use `tkinter.filedialog` — lightweight, no full Tk needed) |
| `1`–`5` | Select exercise mode |
| `+` / `-` | Tempo up/down by 5 BPM |
| `C` | Enter calibration mode |
| `Q` / `Esc` | Quit |

### File Open Dialog

Use `tkinter.filedialog.askopenfilename()` for the native file picker — it's in Python's standard library, requires no extra dependency, and doesn't conflict with Pygame. Import `tkinter` only when the user presses `O`.

### Settings Persistence

All settings stored in a single `~/.leadsheet-utility/config.json` (on Windows: `%USERPROFILE%\.leadsheet-utility\config.json`). Use `pathlib.Path.home() / ".leadsheet-utility"` in code for cross-platform compatibility.
- SoundFont path (`.sf2` file for FluidSynth)
- Projector display index
- Piano range (MIDI low/high)
- Calibration data (marker positions + homography matrix)
- Last used directory and last opened file
- Exercise parameters (flow density, contour shape)
- Colors (customizable RGB values)
- Swing ratio: 50% (straight) to 75% (hard swing)
- Default tempo

---

## 11. Project Structure

```
leadsheet-utility/
├── CLAUDE.md              # Instructions for Claude Code
├── SPEC.md                # This file
├── README.md
├── pyproject.toml         # Project metadata, dependencies (use Poetry or pip)
├── requirements.txt
│
├── src/
│   └── leadsheet_utility/
│       ├── __init__.py
│       ├── main.py                 # Entry point
│       │
│       ├── leadsheet/
│       │   ├── __init__.py
│       │   ├── parser.py           # Parse MIR-style .tsv chord annotation files
│       │   ├── models.py           # ChordEvent, LeadSheet dataclasses
│       │   └── normalizer.py       # Chord symbol parsing (ROOT:QUALITY(ext) → fields)
│       │
│       ├── harmony/
│       │   ├── __init__.py
│       │   ├── analyzer.py         # Chord → scale, chord tones, guide tones
│       │   ├── scales.py           # Scale definitions and mappings
│       │   └── voiceleading.py     # Guide-tone line computation
│       │
│       ├── timeline/
│       │   ├── __init__.py
│       │   └── engine.py           # Musical clock, event emitter
│       │
│       ├── projection/
│       │   ├── __init__.py
│       │   ├── renderer.py         # Render canonical image + cv2.warpPerspective per frame
│       │   ├── calibration.py      # 4-point drag UI + cv2.getPerspectiveTransform
│       │   └── keyboard.py         # 88-key geometry model (KeyRect layout in canonical space)
│       │
│       ├── exercises/
│       │   ├── __init__.py
│       │   ├── base.py             # Exercise ABC + KeyHighlight
│       │   ├── free_mode.py
│       │   ├── guide_tone.py
│       │   ├── contour.py
│       │   ├── flow.py
│       │   └── start_end.py
│       │
│       ├── backing/
│       │   ├── __init__.py
│       │   ├── bass.py             # Walking bass line generator → MidiEvent list
│       │   ├── drums.py            # Drum pattern generator → MidiEvent list
│       │   ├── renderer.py         # Offline FluidSynth rendering: events → NumPy buffer
│       │   └── events.py           # MidiEvent dataclass + timing utilities
│       │
│       ├── gui/
│       │   ├── __init__.py
│       │   ├── hud.py              # Heads-up display rendering (Pygame)
│       │   └── input.py            # Keyboard shortcut handling
│       │
│       └── config/
│           ├── __init__.py
│           ├── settings.py         # App-wide settings (dataclass + JSON persistence)
│           └── defaults.py         # Default values
│
├── data/
│   ├── soundfonts/                 # User places .sf2 SoundFont files here
│   │   └── .gitkeep
│   └── leadsheets/                 # Example .tsv chord annotation files
│       ├── all_the_things.tsv
│       ├── all_the_things.meta.json
│       ├── blues_in_f.tsv
│       ├── blues_in_f.meta.json
│       ├── rhythm_changes_bb.tsv
│       ├── rhythm_changes_bb.meta.json
│       ├── ii_v_i_all_keys.tsv
│       └── ii_v_i_all_keys.meta.json
│
└── tests/
    ├── test_parser.py
    ├── test_harmony.py
    ├── test_bass.py
    ├── test_drums.py
    ├── test_renderer.py          # FluidSynth offline rendering integration test
    ├── test_exercises.py
    └── test_timeline.py
```

---

## 12. Dependencies & Platform Notes

### Target Platform: Windows 10/11

The primary development and deployment platform is **Windows**. The developer has a USB audio interface with studio speakers.

### Python Dependencies

```
# Core
python = ">=3.11"
pygame-ce = ">=2.5.2"          # Community Edition — required for multi-window support
numpy = ">=1.26"
opencv-python = ">=4.9"
pyfluidsynth = ">=1.3"

# Dev / test
pytest = ">=8.0"
```

**Important**: `pygame-ce` and standard `pygame` cannot be installed simultaneously — they conflict. If standard `pygame` is already installed, uninstall it first: `pip uninstall pygame && pip install pygame-ce`. The import name is still `import pygame`; only the pip package name differs.

### System-Level Dependencies

#### FluidSynth C Library (Windows)

`pyfluidsynth` is a thin ctypes wrapper around `libfluidsynth.dll`. The DLL must be installed and findable at runtime.

**Installation options (choose one):**

1. **Chocolatey** (recommended):
   ```
   choco install fluidsynth
   ```
   This installs the binaries and adds them to PATH automatically.

2. **Manual install from GitHub releases**:
   - Download the latest precompiled Windows x64 zip from [FluidSynth releases](https://github.com/FluidSynth/fluidsynth/releases) (e.g., `fluidsynth-v2.4.x-win10-x64.zip`).
   - Extract the zip somewhere permanent (e.g., `C:\tools\fluidsynth\`).
   - Add the `bin\` directory to the system PATH so that `libfluidsynth-3.dll` is findable:
     ```
     setx PATH "%PATH%;C:\tools\fluidsynth\bin"
     ```
   - Restart the terminal. Verify: `fluidsynth --version`.

3. **vcpkg**: `vcpkg install fluidsynth:x64-windows`

**Verification**: after installation, this should work in Python:
```python
import fluidsynth
fs = fluidsynth.Synth()
print("FluidSynth OK")
fs.delete()
```

If `pyfluidsynth` can't find the DLL, it will raise an `OSError`. The most common fix is ensuring the directory containing `libfluidsynth-3.dll` (or `libfluidsynth.dll`) is on the system PATH.

#### General MIDI SoundFont

A `.sf2` SoundFont file is required. Recommended free options:
- **FluidR3_GM.sf2** (~150 MB) — widely used, good quality.
- **MuseScore_General.sf2** (~200 MB) — higher quality, CC0 license.
- **GeneralUser GS** (~30 MB) — smaller, decent quality.

The SoundFont path is configured in `~/.leadsheet-utility/config.json` (on Windows: `%USERPROFILE%\.leadsheet-utility\config.json`). On first launch, the app prompts the user to locate their SoundFont file.

### Audio Output & ASIO

**ASIO is not involved in the MVP architecture.** Here's why:

- FluidSynth renders audio **offline** (no audio driver attached). It produces raw samples in memory via `synth.get_samples()`. FluidSynth's audio driver settings (WASAPI, DirectSound, PortAudio/ASIO) are irrelevant because no driver is created.
- Audio playback goes through **`pygame.mixer`**, which uses **SDL2** under the hood. On Windows, SDL2 outputs audio via **WASAPI** (or DirectSound as fallback). SDL2 does **not** support ASIO directly.
- To route audio to a USB audio interface, the user simply sets the interface as the **default Windows audio output device** in Windows Sound Settings. `pygame.mixer` will then output to it automatically via WASAPI.
- WASAPI in shared mode adds ~10–30ms of latency. For a pre-rendered backing track, this is imperceptible — the latency only affects when playback *starts*, not the timing between notes (which was baked in during pre-rendering).

**If lower-latency real-time playback is needed later** (stretch goal): FluidSynth can be connected directly to a PortAudio driver, which supports ASIO. This would bypass `pygame.mixer` entirely and give <5ms latency. But for the offline pre-render architecture, this is unnecessary.

### Windows-Specific Config Path

On Windows, `~/.leadsheet-utility/` maps to `%USERPROFILE%\.leadsheet-utility\` (e.g., `C:\Users\Alexandre\.leadsheet-utility\`). The app should use `pathlib.Path.home() / ".leadsheet-utility"` for cross-platform compatibility.

### Other Platforms (secondary)

The app should work on macOS and Linux with minimal changes, but these are not the primary target:
- macOS: `brew install fluidsynth`
- Linux: `apt install fluidsynth` / `pacman -S fluidsynth`

Optional (stretch goals):
- `mido` + `python-rtmidi` — for MIDI file export or live MIDI output to a DAW

---

## 13. Data Flow (Runtime)

```
1. User loads a .tsv chord file (+ optional .meta.json) via GUI
       │
       ▼
2. leadsheet.parser produces a LeadSheet IR
       │
       ▼
3. harmony.analyzer enriches each ChordEvent with scale_notes,
   chord_tones, guide_tones; computes guide-tone voice-leading
       │
       ▼
4. User selects exercise + tempo, presses Play
       │
       ├──▶ backing: generates bass + drum MidiEvents
       │    backing.renderer: offline FluidSynth render → NumPy audio buffer
       │         │
       │         ▼
       │    pygame.mixer.Sound plays the buffer → AUDIO OUT
       │
       ├──▶ Main pygame-ce loop (every frame, ~60 FPS):
       │         │
       │         ├── timeline.get_state() reads audio playback position → current beat/chord
       │         │
       │         ├── exercises.*.get_highlights(chord, beat) → list of colored keys
       │         │
       │         ├── projection.renderer draws to proj_window → PROJECTOR (secondary display)
       │         │
       │         ├── gui.hud draws to hud_window → HUD (primary display)
       │         │
       │         └── both renderers present() — same frame, same state, inherently synced
       │
       └──▶ User interacts via keyboard shortcuts (change exercise, tempo, stop, etc.)
```

---

## 14. MVP Scope vs Stretch Goals

### MVP (Bachelor minimum viable product)

- [ ] Lead sheet parser (MIR-style `.tsv` chord annotations + optional `.meta.json`)
- [ ] Harmony analyzer (chord → scale mapping for common jazz chords)
- [ ] Timeline engine (audio-clock-synced, play/stop/loop)
- [ ] Projection engine (Pygame fullscreen, 88-key range, OpenCV homography calibration + warpPerspective)
- [ ] Free Mode exercise
- [ ] Guide Tone exercise
- [ ] Walking bass generator (algorithmic, quarter notes)
- [ ] Simple drum pattern (swing ride + hi-hat on 2 & 4)
- [ ] Offline FluidSynth rendering + `pygame.mixer` playback
- [ ] Keyboard-shortcut-driven Pygame UI with HUD
- [ ] 3–4 example lead sheet files

### Stretch Goals

- [ ] Contour exercise
- [ ] Flow exercise
- [ ] Start & End Note exercise
- [ ] Camera-based automatic calibration (detect key edges with OpenCV, auto-place the 4 markers)
- [ ] OMR / OCR integration for reading scanned lead sheets (reusing [Martinez-Sevilla et al. 2025])
- [ ] MusicXML import (parse with music21, convert to `.tsv` IR)
- [ ] Humanized bass lines (rhythmic variation, chromatic approaches)
- [ ] Chord chart scrolling display in HUD synced to playback
- [ ] MIDI input from the piano to analyze what the user plays
- [ ] Swing ratio control (configurable in GUI)
- [ ] MIDI file export of the backing track
- [ ] Live MIDI output to external DAW (via `mido` + `python-rtmidi`)
- [ ] Multiple form structures (AABA, blues, etc.) with section markers
- [ ] Real-time FluidSynth playback via PortAudio/ASIO (connect synth directly to USB audio interface, bypassing pygame.mixer, enabling live tempo changes without re-render and <5ms latency)
- [ ] Piano comping track (add chord voicings on a piano channel — trivial with FluidSynth, just more MidiEvents on a new channel)

---

## 15. Key Design Decisions & Constraints

1. **Single framework, single thread (pygame-ce)** — use `pygame-ce` (Community Edition) instead of standard `pygame`. pygame-ce provides a `pygame.Window` class that supports multiple windows in one process, which is needed to drive the projector (fullscreen) and the HUD (windowed) simultaneously. Both windows share one event loop: no threading, no synchronization, no framework conflicts. `pip install pygame-ce` is a drop-in replacement for `pip install pygame`.

2. **Pre-rendered audio eliminates real-time timing**: The hardest problem in music software is accurate real-time scheduling. By pre-rendering the entire backing track to a NumPy array before pressing play, we sidestep this entirely. The timeline derives its position from the audio playback clock, so projection and audio are always in sync by construction.

3. **Pure Python harmony (no music21)**: Chord-scale theory is a finite mapping. A dictionary of `{quality: interval_pattern}` plus arithmetic modulo 12 covers every chord quality in the MIR format. This avoids a ~50MB dependency that takes seconds to import.

4. **FluidSynth offline rendering**: The backing track is synthesized by driving a FluidSynth `Synth` object with programmatic `noteon()`/`noteoff()` calls and pulling raw audio via `get_samples()`. No `.mid` files, no disk I/O, no audio driver attached during rendering. The result is high-quality, multi-sampled audio from a GM SoundFont. Adding new instruments (piano comping, etc.) is trivial — just more events on a new MIDI channel.

5. **OpenCV-based projection calibration**: The user drags 4 markers onto the corners of the physical keyboard. `cv2.getPerspectiveTransform()` computes the homography matrix. Each frame, the keyboard is rendered flat in a canonical image, then `cv2.warpPerspective()` warps the whole frame to projector space in one call. Calibration is stored as JSON, done once per physical setup.

6. **No MIDI input in MVP**: The system does not listen to what the user plays. It only projects and plays backing track. MIDI input (for analysis/feedback) is a stretch goal.

7. **Walking bass is algorithmic, not AI-generated**: Deterministic, musically correct, predictable. No ML models, no network calls.

8. **Tempo changes re-render the buffer**: Changing tempo means the sample offsets change, so the backing track must be regenerated. For a 32-bar form this takes <1 second — acceptable since the user is stopped when changing tempo.

---

## 16. Example Lead Sheet Files to Ship

Provide 3–4 `.tsv` chord annotation files (with companion `.meta.json`) of **public-domain or original** chord progressions. Many jazz standard chord progressions are not copyrightable (they are harmonic sequences), but avoid reproducing melodies. Safe choices:

- **12-bar blues in F** (generic, public domain)
- **Rhythm changes in Bb** (generic, based on public domain harmony)
- **A ii-V-I practice progression** cycling through all 12 keys
- **"All The Things You Are"** chord changes (harmony only, no melody)

---

## 17. Testing Strategy: Test-Driven Development

This project uses **Test-Driven Development (TDD)** as the primary development methodology. Claude Code will be writing the majority of the code, and TDD provides two critical benefits in this context:

1. **Specification as code**: tests serve as unambiguous, executable specifications. When Claude Code writes a module, the tests define exactly what "correct" means — particularly important for the harmony analyzer and walking bass generator, where musical correctness is subtle.
2. **Regression safety**: as Claude Code iterates on modules across sessions, tests catch regressions immediately. This is essential when the developer (a human) reviews and refines the context-aware harmony rules — each change can be validated instantly.

### TDD Workflow

For each module, the development cycle is:

1. **Write tests first** — define the expected behavior with concrete examples before any implementation exists.
2. **Run tests** — confirm they fail (red).
3. **Implement** — write the minimum code to make tests pass (green).
4. **Refactor** — clean up, then re-run tests to confirm nothing broke.

Claude Code should follow this cycle for every module. When the developer asks Claude Code to implement a feature, Claude Code should propose tests first, get confirmation, then implement.

### Test Coverage by Module

- **`leadsheet.parser`** — parse various chord symbols, edge cases, multi-chord bars, the "All The Things You Are" example from this spec. Verify `ChordEvent` fields (root, quality, extensions, start_beat, end_beat, duration).
- **`harmony.analyzer`** — verify correct scales for each chord quality, especially extensions like `(b9)`, `(#9)`, `(#5)`. Test context-aware resolution: given `G:7 → C:min7`, assert the scale for G7 is Phrygian dominant, not Mixolydian. Test fallback to default when no context rule matches.
- **`backing.bass`** — verify voice-leading rules, output is valid MIDI range (28–48), approach notes work at chord boundaries, beat 4 approaches beat 1 of next chord by step.
- **`backing.drums`** — verify correct GM note numbers (ride=51, hi-hat=44, kick=36), swing timing offsets match configured ratio.
- **`exercises`** — verify highlight outputs for known chord sequences. For each exercise: given a specific chord and beat position, assert the exact set of highlighted MIDI notes and colors.
- **`backing.renderer`** (integration) — render a 12-bar blues, verify the output is a valid stereo int16 NumPy array of the expected length.
- **Full pipeline** (integration) — parse `.tsv` → analyze → generate events → FluidSynth offline render → verify buffer length and non-silence.
- **Manual testing** — projection alignment, visual correctness, and audio-projection sync. These cannot be automated and require the physical piano + projector setup.

---

## 18. References

Key sources from the research phase (see DS.pdf for full bibliography):

- Spice (2010) — Jazz improvisation pedagogy classification into 5 frameworks.
- Chyu (2004) — Teaching improvisation to piano students; creative reading, Q&A, chord-based improv.
- Deja et al. (2022) — Survey of 56 augmented piano prototypes.
- Sandnes & Eika (2019) — Projector-based piano augmentation for jazz chords with color coding.
- Deja et al. (2025), ImproVisAR — Augmented reality piano roll for teaching improvisation.
- Kitahara et al. (2005) — Improvisation supporting system with melody correction.
- Martinez-Sevilla et al. (2025) — OMR for jazz lead sheets (MIT-licensed Python code).
