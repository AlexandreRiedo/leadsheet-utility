# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Summary

**leadsheet-utility** is a Python AR application for jazz piano improvisation training. A projector mounted above a piano highlights scale tones and guide tones in real time, synchronized with an auto-generated backing track (walking bass + swing drums). The system reads lead sheets, analyzes harmony (chord-scale mapping), and drives both projection and accompaniment from a shared musical timeline.

SPEC.md is the authoritative design reference (treat it as a living document that can evolve, but don't change it casually).

## Project Status: Early Development

Core pipeline is functional end-to-end: lead sheets load, harmony analyzes, a full backing track (walking bass + swing drums + jazz guitar comping + optional metronome) renders via FluidSynth, and playback runs from a shared timeline with a HUD window. The backing track is rendered as **four separate per-instrument layers** (bass/drums/guitar/metronome) in parallel on a background thread (one FluidSynth instance per layer, GIL released during `get_samples`), cached as int16 buffers, then summed by a fast numpy `mix_layers` pass; toggling the metronome or cycling backing density never re-renders. A "Rendering audio..." HUD loading screen covers the initial render, followed by a 2-bar count-in before playback. The `projection` and `calibration` modules are implemented (canonical 88-key layout, homography warp, **5-phase calibration UI** — projector-range endpoints, main markers + global black-key ratios, per-black-key offsets, 1-OCT/2-OCT exercise bands, and audio-delay tuning — persisted to `data/calibration.json`) and exercised via `scripts/preview_projector.py` and `scripts/preview_calibration.py`. **Free Mode** is wired into `main.py` with three orthogonal sub-toggles: a **RangeMode** cycle (FULL / R.HAND / 2-OCT / 1-OCT, key `B`) where R.HAND keeps every scale tone from middle C up while 2-OCT / 1-OCT collapse the highlight set to a single ascending scale run inside the calibrated band, a **ChordToneMode** cycle (OFF / ONLY / OVERLAY, key `T`) that either replaces the scale with chord tones or recolours them, and a **root highlight overlay** (key `R`). A **frozen mode** (key `F`, then `←`/`→`) pins the projection to a single chord for static practice. Projection-lead compensation (default 160 ms minus the calibrated `audio_delay_ms`) accounts for projector input lag so the lights line up with audio. Pressing `C` from the main screen enters calibration; on confirm the homography, layout, bands, and audio-delay reload live. **Guide Tone** (red voice-led 3rd/7th on top of the base highlights, paths cycled with `H`, octave shifted with arrows, next-chord preview toggled with `N`) and **Flow** (pre-generated on/off gate that slips across barlines, three phrasing presets cycled with `D` — SHORT / MEDIUM / LONG, varying phrase length rather than play fraction) are also wired into `main.py`. **Start & End Note** (red entry note + orange target per phrase, drawn from chord tones of the phrase's first / last chord, hashed when outside the current chord-scale; phrase length 2/4/8 bars cycled with `P`, fresh roll with `Shift+P`) is wired as a post-overlay on top of the Free Mode base. **Contour** filters the base highlights to a sliding ±N-semitone window around a pre-rolled smoothed random walk in the right-hand register (width NARROW/MEDIUM/WIDE = ±2/±3/±5 semitones cycled with `W`; speed SLOW/MEDIUM/FAST = 4-8 / 2-4 / 1-2 bars per arc cycled with `X`; curve re-rolled with `Shift+W`); the filter runs before the colour overlays so chord-tone / root / Start & End all paint on the survivors. All five exercises are now implemented.

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
    harmony -> backing (bass + drums + guitar + metronome MIDI events)
    -> FluidSynth offline render, one layer per instrument, rendered in parallel
    -> int16 layer cache -> mix_layers (numpy sum) -> pygame.mixer playback

Sync: timeline uses wall-clock elapsed time (perf_counter) -> drives both projection and HUD
       projection is led by `_PROJECTION_LEAD_SECONDS - audio_delay_ms/1000` to mask projector input lag
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
| `gui` | HUD window on primary display (song info, exercise selection, transport controls) + iReal Pro-style chord-chart window |

### What Exists Now (implemented modules)

- **`src/leadsheet_utility/leadsheet/`** — `parser.py` (TSV + sidecar parsing), `models.py` (ChordEvent/LeadSheet dataclasses)
- **`src/leadsheet_utility/harmony/`** — `constants.py` (scale/chord-tone tables, quality-to-scale map), `core.py` (scale resolver with 6 context rules, guide-tone line computation, `analyze()` entry point)
- **`src/leadsheet_utility/timeline/`** — `engine.py`: wall-clock-based musical clock with play/pause/stop transport. Uses `ClockSource` protocol for testability. Binary-searches chord list to resolve current chord each frame. Supports a **wrap-around** mode (`Timeline(..., wrap_around=True)`): when the clock passes the end of all repeats it wraps modulo the total length instead of clamping — used by loop-practice mode so a short temporary form repeats indefinitely while chord resolution still works through the form's own `form_repeats`.
- **`src/leadsheet_utility/backing/`** — `events.py` (MidiEvent dataclass, metronome, count-in, and swing drum pattern generators), `walking_bass.py` (algorithmic walking bass with phrase-direction arcs, chord-tone variation, approach notes), `comping.py` + `comping_voicings.py` + `comping_rhythms.py` (jazz guitar comping: drop-2/drop-3 voicings with voice-leading optimisation, 12 one-bar + 4 two-bar Phil DeGreg swing rhythm patterns with anticipations), `renderer.py` (`render_layer` runs one FluidSynth instance per instrument and returns a raw float32 buffer; `mix_layers` clips + converts to int16 for `pygame.mixer`)
- **`src/leadsheet_utility/gui/`** — `hud.py` (HUD rendering: song info, current/next chord, exercise selector, progress bar, shortcuts, frozen-mode indicator, count-in grid), `chart.py` (`render_chart` — iReal Pro-style chord grid on its own primary-display window: 4 bars per row, auto-scaled so a 32-bar+ form fits one screen, chords quantized to quarter-note slots so a bar can hold up to 4 chords, active chord cell highlighted; held-over chords show one symbol while the highlight advances bar-by-bar — driven by `App._render_chart` with the live playhead / frozen-chord beat. Also draws the **loop band** — `loop_select` (amber, while editing) / `loop_active` (blue, confirmed) tint the selected bars and bracket the range), `input.py` (key-to-action mapping via enum; loop selection uses `L` to enter, `Alt+←/→` to move the band, `Shift+←/→` to resize, `Enter` to confirm, `K` to clear/cancel)
- **`src/leadsheet_utility/main.py`** — `App` class: three-window pygame-ce loop (projection + HUD + chord chart), transport controls, file dialog, async **parallel** layer rendering (one thread per instrument inside a worker thread) with HUD loading screen, 2-bar count-in before playback. Caches per-instrument int16 buffers in `self._layers` and remixes via numpy sum when the metronome (`M`) or BackingMode cycle (`G`: NONE → DRUMS → DRUMS_BASS → FULL) changes — no re-render. Mid-stream remix splices from the current playhead so toggling never restarts the song. On startup loads `data/calibration.json` (or falls back to `make_default_homography`); during playback `_render_projection()` looks ahead by `_PROJECTION_LEAD_SECONDS - audio_delay_ms` to compensate for projector input lag, runs the Free-Mode pipeline (`free_mode_highlights` / `chord_tone_only_highlights` plus `apply_chord_tone_highlight` overlay and `apply_root_highlight` overlay), renders the canonical surface, and warps it through the saved homography onto the projector window. Frozen mode (`F`) stops playback and pins the projection to one chord, stepped with `←`/`→`. **Loop selection** (`L` enters select mode; `Alt+←/→` slides the bar window, `Shift+←/→` resizes it, `Enter` confirms, `K` clears/cancels): on confirm, `_start_loop` turns the selected bars into a **temporary form** — a mini `LeadSheet` (`_loop_chords` clips + re-bases the chords to beat 0) with `form_repeats` set so it spans `_LOOP_TARGET_SECONDS` (~4 min), analysed, with a `wrap_around=True` `Timeline` (`_loop_timeline`) and its own freshly-rendered backing (so the walking bass / comping **vary each pass**). The exercise patterns (Flow / Contour / Start-End) are regenerated over this temp form, so **the game modes treat the loop as one new continuous form** — phrases and contours progress across passes instead of replaying the same motions. While a loop is active, `_active_lead_sheet` / `_active_timeline` (used by the projection, exercises, and HUD) point at the temp form; the **chart still shows the original tune** and folds the temp cursor back onto the real bars (`loop_start + current_beat % loop_beats`). `_loop_layers` (separate from `_layers`) plays with `loops=-1`; play/pause toggles the loop transport; remix restarts the loop; `_stop_playback` tears down the temp form and restores the original-tune patterns (deterministic via unchanged seeds). Opts the Windows process into per-monitor DPI awareness so the projector window opens at the real physical resolution and the saved calibration stays valid.
- **`src/leadsheet_utility/exercises/`** — `free.py` (`free_mode_highlights(chord, range_mode, band_low)` with the `RangeMode` enum FULL / RIGHT_HAND / TWO_OCTAVE / ONE_OCTAVE and `next_range_mode`), `chord_tones.py` (`ChordToneMode` enum OFF / ONLY / OVERLAY with `chord_tone_pitch_classes`, `chord_tone_only_highlights`, `apply_chord_tone_highlight`; honours the `#11`/`b5`/`maj7#11` → 5→#11 substitution to match the comping voicings; altered dominants (`b9`/`b13`) keep their natural 5th — plain R-3-5-b7), `root.py` (`apply_root_highlight` post-processing overlay that recolours every highlight matching the chord's root pitch class), `guide_tone.py` (`guide_tone_midi(lead_sheet, chord_idx, path_idx, octave_offset, range_mode, band_low)` + `apply_guide_tone_highlight` overlay; reads the analyzer's two voice-led paths and snaps into the calibrated band in 1/2-OCT mode), `flow.py` (`FlowPhrasing` enum SHORT / MEDIUM / LONG and `generate_flow_pattern(total_beats, phrasing, seed)` producing a tuple of `(start_beat, end_beat)` "open" windows in absolute beats that slip across bar/chord boundaries; playing windows are longer than resting on average), `start_end.py` (`PhraseLength` enum TWO_BARS / FOUR_BARS / EIGHT_BARS and `generate_start_end_pattern(lead_sheet, phrase_length, *, midi_full_low, midi_full_high, seed)` rolling one `StartEndPhrase(start_beat, end_beat, start_midi, end_midi)` per fixed-bar window across every form repeat — `start_midi` is a random chord tone of the phrase's first chord, `end_midi` is a random chord tone of the last chord, both clipped to the right-hand register `[max(C4, midi_full_low), midi_full_high]` independent of the active RangeMode; `apply_start_end_highlight` paints them red / orange on top with hashed stripes when the target's pitch class isn't in the *current* chord-scale, matching the Guide Tone next-chord preview convention), `contour.py` (`WindowWidth` enum NARROW / MEDIUM / WIDE = ±2/±3/±5 semitones, `ContourSpeed` enum SLOW / MEDIUM / FAST = 4-8 / 2-4 / 1-2 bars per arc, `generate_contour_pattern(total_beats, *, midi_full_low, midi_full_high, beats_per_bar, speed, seed)` rolling a smoothed random walk of `(beat, midi_center)` control points inside the right-hand register; `ContourPattern.center_at(beat)` smoothstep-interpolates between control points; `apply_contour_window(highlights, beat, pattern, width)` is a pre-overlay filter that keeps only highlights within ±width semitones of the center — empty result → blackout, no auto-widen)
- **`src/leadsheet_utility/projection/`** — `layout.py` (88-key `KeyRect` geometry, configurable MIDI range, per-instrument `black_width_ratio`/`black_height_ratio`, and per-black-key `(dx, dy)` offsets; default range F2–E6 so both edges align to the left side of an F-key landmark; white-key endpoint validation), `renderer.py` (`render_canonical` draws `KeyHighlight`s into a flat 1920×200 surface), `warp.py` (`warp_canonical_to_projector` via `cv2.warpPerspective`, `make_default_homography` for identity preview)
- **`src/leadsheet_utility/calibration/`** — `models.py` (`Calibration` dataclass: canonical_size, projector_size, 4 markers TL/TR/BR/BL, global black-key ratios, per-key `black_key_offsets`, `midi_full_low/high`, `midi_one_octave_low/high`, `midi_two_octave_low/high`, `audio_delay_ms`, `homography()` via `cv2.getPerspectiveTransform`), `persistence.py` (JSON load/save to `data/calibration.json`, missing fields fall back to spec defaults), `ui.py` (`CalibrationUI` 5-phase state machine — RANGE_EDIT (full projector reach) → MAIN (markers + global ratios) → BLACK_KEY_TUNE (per-key offsets via Tab) → BAND_EDIT (1-OCT and 2-OCT exercise bands) → AUDIO_DELAY (ms tuning) — with arrow-key nudge / Shift=×10, Q/W width and A/S height ratio tuning with Shift=×5, R reset, Enter advances phases, Esc cancels)
- **`scripts/preview_projector.py`** — standalone harness rendering a static C-minor highlight through a default identity homography on the projector display
- **`scripts/preview_calibration.py`** — standalone calibration harness: loads existing calibration (or defaults), runs `CalibrationUI`, saves the result, then drops into a static C-minor verification render so alignment can be eyeballed on the real piano
- **`data/leadsheets/`** — 19 lead sheets as `.tsv` + `.meta.json` pairs
- **`data/soundfonts/GeneralUser-GS.sf2`** — bundled GM SoundFont for FluidSynth rendering

Multi-monitor: the main app assigns one window per display — HUD on 0, chart on 1 (when 3+ displays exist, else primary), projector fullscreen on the last display — via the SDL `WINDOWPOS_CENTERED | index` placement trick; `HUD_DISPLAY` / `CHART_DISPLAY` / `PROJ_DISPLAY=<index>` env vars override (the preview scripts honour `PROJ_DISPLAY` too). The projector should have keystone correction disabled in its OSD — the app's homography is the only transform that should be active. A single planar homography cannot fully correct black-key parallax (black-key tops sit on a physically higher plane than whites), so a small residual black-key drift is expected and accepted; the `black_width_ratio`/`black_height_ratio` knobs address the related but distinct issue of canonical proportions not matching the specific piano.

### What Does NOT Exist Yet

All five exercises (Free, Guide Tone, Contour, Flow, Start & End Note) are now wired into `main.py`.

Harmony integration tests are fixture-driven: JSON files in `tests/fixtures/harmony/` define expected pitch-class sets per chord for real lead sheets — update these when adding pieces or changing scale resolution.

### Key Design Decisions

- **pygame-ce** (Community Edition) — required for `pygame.Window` multi-window support (projector fullscreen + HUD windowed in one process)
- **Main loop is single-threaded** — projection and HUD update in the same 60 FPS loop. The only threading is for offline audio rendering: a worker thread runs a `ThreadPoolExecutor` that renders the four instrument layers in parallel (FluidSynth's `get_samples` releases the GIL, so this actually overlaps on multiple cores). The main loop polls the worker via `_update_render` and stays responsive throughout.
- **Per-instrument layer cache** — each instrument is rendered to its own int16 buffer and stored in `self._layers`. Toggling the metronome or cycling backing density re-mixes via a numpy sum (microseconds), not a fresh FluidSynth pass. Mid-stream remix splices from the current playhead.
- **Pre-rendered audio** — backing track fully rendered before playback; timeline syncs to audio clock, eliminating real-time scheduling complexity
- **Pure Python harmony** — chord-scale mapping is a dictionary + modulo-12 arithmetic, no heavy music theory libraries
- **FluidSynth offline** — no audio driver during synthesis; events go through `synth.noteon()`/`noteoff()` then `synth.get_samples()`
- **Homography-based projection** — render axis-aligned key rectangles into a flat canonical image, then `cv2.warpPerspective` corrects for projector angle
- **Projection leads audio** — `_PROJECTION_LEAD_SECONDS = 0.16` minus the calibrated `audio_delay_ms` is added to the timeline's current beat before resolving the projected chord, hiding projector input lag
- **Free Mode overlays compose** — `range_mode` and `chord_tone_mode` produce the base highlight list, then `apply_chord_tone_highlight` (OVERLAY mode) and `apply_root_highlight` are run as pure post-processing passes. Future exercises can opt into the same overlays by emitting `KeyHighlight`s and letting `main._render_projection()` apply the overlays.

### Lead Sheet Format (MIR TSV)

Tab-separated: `START_BEAT<TAB>END_BEAT<TAB>CHORD_SYMBOL`

```
0.000	4.000	A:min7
4.000	8.000	D:7
8.000	12.000	G:maj7
```

Chord symbols use colon notation: `Root:quality` with optional parenthesized extensions like `B:7(b9)` and optional slash bass like `G:7(b9)/F`. Metadata lives in a `.meta.json` sidecar file (title, composer, key, time signature, tempo, form repeats).

### User Config

- `data/calibration.json` (project-local, gitignored) — projector resolution, marker positions, black-key ratios. Loaded by `main.py` on startup; falls back to an identity homography if missing.
- `~/.leadsheet-utility/config.json` (not yet implemented) — SoundFont path overrides etc.
