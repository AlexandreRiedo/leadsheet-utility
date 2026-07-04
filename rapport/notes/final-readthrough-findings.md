# Final read-through findings — Projet de Bachelor (Alexandre RIEDO)

Read-through of `rapport/final_export/Projet de Bachelor - Alexandre RIEDO.pdf` (94 pages),
cross-referenced against actual source code and data, not just planning docs.

**Status:** in progress. Findings are streamed as I work through the PDF so nothing is lost
if the session breaks.

**Severity legend:**
- 🔴 **BLOCKER** — factual error, contradicts code/data, or breaks an argument. Fix before submission.
- 🟠 **SHOULD-FIX** — inaccurate, misleading, or inconsistent; weakens credibility.
- 🟡 **NICE-TO-HAVE** — typo, style, polish, minor wording.
- 🔵 **NOTE / VERIFY** — something to double-check; may be fine.

---

## Progress log

- [x] Structure / TOC mapped — **TOC stale for tail (off by 7–8 pp)**
- [x] Ch.1 Introduction
- [x] Ch.2 État de l'art
- [x] Ch.3 Solution conceptuelle (incl. OMR) — OMR numbers & ATTYA example verified
- [x] Ch.4 Solution technique — colors, drums, bass, comping, calibration all verified vs code
- [x] Ch.5 Évaluations — **every stat recomputed from data and confirmed**
- [x] Ch.6 Conclusion
- [x] Annexes — complete
- [x] Cross-checks against code & data (exercises colors, drum pattern, harmony scales, profile/Wilcoxon/TLX data, piece assignments)

## Summary

**The thesis is in very good shape.** The substance is sound: every quantitative claim I could
recompute (8×2 composites, 3× Wilcoxon W/r/p, TLX subscale medians, profile figures, piece
assignments) matched the data exactly, and every technical description I checked against the code
(projection colors, drum/bass/comping generators, harmony scale set, calibration phases, game loop)
was accurate. The evaluation chapter is a model of honest small-n reporting (effect-size trends, no
significance overclaim, confounds disclosed, qual/quant coherence). No fabricated or contradicted
numbers were found.

**The defects are presentation/citation hygiene, not substance:**

| # | Severity | Issue | Where |
|---|---|---|---|
| 1 | 🔴 | Martinez-Sevilla OMR paper **missing from bibliography**; in-text "[15]" points to the diminished-reality review | p15–16 + biblio |
| 2 | 🟠 | **TOC page numbers stale** for everything from "Interprétation des résultats" on (off +7/+8) | p3 TOC |
| 3 | 🟠 | **SQ1/SQ2 vs QR1/QR2** mixed | p46, p66 vs p4, p67 |
| 4 | 🟠 | **Figure numbering**: no Fig 14, ad-hoc Fig 4b / 13b | Ch.4 |
| 5 | 🟠 | Biblio **[17] author list mangled**, **[23] "M. Field" = misparsed "Moffett Field"** | biblio |
| 6 | 🟡 | "Sandnens"→"Sandnes" caption, [11] missing authors, several typos/grammar | various |

Counts: 🔴×1, 🟠×~5, plus a batch of 🟡 typos and 🔵 notes (all detailed below).

### Quick 🟡 typo/grammar list (collected)
- p3 TOC + p39 body heading: **"Context" → "Contexte"**.
- p4: "deux-sous questions" → "deux sous-questions"; "franchir le pas.Nous" missing space.
- p9: "au dessus un clavier" → "au-dessus d'un clavier"; p11 "projecteur surmonté" → "surplombant".
- p12 caption: **"Sandnens" → "Sandnes"**.
- p14: run-on "positionner le projecteur afin d'éloigner le projecteur…" (repeats).
- p55: "STAi-6" → "STAI-6".
- "bleu" vs "bleu foncé" for the root color — pick one descriptor.

### 🔵 Notes / verify-with-author (not errors)
- p47 "p bilatéral" choice is internally consistent and well-justified — keep, just ensure the same rule is visibly applied in Tables 6 & 8 (it is).
- P08's AVEC/SANS pieces are at different difficulty levels (disclosed as a confound).
- OMR raw data (`JM_MIR_*`, `evaluate_custom`) not in this repo — derived figures verified instead.
- Heavy color-coding with no colorblind-accessibility note (all participants non-daltonien); could be a one-line limitation.
- TDD-with-Claude-Code disclosed in the tools table — confirm that's intended for the body.

---

# COPY-PASTABLE EDITS

> French replacements are written in the author's voice (no "—"/"–", straight quotes, "nous/on",
> colon-introduces-the-concrete). "FIND" = current text (reconstructed from the PDF; wording in the
> master Doc may differ by a word — search on the distinctive part). "REPLACE" = paste this.

## 1. Bibliography (do this first)

### 1a. Add the missing OMR reference
The OMR tool tested in §3.4 is **not in the bibliography**. Add this entry (IEEE style, matches the others). By order of first appearance it belongs at **[18]** (right after the diminished-reality refs [15]–[17], before DeGreg). If you use a reference manager, just insert the citation at the §3.4 location and let it renumber; if manual, insert as [18] and shift the current [18]–[27] to [19]–[28].

```
[18] J. C. Martinez-Sevilla, F. Foscarin, P. Garcia-Iasci, D. Rizo, J. Calvo-Zaragoza, and G. Widmer, "Optical Music Recognition of Jazz Lead Sheets," in Proc. 26th Int. Society for Music Information Retrieval Conf. (ISMIR), 2025. doi: 10.48550/arXiv.2509.05329.
```

### 1b. Fix the in-text citation (§3.4, p15)
**FIND:** `L'outil que nous avons testé est celui de Martinez-Sevilla et al. [15]`
**REPLACE:** `L'outil que nous avons testé est celui de Martinez-Sevilla et al. [18]`
*(use whatever number the new OMR entry gets; the point is it must NOT be [15], which is the diminished-reality review). Also fix the same wrong "[15]" in `rapport/omr-evaluation.md` line 114.*

### 1c. Fix mangled reference [17] (McLaughlin et al.)
**REPLACE the whole [17] entry with:**
```
[17] A. C. McLaughlin, M. Gandy Coleman, V. Byrne, R. Benton, F. Lodge, and T. Patten, "Cognitive Aid Design Using Diminished Reality to Support Selective Attention by Reducing Distraction," Human Factors, Mar. 2025. doi: 10.1177/00187208251325169.
```

### 1d. Fix reference [23] ("M. Field" is "Moffett Field" misparsed)
**REPLACE the whole [23] entry with:**
```
[23] S. G. Hart, "NASA-Task Load Index (NASA-TLX); 20 Years Later," in Proc. Human Factors and Ergonomics Society Annual Meeting, vol. 50, no. 9, 2006, pp. 904-908. doi: 10.1177/154193120605000909.
```

### 1e. Add authors to reference [11]
**REPLACE the whole [11] entry with:**
```
[11] J. A. Deja, S. Mayer, K. C. Pucihar, and M. Kljun, "A Survey of Augmented Piano Prototypes: Has Augmentation Improved Learning Experiences?," Proc. ACM Hum.-Comput. Interact., vol. 6, no. CSCW2, pp. 1-28, Nov. 2022. doi: 10.1145/3567719.
```

## 2. SQ1/SQ2 vs QR1/QR2 — make uniform (use SQ1/SQ2)

Four find/replace (keep standalone "la QR" = question de recherche mère if you like, but the *sub-questions* must be SQ):

1. **FIND:** `(QR1 prédit une baisse de la charge, QR2 une baisse de l'anxiété et une hausse de l'auto-efficacité)`
   **REPLACE:** `(SQ1 prédit une baisse de la charge, SQ2 une baisse de l'anxiété et une hausse de l'auto-efficacité)`
2. **FIND:** `deux sous-questions : la charge cognitive (QR1) et la barrière affective (QR2)`
   **REPLACE:** `deux sous-questions : la charge cognitive (SQ1) et la barrière affective (SQ2)`
3. **FIND:** `sur QR1, tout converge vers une charge allégée`
   **REPLACE:** `sur SQ1, tout converge vers une charge allégée`
4. **FIND:** `Sur QR2, le signal est plus faible`
   **REPLACE:** `Sur SQ2, le signal est plus faible`

*(Optional, for full consistency:* **FIND** `pour répondre à la QR` → **REPLACE** `pour répondre à la question de recherche`.*)*

## 3. Typos & grammar (find → replace)

| FIND | REPLACE |
|---|---|
| `Context` (TOC entry + body heading under "Interview avec un professeur") | `Contexte` |
| `Nous dérivons deux-sous questions` | `Nous dérivons deux sous-questions` |
| `franchir le pas.Nous pensons` (missing space) | `franchir le pas. Nous pensons` |
| `un projecteur placé au dessus un clavier MIDI` | `un projecteur placé au-dessus d'un clavier MIDI` |
| `un projecteur surmonté` | `un projecteur surplombant le clavier` |
| `Le système de Sandnens/Eika` (Figure 2 caption) | `Le système de Sandnes/Eika` |
| `préférablement droit pour plus facilement positionner le projecteur afin d'éloigner le projecteur des touches et d'élargir la tessiture projetée` | `préférablement droit : on positionne alors plus facilement le projecteur, en l'éloignant des touches pour élargir la tessiture projetée` |
| `Seulement pour le STAi-6` | `Seulement pour le STAI-6` |
| `les participants se sont senti moins distraits` | `les participants se sont sentis moins distraits` |

*(For "bleu" vs "bleu foncé" for the root: pick one. Recommend "bleu" everywhere, since the chord tones are already "bleu clair".)*

## 4. Figure renumbering (fills the missing 14, removes "4b"/"13b")

Relabel captions per this map, then update in-text "Figure N" references. **Do the renumber from the highest number downward (38 first) to avoid collisions.**

| Current caption label | → New |
|---|---|
| Figure 1 … Figure 12 | unchanged |
| **Figure 4b** (Pipeline logique de la codebase) | **Figure 13** |
| **Figure 13** (Dépendances d'import) | **Figure 14** |
| Figure 15 … Figure 21 | unchanged |
| **Figure 13b** (Boucle de jeu pygame) | **Figure 22** |
| Figure 22 (HUD) | Figure 23 |
| Figure 23 (calibration HUD) | Figure 24 |
| Figure 24 (grille iReal) | Figure 25 |
| Figure 25 (grille boucle) | Figure 26 |
| Figure 26 (projecteur homographie) | Figure 27 |
| Figure 27 (âge) | Figure 28 |
| Figure 28 (instruments) | Figure 29 |
| Figure 29 (expérience) | Figure 30 |
| Figure 30 (formation) | Figure 31 |
| Figure 31 (aisance) | Figure 32 |
| Figure 32 (réponses libres) | Figure 33 |
| Figure 33 (piano augmenté) | Figure 34 |
| Figure 34 (slope NASA-TLX) | Figure 35 |
| Figure 35 (médiane TLX/dimension) | Figure 36 |
| Figure 36 (slope STAI-6) | Figure 37 |
| Figure 37 (slope auto-efficacité) | Figure 38 |

Tables 1–8 are a separate sequence and stay unchanged.

## 5. Regenerate the Table of Contents
After moving the interview table to the annexe, the TOC tail is off by 7–8 pages. Right-click → Update Table (Word) / regenerate (Docs). Add an "Annexes" entry. Verify Conclusion lands on ~67, Bibliographie ~68.

## 6. Repetition cuts

### 6a. Delete the duplicated NASA-TLX sentence (p60)
The sentence *"Les participants P04 et P08 ont … pensé que la projection ajoutait une charge cognitive importante à leur improvisation"* appears **twice** (p59 and p60). Keep the first; replace the **second** occurrence (end of the barchart paragraph).
**FIND:** `Il semble donc que la projection aide, mais la tâche d'improvisation reste toutefois exigeante. Les participants P04 et P08 ont, au contraire, pensé que la projection ajoutait une charge cognitive importante à leur improvisation (nous y reviendrons dans le croisement des regards).`
**REPLACE:** `Il semble donc que la projection aide, mais la tâche d'improvisation reste toutefois exigeante.`

### 6b. Professor coverage (Table 2 + "Interview du professeur" + Croisement = 3×)
**Replace the entire "Interview du professeur" subsection** (heading through "… moments cadentiels.") with the condensed version below. It cuts ~40 %, stops re-quoting Table 2, and **folds in edit 7c** (so don't also apply 7c separately).

**REPLACE (whole subsection):**
> **Interview du professeur.** L'entretien est l'avis d'un seul expert, qui a vu la démonstration et échangé avec le concepteur : ce n'est pas une donnée mesurée mais une validation du cadrage, avec un risque de désirabilité. Nous le lisons comme un appui qualitatif, pas comme une preuve de l'effet. Le détail des verbatims et de leur analyse figure dans la Table 2 ; nous n'en retenons ici que ce qui pèse sur la question de recherche.
>
> Le thème central est la charge cognitive. Le professeur cherche lui-même à empêcher ses élèves de "trop réfléchir" en improvisant, autrement dit à réduire une forme de charge cognitive, et il voit dans l'artefact un moyen d'y arriver : suivre la couleur pour "juste jouer, puis se taire". Restons toutefois prudents : c'est nous qui avons formulé l'hypothèse, et le professeur y a souscrit ("c'est ce que je suis en train de dire à l'instant"). L'appui le plus convaincant ne vient donc pas de cet acquiescement, mais de sa formulation spontanée, antérieure à notre question. Nous y lisons une convergence sur l'orientation du travail, pas une confirmation de la baisse mesurée au NASA-TLX.
>
> Le professeur décrit un outil réglable, applicable à tout niveau pourvu qu'on en adapte la complexité (morceaux, tempo, jeux) : cela recoupe notre public débutant à intermédiaire tout en ouvrant la porte vers le haut (gammes de substitution pour les avancés). Il lui donne une légitimité pédagogique en l'ancrant dans les pédagogies alternatives (école Suzuki), où l'on sacrifie un paramètre pour en développer un autre beaucoup plus : l'artefact ne travaille donc qu'une partie de l'improvisation mélodique, mais c'est assumé.
>
> Côté critique, il pointe lui-même le contre-risque de surcharge : une nouvelle gamme à chaque accord peut être trop dense, et il propose des "gammes passe-partout" moins mobiles (idée explorée dans "The Blues Scales" [19]). Il juge le logiciel "bien foutu, mais très serré" et craint que les apprenants n'aient pas le temps de capter : le système devrait suivre le rythme de l'utilisateur, pas l'inverse. C'est un avertissement important, car un temps d'adaptation propre à chacun existe et notre protocole en une seule séance ne le laisse pas apparaître, point repris dans le croisement des regards. Enfin, sur le désétayage, il rejoint l'idée d'une aide faite pour être retirée : éteindre la lumière peu à peu, ou ne laisser allumées que les cadences (une variante du jeu du flux sur les turnarounds, avec gammes de substitution).

### 6c. Participant interviews (Quelques résultats + Interviews des participants = heavy overlap)
"Quelques résultats" (results section, p57–58) and "Interviews des participants" (interpretation, p61–62) both give the facilité/charge/confiance/sécurité counts, the "filet" quote, the P04/P08 reservations, the "petites roues" image and the 4-vs-4 auto-évaluation. **Keep the analysis in the interpretation pass and shrink "Quelques résultats" to a brief descriptive lead-in.**

**FIND** (the "Quelques résultats" paragraph, from "Quelques résultats Sur la table thématique…" through "…dans l'interprétation des résultats.")
**REPLACE:**
> **Quelques résultats.** Sur la table thématique, la lecture des couleurs donne d'emblée la tendance : la grande majorité des lignes ressort en vert, signe d'une attitude globalement favorable qui recoupe les trois questionnaires. Les réserves, en rouge, se concentrent sur deux participants, P04 et P08. Deux thématiques seulement basculent en rouge dominant : le partage de l'attention (le regard est soulagé, tout est sur le clavier, mais plusieurs craignent de moins s'écouter) et la rétention de la grille jouée, faible sur une séance unique. Plusieurs lignes restent blanches, donc descriptives (lisibilité, image du dispositif, améliorations souhaitées). Nous détaillons ces tendances, les comptages par thème et le cas de P04 et P08 dans l'interprétation des résultats ci-dessous.

*(All the detailed counts — facilité 6/8, charge 6/7, confiance 6/7, sécurité 6/8 + "filet", 3ᵉ essai 6/8 — plus "petites roues" and the 4-vs-4 auto-évaluation already live in "Interviews des participants", so nothing is lost.)*

### 6d. Caveat dedup (n=8 / non-significatif / désirabilité / confound)
The post-hoc level-split caveat is explained at near-full length in **three** places (Croisement, Discussion, Conclusion). Keep it full in the **Croisement**, shorten the **Discussion** to a back-reference, leave the **Conclusion**'s brief recap. Plus stop the verbatim "indicatif et sous-puissant (n = 8)" echoing across measures. The per-measure n.s. notes stay (one each is legitimate).

**6d-1 — shorten the Discussion's re-explanation (p66).** The Croisement already covers it in full just before.
**FIND:** `Toutefois, comme l'a montré le croisement des regards, ce résultat moyen recouvre deux populations : pour une partie des participants, les débutants à intermédiaires, le dispositif fonctionne nettement, là où les lecteurs de grille chevronnés vont à contre-sens. Cette lecture par profil reste cependant à confirmer : il faudrait découper la population et conduire un test sur chaque sous-groupe, ce que notre échantillon ne permet pas (quatre personnes par cellule). Nous la posons donc comme une piste pour une étude future mieux dimensionnée, point que nous reprendrons en conclusion. Elle appelle de toute façon la prudence, car elle est post-hoc et se confond avec l'ordre de passage et la difficulté des morceaux : c'est une tendance prometteuse, pas une preuve.`
**REPLACE:** `Toutefois, comme le détaille le croisement des regards, ce résultat moyen recouvre deux populations : le dispositif fonctionne nettement pour les débutants à intermédiaires, là où les lecteurs de grille chevronnés vont à contre-sens. Cette lecture par profil reste post-hoc et confondue avec l'ordre de passage et la difficulté des morceaux : une piste prometteuse pour une étude mieux dimensionnée (découpage par niveau, plusieurs séances), pas une preuve.`

**6d-2 — stop the verbatim "indicatif et sous-puissant (n = 8)" echo.** It closes both the STAI-6 and the auto-efficacité subsections; keep it on STAI-6, vary the auto-efficacité one.
**FIND:** `L'effet et les rangs vont dans le sens de H1, mais le résultat reste indicatif et sous-puissant (n = 8).`
**REPLACE:** `L'effet et les rangs vont dans le sens de H1, mais c'est ici le signal le plus ténu des trois : à ne tenir que pour une tendance.`

**6d-3 — leave the Conclusion's recap as-is** ("Une piste est apparue … mais elle reste post-hoc et confondue avec l'ordre et la difficulté des morceaux"). After 6d-1 the progression is full (Croisement) → short (Discussion) → one-line recap (Conclusion).

*(Judgment call: 6d-1 drops "quatre personnes par cellule" from the Discussion — that exact figure is already in the Croisement, so nothing is lost; restore it if you want the Discussion to keep a concrete number.)*

## 7. Soundness rewrites (before → after)

### 7a. "Défavorable au dispositif" — remove the special pleading (p64)
**FIND:** `Un point joue néanmoins en leur faveur : le protocole de test était plutôt défavorable au dispositif, car lorsqu'un écart de difficulté entre les deux morceaux inconnus était inévitable, nous avons confié le plus exigeant à la condition avec projection (26−2 pour P04, Giant Steps pour P08). Toutefois, il faut admettre que juger le niveau d'un morceau n'est pas une science exacte. Typiquement, le participant P08 a pensé que son morceau avec et sans était du même niveau !`
**REPLACE:** `Un facteur de confusion mérite d'être nommé : quand un écart de difficulté entre les deux morceaux inconnus était inévitable, le plus exigeant est parfois revenu à la condition avec projection (26−2 pour P04, Giant Steps pour P08). On pourrait y voir un protocole défavorable au dispositif, donc des effets sous-estimés, mais nous ne pouvons pas l'affirmer : juger le niveau d'un morceau n'est pas une science exacte, et P08 a d'ailleurs trouvé ses deux morceaux de difficulté équivalente. Cet écart joue donc dans les deux sens, il brouille la comparaison avec/sans pour ces deux participants plutôt qu'il ne la tranche en faveur de l'artefact.`

### 7b. "75 → 35" — say plainly it is descriptive, not tested (p59)
**FIND:** `le score passe de 75 à 35, cela semble fortement favoriser une réponse positive à notre sous-question 1.`
**REPLACE:** `le score passe de 75 à 35. C'est notre indice le plus parlant en faveur de la sous-question 1, mais il faut le lire pour ce qu'il est : une médiane descriptive sur une seule des six sous-échelles, que nous n'avons pas testée isolément (seul le score composite RTLX a été soumis au Wilcoxon, p = 0.25). Il illustre la tendance, il ne la démontre pas.`

### 7c. Professor "endorsement" — flag the led question (p41, Table 2 analysis / or the Interview du professeur prose)
**FIND:** `Le professeur partage l'hypothèse que ce système permet de réduire la charge cognitive. Combiné avec les 2 lignes de dessus, nous avons donc confirmé l'orientation principale de ce travail dans l'étude de la réduction de charge mentale pour aider l'improvisateur jazz.`
**REPLACE:** `Restons toutefois prudents : c'est nous qui avons formulé l'hypothèse de la charge cognitive, et le professeur y a souscrit ("c'est ce que je suis en train de dire à l'instant"). L'appui le plus convaincant ne vient donc pas de cet acquiescement, mais de sa formulation spontanée, antérieure à notre question ("tu suis la couleur, tu as moins de questions", "juste jouer, puis se taire"). Nous y lisons une convergence sur l'orientation du travail, pas une confirmation de l'effet.`

### 7d. r / p are not independent — add one clarifying sentence (Méthodologie statistique, end)
**INSERT after the paragraph defining "r":**
`Précisons que, pour un échantillon de cette taille, la statistique W, la valeur de p et la taille d'effet r sont calculées à partir des mêmes rangs. Un r moyen accompagné d'un p élevé n'est donc pas une confirmation indépendante : c'est une seule et même information, une tendance cohérente en direction mais trop petite pour être assurée.`

### 7e. (Optional) one sentence on directional H1 + two-sided p (Méthodologie statistique)
**INSERT after "nous retenons le p bilatéral …":**
`Nous gardons donc un test bilatéral tout en décrivant les résultats de façon directionnelle (part des participants et somme des rangs allant dans le sens de H1) : ces deux lectures ne se contredisent pas, la première borne la significativité, la seconde décrit l'orientation de l'effet.`

---

## Findings

> **TOP 3 to fix first (blockers / high-priority):**
> 1. 🔴 **Missing OMR reference + [15] collision.** "Martinez-Sevilla et al. [15]" (p15/16) points to bibliography entry [15], which is actually *Eskandari & Motamedi, "Observation-based diminished reality"*. The actual Martinez-Sevilla OMR paper is **absent from the bibliography entirely** (refs run [1]–[27], no OMR entry). Add the OMR paper as a new reference and fix the in-text citation number. Same wrong "[15]" in `omr-evaluation.md` line 114.
> 2. 🟠 **SQ1/SQ2 vs QR1/QR2 not uniform.** Intro (p4) + Conclusion (p67) use **SQ1/SQ2**; stats methodology (p46) and the Discussion paragraph (p66) use **QR1/QR2** (+ "répondre à la QR"). Pick one (SQ1/SQ2 matches intro, conclusion, and `question-de-recherche.md`) and replace globally.
> 3. 🟠 **Figure numbering broken.** No "Figure 14" (jumps 13→15); ad-hoc "Figure 4b" (p26) and "Figure 13b" (p35). Renumber 1..N and fix any in-text references.

---

## Évaluation — CONTENT & ARGUMENTATION review (2nd pass)

*Asked: (a) is there a lot of repetition? (b) are the points solid? Smallest doubts included.*

### (a) Repetition — yes, substantial. Structural, not just stylistic.

**Root cause:** the chapter covers the same small set of findings at four successive altitudes —
**Résultats** (tables + figure captions) → **Interprétation des résultats** (per-measure prose) →
**Croisement des regards** (synthesis) → **Discussion** → **Conclusion**. The same ~6 motifs recur
at every level. Motif counts inside the eval chapter (PDF p40–68):

| Motif | ≈ occurrences | Appears in |
|---|---|---|
| "P04 et P08" (the two reversers) | **13** (P04 alone 29, P08 27) | TLX/STAI/self-eff interp, Interviews participants, Croisement, Discussion, Conclusion |
| "à contre-sens" | 10 | same cluster |
| chevronné/aguerri/habitué (experienced-reader split) | 9 | Croisement, Discussion, Conclusion |
| béquille / petites roues de vélo / désétayage | 9 | Quelques résultats, Interviews participants, Interview prof, Conclusion |
| n = 8 / sous-puissant / non-significatif | ~8 | every interp subsection + Discussion + Conclusion |
| "exigence mentale 75 → 35" | 3 (p60, p67, p68) | TLX interp, Discussion, Conclusion |
| séance unique / temps humain / appropriation | ~11 combined | Interview prof, Interviews participants, Croisement |
| passe-partout | 4 | Interview prof (×2), Croisement, Conclusion |
| désirabilité / concepteur a mené les tests | 4 | Méthodo, Interview prof, Interviews participants, Croisement |

**Concrete redundancies to fix:**
- 🟠 **Literal near-duplicate sentence inside ONE subsection.** In the NASA-TLX interpretation, *"Les participants P04 et P08 ont, au contraire, pensé que la projection ajoutait une charge cognitive importante à leur improvisation"* appears **twice** — ending the slope-graph paragraph (p59) **and again** ending the barchart paragraph (p60, +"nous y reviendrons dans le croisement"). One of the two should go.
- 🟠 **The professor is analysed three times.** Table 2 "Analyse par thèmes" already has an *Analyse* column **and** a *Lien avec la QR* column (i.e. it already interprets every quote). Then "Interview du professeur" (p62–63) re-narrates the same quotes ("impétuosité", "se taire", Suzuki, "bien foutu mais serré", passe-partout, désétayage) in prose, and "Croisement des regards" invokes the professor a third time. The prose synthesis essentially restates Table 2. → Cut "Interview du professeur" down to what the **Croisement** needs, or make Table 2 purely descriptive (move interpretation out of it).
- 🟠 **Participants' interviews are covered three times in the body:** "Quelques résultats" (p57–58) → "Interviews des participants" (p61–62) → "Croisement des regards" (p63–66) — plus the full table in the annexe. The same lines ("filet", "petites roues", P02 "peur de moins anticiper", 4-vs-4 auto-évaluation) recur. → "Quelques résultats" and "Interviews des participants" overlap heavily; merge them, and let Croisement be the only synthesis.
- 🟠 **The caveat stack (n=8, non-significatif, post-hoc, ordre/difficulté confound, désirabilité) is restated ~5–6×.** Good instinct (honesty), but it can be stated once forcefully in the Croisement + once in the Discussion, then referenced. As written, nearly every subsection re-opens and re-closes with the same disclaimer.

**What's NOT objectionable repetition (keep):** Results-table → Interpretation split is legitimate; the figure captions restating "6/8 follow H1" is fine; Conclusion re-summarising headline numbers once is expected.

**Net:** the evaluation could lose an estimated 1–2 pages with no loss of content by (i) deduping the P04/P08 + caveat refrains, (ii) collapsing the professor's triple coverage, (iii) merging the two participant-interview passes.

### (b) Are the points solid? Mostly yes — the honesty is the chapter's strength — but specific soft spots:

- 🟠 **"Protocole défavorable au dispositif" is special pleading (p64).** The claim: because the *harder* of two pieces was given to AVEC for P04 & P08, the protocol handicapped the device, so the real effect is understated. But (1) it applies to only **2 of 8** participants; (2) the report immediately concedes *"juger le niveau d'un morceau n'est pas une science exacte"* and that **P08 thought both pieces were the same level** — which undercuts the premise that AVEC was reliably harder; (3) it contradicts the protocol's own rule (p45) that the pair should be *"plus ou moins la même difficulté"*. You can't lean on "we deliberately gave AVEC the harder tune" *and* "we couldn't judge difficulty." A difficulty mismatch is a **two-way confound**, not a one-way handicap. Recommend softening from "défavorable au dispositif" to "a confound we cannot sign."
- 🟠 **The headline "exigence mentale 75 → 35" carries more weight than its analysis supports.** It is a **descriptive median of one of six subscales**, never tested (only the composite RTLX was Wilcoxon-tested, p=.25 n.s.). Per-subscale testing would also raise multiple-comparison issues. It's the emotional core of the SQ1 claim and is repeated 3×, yet it's the *least* formal number in the chapter. Keep it (it's hedged with "semble"), but don't let it read as the proof of SQ1 — it's a suggestive descriptive.
- 🟡 **r / rank-sums / W / p are treated as semi-independent corroboration; they are the same information.** E.g. self-eff (p61): "p est élevée … mais l'effet et les rangs vont dans le sens de H1." At n≤8 the rank-biserial r, the T⁺/T⁻ split and the p-value are all computed from the identical ranks — a "medium r with high p" is one fact ("consistent direction, too small to confirm"), not two. The report mostly says this ("tempérer la lecture de r"), but the phrasing in places stacks r + ranks + median as if they were separate witnesses. Tighten so r isn't read as evidence *additional* to p.
- 🟠 **The professor's "endorsement" of SQ1 partly rests on a led exchange.** The strongest quote is: [ETUDIANT] states *"l'hypothèse … c'est qu'en faisant ça, on réduit … la charge cognitive"* → [PROFESSEUR] *"C'est ce que je suis en train de dire à l'instant."* The author introduced the hypothesis; the professor agreed. Reporting this as *"nous avons confirmé l'orientation principale"* (p41) overstates it. The professor's *own* unsolicited framing ("tu suis la couleur … se taire", "ta gueule dedans") is the real evidence; the "c'est ce que je dis" line is confirmation bias and should be presented as such, not as independent endorsement. (The chapter does flag desirability bias generally — but not for this specific exchange.)
- 🔵 **Directional H1 + two-sided p, mixed framing.** Using the two-sided p (conservative) is fine and the report says it changes nothing. But it then argues throughout in directional terms ("6/8 follow H1", "rangs en faveur de H1"). That's not wrong, just be aware a stats-minded reader sees directional effect-size talk wrapped around a non-directional test. One sentence acknowledging this would pre-empt the question.
- 🔵 **Self-efficacy median moves *against* H1 (4.4→4.2)** while r is +0.36. The report handles this correctly (median≠effect size) and concludes self-eff is the weakest measure — solid. Just the cleanest example of why r-vs-median needs the careful wording above.
- 🔵 **"Temps humain" / single-session adaptation** is the load-bearing explanation for why experienced readers reversed, but it is unfalsifiable within a one-session design and is asserted by the author, the professor, *and* read into the participants. It's correctly posed as future work, but it currently does a lot of explanatory work for an untestable claim — keep it clearly hypothetical.
- ✅ **Genuinely solid:** no significance is ever overclaimed; the SQ1-strong / SQ2-weak ordering matches the data; confounds (order, difficulty, desirability, n=8) are disclosed; qual and quant are cross-checked rather than cherry-picked; the level-split is explicitly labelled post-hoc and non-probant. This is the right posture for n=8 — the soft spots above are about *over-leaning* on a few favourable readings, not about dishonesty.

### Ch.5 Évaluation — stats verification (running)

**All quantitative results recomputed from `rapport/stats/data/` and confirmed:**
- ✅ **NASA-TLX** Table 3 composites match `scores_tableur.csv` exactly (all 8 × 2). T⁺=9, T⁻=27, W=9, r_rb=−0.5, p_uni=.125, p_bi=.250, 6/8 follow H1. Medians 33.3/54.2. All correct.
- ✅ **STAI-6** recomputed: diffs → W=10, T⁺=10/T⁻=26, r_rb=−0.44, 5/8 follow H1, Mdn 33.3/46.7. Matches `wilcoxon_summary.md`.
- ✅ **Self-efficacy** recomputed: P03 is a true tie (0), effective n=7, 4/7 follow H1, T⁺=19/T⁻=9, W=9, r_rb=+0.357≈+0.36, Mdn 4.25/4.375≈4.4. Matches.
- ✅ **p-bilateral choice is internally consistent**: stated p47 ("nous retenons le p bilatéral") and applied p52 (Table 4 retains 0.25, gives 0.125 "à titre indicatif"). Well-justified (overload risk + P04/P08 reversers). Defensible and honest. *Verify STAI-6/self-eff tables apply the same rule.*
- ✅ **Profile figures 27–33** all match `q0_profil.csv`: ages 19–64 median **24.5** (caption correct), 5/8 piano, jazz 0–20 yrs, piano 1–30 yrs, 7/8 conservatory + 1 private, 0/8 prior augmented-piano, 0/8 daltonien. STAI-6 scoring (reverse 1/4/5, ×20/6) and self-eff (mean Q7–10, Q11 unused) are standard and correctly described.

**Évaluation — interpretation & interviews (verified against data):**
- ✅ STAI-6 interp: r=0.44, p=0.31 (bilat, exact), rank sums 26 (H1) vs 10, P01/P06 strongest & most anxious SANS, P04 increase = P03/P05 decreases (all 30) — all recomputed correct.
- ✅ Self-eff interp: r=0.36, p=0.47, median 4.4→4.2 (against H1), 4 gain (P01/P02/P05/P06), 3 lose (P04/P07/P08), P03 identical 2.25, P06 jumps 2.5→6.25, rank sums 19 vs 9 — all correct.
- ✅ TLX subscales (Fig 35) recomputed from `tlx_items_tableur.csv`: mental 75→35 (claim exact), all 6 subscales lower AVEC; effort 70→50 ("reste élevé" ✓). Performance note (low=success) correct.
- ✅ Qual claims verified vs `q0_profil.csv`/`responses.csv`: P07 = 20 yrs jazz & 5/7 ✓; P04/P08 ages 58/64 ✓; **P04 AVEC="26-2", P08 AVEC="Giant Steps"** ✓ (both hardest); order counterbalanced 4-4.
- 🔵 **P08 difficulty mismatch (already disclosed):** P08's AVEC piece (Giant Steps, level "P") is harder than the SANS piece (There Will Never Be Another You, level "M"), unlike the protocol's "paire … même difficulté". The interpretation **does** flag this as a confound ("morceaux les plus exigeants … en condition avec"), so it's handled — just be aware a careful reader/jury may note the protocol-vs-execution gap. P04's pair (26-2 / Giant Steps) is matched (both "P").
- ✅ Qual/quant coherence is strong and honestly hedged: P04/P08 reverse on all three; P07 reverses on STAI-6 & self-eff but stays favorable in interview; desirability bias disclosed (concepteur ran the tests). This is a model of honest small-n reporting.

### Front matter & TOC (PDF p1–3)

- 🟡 **TOC: English "Context" instead of "Contexte"** (p3 PDF, interview subsection). The body heading should also be checked. → *verify in body.*
- 🟡 **TOC: "Discussion 73" and "Conclusion 73" on the same page.** Discussion is listed as a sub-item but visually collides with Conclusion. Confirm Discussion is meant to be its own subsection vs. folded into Conclusion. → *verify in body p73.*
- 🔵 Title page date "26 Juin 2026" vs. memory's deadline 2026-06-24. Likely the defense/submission date — not flagging unless wrong.

- 🟠 **TOC PAGE NUMBERS ARE STALE for the whole tail (from "Interprétation des résultats" on).** Verified offsets:
  | Section | TOC says | Actual printed page | Off by |
  |---|---|---|---|
  | Interprétation des résultats | 66 | **58** | +8 |
  | Croisement des regards | 70 | **63** | +7 |
  | Discussion | 73 | **66** | +7 |
  | Conclusion | 73 | **66–67** | +7 |
  | Bibliographie | 75 | **68** | +7 |
  Everything *through* "Interviews semi-structurées … 57" is correct; the drift begins exactly at "Interprétation des résultats". Almost certainly because the ~9-page participant-interview thematic table was inline in the body when the TOC was generated, then moved to the Annexe (now p72–80) without regenerating the TOC. **Fix: regenerate the table of contents.** (Also: TOC has no entry for "Annexes", which is p70+.)

### Ch.6 Discussion & Conclusion (PDF p67–68)
- ✅ Honest, well-argued, consistent with the verified results (mental 75→35, r=0.50/0.44/0.36, none significant, post-hoc level-split flagged as a future-work hypothesis). Strong close.
- 🟠 **SQ/QR label mixing lands here:** Discussion's opening sentence uses "(QR1)…(QR2)" and "répondre à la QR", while the Conclusion right below uses "(SQ1)…(SQ2)". Uniformize (see Top-3 #2).
- 🔵 Discussion is a single tight paragraph — fine for this report's scope; just confirm the supervisor didn't expect a longer standalone Discussion (the cross-analysis already lives in "Croisement des regards").

### Bibliography (PDF p69–70) — refs [1]–[27]
- 🔴 **No Martinez-Sevilla OMR entry at all** (see Top-3 #1). [15] = "R. Eskandari and A. Motamedi, Observation-based diminished reality: a systematic literature review, Virtual Real. 2024". Add the OMR paper and fix the in-text "[15]".
- 🟠 **[17] author list is mangled:** "A. C. M. Patten Maribeth Gandy Coleman,Vicky Byrne,Rachel Benton,Frank Lodge,Trevor, 'Cognitive Aid Design Using Diminished Reality…'". Names are scrambled (first author should be A. C. McLaughlin; "Trevor Patten" split apart) and the title field has the whole author list + "2025" embedded. Clearly a citation-manager import error — clean it up.
- 🟠 **[23] NASA-TLX citation looks wrong:** "S. G. Hart and M. Field, 'NASA-TASK LOAD INDEX (NASA-TLX); 20 YEARS LATER'" — no year/venue, and **"M. Field" is almost certainly "Moffett Field"** (NASA Ames location) misparsed as a second author. Correct to Hart, S. G. (2006), *Proc. Human Factors and Ergonomics Society 50th Annual Meeting*, pp. 904–908.
- 🟡 **[11] has no authors** in the reference (just title + ACM URL), although the in-text [11] correctly names Deja, Mayer, Pucihar, Kljun. Add the author list to the entry.
- 🔵 Source-quality: STAI-6 scoring cites Scribd [24]; Wilcoxon cites Wikipedia [21]; several MetricGate/online-calculator links [20][22][25][26]. Defensible given the "auditable hand-calc" methodology, but the jury may prefer primary sources — at least swap [24] for Marteau & Bekker (1992) for the STAI-6 short form. Not an error.
- 🔵 Diacritics dropped on some names (Pucihar/Kljun in-text); biblio entries vary. Minor consistency.

### Annexes (PDF p71–94) — complete
- ✅ Present and well-structured: full participant interview thematic table (p72–80), professor interview guide (p81–84), participant roadmap (p85), consent form (p86), Q0 initial questionnaire + tune-familiarity grid (p87–88), Q1A/Q2A + Q1B/Q2B NASA-TLX & "Assurance" forms (p89–92), Q3 semi-structured interview guide (p93–94). Matches the protocol and `append_annexes.py` insertion plan.
- ✅ STAI-6 items (calme/tendu/ému/décontracté/satisfait/inquiet → reverse 1/4/5) and self-eff Q7–10 + confirmation Q11 in the forms match the scoring described in §5 and the `responses.csv` column layout.
- ✅ Annex p73 confirms "le morceau de la condition avec … était 26−2" for P04 — matches `responses.csv`.

### Ch.1 Introduction (PDF p4–5)

Strong, in-voice, no em-dashes, SQ1/SQ2 used consistently here. Minor:

- 🟡 **"Nous dérivons deux-sous questions"** (p5) → should be "deux sous-questions" (hyphen is misplaced).
- 🟡 **Missing space: "franchir le pas.Nous pensons"** (p5) — no space after the period.
- 🔵 **SQ1/SQ2 vs QR1/QR2 consistency** — CLAUDE.md flags that the Discussion uses QR1/QR2 while the intro uses SQ1/SQ2. Intro confirmed to use SQ1/SQ2. → *must verify Discussion (p73) and Évaluation framing use the same labels.*
- 🔵 Problématique hedges nicely ("en tout cas, nous le supposons") — consistent with stats-honesty voice. Good.

### Ch.2 État de l'art (PDF p6–10)

Content solid; covers the 6 pedagogical frameworks (Spice), Chyu thesis, the Deja et al. 2022 literature review, Sandnes/Eika, the Deja piano-roll system (do-major-only weakness is the key justification for "toutes tonalités"), the 2005 ISS, and diminished reality (cognitive load). Issues:

- 🟠 **Author name inconsistency "Sandnens" vs "Sandnes"** — Figure 2 caption (p12) reads "Le système de Sandnens/Eika" but the body text on the same page and p9 reads "Sandnes". Fix the caption to "Sandnes".
- 🟡 **"un projecteur placé au dessus un clavier MIDI"** (p9) → "au-dessus d'un clavier MIDI" (missing hyphen + "d'").
- 🟡 **"un projecteur surmonté"** (p11) — "surmonté" means *topped by*, wrong sense; should be "surplombant" / "monté au-dessus".
- 🔵 Author names without diacritics: "Klen Pucihar", "Matjaz Kljun" (correct: Klen Čopič Pucihar, Matjaž Kljun). Acceptable in FR prose but be consistent with the bibliography. → *cross-check biblio.*
- 🔵 "les participants se sont senti moins distraits" (p10) → agreement "sentis". Minor.

### Ch.3 Solution conceptuelle (PDF p11–24)

#### Concept / overview (p11–15)
- 🟠 **Repetitive sentence (p14):** "préférablement droit pour plus facilement positionner le projecteur afin d'éloigner le projecteur des touches et d'élargir la tessiture projetée" — "le projecteur" appears twice in one clause and the sentence runs on. Rephrase.
- 🟡 Confirmation example, .tsv-by-hand-or-LLM workflow, dark-room diminished reality: all coherent and on-message.

#### OMR section §3.4 (p15–18) — cross-checked against `omr-evaluation.md` and figure scripts
- ✅ **Numbers verified:** 11 standards; mean weighted precision 44/100; "jusqu'à 42 temps d'écart sur Oleo" matches the table (Oleo Δ −42, the largest); substitution cost 0.10 (triad↔seventh) → 1.0 (wrong root) matches the barème.
- ✅ **ATTYA Figure 8 example verified** against [omr_alignment.py](rapport/figures/solution-conceptuelle/omr_alignment.py): ref Fm7 read as F7 / F:maj (text cites F7/Fmaj → dorien/mixolydien/ionien, correct), and Db:maj7 → D:maj7. Sound.
- 🔴 **REFERENCE [15] COLLISION (p16).** "L'outil que nous avons testé est celui de Martinez-Sevilla et al. [15]" reuses citation **[15]**, which on p9–10 is the 2024 diminished-reality literature review. The Martinez-Sevilla OMR tool needs its **own** reference number. NOTE: `omr-evaluation.md` line 114 carries the same erroneous "[15]". → **Must fix in body + biblio.** *Verify final biblio numbering.*
- 🔵 OMR raw data (`JM_MIR_*`, `GT_MIR_*`, `REPORT_*`, `evaluate_custom`) is **not in this repo** — only the derived figures/table are. Aggregate + example claims verified via `omr-evaluation.md` + figure scripts, which is sufficient, but the primary data isn't reproducible from this checkout.

#### 5 exercises + projection design (p20–24) — cross-checked against `exercises/` code
- ✅ **All 5 colors verified in code:** scale=green `(60,220,90)` [free.py], root=blue `(60,130,255)` [root.py], chord tones=light blue `(100,200,255)` [chord_tones.py], guide tone/start=red `(255,50,50)` [guide_tone.py, start_end.py], target/end=orange `(255,140,40)` [start_end.py]. Report's color vocabulary (vert/bleu/bleu clair/rouge/orange + hachuré for out-of-scale) matches exactly.
- ✅ RangeMode description (complet / main droite from middle-C / 1-2 oct ascending run) matches `free.py` (FULL/RIGHT_HAND/TWO_OCTAVE/ONE_OCTAVE). Anticipation (croche/noire, constant across tempo) matches code.
- 🔵 Category assignments (contour=cat6, flux=cat6, guide tone=cat2, début/fin=cat6, libre=cat1) are the author's own framework mapping — internally consistent. Fine.
- 🟡 **Reference [18] = Phil DeGreg** confirmed (p25). This *closes off* [18] for OMR, so the OMR's "[15]" really is a duplicate that needs its own (new highest) number. → reinforces the 🔴 above.

#### Backing track / réglage / grille iReal (p23–25)
- ✅ "4 buffers (métronome, batterie, basse, comping guitare)" + conditional limiter matches the per-layer renderer + `mix_layers`. Drop-2/drop-3 voicings, DeGreg rhythms, loop-practice with regenerated backing all match code/CLAUDE.md.
- ✅ Test-condition framing is correct & important: SANS keeps the iReal chart + backing track, removes only projection — matches the within-subject AVEC/SANS stats design.
- 🔵 Fig.12 caption "F ionien est anticipé alors que la grille est sur Gbmaj7" — anticipation showing next chord (Fmaj7 after Gbmaj7, descending half-step). Plausible; depends on the tune shown. Not flagging.

### Ch.4 Solution technique (PDF p25–38)

#### 🟠 FIGURE NUMBERING IS INCONSISTENT (whole chapter)
Full observed order of float labels:
`Fig 1,2,3,4,5,6,7,8,9,10,11,12, [Fig 4b], 13, Table 1, [Fig 15], 16,17,18,19,20,21, [Fig 13b], 22,23,24,25,26, Table 2, 27…37, Table 3–8`
- 🟠 **No "Figure 14".** Sequence jumps from Figure 13 (p27) straight to Figure 15 (p30). A reader following figure numbers hits a gap.
- 🟠 **"Figure 4b"** (p26, pipeline logique) and **"Figure 13b"** (p35, pygame game loop) are ad-hoc "b" insertions that break the 1..N scheme. "Figure 4b" is conceptually unrelated to Figure 4 (Schéma du système); "Figure 13b" unrelated to Figure 13 (Dépendances d'import). Looks like leftover from a renumber.
- **Recommendation:** renumber all floats sequentially (1..N), fold 4b/13b into the sequence, eliminate the missing-14 gap. Also check in-text figure references point to the right numbers after renumber.

#### Prose / content (p25–30)
- ✅ Architecture description (timeline via `perf_counter`, pipeline pur entrée→sortie, dataclasses frozen for TDD, harmony cascade with chain pre-pass for ii-V / I-vi-ii-V / ii-V-i mineur) matches `harmony/core.py` design in CLAUDE.md.
- 🔵 "module fait-maison ... arithmétique mod-12" and tools table (pygame-ce, FluidSynth, OpenCV, numpy, Poetry, pytest, ruff) all accurate.
- 🟡 Tools table mentions TDD "avec l'aide d'outils IA agentiques comme Claude Code" (p27) — fine to keep, just confirm the author wants this disclosed in the thesis body.

#### Backing / audio / overlays / calibration / loop (p30–37) — cross-checked against code
- ✅ **Drum pattern verified** against [events.py](src/leadsheet_utility/backing/events.py): ride on every beat, skip on the "and" of 2&4, hi-hat pedal on 2&4, soft kick on beat 1, ~25% ghost snares on swung offbeats. All correct.
- ✅ Walking-bass description (root on 1, scale/chord tones on inner beats, approach note on beat 4 targeting next root, 1-2 bar direction arcs) matches `walking_bass.py`.
- ✅ Comping (drop-2/drop-3, nearest voice-leading, DeGreg rhythms, anticipations, humanize) ✓; 4-layer parallel render + 2-bar count-in + conditional limiter ✓; 5-phase calibration ✓; 60 FPS single-thread loop steps ✓.
- 🟡 **Root called "bleu foncé" (p32 overlay chain)** but "bleu" earlier (p21). Code root=`(60,130,255)` (saturated blue, darker than the `(100,200,255)` chord-tone light-blue). Consistent enough but pick one descriptor.
- 🔵 "le skip sur le 2 et 4" (p30) is slightly loose — the skip note lands on the *swung "and"* of 2 and 4 (code: `skip_beat = beat + swing_ratio`), not on 2/4 themselves. Common shorthand; optionally tighten.
- 🔵 "secondes × tempo donne le beat" (p35) — loose (beat = seconds × BPM/60). High-level description, fine but technically imprecise.
- ✅ Honest chart limitation noted: no section data → no DS al coda / repeat signs (p37). Good.







