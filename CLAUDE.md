# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Summary

**leadsheet-utility** is a Python AR application for jazz piano improvisation training. A projector mounted above a piano highlights scale tones and guide tones in real time, synchronized with an auto-generated backing track (walking bass + swing drums). The system reads lead sheets, analyzes harmony (chord-scale mapping), and drives both projection and accompaniment from a shared musical timeline.

SPEC.md is the authoritative design reference (treat it as a living document that can evolve, but don't change it casually).

## Project Status: Feature-Complete — Writing Phase

**The software is essentially done.** All five exercises, calibration, the full backing track, loop-practice mode, and multi-window projection are implemented and have been used in real testing sessions (see `proto-media/`). Active work has shifted from coding to the **written bachelor thesis** (see "Written Work" below). Code changes from here are expected to be small fixes and polish surfaced while writing, not new features. When helping, default to supporting the report — clarifying how a subsystem works, producing diagrams, reconciling docs with the code — rather than expanding scope.

## Written Work

The bachelor report lives under `rapport/` (gitignored media and drafts; the LaTeX/Word source and PDFs accumulate here). Target length **40–60 pages**. Structure agreed with the supervisor (Patrick Roth), per `rapport/notes/final-meeting-notes.txt`:

1. **Introduction**
2. **État de l'art** — restructured by theme; must cover cognitive load and anxiety in improvisation learning. Builds on the prior design-science work.
3. **Solution conceptuelle de l'artefact** — the high-level concept diagram, the automatic-analysis → grid flow, and the role of OMR (the reliability test showed OMR is too unreliable for direct ingestion, which is exactly what justifies starting from hand-entered grids; the automatic harmonic analysis is the real value-add).
4. **Solution technique** — code architecture, the technical building blocks, high-level phase/sequence diagrams (reference style: bachelor-carusi).
5. **Évaluations** — strictly framed around the research question (QR): (a) the supervisor interview as a pedagogical/cognitive evaluation of the artefact, (b) the participant tests with thematic-trend analysis of the interviews; demo videos are supporting, not central.
6. **Conclusion**

Reference theses are in `rapport/refs/` (carusi, courtin, huynh, mehmeti). The supervisor's annotated design-science doc is in `rapport/ds/`. `proto-media/` holds the prototype history and testing-session footage that feed the evaluation chapter.

**Research question (formalized in `rapport/plans/question-de-recherche.md`).** One umbrella question — does an RA-augmented piano support jazz-improvisation learning *in a realistic context* (a real scrolling grid + backing track + several keys, vs the C-major / right-hand-only of ImproVisAR) — split into two ordered sub-questions: **SQ1** (cognitive, the confirmatory core: does projection reduce *perceived* cognitive load? measured by NASA-TLX AVEC<SANS + the expert interview) and **SQ2** (the affective payoff: does the lighter load lower the barrier to *daring to play* — less anxiety, more confidence? measured by STAI-6 and self-efficacy). The order encodes a causal chain: SQ2 only matters if SQ1 holds, which is also the n=8 underpowering insurance (coherent-but-nonsignificant effects read as "the mechanism goes the predicted way," not "the test failed"). "Augmentation" deliberately spans both *réalité augmentée* (adding light) and *réalité diminuée* (removing keys to constrain — Contour / Flow / Start&End). Known open issue: the intro labels these SQ1/SQ2 while the Discussion uses QR1/QR2 — to be uniformized.

**Writing scaffolding (drafting underway; report deadline 2026-06-24).** The section-by-section master plan is `rapport/plans/plan-redaction.md` (what to write, where, with which sources, plus the page budget and Patrick's recurring corrections). Per-chapter plans: `rapport/plans/plan-solution-conceptuelle.md`, `rapport/plans/plan-solution-technique.md`. Draft chapters so far: `rapport/chapitres/introduction.md`, `rapport/chapitres/conclusion.md`. Generated report figures + their Mermaid sources live under `rapport/figures/solution-technique/` (2A–2K: data-flow, module deps, load/render phases, 60 FPS game loop, overlay pipeline, calibration FSM, scale resolution, backing / walking-bass / comping / swing-drums, fire-and-forget sync) and `rapport/figures/solution-conceptuelle/` (concept flow + the OMR reliability figures).

**OMR reliability test (`rapport/chapitres/omr-evaluation.md`, appendix to §3.4).** A custom weighted-Levenshtein metric (per-beat unrolling so errors are duration-weighted; graded harmonic-distance substitution cost) compares the OMR output to a hand-made ground truth across 11 standards: mean weighted precision **44/100** (median 40.2), and **11/11 standards land on a wrong beat count**. The takeaway is the inverse of "the tests demonstrate OMR's value": OMR is too unreliable to ingest directly, and that is precisely the evidence that justifies the hand-entered-grid design choice.

### Statistics & evaluation analysis (`rapport/stats/`)

The quantitative side of the Évaluations chapter (§5b, participant tests) lives in `rapport/stats/`. **Design:** within-subject AVEC/SANS (augmented vs. plain), **n = 8** participants, one piece per condition. Three measures, each a composite score per participant per condition: **NASA-TLX (RTLX, 0–100)** = cognitive load, **STAI-6 (20–80)** = state anxiety, **self-efficacy (1–7)** = confidence.

**Two paths, one source of truth** (see `rapport/stats/README.md`):
1. **Spreadsheet + online calculator = source of truth, auditable, defended to the jury.** Raw values → composite scores → Wilcoxon (W, W⁺/W⁻, p) by hand. The Google Sheets layout (tabs, headers, formulas, CSV export) is in `rapport/stats/SHEETS-LAYOUT.md`. Since spreadsheets have no Wilcoxon function, the exact-p lookup table to paste in is generated by `wilcoxon_ptable.py` (per W = min(T⁺,T⁻) at each n, via scipy).
2. **`present.py` (presentation only).** Reads the exported composites (`data/scores_tableur.csv`) + raw TLX items (`data/tlx_items_tableur.csv`) and draws the **report figures** (`figures/slope_*.png` ×3 + `figures/tlx_subscales.png`, A4-width, embedded Plus Jakarta Sans). It (re)computes **nothing** and re-runs **no** test — a figure cannot contradict the hand calc.
3. **`analyze_tests.py` (recoupement / verification).** Recomputes everything from raw `data/responses.csv` to *check* the spreadsheet: scoring → Wilcoxon signed-rank **exact** (`scipy`, exact at n ≤ 50) in the predicted direction → r_rb + dz → `results/scores.csv` + `results/wilcoxon_summary.md`. Run once, confirm W/p/r_rb concord, investigate any gap. **Its figures go to `figures/_verify/` (gitignored, throwaway)** — a dedicated subdir so verification can never clobber the report figures in `figures/`; whichever script you run last, the thesis figures stay intact.

**Directional hypotheses (applied automatically, don't "fix" by hand):** TLX & STAI → AVEC < SANS (`less`); self-efficacy → AVEC > SANS (`greater`). Effect sizes: rank-biserial r_rb `(W⁺−W⁻)/(W⁺+W⁻)` + Cohen's dz. `analyze_tests.py` rounds the paired differences before ranking so true ties (composites land on 1/6 or 1/4 fractions) get averaged ranks and the exact p matches the hand spreadsheet instead of drifting on float epsilon.

**Current results (verified, reproducible):** moderate-to-large effects all in the predicted direction (r_rb ≈ −.50 RTLX, −.44 STAI-6, +.36 self-eff), but **none reach p < .05** — the study is underpowered at n = 8. Report these as **effect-size trends in the predicted direction**, not as significant differences. Methodology and sources: `rapport/plans/guide-interpretation-stats.md`; analysis plan: `rapport/plans/plan-analyse-tests.md`. Deps are in the Poetry `stats` group: `poetry install --with stats` (scipy + matplotlib).

### Report writing style (French prose)

When drafting or editing prose **for the report** (above all the Évaluations chapter), match the author's voice. The reference sample is `rapport/stats/_style_sample.txt` (his own Introduction, État de l'art, Solution conceptuelle, and the NASA-TLX / STAI-6 / auto-efficacité interpretations). Observable rules:

- **Language & register:** French, academic but engaged. Default to the impersonal first person plural ("nous", "on"): "nous remarquons", "on remarque", "nous discuterons". Conceptual/design chapters occasionally slip into "je / ma proposition"; evaluation and stats prose stays in "nous".
- **No dashes:** never "—" or "–". Use ":", commas, or parentheses instead. Hard rule (also in memory).
- **Straight quotes only:** "comme ceci", never guillemets « ». Participant and professor citations go in straight double quotes.
- **":" introduces the concrete:** the signature move is a claim, then a colon, then its elaboration / example / list ("Concrètement : si l'artefact…", "C'est particulièrement fort avec la question sur l'exigence mentale : le score passe de 75 à 35").
- **Open paragraphs by naming the artifact under discussion:** "Sur le graphique en pente du NASA-TLX…", "Sur le barchart des médianes…", "Sur la table thématique des entretiens…", "En observant les rangs de Wilcoxon…".
- **Connectors he actually uses:** En effet, Toutefois, Néanmoins, Ainsi, Concrètement, Surtout, Finalement, En somme, Du reste, donc, par conséquent.
- **Stats honesty:** report effect-size *trends*, never significance. House phrases: "en faveur de H1" / "à contre-sens", "graphique en pente", "la médiane s'oriente en faveur de H1", "il faut tempérer la lecture de r", "indicatif et sous-puissant (car n = 8)", "il semblerait que", "tend à". State the n = 8 limits openly (échantillon petit, profils non testés, biais de désirabilité car le concepteur a mené les tests).
- **English jazz / technical terms in italics:** *changes*, *guide tones*, *comping*, *target notes*, *backing track*, *Raw TLX*.
- **Counts written as "6 sur 8" or "6/8"**, with "6 des 7 participants qui en parlent" when the denominator differs.
- **Defer deeper analysis to its section:** "Nous discuterons des cas de P04 et P08 dans la section de croisement des regards" rather than resolving it inline.

## Project Status: Implementation Notes

Core pipeline is functional end-to-end: lead sheets load, harmony analyzes, a full backing track (walking bass + swing drums + jazz guitar comping + optional metronome) renders via FluidSynth, and playback runs from a shared timeline with a HUD window. The backing track is rendered as **four separate per-instrument layers** (bass/drums/guitar/metronome) in parallel on a background thread (one FluidSynth instance per layer, GIL released during `get_samples`), cached as int16 buffers, then summed by a fast numpy `mix_layers` pass; toggling the metronome or cycling backing density never re-renders. A "Rendering audio..." HUD loading screen covers the initial render, followed by a 2-bar count-in before playback. The `projection` and `calibration` modules are implemented (canonical 88-key layout, homography warp, **5-phase calibration UI** — projector-range endpoints, main markers + global black-key ratios, per-black-key offsets, 1-OCT/2-OCT exercise bands, and audio-delay tuning — persisted to `data/calibration.json`) and exercised via `scripts/preview_projector.py` and `scripts/preview_calibration.py`. **Free Mode** is wired into `main.py` with three orthogonal sub-toggles: a **RangeMode** cycle (FULL / R.HAND / 2-OCT / 1-OCT, key `B`) where R.HAND keeps every scale tone from middle C up while 2-OCT / 1-OCT collapse the highlight set to a single ascending scale run inside the calibrated band, a **ChordToneMode** cycle (OFF / ONLY / OVERLAY, key `T`) that either replaces the scale with chord tones or recolours them, and a **root highlight overlay** (key `R`). A **frozen mode** (key `F`, then `←`/`→`) pins the projection to a single chord for static practice. Projection-lead compensation (default 160 ms minus the calibrated `audio_delay_ms`) accounts for projector input lag so the lights line up with audio. On top of that hardware (seconds-based) lead, a **musical anticipation** (key `A`, `AnticipationMode` OFF / 8TH / QUARTER) shifts the projected chord forward by a note value — an 8th or a quarter — so the lights switch to the next chord on the last 8th/quarter before the change and the look-ahead stays rhythmically constant across tempos. Pressing `C` from the main screen enters calibration; on confirm the homography, layout, bands, and audio-delay reload live. **Guide Tone** (red voice-led 3rd/7th on top of the base highlights, paths cycled with `H`, octave shifted with arrows, next-chord preview toggled with `N`) and **Flow** (pre-generated on/off gate that slips across barlines, three phrasing presets cycled with `D` — SHORT / MEDIUM / LONG, varying phrase length rather than play fraction) are also wired into `main.py`. **Start & End Note** (red entry note + orange target per phrase, drawn from chord tones of the phrase's first / last chord, hashed when outside the current chord-scale; phrase length 2/4/8 bars cycled with `P`, fresh roll with `Shift+P`) is wired as a post-overlay on top of the Free Mode base. **Contour** filters the base highlights to a sliding ±N-semitone window around a pre-rolled smoothed random walk in the right-hand register (width NARROW/MEDIUM/WIDE = ±2/±3/±5 semitones cycled with `W`; speed SLOW/MEDIUM/FAST = 4-8 / 2-4 / 1-2 bars per arc cycled with `X`; curve re-rolled with `Shift+W`); the filter runs before the colour overlays so chord-tone / root / Start & End all paint on the survivors. All five exercises are now implemented.

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

# Assemble the final report: insert the annex PDFs after their title/separator
# pages in the base. Interview script -> after base p.80 ("Questions de
# l'interview..."); participant session -> after base p.81 ("Feuille de route...").
# Base = rapport/final_export/to_finalize.pdf; output = rapport/final_export/
# Projet de Bachelor - Alexandre RIEDO.pdf. Insertion points are in INSERTIONS
# inside the script; --base / --output override the paths.
poetry run python scripts/append_annexes.py
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
| `timeline` | Musical clock deriving beat position from wall-clock elapsed time (`perf_counter`, started in sync with audio), resolving current chord |
| `projection` | Render 88-key keyboard into canonical flat image (1920x200), warp via `cv2.warpPerspective` |
| `backing` | Algorithmic walking bass + swing drums -> FluidSynth offline `get_samples()` -> numpy buffer |
| `exercises` | 5 modes (Free, Guide Tone, Contour, Flow, Start & End Note) computing colored highlights per beat |
| `calibration` | 5-phase UI (range, markers + black-key ratios, per-black-key offsets, exercise bands, audio delay) -> `cv2.getPerspectiveTransform` -> homography matrix |
| `gui` | HUD window on primary display (song info, exercise selection, transport controls) + iReal Pro-style chord-chart window |

### What Exists Now (implemented modules)

- **`src/leadsheet_utility/leadsheet/`** — `parser.py` (TSV + sidecar parsing), `models.py` (ChordEvent/LeadSheet dataclasses)
- **`src/leadsheet_utility/harmony/`** — `constants.py` (scale/chord-tone tables, quality-to-scale map), `core.py` (scale resolver: a layered priority system — extension overrides → **7 context rules** (1 V7→minor, 2 tritone sub, 3/4 ii-V & I-vi-ii-V chains, 5 IV→lydian, 6 standalone hdim7, 7 minor ii-V-i resting tonic; rules 3/4/7 run in a `_assign_chain_overrides` pre-pass, the rest in `resolve_scale`) → default quality lookup — plus guide-tone line computation and the `analyze()` entry point)
- **`src/leadsheet_utility/timeline/`** — `engine.py`: wall-clock-based musical clock with play/pause/stop transport. Uses `ClockSource` protocol for testability. Binary-searches chord list to resolve current chord each frame. Supports a **wrap-around** mode (`Timeline(..., wrap_around=True)`): when the clock passes the end of all repeats it wraps modulo the total length instead of clamping — used by loop-practice mode so a short temporary form repeats indefinitely while chord resolution still works through the form's own `form_repeats`.
- **`src/leadsheet_utility/backing/`** — `events.py` (MidiEvent dataclass, metronome, count-in, and swing drum pattern generators), `walking_bass.py` (algorithmic walking bass with phrase-direction arcs, chord-tone variation, approach notes), `comping.py` + `comping_voicings.py` + `comping_rhythms.py` (jazz guitar comping: drop-2/drop-3 voicings with voice-leading optimisation, sounded rootless — the root is kept for voice-leading but omitted at emit (`COMP_OMIT_ROOT`) so the bass owns the low register; 12 one-bar + 4 two-bar Phil DeGreg swing rhythm patterns with anticipations), `renderer.py` (`render_layer` runs one FluidSynth instance per instrument — bass=GM Acoustic Bass, guitar=GM Electric Guitar Jazz, drums=ch.9, balanced via CC7 — and returns a raw float32 buffer; `mix_layers` sums the active layers, applies a fixed master gain (2.5×) plus a **conditional** peak limiter (attenuates only if the sum would clip, so dynamics/balance stay linear across remixes), then converts to int16 for `pygame.mixer`)
- **`src/leadsheet_utility/gui/`** — `hud.py` (HUD rendering: song info, current/next chord, exercise selector, progress bar, shortcuts, frozen-mode indicator, count-in grid), `chart.py` (`render_chart` — iReal Pro-style chord grid on its own primary-display window: 4 bars per row, auto-scaled so a 32-bar+ form fits one screen, chords quantized to quarter-note slots so a bar can hold up to 4 chords, active chord cell highlighted; held-over chords show one symbol while the highlight advances bar-by-bar — driven by `App._render_chart` with the live playhead / frozen-chord beat. Also draws the **loop band** — `loop_select` (amber, while editing) / `loop_active` (blue, confirmed) tint the selected bars and bracket the range), `input.py` (key-to-action mapping via enum; loop selection uses `L` to enter, `Alt+←/→` to move the band, `Shift+←/→` to resize, `Enter` to confirm, `K` to clear/cancel)
- **`src/leadsheet_utility/main.py`** — `App` class: three-window pygame-ce loop (projection + HUD + chord chart), transport controls, file dialog, async **parallel** layer rendering (one thread per instrument inside a worker thread) with HUD loading screen, 2-bar count-in before playback. Caches per-instrument int16 buffers in `self._layers` and remixes via numpy sum when the metronome (`M`) or BackingMode cycle (`G`: NONE → DRUMS → DRUMS_BASS → FULL) changes — no re-render. Mid-stream remix splices from the current playhead so toggling never restarts the song. On startup loads `data/calibration.json` (or falls back to `make_default_homography`); during playback `_render_projection()` looks ahead by `_PROJECTION_LEAD_SECONDS - audio_delay_ms` to compensate for projector input lag, runs the Free-Mode pipeline (`free_mode_highlights` / `chord_tone_only_highlights` plus `apply_chord_tone_highlight` overlay and `apply_root_highlight` overlay), renders the canonical surface, and warps it through the saved homography onto the projector window. Frozen mode (`F`) stops playback and pins the projection to one chord, stepped with `←`/`→`. **Loop selection** (`L` enters select mode; `Alt+←/→` slides the bar window, `Shift+←/→` resizes it, `Enter` confirms, `K` clears/cancels): on confirm, `_start_loop` turns the selected bars into a **temporary form** — a mini `LeadSheet` (`_loop_chords` clips + re-bases the chords to beat 0) with `form_repeats` set so it spans `_LOOP_TARGET_SECONDS` (~4 min), analysed, with a `wrap_around=True` `Timeline` (`_loop_timeline`) and its own freshly-rendered backing (so the walking bass / comping **vary each pass**). The exercise patterns (Flow / Contour / Start-End) are regenerated over this temp form, so **the game modes treat the loop as one new continuous form** — phrases and contours progress across passes instead of replaying the same motions. While a loop is active, `_active_lead_sheet` / `_active_timeline` (used by the projection, exercises, and HUD) point at the temp form; the **chart still shows the original tune** and folds the temp cursor back onto the real bars (`loop_start + current_beat % loop_beats`). `_loop_layers` (separate from `_layers`) plays with `loops=-1`; play/pause toggles the loop transport; remix restarts the loop; `_stop_playback` tears down the temp form and restores the original-tune patterns (deterministic via unchanged seeds). Opts the Windows process into per-monitor DPI awareness so the projector window opens at the real physical resolution and the saved calibration stays valid.
- **`src/leadsheet_utility/exercises/`** — `free.py` (`free_mode_highlights(chord, range_mode, band_low)` with the `RangeMode` enum FULL / RIGHT_HAND / TWO_OCTAVE / ONE_OCTAVE and `next_range_mode`), `chord_tones.py` (`ChordToneMode` enum OFF / ONLY / OVERLAY with `chord_tone_pitch_classes`, `chord_tone_only_highlights`, `apply_chord_tone_highlight`; honours the `#11`/`b5`/`maj7#11` → 5→#11 substitution to match the comping voicings; altered dominants (`b9`/`b13`) keep their natural 5th — plain R-3-5-b7), `root.py` (`apply_root_highlight` post-processing overlay that recolours every highlight matching the chord's root pitch class), `guide_tone.py` (`guide_tone_midi(lead_sheet, chord_idx, path_idx, octave_offset, range_mode, band_low)` + `apply_guide_tone_highlight` overlay; reads the analyzer's two voice-led paths and snaps into the calibrated band in 1/2-OCT mode), `flow.py` (`FlowPhrasing` enum SHORT / MEDIUM / LONG and `generate_flow_pattern(total_beats, phrasing, seed)` producing a tuple of `(start_beat, end_beat)` "open" windows in absolute beats that slip across bar/chord boundaries; playing windows are longer than resting on average), `start_end.py` (`PhraseLength` enum TWO_BARS / FOUR_BARS / EIGHT_BARS and `generate_start_end_pattern(lead_sheet, phrase_length, *, midi_full_low, midi_full_high, seed)` rolling one `StartEndPhrase(start_beat, end_beat, start_midi, end_midi)` per fixed-bar window across every form repeat — `start_midi` is a random chord tone of the phrase's first chord, `end_midi` is a random chord tone of the last chord, both clipped to the right-hand register `[max(C4, midi_full_low), midi_full_high]` independent of the active RangeMode; `apply_start_end_highlight` paints them red / orange on top with hashed stripes when the target's pitch class isn't in the *current* chord-scale, matching the Guide Tone next-chord preview convention), `contour.py` (`WindowWidth` enum NARROW / MEDIUM / WIDE = ±2/±3/±5 semitones, `ContourSpeed` enum SLOW / MEDIUM / FAST = 4-8 / 2-4 / 1-2 bars per arc, `generate_contour_pattern(total_beats, *, midi_full_low, midi_full_high, beats_per_bar, speed, seed)` rolling a smoothed random walk of `(beat, midi_center)` control points inside the right-hand register; `ContourPattern.center_at(beat)` smoothstep-interpolates between control points; `apply_contour_window(highlights, beat, pattern, width)` is a pre-overlay filter that keeps only highlights within ±width semitones of the center — empty result → blackout, no auto-widen)
- **`src/leadsheet_utility/projection/`** — `layout.py` (88-key `KeyRect` geometry, configurable MIDI range, per-instrument `black_width_ratio`/`black_height_ratio`, and per-black-key `(dx, dy)` offsets; default range F2–E6 so both edges align to the left side of an F-key landmark; white-key endpoint validation), `renderer.py` (`render_canonical` draws `KeyHighlight`s into a flat 1920×200 surface), `warp.py` (`warp_canonical_to_projector` via `cv2.warpPerspective`, `make_default_homography` for identity preview)
- **`src/leadsheet_utility/calibration/`** — `models.py` (`Calibration` dataclass: canonical_size, projector_size, 4 markers TL/TR/BR/BL, global black-key ratios, per-key `black_key_offsets`, `midi_full_low/high`, `midi_one_octave_low/high`, `midi_two_octave_low/high`, `audio_delay_ms`, `homography()` via `cv2.getPerspectiveTransform`), `persistence.py` (JSON load/save to `data/calibration.json`, missing fields fall back to spec defaults), `ui.py` (`CalibrationUI` 5-phase state machine — RANGE_EDIT (full projector reach) → MAIN (markers + global ratios) → BLACK_KEY_TUNE (per-key offsets via Tab) → BAND_EDIT (1-OCT and 2-OCT exercise bands) → AUDIO_DELAY (ms tuning) — with arrow-key nudge / Shift=×10, Q/W width and A/S height ratio tuning with Shift=×5, R reset, Enter advances phases, Esc cancels)
- **`scripts/preview_projector.py`** — standalone harness rendering a static C-minor highlight through a default identity homography on the projector display
- **`scripts/preview_calibration.py`** — standalone calibration harness: loads existing calibration (or defaults), runs `CalibrationUI`, saves the result, then drops into a static C-minor verification render so alignment can be eyeballed on the real piano
- **`data/leadsheets/`** — 21 lead sheets as `.tsv` + `.meta.json` pairs
- **`data/soundfonts/GeneralUser-GS.sf2`** — bundled GM SoundFont for FluidSynth rendering

Multi-monitor: the main app assigns one window per display — HUD on 0, chart on 1 (when 3+ displays exist, else primary), projector fullscreen on the last display — via the SDL `WINDOWPOS_CENTERED | index` placement trick; `HUD_DISPLAY` / `CHART_DISPLAY` / `PROJ_DISPLAY=<index>` env vars override (the preview scripts honour `PROJ_DISPLAY` too). The projector should have keystone correction disabled in its OSD — the app's homography is the only transform that should be active. A single planar homography cannot fully correct black-key parallax (black-key tops sit on a physically higher plane than whites), so a small residual black-key drift is expected and accepted; the `black_width_ratio`/`black_height_ratio` knobs address the related but distinct issue of canonical proportions not matching the specific piano.

### Scope Status

All planned features are implemented: all five exercises (Free, Guide Tone, Contour, Flow, Start & End Note) are wired into `main.py`, calibration and projection are integrated, loop-practice mode works, and the backing track renders in parallel layers. The only items left unbuilt are the explicit **stretch goals** in SPEC.md §12 (camera-based automatic calibration; a separate piano comping track) — out of scope for the thesis.

Harmony integration tests are fixture-driven: JSON files in `tests/fixtures/harmony/` define expected pitch-class sets per chord for real lead sheets — update these when adding pieces or changing scale resolution.

### Key Design Decisions

- **pygame-ce** (Community Edition) — required for `pygame.Window` multi-window support (projector fullscreen + HUD windowed in one process)
- **Main loop is single-threaded** — projection and HUD update in the same 60 FPS loop. The only threading is for offline audio rendering: a worker thread runs a `ThreadPoolExecutor` that renders the four instrument layers in parallel (FluidSynth's `get_samples` releases the GIL, so this actually overlaps on multiple cores). The main loop polls the worker via `_update_render` and stays responsive throughout.
- **Per-instrument layer cache** — each instrument is rendered to its own int16 buffer and stored in `self._layers`. Toggling the metronome or cycling backing density re-mixes via a numpy sum (microseconds), not a fresh FluidSynth pass. Mid-stream remix splices from the current playhead.
- **Pre-rendered audio** — backing track fully rendered before playback; the timeline runs off a wall-clock (`perf_counter`) started in sync with playback, eliminating real-time scheduling complexity
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
