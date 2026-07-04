# Tutorial

A first session, install to practice run. Shortcuts: [CONTROLS.md](CONTROLS.md). Setup: [README.md](README.md).

## 1. Setup

Projector above the piano as a secondary display, keystone correction off, dark room.

```bash
poetry install
cd src
poetry run python -m leadsheet_utility
```

Three windows open: HUD, chord chart, fullscreen projection. Override placement with `HUD_DISPLAY` / `CHART_DISPLAY` / `PROJ_DISPLAY=<index>`.

## 2. Calibrate (first run only)

Press `C`. Five phases, `Enter` advances:

1. **Range**: set the lowest/highest key the projector reaches.
2. **Markers**: drag the four corners onto the real keys; tune black-key proportions with `Q`/`W`/`A`/`S`.
3. **Black-key tuning**: nudge individual black keys.
4. **Exercise bands**: place the 1-octave and 2-octave bands.
5. **Audio delay**: adjust until lights and click line up.

Saved to `data/calibration.json`; redo only when the setup moves.

## 3. Open a tune and play

`O` opens a lead sheet from `data/leadsheets/`, e.g. `autumn_leaves.tsv`. `Space` plays: the backing renders once, a 2-bar count-in runs, then the projection lights the current chord-scale while the chart follows. `Space` pauses, `S` stops, `+`/`-` changes tempo.

## 4. Shape the difficulty

Live in any exercise:

- `B` highlight range: FULL / R.HAND / 2-OCT / 1-OCT. Start narrow.
- `T` chord tones: OFF / ONLY / OVERLAY. `R` root overlay.
- `G` backing density, `M` metronome (instant remix).
- `A` anticipation: lights switch to the next chord an 8th or quarter early.
- `F` freezes on one chord, `←`/`→` steps through the form.

## 5. Try the exercises

`1`-`5` selects; step 4 settings stay active underneath.

1. **Free**: the plain chord-scale.
2. **Guide Tone**: red voice-led 3rd/7th line. `H` swaps path, `N` previews the next chord.
3. **Contour**: a sliding lit window forces your line to follow a shape. `W` width, `X` speed.
4. **Flow**: projection gates on/off to force phrasing. `D` phrase feel.
5. **Start & End Note**: red entry and orange target note per phrase. `P` phrase length.

## 6. Loop a hard passage

`L` opens loop selection on the chart; `Alt+←/→` slides, `Shift+←/→` resizes, `Enter` confirms, `K` cancels. The bars loop with fresh backing each pass and regenerated exercise patterns. `S` restores the full tune.

## 7. A typical session

Autumn Leaves, exercise 1, R.HAND range, chord tones OVERLAY, DRUMS_BASS. Then exercise 2 for the guide-tone line, `L` to drill the bridge, exercise 5 over the full form, and finish on FULL range with overlays off.
