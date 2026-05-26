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
3. On first launch the app loads a default identity homography and runs with the spec defaults until the user presses `C` to enter calibration. The UI walks through five phases (Enter advances, Esc cancels):
   1. **RANGE_EDIT** — drag the low/high endpoints to match the leftmost and rightmost keys the projector light can physically reach. A solid green pad fills that range for visual confirmation.
   2. **MAIN** — drag the 4 corner markers onto the corners of the keyboard and tune global black-key width/height ratios (Q/W, A/S) so the rendered keys line up.
   3. **BLACK_KEY_TUNE** — step through each black key with Tab and nudge its canonical position to absorb per-key drift the homography can't model.
   4. **BAND_EDIT** — set the 1-OCT and 2-OCT exercise bands somewhere inside the FULL range. The bands are highlighted on the real piano so the user can pick a comfortable practice region.
   5. **AUDIO_DELAY** — tune the audio/projection offset in milliseconds until the lit-up scale tones land with the audio.
4. Calibration is saved to `data/calibration.json`. **These steps never need to be repeated** unless the projector is physically moved.

### Normal Usage (every session)

1. User launches the app. It loads `data/calibration.json` (and, eventually, user config from `~/.leadsheet-utility/`).
2. The projector display goes fullscreen black (no light on the piano yet). The primary display shows the HUD.
3. User presses `O` to open a `.tsv` lead sheet file (or the app loads the last-used file).
4. The HUD shows: title, chord chart, tempo, exercise selection.
5. User selects an exercise with keys `1`–`5` (default: Free Mode) and adjusts tempo with `+`/`-`.
6. User presses `Space` to play:
   - The four backing layers (bass, drums, guitar, metronome) are rendered in parallel on a worker thread (one FluidSynth instance per layer). The HUD shows an animated "Rendering audio..." indicator while the render is in flight.
   - Once the render completes, layers are cached as int16 buffers and the active mix is summed via numpy. A 2-bar count-in plays (side-stick clicks with a visual grid in the HUD).
   - After the count-in, `pygame.mixer` starts the backing-track buffer and the timeline starts.
   - The projector lights up the appropriate keys on the piano, leading the audio by ~`_PROJECTION_LEAD_SECONDS - audio_delay_ms` so projector input lag is masked.
   - The HUD shows the current chord, bar number, and a progress bar.
7. The user improvises on the piano, guided by the colored lights. While playing they can adjust overlays without restarting:
   - `M` toggles the metronome; `G` cycles the backing density (NONE → DRUMS → DRUMS_BASS → FULL). Both remix from the cached layers instantly.
   - `R` toggles a root-pitch-class overlay (blue). `B` cycles the Free-Mode range (FULL / 2-OCT / 1-OCT) within the calibrated bands. `T` cycles the chord-tone mode (OFF / ONLY / OVERLAY).
   - `F` enters/exits frozen mode: playback halts and the projection pins to one chord, stepped with `←`/`→` for static practice. `Space` resumes from the top.
8. When the form ends (or loops), the user presses `Space` to pause or `S` to stop.
9. The user can switch exercises, change the tune, or adjust tempo at any time while stopped. Tempo changes invalidate the layer cache; the next play triggers a re-render.
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

1. **Single framework, one main loop (pygame-ce)** — `pygame.Window` lets both windows live in one process (projector fullscreen + HUD windowed). The main loop is single-threaded; the only background work is offline audio rendering (see below), which the loop polls each frame.

2. **Pre-rendered backing, per-instrument layer cache** — chord chart and tempo are fully known before playback, so audio is synthesized into NumPy arrays *before* pressing play using FluidSynth offline. The four instruments (bass / drums / guitar / metronome) are rendered in parallel as separate int16 layers and cached in memory. Toggling the metronome or cycling backing density remixes via a numpy sum — no FluidSynth re-render. Mid-stream remix splices from the current playhead.

3. **Pure Python harmony** — chord-to-scale mapping is a dictionary of interval patterns plus modulo-12 arithmetic. No music21.

4. **FluidSynth offline rendering** — `Synth` object not connected to any audio driver. Events via `noteon()`/`noteoff()`, audio pulled via `get_samples()`. Adding instruments is just more MidiEvents on a new channel.

5. **Homography-based projection** — render axis-aligned key rectangles into a flat canonical image, then `cv2.warpPerspective` corrects for projector angle. Calibration done once per physical setup.

### Module Summary

| Module | Status | Responsibility |
|---|---|---|
| `leadsheet` | **Done** | Parse MIR-style `.tsv` + `.meta.json` into `LeadSheet`/`ChordEvent` dataclasses |
| `harmony` | **Done** | Chord symbol → scale pitches, chord tones, guide tones (lookup + 6 context rules) |
| `timeline` | **Done** | Musical clock deriving beat position from audio playback, resolving current chord |
| `backing` | **Done** | Walking bass + swing drums + jazz guitar comping (drop-2/drop-3 voicings, Phil DeGreg swing patterns) + metronome + count-in + FluidSynth offline rendering with per-instrument layer cache for instant remix |
| `gui` | **Done** | HUD window: chord display, exercise selection, transport, progress bar, frozen-mode indicator, count-in grid |
| `projection` | **Done (wired into main)** | Canonical 88-key layout + `cv2.warpPerspective`; main app loads saved calibration on startup and warps Free-Mode highlights every frame with audio-delay compensated lead time |
| `calibration` | **Done (wired into main)** | 5-phase UI (range → markers/ratios → per-black-key offsets → exercise bands → audio delay); loaded by main on startup, re-entered in-session via `C` |
| `exercises` | **Free, Guide Tone, Flow done; Contour / Start & End pending** | Free Mode (all scale notes) wired with `RangeMode` (FULL / R.HAND / 2-OCT / 1-OCT), `ChordToneMode` (OFF / ONLY / OVERLAY), and a root-overlay pass. Guide Tone post-overlay using the analyzer's voice-led line. Flow gates the projection on/off across barlines via a pre-generated pattern, density cycled with `D` |

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

### 6.1 Free Mode (Mode Libre) — Implemented

- **Projection**: All chord-scale notes in **green** (debug colour during prototyping; will return to white once projection calibration is finalised).
- **Purpose**: Introductory mode; the player sees which notes are "safe" and improvises freely.
- **Logic**: Implemented in `exercises/free.py` as `free_mode_highlights(chord, range_mode, band_low)`. Called once per frame by `App._render_projection` against a chord resolved with projection-lead compensation, then rendered → warped → blitted onto the projector window.

Three orthogonal sub-toggles compose with Free Mode:

- **RangeMode** (`exercises/free.py`, key `B`) — `FULL` highlights every scale tone on the keyboard; `TWO_OCTAVE` and `ONE_OCTAVE` collapse the set to a single ascending run of scale degrees starting at the lowest root inside the calibrated band. Lets the player practice the scale shape in one position.
- **ChordToneMode** (`exercises/chord_tones.py`, key `T`) — `OFF` (no treatment), `ONLY` (replace scale with just R, 3, 5/#11/b6, 7), `OVERLAY` (keep scale, recolour chord-tone pitch classes in cyan-blue). Honours the same `#11`/`b5`/`maj7#11` → #11 and `b9`/`b13`-without-13 → b6 substitutions as the comping voicings.
- **Root overlay** (`exercises/root.py`, key `R`) — recolours every highlight whose pitch class matches the chord root in saturated blue. Applied last so the root keeps its colour over the chord-tone overlay.

These overlays are pure post-processing passes over a `list[KeyHighlight]`, so future exercises can adopt them by emitting highlights and letting `App._render_projection` run the overlays.

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

### 6.4 Flow Game (Jeu du Flux) — Implemented

- **Projection**: Whatever the base exercise (Free Mode + sub-toggles) would have shown when the pattern is "open"; **blackout** when "closed".
- **Purpose**: Train rhythmic phrasing by forcing silence and pushing the player to think in phrases that cross chord and barline boundaries.
- **Logic** (`exercises/flow.py`):
  - `generate_flow_pattern(total_beats, density, seed)` pre-generates a list of `(start_beat, end_beat)` "open" windows spanning every form repeat. Switches do **not** align to bars or chord boundaries — a window can start on beat 4 of one bar and end on beat 3 of the next-next chord.
  - Three phrasings cycled with `D` (SHORT / MEDIUM / LONG) selected from `_PHRASING_PARAMS`: each band gives `(min_play, max_play, min_rest, max_rest)` in beats, tuned so playing always dominates resting on average (MEDIUM = play 6–12, rest 2–4). The total play *fraction* is similar across phrasings — what varies is phrase length: SHORT chops the form into many short runs, LONG spreads long uninterrupted phrases across long rests.
  - Pattern is regenerated on phrasing change and on lead-sheet load (length depends on the form); tempo changes do not invalidate it since the pattern is measured in beats.
  - Frozen mode and the stopped state bypass the gate entirely so the player can still study a chord with no flow noise.

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

## 7. Projection Engine — Implemented

Implemented in `projection/layout.py` (88-key `KeyRect` geometry with configurable MIDI range, per-instrument `black_width_ratio`/`black_height_ratio`, and per-black-key `(dx, dy)` offsets), `projection/renderer.py` (`render_canonical` draws `KeyHighlight`s into a flat 1920×200 surface), and `projection/warp.py` (`warp_canonical_to_projector` via `cv2.warpPerspective`). Default range is **F2–E6** so both edges align to the left side of an F-key — a single physical landmark for both calibration corners. Range endpoints are validated to be white keys. Wired into `main.py`: each frame, the timeline's current beat is shifted by `+_PROJECTION_LEAD_SECONDS - audio_delay_ms/1000` to mask projector input lag, the chord at that beat is resolved, Free-Mode (plus overlays) produces a `list[KeyHighlight]`, those are rendered → warped → blitted onto the projector window. `scripts/preview_projector.py` still exercises the same pipeline against a static C-minor highlight.

### Reference Specification

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

### Calibration — Implemented

The calibration module lives in `calibration/models.py` (`Calibration` dataclass holding markers, global black-key ratios, per-key `black_key_offsets`, full/1-OCT/2-OCT MIDI bands, and `audio_delay_ms`; `homography()` via `cv2.getPerspectiveTransform`), `calibration/persistence.py` (JSON load/save, missing fields fall back to defaults), and `calibration/ui.py` (`CalibrationUI` 5-phase state machine). Loaded by `main.py` on startup and re-entered in-session via `C`. Exercised standalone by `scripts/preview_calibration.py`.

A single planar homography cannot fully correct black-key parallax (black-key tops sit on a higher physical plane than whites). Two mitigations: the global `black_width_ratio`/`black_height_ratio` knobs adjust the canonical proportions for the specific piano, and the BLACK_KEY_TUNE phase records per-key `(dx, dy)` offsets to absorb residual drift on individual keys.

#### Calibration Flow (5 phases, advanced with Enter)

1. **RANGE_EDIT** — set the FULL MIDI range the projector light can physically reach. A solid green pad covers the active range so it's verifiable visually. Endpoints must be white keys.
2. **MAIN** — drag the 4 corner markers (TL, TR, BR, BL) onto the corners of the physical keyboard within the range; arrow keys nudge (Shift=×10), Tab cycles markers, Q/W tune black-key width and A/S tune black-key height (Shift=×5), R resets.
3. **BLACK_KEY_TUNE** — Tab steps through each black key; arrows nudge its canonical `(dx, dy)` offset to fix per-key drift the homography can't model.
4. **BAND_EDIT** — set the 1-OCT and 2-OCT exercise band endpoints (clipped to the FULL range, must satisfy ≥1 octave of headroom for the FreeMode runs).
5. **AUDIO_DELAY** — tune `audio_delay_ms` (positive = projection should appear N ms later than audio) until the lit-up scale lines up with the backing track.

On Enter past phase 5 the calibration is saved to `data/calibration.json` (per-machine, gitignored) with all five layers of state. Escape at any phase cancels and discards changes.

### Multi-Display Architecture

Both windows use `pygame.Window` (pygame-ce). The projection window is positioned on the secondary monitor by offsetting past the primary display width. Both share the same event loop and `timeline.get_state()` call — inherently synchronized.

### Refresh Rate

Target **60 FPS**. Per-frame work: ~7–15 filled rectangles into a small canonical image + one `warpPerspective` + a surface blit. Well within budget.

---

## 8. Backing Track Engine — Implemented

### Current State

`backing/events.py` has the `MidiEvent` dataclass, metronome click generator, count-in generator, and swing drum pattern (`generate_drums`). `backing/walking_bass.py` implements the full algorithmic walking bass (`generate_walking_bass`). `backing/comping.py` + `comping_voicings.py` + `comping_rhythms.py` implement jazz guitar comping with drop-2/drop-3 voicings and a pool of Phil DeGreg swing rhythm patterns. `backing/renderer.py` does offline FluidSynth rendering per layer (`render_layer`) and mixes with `mix_layers`.

### Architecture: Generate Events → Render Layers in Parallel → Mix → Play

1. **Event generation** (pure Python): bass / drums / guitar / metronome algorithms each produce a `list[MidiEvent]`.
2. **Parallel per-layer rendering** (FluidSynth): a worker thread spins a `ThreadPoolExecutor` and runs `render_layer` for each layer concurrently. Each layer gets its own `Synth` instance (own SoundFont load, own state — no shared mutable state), and FluidSynth's `get_samples` releases the GIL, so layers actually overlap on multiple cores. Each layer returns a raw float32 buffer, unclipped, so dense moments don't get pre-shorn.
3. **Layer cache**: the four buffers are kept in memory (`App._layers`).
4. **Mix** (`mix_layers`): sums the active layers, clips, and converts to int16. Called every time the mix changes (metronome toggle, BackingMode cycle). Mid-stream changes slice the new mix from the current playhead so audio continues seamlessly.
5. **Playback** (`pygame.mixer`): final int16 buffer loaded as `pygame.mixer.Sound`.

### SoundFont

GM SoundFont (`.sf2`) required. The bundled `data/soundfonts/GeneralUser-GS.sf2` is used by default. Path configurable in `~/.leadsheet-utility/config.json`.

### Walking Bass Generator — Implemented

Algorithmic walking bass in `backing/walking_bass.py`. Generates a 4-note (quarter-note) bass line per bar as `MidiEvent` objects on channel 0 (GM Acoustic Bass, program 33).

**Algorithm:**
1. **Beat 1**: Root of the chord (in bass range). Alternate chord tones (5th/3rd) for repeated chords.
2. **Beats 2–3**: Phrase-direction mix of chord tones and scale tones. ~5% chance of a mid-bar arch (direction reversal on beat 3) for variety. Occasionally enters "chord-tones-only" streaks for a more harmonic, outlined sound.
3. **Beat 4**: Diatonic approach note targeting next bar's beat 1. ~25% chance of a "dominant approach" (P4 below or P5 above target).
4. **Range**: MIDI 28 (E1) to MIDI 48 (C3).
5. Legato duration (0.95 × beat). Consecutive repeats replaced by nearest scale tone.

**Direction**: Ascending/descending phrases of 1–2 bars that flip at boundaries. Range limits (within 3 semitones of ceiling/floor) force a direction reversal.

**Two-beat chords**: Root + approach note. Three-beat chords: root + scale step + approach.

### Drum Pattern Generator — Implemented

Swing ride pattern per bar in `backing/events.py` (`generate_drums`). `MidiEvent` objects on channel 9 (GM drums).

**GM drum mapping**: Ride=51, Hi-hat pedal=44, Kick=36, Ghost snare=38 (low velocity), Side-stick=37 (metronome/count-in).

**Pattern per bar:**
- Ride: quarter notes on 1, 2, 3, 4 + swing-eighth skip on the "and" of 2 and 4
- Hi-hat pedal: beats 2 and 4
- Kick: beat 1 (velocity ~50)
- Ghost snare: ~25% chance on each swung offbeat (velocity ~60, humanized)
- Minor humanization: velocity ±10, timing ±5ms (±220 samples at 44.1kHz)

**Count-in**: `generate_count_in` produces side-stick metronome clicks for N bars before playback, with visual grid feedback in the HUD.

### Swing Timing

Applied during event generation. The "and" of each beat is shifted later:
- Default swing ratio: 0.67 (triplet feel). Configurable 0.5 (straight) to 0.75 (hard swing).
- Swung: ride skips, offbeat bass notes, ghost snares
- Not swung: quarter-note hits, hi-hat, chord changes, the timeline clock

### Guitar Comping Generator — Implemented

Algorithmic jazz guitar comping in `backing/comping.py`. Generates `MidiEvent` objects on channel 1 (GM nylon/electric guitar). Two-layer design:

- **Voicings** (`comping_voicings.py`): drop-2 and drop-3 root-bass voicings built from `chord.chord_tones`. 4-note drop-2 = `[R, 5, 7, 3+12]`, drop-3 = `[R, 7, 3+12, 5+12]`; triads use a 3-note drop-2 analog. Root register clamped to A2–A3, top voice ≤ G5. The natural 5th is substituted with `#11` when the chord has `#11`/`b5`/`maj7#11`, or with `b6` when the chord has `b9`/`b13` without a natural 13 (phrygian-dominant / harmonic-minor V feel). `best_voicing()` picks the candidate that minimises total semitone movement from the previous voicing.
- **Rhythm patterns** (`comping_rhythms.py`): 12 one-bar and 4 two-bar swing patterns transcribed from Phil DeGreg's *Jazz Keyboard Harmony* comping-rhythms page. Two-bar patterns include anticipations (hits in bar 1 that ring into bar 2 using bar 2's harmony). `pick_pattern()` chooses randomly per 2-bar window.

Each hit emits note-on/off pairs with swing applied to offbeat 8ths, ±8 velocity humanization, ±180 sample timing humanization, accent on marked hits, and a `COMP_SKIP_PROBABILITY = 0.2` for sparseness. Toggle with `G` in the HUD.

### Tempo / Toggle Changes

- **Tempo change** invalidates the layer cache (the new tempo would change every layer's timing). Playback stops; the next play triggers a fresh parallel re-render with the "Rendering audio..." HUD screen.
- **Metronome toggle (`M`)** and **BackingMode cycle (`G`: NONE → DRUMS → DRUMS_BASS → FULL)** only change *which* cached layers are summed. They run a `mix_layers` pass (microseconds) and splice from the current playhead, so toggles are inaudibly instant and never restart the song.

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
| `Space` | Play / Pause (also exits frozen mode and starts from the top) |
| `S` | Stop (reset to beginning) |
| `O` | Open file dialog (`tkinter.filedialog`) |
| `1`–`5` | Select exercise mode (only Free is implemented) |
| `+` / `-` | Tempo up/down by 5 BPM (invalidates layer cache) |
| `M` | Toggle metronome (instant remix from cache) |
| `G` | Cycle backing density: NONE → DRUMS → DRUMS_BASS → FULL |
| `R` | Toggle root-pitch-class overlay (blue) |
| `B` | Cycle Free-Mode range: FULL → 2-OCT → 1-OCT |
| `T` | Cycle chord-tone mode: OFF → ONLY → OVERLAY |
| `F` | Enter / exit frozen mode (pin projection to one chord) |
| `←` / `→` | In frozen mode, step to previous / next chord |
| `D` | Cycle Flow phrasing: SHORT → MEDIUM → LONG |
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
- [x] Walking bass generator (algorithmic, quarter notes, phrase-direction arcs)
- [x] Drum pattern (swing ride + hi-hat on 2 & 4, ghost snares, humanization)
- [x] Jazz guitar comping (drop-2/drop-3 voicings, Phil DeGreg swing rhythm patterns, anticipations)
- [x] Parallel per-layer FluidSynth rendering (bass/drums/guitar/metronome), int16 layer cache, instant mid-stream remix on toggle, "Rendering audio..." HUD screen
- [x] Count-in (visual grid in HUD + side-stick audio)
- [x] Keyboard-shortcut-driven Pygame UI with HUD
- [x] Metronome (toggleable, `M`)
- [x] Backing density cycle (NONE / DRUMS / DRUMS_BASS / FULL, `G`)
- [x] 14 example lead sheet files

- [x] Projection engine (canonical 88-key F2–E6 layout, OpenCV homography warp, per-black-key offsets, projection-lead compensation, standalone preview script)
- [x] Calibration: 5-phase UI (range → markers/ratios → per-black-key offsets → exercise bands → audio delay) + JSON persistence, standalone preview script
- [x] Main-app integration of projection: calibration loaded on startup, Free Mode rendered through the saved homography during playback
- [x] Free Mode exercise with `RangeMode` (FULL / 2-OCT / 1-OCT, `B`), `ChordToneMode` (OFF / ONLY / OVERLAY, `T`), and root overlay (`R`) sub-toggles
- [x] Frozen mode (`F` + arrow keys) for static per-chord practice
- [x] In-app calibration entry (`C` keybinding) — stops playback, runs the `CalibrationUI` on the projector, reloads homography/layout/bands/audio-delay on confirm
- [x] Windows per-monitor DPI awareness opt-in (projector window opens at true physical resolution)

### TODO (MVP)

- [x] Guide Tone exercise
- [x] Flow exercise

### Stretch Goals

- [ ] Contour exercise
- [ ] Start & End Note exercise
- [ ] Camera-based automatic calibration
- [ ] Piano comping track

---

## 13. Testing Strategy

Test-driven development. Tests define expected behavior before implementation. The harmony analyzer has fixture-driven regression tests (JSON files in `tests/fixtures/harmony/` with expected pitch-class sets per chord for real lead sheets).

### Existing Tests

- `test_parser.py` — chord symbol parsing, edge cases, `ChordEvent` field validation
- `test_harmony.py` — scale resolution per quality, extension overrides, context rules
- `test_harmony_fixtures.py` — fixture-based full-form harmony regression (parametrized per piece per chord)
- `test_timeline.py` — musical clock, transport, chord resolution
- `test_walking_bass.py` — voice-leading, valid MIDI range (28–48), approach notes at chord boundaries
- `test_drums.py` — correct GM note numbers, swing timing offsets, humanization
- `test_main.py` — app integration

### Planned Tests

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
