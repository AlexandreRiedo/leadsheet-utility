# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Summary

**leadsheet-utility** is a Python AR application for jazz piano improvisation training. A projector mounted above a piano highlights scale tones and guide tones in real time, synchronized with an auto-generated backing track (walking bass + swing drums). The system reads lead sheets, analyzes harmony (chord-scale mapping), and drives both projection and accompaniment from a shared musical timeline.

SPEC.md is the authoritative design reference (treat it as a living document that can evolve, but don't change it casually).

## Project Status: Early Development

Core pipeline is functional end-to-end: lead sheets can be loaded, harmony analyzed, a full backing track (walking bass + swing drums + jazz guitar comping) rendered via FluidSynth, and playback driven from a shared timeline with a HUD window. Backing track rendering happens on a background thread with a "Rendering audio..." loading screen on the HUD, followed by a 2-bar count-in before playback begins. The `projection` and `calibration` modules are implemented as standalone components (canonical 88-key layout, homography warp, 4-point marker drag UI with persistence to `~/.leadsheet-utility/calibration.json`) and exercised via `scripts/preview_projector.py` and `scripts/preview_calibration.py`, but are **not yet wired into `main.py`**. The `exercises` module is **not yet implemented**.

## Commands

This project uses **Poetry** with `package-mode = false` (no installable package). Always prefix commands with `poetry run` to use the virtualenv, or activate the shell first with `poetry shell`.

```bash
# Install dependencies (Poetry, Python 3.13+)
poetry install

# Run the application
poetry run python -m leadsheet_utility

# Run all tests
poetry run pytest

# Run a single test file
poetry run pytest tests/test_harmony.py

# Run a single test by name
poetry run pytest tests/test_harmony.py::test_minor7_dorian -v

# Run fixture-driven tests (parametrized per piece per chord)
poetry run pytest tests/test_harmony_fixtures.py -v

# Lint
poetry run ruff check .

# Format
poetry run ruff format .
```

The `src/` layout is configured via `[tool.pytest.ini_options] pythonpath = ["src"]` in `pyproject.toml` so pytest can find `leadsheet_utility` without installing it.

## Architecture

### Module Pipeline

```
Lead Sheet (.tsv + .meta.json)
    -> leadsheet (parser)
    -> harmony (chord-scale analysis)
    -> exercises (highlight logic per exercise mode)
    -> projection (render flat image -> homography warp -> projector display)

Backing track:
    harmony -> backing (walking bass + drums MIDI events)
    -> FluidSynth offline render -> numpy audio buffer
    -> pygame.mixer playback

Sync: timeline uses wall-clock elapsed time (perf_counter) -> drives both projection and HUD
```

### 8 Core Modules

| Module | Role |
|--------|------|
| `leadsheet` | Parse MIR TSV files + `.meta.json` sidecar into `LeadSheet`/`ChordEvent` dataclasses |
| `harmony` | Map chord qualities to scales via lookup table + modulo-12 arithmetic (no music21) |
| `timeline` | Musical clock deriving beat position from audio playback, resolving current chord |
| `projection` | Render 88-key keyboard into canonical flat image (1920x200), warp via `cv2.warpPerspective` |
| `backing` | Algorithmic walking bass + swing drums -> FluidSynth offline `get_samples()` -> numpy buffer |
| `exercises` | 5 modes (Free, Guide Tone, Contour, Flow, Start & End Note) computing colored highlights per beat |
| `calibration` | 4-point marker drag UI -> `cv2.getPerspectiveTransform` -> homography matrix |
| `gui` | HUD window on primary display: chord chart, exercise selection, transport controls |

### What Exists Now (implemented modules)

- **`src/leadsheet_utility/leadsheet/`** — `parser.py` (TSV + sidecar parsing), `models.py` (ChordEvent/LeadSheet dataclasses)
- **`src/leadsheet_utility/harmony/`** — `constants.py` (scale/chord-tone tables, quality-to-scale map), `core.py` (scale resolver with 6 context rules, guide-tone line computation, `analyze()` entry point)
- **`src/leadsheet_utility/timeline/`** — `engine.py`: wall-clock-based musical clock with play/pause/stop transport. Uses `ClockSource` protocol for testability. Binary-searches chord list to resolve current chord each frame.
- **`src/leadsheet_utility/backing/`** — `events.py` (MidiEvent dataclass, metronome, count-in, and swing drum pattern generators), `walking_bass.py` (algorithmic walking bass with phrase-direction arcs, chord-tone variation, approach notes), `comping.py` + `comping_voicings.py` + `comping_rhythms.py` (jazz guitar comping: drop-2/drop-3 voicings with voice-leading optimisation, 12 one-bar + 4 two-bar Phil DeGreg swing rhythm patterns with anticipations), `renderer.py` (offline FluidSynth rendering to numpy int16 buffer for pygame.mixer)
- **`src/leadsheet_utility/gui/`** — `hud.py` (HUD rendering: song info, current/next chord, exercise selector, progress bar, shortcuts), `input.py` (key-to-action mapping via enum)
- **`src/leadsheet_utility/main.py`** — `App` class: two-window pygame-ce loop (projection + HUD), transport controls, file dialog, async background-thread audio rendering with loading screen, 2-bar count-in before playback. Toggleable metronome (`M`) and guitar comping (`G`).
- **`src/leadsheet_utility/projection/`** — `layout.py` (88-key `KeyRect` geometry, configurable MIDI range + per-instrument `black_width_ratio`/`black_height_ratio`; default range F2–E6 so both edges align to the left side of an F-key landmark; white-key endpoint validation), `renderer.py` (`render_canonical` draws `KeyHighlight`s into a flat 1920×200 surface), `warp.py` (`warp_canonical_to_projector` via `cv2.warpPerspective`, `make_default_homography` for identity preview)
- **`src/leadsheet_utility/calibration/`** — `models.py` (`Calibration` dataclass: canonical_size, projector_size, 4 markers TL/TR/BR/BL, black-key ratios, `homography()` via `cv2.getPerspectiveTransform`), `persistence.py` (JSON load/save to `~/.leadsheet-utility/calibration.json`, legacy files without ratio keys fall back to defaults), `ui.py` (`CalibrationUI` state machine: marker drag, Tab/1-4 selection, arrow-key nudge with Shift=×10, Q/W width and A/S height ratio tuning with Shift=×5, R reset, Enter/Esc confirm/cancel; renders green-white/pink-black filled overlay through current homography for visual alignment)
- **`scripts/preview_projector.py`** — standalone harness rendering a static C-minor highlight through a default identity homography on the projector display
- **`scripts/preview_calibration.py`** — standalone calibration harness: loads existing calibration (or defaults), runs `CalibrationUI`, saves the result, then drops into a static C-minor verification render so alignment can be eyeballed on the real piano
- **`data/leadsheets/`** — 14 lead sheets as `.tsv` + `.meta.json` pairs
- **`data/soundfonts/GeneralUser-GS.sf2`** — bundled GM SoundFont for FluidSynth rendering

Multi-monitor: `PROJ_DISPLAY=<index>` env var picks which display the projector window fullscreens on. The projector should have keystone correction disabled in its OSD — the app's homography is the only transform that should be active. A single planar homography cannot fully correct black-key parallax (black-key tops sit on a physically higher plane than whites), so a small residual black-key drift is expected and accepted; the `black_width_ratio`/`black_height_ratio` knobs address the related but distinct issue of canonical proportions not matching the specific piano.

### What Does NOT Exist Yet

- **`exercises`** — highlight logic per exercise mode (Free, Guide Tone, Contour, Flow, Start & End Note)
- **Main-app integration of projection/calibration** — `main.py` does not yet load calibration on startup, has no `C` key handler to enter calibration mode mid-session, and its `_render_projection()` stub does not yet draw highlights through the saved homography

Harmony integration tests are fixture-driven: JSON files in `tests/fixtures/harmony/` define expected pitch-class sets per chord for real lead sheets — update these when adding pieces or changing scale resolution.

### Key Design Decisions

- **pygame-ce** (Community Edition) — required for `pygame.Window` multi-window support (projector fullscreen + HUD windowed in one process)
- **Single-thread, single event loop** — no threading; projection and HUD both update in the same 60 FPS loop
- **Pre-rendered audio** — backing track fully rendered before playback; timeline syncs to audio clock, eliminating real-time scheduling complexity
- **Pure Python harmony** — chord-scale mapping is a dictionary + modulo-12 arithmetic, no heavy music theory libraries
- **FluidSynth offline** — no audio driver during synthesis; events go through `synth.noteon()`/`noteoff()` then `synth.get_samples()`
- **Homography-based projection** — render axis-aligned key rectangles into a flat canonical image, then `cv2.warpPerspective` corrects for projector angle

### Lead Sheet Format (MIR TSV)

Tab-separated: `START_BEAT<TAB>END_BEAT<TAB>CHORD_SYMBOL`

```
0.000	4.000	A:min7
4.000	8.000	D:7
8.000	12.000	G:maj7
```

Chord symbols use colon notation: `Root:quality` with optional parenthesized extensions like `B:7(b9)` and optional slash bass like `G:7(b9)/F`. Metadata lives in a `.meta.json` sidecar file (title, composer, key, time signature, tempo, form repeats).

### User Config

Stored in `~/.leadsheet-utility/`:
- `config.json` — SoundFont path
- `calibration.json` — projector resolution, marker positions, homography matrix
