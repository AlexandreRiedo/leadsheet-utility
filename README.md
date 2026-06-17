# Tips
- WINDOWS + SHIFT + LEFT/RIGHT to move the borderless projection window to a different monitor

# Running the project
- `cd src` -> `poetry run python -m leadsheet_utility`
- `poetry run python scripts/preview_projector.py`
- `poetry run python scripts/preview_calibration.py`

# Projector calibration

`scripts/preview_calibration.py` runs the 4-point calibration UI on the projector and saves the result to `data/calibration.json` (gitignored — geometry depends on your physical setup). After confirming, it enters a static C-minor verification render so you can eyeball alignment on the real keys.j Re-run anytime the projector or piano moves.

## Controls

Calibration runs in two phases. `Enter` advances: phase 1 → phase 2 → save.

### Phase 1 — main alignment (markers + global black-key ratios)

| Input | Action |
|---|---|
| Drag a marker (mouse) | Move it |
| `Tab` / `Shift+Tab` | Cycle active marker |
| `1`–`4` | Jump to marker (TL, TR, BR, BL) |
| Arrow keys | Nudge active marker by 1 px (`Shift` = 10 px) |
| `Q` / `W` | Black-key narrower / wider (`Shift` = ×5 step) |
| `A` / `S` | Black-key shorter / longer (`Shift` = ×5 step) |
| `R` | Reset markers |
| `Enter` | Continue to per-key tuning |
| `Esc` | Cancel |

### Phase 2 — per-black-key fine tuning

The active black key is drawn yellow. Use this phase to nudge individual black keys to mop up the residual drift the homography can't fix.

| Input | Action |
|---|---|
| `Tab` / `Shift+Tab` | Next / previous black key |
| Arrow keys | Nudge active black key by 1 px (`Shift` = 10 px) |
| `R` | Reset all per-key offsets |
| `Enter` | Confirm + save |
| `Esc` | Cancel |

## Tips

- Default projected range is **F2–E6**: both edges of the band align to the left side of an F key, so you've got the same physical landmark to drag both corners onto.
- After dragging the 4 white-corner markers, use `Q`/`W` and `A`/`S` to tune the black-key proportions to your specific piano — the "standard" 0.60 / 0.65 ratios won't match every instrument. Expect a small residual misalignment on the black keys: a single planar homography can't fully account for the fact that black keys sit on a physically higher plane than the whites. Good enough for highlighting.
- The projector should have **keystone correction disabled** in its OSD — the app's homography is the only transform that should be active.
- On a multi-monitor setup the main app places its windows per display: HUD on display 0, chart on display 1 (with 3+ displays, else primary), projection fullscreen on the last display. Override with `HUD_DISPLAY` / `CHART_DISPLAY` / `PROJ_DISPLAY=<index>` (the preview scripts honour `PROJ_DISPLAY` too).

# Projector lag compensation

Projectors have non-trivial input + processing lag, so the lit-up chord-scale will trail the backing track if we show it on the audio chord boundary. To compensate, the main app projects the chord that will be active `_PROJECTION_LEAD_SECONDS` (default **0.12 s**) ahead of the timeline. Tune this in [src/leadsheet_utility/main.py](src/leadsheet_utility/main.py): bump up if the projector still trails, down if it now leads.