# SPEC.md — leadsheet-utility: Augmented Piano for Jazz Improvisation

## 1. Project Overview

**leadsheet-utility** is a Python application that augments a physical piano with projected light to help users learn and practice jazz improvisation. A projector mounted above the keyboard highlights scale tones, guide tones, and exercise-specific notes in real time, synchronized with an auto-generated backing track (walking bass + drums). The system reads a lead sheet file describing chord changes and timing, analyzes the harmony to compute chord-scales, and drives both the projection and the accompaniment from a shared musical timeline.

### Core Value Proposition

Jazz improvisation is hard because the harmonic context changes rapidly and the player must simultaneously think about scales, voice-leading, phrasing, and rhythmic placement. leadsheet-utility offloads the "which notes are correct right now?" question to the projector, freeing the player to focus on *creative* melodic decisions. Five structured exercises use color-coded projection to train specific improvisation skills drawn from established jazz pedagogy.

---

## 2. Concrete User Flow

### First-Time Setup (once)

1. The user physically mounts the projector above the piano. **The projector stays fixed from this point on.**
2. The user connects the projector as a secondary display and launches the app: `python -m leadsheet_utility`.
3. On first launch, no `~/.leadsheet-utility/calibration.json` exists, so the app enters **calibration mode**. Four bright markers appear on the projector display.
4. The user drags the 4 markers until they sit on the physical corners of the keyboard. Presses Enter to confirm.
5. The app computes the homography, draws a preview of all 88 key outlines. If alignment looks good, the user confirms. If not, re-drag and retry.
6. Calibration is saved. **These steps never need to be repeated** unless the projector is physically moved.

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
9. The user can switch exercises, change the tune, or adjust tempo at any time while stopped.
10. Press `Q` to quit.

### Re-Calibration (rare)

If the projector or piano gets bumped, the user presses `C` from the main screen to re-enter calibration mode. Existing marker positions are loaded as a starting point.

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

1. **Single framework, single thread (pygame-ce)** — `pygame-ce` provides `pygame.Window` for multiple windows in one process (projector fullscreen + HUD windowed). One event loop, zero thread conflicts.

2. **Pre-rendered backing track** — chord chart and tempo are fully known before playback, so audio is synthesized into a NumPy array *before* pressing play using FluidSynth offline. Eliminates all real-time MIDI timing concerns.

3. **Pure Python harmony** — chord-to-scale mapping is a dictionary of interval patterns plus modulo-12 arithmetic. No music21.

4. **FluidSynth offline rendering** — `Synth` object not connected to any audio driver. Events via `noteon()`/`noteoff()`, audio pulled via `get_samples()`. Adding instruments is just more MidiEvents on a new channel.

5. **Homography-based projection** — render axis-aligned key rectangles into a flat canonical image, then `cv2.warpPerspective` corrects for projector angle. Calibration done once per physical setup.

### Module Summary

| Module | Status | Responsibility |
|---|---|---|
| `leadsheet` | **Done** | Parse MIR-style `.tsv` + `.meta.json` into `LeadSheet`/`ChordEvent` dataclasses |
| `harmony` | **Done** | Chord symbol → scale pitches, chord tones, guide tones (lookup + 6 context rules) |
| `timeline` | **Done** | Musical clock deriving beat position from audio playback, resolving current chord |
| `backing` | **Partial** | Currently: metronome clicks + FluidSynth offline rendering. TODO: walking bass + drums |
| `gui` | **Done** | HUD window: chord display, exercise selection, transport, progress bar |
| `exercises` | **Not started** | 5 exercise modes computing colored highlights per beat |
| `projection` | **Not started** | Render canonical keyboard image, warp with homography, display on projector |
| `calibration` | **Not started** | 4-point marker drag UI + `cv2.getPerspectiveTransform` |

### Application States

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

---

## 4. Lead Sheet Format (Input) — Implemented

The parser is implemented in `leadsheet/parser.py` and `leadsheet/models.py`. This section is a reference for the format specification.

### Format

MIR-style TSV chord annotation. Each line: `START_BEAT<TAB>END_BEAT<TAB>CHORD_SYMBOL` (beats are 0-indexed floats).

```tsv
0.000	4.000	F:min7
4.000	8.000	Bb:min7
8.000	12.000	Eb:7
```

### Chord Symbol Grammar

```
SYMBOL     = ROOT ":" QUALITY [EXTENSION] [BASS]
ROOT       = C | C# | Db | D | ... | Bb | B
QUALITY    = matched by prefix family (hdim > min > maj > dim > aug > sus > dominant)
EXTENSION  = "(" ALTERATION {"," ALTERATION} ")"    e.g. (b9), (#9), (#5), (#11)
BASS       = "/" ROOT                                e.g. /F
```

### Slash-Chord Reclassification

Two notational shorthands write a 7sus4 as a slash chord. The parser detects and reclassifies:

- `(bass_pc - root_pc) % 12 == 2` AND quality NOT starting with `"7"` → `(bass_pc, "7sus4")`
- `quality.startswith("min")` AND `(root_pc - bass_pc) % 12 == 7` → `(bass_pc, "7sus4")`

### Metadata Sidecar

Companion `.meta.json` with same base name:

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

Defaults if missing: 4/4, tempo 120, unknown title. 14 lead sheet pairs ship in `data/leadsheets/`.

---

## 5. Harmony Analyzer — Implemented

The harmony module is implemented in `harmony/constants.py` (all tables) and `harmony/core.py` (resolution logic + guide-tone computation). This section serves as a **reference for the musical rules**. The code is authoritative for exact values.

### Two-Layer Resolution

1. **Layer 1 — Default lookup**: `QUALITY_TO_SCALE` dict maps chord quality (+ extensions) to a default scale. See `constants.py` for the full mapping.
2. **Layer 2 — Context-aware resolution**: examines previous/next chords to refine scale choice. 6 rules implemented in `resolve_scale()`.

### Context Rules (Layer 2)

**Rule 1: V7 → minor** — `X:7` → `Y:min*` where `(X_root - Y_root) % 12 == 7` → Phrygian dominant.

**Rule 2: Tritone substitution** — `X:7` → `Y` where `(X_root - Y_root) % 12 == 1` AND exact quality `"7"` → Lydian dominant.

**Rule 3: Extended ii-V chain (iii-vi-ii-V)** — Roots ascending by P4 (5 semitones), ending with ii-V. Each chord gets diatonic mode for its degree: iii=Phrygian, vi=Aeolian, ii=Dorian, V=Mixolydian.

**Rule 4: I-vi-ii-V turnaround** — Rule 3 chain preceded by a `maj*` chord a minor 3rd above the vi chord. I=Ionian, vi=Aeolian, ii=Dorian, V=Mixolydian.

**Rule 5: IV chord in major context** — `X:maj*` preceded by `Y:maj*` where `(X_root - Y_root) % 12 == 5` → Lydian.

**Rule 6: Half-diminished standalone** — `X:hdim7` where next chord is NOT dominant-function → Locrian natural 9 (instead of default Locrian natural 6).

### Resolution Priority

1. Extension overrides (explicit `b9`, `#9`, etc.) — always win
2. Context rules (V→minor, tritone sub, ii-V chain)
3. Default quality lookup

### Guide-Tone Voice-Leading

Pre-computed as two voice-led paths across the form (`LeadSheet.guide_tone_line`). Algorithm: start both paths in E3–E5 range, at each chord try both voice-to-PC assignments and pick minimum total semitone movement. Range-clamped to MIDI 52–76.

---

## 6. Exercises (Projection Modes) — Not Implemented

All exercises share a common interface:

```python
class Exercise(ABC):
    name: str
    description: str

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

### 6.1 Free Mode (Mode Libre)

- **Projection**: All chord-scale notes in **white**.
- **Purpose**: Introductory mode; the player sees which notes are "safe" and improvises freely.
- **Logic**: Return all `scale_notes` in white.

### 6.2 Guide Tone Game

- **Projection**: Chord-scale in **white** + one guide tone in **red**.
- **Purpose**: Train the player to target the 3rd or 7th, outlining the harmony.
- **Logic**: Use the pre-computed voice-led guide-tone line. Highlight the chosen guide tone in red.

### 6.3 Contour Game

- **Projection**: A *window* of ~5–7 consecutive chord-scale notes in **white**, moving up or down the keyboard over time.
- **Purpose**: Force the player to think about melodic direction at a macro level.
- **Logic**:
  - Pre-generate a contour curve (slow sine wave or random walk) mapping `form_position → register (MIDI note center)`.
  - Highlight only chord-scale notes within ±3 semitones of the contour center.
  - The illuminated window drifts left/right on the keyboard.

### 6.4 Flow Game (Jeu du Flux)

- **Projection**: Chord-scale in **white** when "open", **nothing** when "closed".
- **Purpose**: Train rhythmic phrasing by forcing silence.
- **Logic**:
  - Pre-generate an on/off pattern (e.g., 2 bars on, 1 bar off, or random pattern).
  - When "on": highlight all scale notes. When "off": blackout.
  - Configurable parameter: `flow_density` (0.0–1.0).

### 6.5 Start & End Note Game

- **Projection**: Chord-scale in **white** + one note in **green** (start) + one note in **red** (end/target).
- **Purpose**: Give the player an entry point and a target.
- **Logic**:
  - For each chord, randomly pick a start and end note from chord tones or scale tones.
  - End note of one phrase should ideally be near the start note of the next.

### Color Palette

| Element | Color | RGB |
|---|---|---|
| Chord-scale notes (base) | White | `(255, 255, 255)` |
| Guide tone / target / end note | Red | `(255, 50, 50)` |
| Start note | Green | `(50, 255, 50)` |
| All other keys / blackout | Black | `(0, 0, 0)` — **no light** |

Black background is critical: the projector emits no light for black pixels, so only highlighted keys are visible on the physical piano.

---

## 7. Projection Engine — Not Implemented

### Rendering Principle

The projector runs fullscreen on the secondary display with a **pure black background**. Only highlighted keys receive color — the player sees colored light appearing on their real piano keys.

### Key Geometry

Each piano key is a `KeyRect` in a **canonical (undistorted) coordinate space**:

```python
@dataclass
class KeyRect:
    midi_note: int
    is_black: bool
    x: int          # pixel x in canonical image
    y: int          # pixel y in canonical image
    width: int
    height: int
```

The canonical image is a fixed-size buffer (e.g., 1920×200 pixels) containing a flat, top-down keyboard layout. Computed once at startup from standard piano proportions.

### Rendering Pipeline: Render Flat, Then Warp

1. Render colored rectangles into the canonical flat image
2. `cv2.warpPerspective(canonical, H, projector_size)` — one call warps the entire frame
3. Convert BGR→RGB, blit to the projection `pygame.Window`

### Calibration

Calibration is a **mode within the main app** (not a separate script). Entered on first launch (no `calibration.json`) or when user presses `C`.

#### Calibration Flow

1. Display 4 bright marker circles on the projector, initially at screen corners. Each corresponds to a known corner in the canonical keyboard image (top-left/right of A0/C8, bottom-left/right of A0/C8).
2. User drags each marker to the corresponding corner of the physical piano. Arrow keys nudge for precision. Tab cycles markers.
3. Compute homography: `H = cv2.getPerspectiveTransform(src, dst)` where `src` = canonical corners, `dst` = marker positions.
4. Preview: render all 88 key outlines through the homography for visual verification.
5. Save to `~/.leadsheet-utility/calibration.json`:

```json
{
    "projector_resolution": [1920, 1080],
    "canonical_size": [1920, 200],
    "marker_positions_px": [[45, 62], [1875, 58], [42, 890], [1878, 895]],
    "homography_matrix": [[1.02, -0.01, 45.0], [0.003, 0.98, 62.0], [0.0, 0.0, 1.0]]
}
```

### Multi-Display Architecture

Both windows use `pygame.Window` (pygame-ce). The projection window is positioned on the secondary monitor by offsetting past the primary display width. Both share the same event loop and `timeline.get_state()` call — inherently synchronized.

### Refresh Rate

Target **60 FPS**. Per-frame work: ~7–15 filled rectangles into a small canonical image + one `warpPerspective` + a surface blit. Well within budget.

---

## 8. Backing Track Engine — Partially Implemented

### Current State

`backing/events.py` has the `MidiEvent` dataclass and a metronome click generator. `backing/renderer.py` does offline FluidSynth rendering to a NumPy int16 buffer for `pygame.mixer`. **Walking bass and drum generators are not yet implemented.**

### Architecture: Generate Events → Offline FluidSynth Render → Play

1. **Event generation** (pure Python): walking bass + drum algorithms produce `MidiEvent` objects.
2. **Offline rendering** (FluidSynth): `Synth` object processes events, outputs raw audio via `get_samples()`. No disk I/O — all in memory.
3. **Playback** (`pygame.mixer`): buffer loaded as `pygame.mixer.Sound`.

### SoundFont

GM SoundFont (`.sf2`) required. The bundled `data/soundfonts/GeneralUser-GS.sf2` is used by default. Path configurable in `~/.leadsheet-utility/config.json`.

### Walking Bass Generator — Not Implemented

Algorithmic walking bass: for each bar, generate a 4-note (quarter-note) bass line as `MidiEvent` objects on channel 0 (GM Acoustic Bass, program 33).

**Algorithm:**
1. **Beat 1**: Root of the chord (in bass range). If repeating same chord, may use 5th or 3rd.
2. **Beat 2**: Scale tone between beat 1 and beat 3 (stepwise motion).
3. **Beat 3**: 5th or another chord tone. Should differ from beat 1.
4. **Beat 4**: Approach note targeting next bar's beat 1 — chromatic half step above/below next root (strongest), whole step (diatonic), or 5th of next chord (dominant approach).
5. **Range**: MIDI 28 (E1) to MIDI 48 (C3).
6. Quarter-note duration (legato). Notes generally move by step or small skip.

**Direction**: Alternate ascending/descending across bars. If near range ceiling (48), walk down. Near floor (28), walk up.

**Two-beat chords**: Beat 1 = root, Beat 2 = approach note to next chord.

### Drum Pattern Generator — Not Implemented

Swing ride pattern per bar, as `MidiEvent` objects on channel 9 (GM drums).

**GM drum mapping**: Ride=51, Hi-hat pedal=44, Kick=36, Ghost snare=38 (low velocity).

**Pattern per bar:**
- Ride: quarter notes on 1, 2, 3, 4 + swing eighth "skip" on the and of 2 and 4
- Hi-hat pedal: beats 2 and 4
- Kick: beat 1 (velocity ~50)
- Minor humanization: velocity ±10, timing ±5ms (±220 samples at 44.1kHz)

### Swing Timing

Applied during event generation. The "and" of each beat is shifted later:
- Default swing ratio: 0.67 (triplet feel). Configurable 0.5 (straight) to 0.75 (hard swing).
- Swung: ride skips, offbeat bass notes, ghost snares
- Not swung: quarter-note hits, hi-hat, chord changes, the timeline clock

### Tempo Changes

Tempo change → re-render the buffer (<1 second for 32 bars). User is stopped when changing tempo.

---

## 9. Timeline Engine — Implemented

Implemented in `timeline/engine.py`. Wall-clock-based musical clock with play/pause/stop transport. Uses `ClockSource` protocol for testability. Binary-searches chord list to resolve current chord each frame.

Key design: no dedicated thread. `timeline.get_state()` is polled each frame by the main loop, returning `(current_beat, current_chord, prev_chord, form_repeat)`. Beat position derived from audio playback position.

---

## 10. GUI — Implemented

Implemented in `gui/hud.py` and `gui/input.py`. HUD renders in a second `pygame.Window` on the primary display.

### Keyboard Shortcuts

| Key | Action |
|---|---|
| `Space` | Play / Pause |
| `S` | Stop (reset to beginning) |
| `O` | Open file dialog (`tkinter.filedialog`) |
| `1`–`5` | Select exercise mode |
| `+` / `-` | Tempo up/down by 5 BPM |
| `M` | Toggle metronome |
| `C` | Enter calibration mode |
| `Q` / `Esc` | Quit |

### Settings Persistence

`~/.leadsheet-utility/config.json` (cross-platform via `pathlib.Path.home()`):
- SoundFont path, projector display index, piano range
- Calibration data (marker positions + homography matrix)
- Last used directory/file, exercise parameters, colors, swing ratio, default tempo

---

## 11. Dependencies

### Target Platform: Windows 10/11

### Python Dependencies

```
python = ">=3.13"
pygame-ce = ">=2.5.2"          # Community Edition — required for multi-window
numpy = ">=1.26"
opencv-python = ">=4.9"
pyfluidsynth = ">=1.3"
pytest = ">=8.0"
ruff = ">=0.4"
```

**Important**: `pygame-ce` and standard `pygame` conflict — cannot coexist.

### System-Level: FluidSynth DLL

`pyfluidsynth` wraps `libfluidsynth.dll` via ctypes. Install via `choco install fluidsynth` or download from [FluidSynth releases](https://github.com/FluidSynth/fluidsynth/releases) and add `bin\` to PATH.

---

## 12. MVP Scope

### Done

- [x] Lead sheet parser (MIR-style `.tsv` + `.meta.json`)
- [x] Harmony analyzer (chord → scale, 6 context rules, guide-tone voice-leading)
- [x] Timeline engine (audio-clock-synced, play/pause/stop, form looping)
- [x] Offline FluidSynth rendering + `pygame.mixer` playback
- [x] Keyboard-shortcut-driven Pygame UI with HUD
- [x] Metronome (toggleable)
- [x] 14 example lead sheet files

### TODO (MVP)

- [ ] Projection engine (Pygame fullscreen, 88-key range, OpenCV homography warp)
- [ ] Calibration (4-point marker drag UI)
- [ ] Free Mode exercise
- [ ] Guide Tone exercise
- [ ] Walking bass generator (algorithmic, quarter notes)
- [ ] Drum pattern (swing ride + hi-hat on 2 & 4)

### Stretch Goals

- [ ] Contour exercise
- [ ] Flow exercise
- [ ] Start & End Note exercise
- [ ] Camera-based automatic calibration
- [ ] Humanized bass lines (rhythmic variation, chromatic approaches)
- [ ] Chord chart scrolling display in HUD
- [ ] MIDI input from the piano
- [ ] Swing ratio control in GUI
- [ ] Piano comping track
- [ ] Real-time FluidSynth playback via PortAudio/ASIO

---

## 13. Testing Strategy

Test-driven development. Tests define expected behavior before implementation. The harmony analyzer has fixture-driven regression tests (JSON files in `tests/fixtures/harmony/` with expected pitch-class sets per chord for real lead sheets).

### Existing Tests

- `test_parser.py` — chord symbol parsing, edge cases, `ChordEvent` field validation
- `test_harmony.py` — scale resolution per quality, extension overrides, context rules
- `test_harmony_fixtures.py` — fixture-based full-form harmony regression (parametrized per piece per chord)
- `test_timeline.py` — musical clock, transport, chord resolution
- `test_main.py` — app integration

### Planned Tests

- Walking bass — voice-leading, valid MIDI range (28–48), approach notes at chord boundaries
- Drums — correct GM note numbers, swing timing offsets
- Exercises — highlight outputs for known chord sequences
- FluidSynth rendering (integration) — valid stereo int16 buffer of expected length

---

## 14. References

- Spice (2010) — Jazz improvisation pedagogy classification into 5 frameworks.
- Chyu (2004) — Teaching improvisation to piano students.
- Deja et al. (2022) — Survey of 56 augmented piano prototypes.
- Sandnes & Eika (2019) — Projector-based piano augmentation for jazz chords.
- Deja et al. (2025), ImproVisAR — AR piano roll for teaching improvisation.
- Martinez-Sevilla et al. (2025) — OMR for jazz lead sheets.
