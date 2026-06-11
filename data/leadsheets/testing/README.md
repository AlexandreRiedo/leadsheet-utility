# Testing lead sheets — naming convention

Files are prefixed with a difficulty tier chosen so that **alphabetical order
= difficulty order** (a plain `ls` shows the progression). No numeric
prefixes.

Current tiers, easiest first:

| Prefix    | Meaning                                          |
|-----------|--------------------------------------------------|
| `demo_`   | Shown to participants as a demo, not played      |
| `drill_`  | Exercises / vamps (ii-V-I study, modal vamp)     |
| `easy_`   | First real tunes (diatonic, slow harmonic rhythm)|
| `medium_` | Tunes with modulations / faster changes          |
| `pro_`    | Advanced harmony (Coltrane changes, non-functional) |

## Adding a new tier

Pick a word that lands in the right alphabetical gap:

- before `demo`: `a*`–`dem*` (e.g. `basics_`)
- between `easy` and `medium`: `f*`–`l*` (e.g. `gentle_`, `light_`)
- between `medium` and `pro`: `n*`–`o*`
- after `pro`: `q*`–`z*` (e.g. `tough_`, `ultra_`, `virtuoso_`)

⚠ Do **not** name a harder-than-medium tier `hard_` — "h" sorts *before*
"medium" and would break the ordering.

Within a tier, files sort by song name, not difficulty.
