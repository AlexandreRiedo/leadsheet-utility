---
name: No chromatic approach notes in walking bass
description: User dislikes chromatic approach notes in the walking bass — use diatonic (scale-tone) approaches instead
type: feedback
---

Don't use chromatic approach notes in the walking bass generator — they don't sound great.

**Why:** The user found the half-step chromatic approaches on beat 4 sounded bad in practice.

**How to apply:** When generating beat 4 (approach to next chord root), pick the nearest scale tone above or below the target rather than a chromatic half step. This applies to `_pick_approach` in `backing/walking_bass.py`.
