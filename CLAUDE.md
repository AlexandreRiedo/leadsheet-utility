# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Summary

**leadsheet-utility** is a Python AR application for jazz piano improvisation training. A projector mounted above a piano highlights scale tones and guide tones in real time, synchronized with an auto-generated backing track (walking bass + swing drums). The system reads lead sheets, analyzes harmony (chord-scale mapping), and drives both projection and accompaniment from a shared musical timeline.

SPEC.md is the authoritative design reference (treat it as a living document that can evolve, but don't change it casually).

## Project Status: Greenfield

**Note to AI:** This project is currently in the initial setup phase. Many of the files, modules, tests, and directories mentioned in this document represent the **target architecture** and do not exist yet. Your immediate goal is to help me build towards this specification step-by-step. If a referenced file is missing, do not assume it's an error; assume we need to create it.

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
    → leadsheet (parser)
    → harmony (chord-scale analysis)
    → exercises (highlight logic per exercise mode)
    → projection (render flat image → homography warp → projector display)

Backing track:
    harmony → backing (walking bass + drums MIDI events)
    → FluidSynth offline render → numpy audio buffer
    → pygame.mixer playback

Sync: timeline reads pygame.mixer playback position → drives both projection and HUD
```

### 8 Core Modules

| Module | Role |
|--------|------|
| `leadsheet` | Parse MIR TSV files + `.meta.json` sidecar into `LeadSheet`/`ChordEvent` dataclasses |
| `harmony` | Map chord qualities to scales via lookup table + modulo-12 arithmetic (no music21) |
| `timeline` | Musical clock deriving beat position from audio playback, resolving current chord |
| `projection` | Render 88-key keyboard into canonical flat image (1920x200), warp via `cv2.warpPerspective` |
| `backing` | Algorithmic walking bass + swing drums → FluidSynth offline `get_samples()` → numpy buffer |
| `exercises` | 5 modes (Free, Guide Tone, Contour, Flow, Start & End Note) computing colored highlights per beat |
| `calibration` | 4-point marker drag UI → `cv2.getPerspectiveTransform` → homography matrix |
| `gui` | HUD window on primary display: chord chart, exercise selection, transport controls |

### Key Design Decisions

- **pygame-ce** (Community Edition) — required for `pygame.Window` multi-window support (projector fullscreen + HUD windowed in one process)
- **Single-thread, single event loop** — no threading; projection and HUD both update in the same 60 FPS loop
- **Pre-rendered audio** — backing track fully rendered before playback; timeline syncs to audio clock, eliminating real-time scheduling complexity
- **Pure Python harmony** — chord-scale mapping is a dictionary + modulo-12 arithmetic (~100 lines), no heavy music theory libraries
- **FluidSynth offline** — no audio driver during synthesis; events go through `synth.noteon()`/`noteoff()` then `synth.get_samples()`
- **Homography-based projection** — render axis-aligned key rectangles into a flat canonical image, then `cv2.warpPerspective` corrects for projector angle

### Lead Sheet Format (MIR TSV)

Tab-separated: `START_BEAT<TAB>END_BEAT<TAB>CHORD_SYMBOL`

```
0.000	4.000	A:min7
4.000	8.000	D:7
8.000	12.000	G:maj7
```

Chord symbols use colon notation: `Root:quality` with optional parenthesized extensions like `B:7(b9)`. Metadata lives in a `.meta.json` sidecar file (title, composer, key, time signature, tempo, form repeats).

11 example lead sheets are in `data/leadsheets/`.

### User Config

Stored in `~/.leadsheet-utility/`:
- `config.json` — SoundFont path
- `calibration.json` — projector resolution, marker positions, homography matrix

## Development Approach

- **Test-Driven Development (TDD)** — write tests first, then implement. Critical for harmony analysis and walking bass correctness.
- The `python-testing-patterns` and `python-design-patterns` skills are available for guidance.
- **Look up docs before writing code** — use the `DocsExplorer` agent (`.claude/agents/DocsExplorer.md`) to fetch current documentation for any library or API before using it. Do not rely on training data alone; always verify against up-to-date docs.
- SPEC.md sections contain detailed contracts, data structures, and edge cases for each module — consult them before implementing.
