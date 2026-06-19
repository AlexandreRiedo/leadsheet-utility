# Plan du classeur Google Sheets — saisie → export CSV

Ce classeur est la **surface de saisie** des tests utilisateurs : on y saisit les valeurs
brutes des questionnaires, on calcule les scores composites + le Wilcoxon (à la main +
calculateur en ligne), puis on **exporte des CSV** que les scripts Python lisent pour tracer
les figures. Le classeur lui-même ne fait pas partie du dépôt — seuls les CSV exportés (dans
`data/`) y entrent.

## Qui lit quoi

| Onglet | Export (`data/…`) | Consommé par |
|---|---|---|
| `raw` | `responses.csv` | `analyze_tests.py` (recoupement) |
| `scores_tableur` | `scores_tableur.csv` | **`present.py`** — slope plots ×3 |
| `tlx_items_tableur` | `tlx_items_tableur.csv` | **`present.py`** — figure par dimension |
| `q0_profil` | `q0_profil.csv` | tableau descriptif (à la main) |
| `wilcoxon_nasaTLX` · `wilcoxon_STAI` · `wilcoxon_SELFEFF` | *(pas d'export)* | calculateur en ligne + report W/p/r_rb |

`present.py` ne (re)calcule rien : il dessine les valeurs déjà saisies. Les scores composites
et le test sont la **source de vérité faite à la main** (cf. `README.md` + `../guide-interpretation-stats.md`).

## Règle d'ordre des lignes (à respecter)

Dans `raw`, **AVEC est toujours la 1ʳᵉ ligne de chaque paire** (lignes paires 2, 4, 6 … 16),
**SANS la 2ᵉ** (lignes impaires 3, 5 … 17) — *quel que soit l'ordre réellement joué*. La
colonne `ordre` (1 / 2) note, elle, l'ordre réel de la séance. Aucun script ne lit `ordre` :
c'est de la métadonnée. Les formules `scores_tableur` reposent sur cette disposition fixe ; si
une paire est saisie SANS en premier, AVEC et SANS sont **silencieusement inversés** pour ce
participant. Vérifier après saisie que chaque `RTLX_AVEC` correspond bien à la ligne `condition = AVEC`.

---

## 1. Onglet `raw` — saisie des valeurs brutes (16 lignes)

**Import** `data/responses.csv` (File → Import → Replace), ou coller en **A1** puis
Data → Split text to columns → Comma :

```
participant,niveau,morceau,condition,ordre,tlx_mental,tlx_physique,tlx_temporel,tlx_perf,tlx_effort,tlx_frustration,stai_calme,stai_tendu,stai_emu,stai_decontracte,stai_satisfait,stai_inquiet,se_q7,se_q8,se_q9,se_q10,conf_globale_q11
```

Saisir les **valeurs brutes** uniquement (TLX 0–100 par pas de 5, Performance **non inversée** ;
STAI 1–4, **non inversé** ; se 1–7 ; q11 0–10). Cellule vide = pas encore saisie (ignorée en aval).

Repères de colonnes (utilisés par les formules ci-dessous) :

| Bloc | Colonnes |
|---|---|
| contexte | A `participant` · B `niveau` · C `morceau` · D `condition` · E `ordre` |
| NASA-TLX (6) | **F:K** (mental, physique, temporel, perf, effort, frustration) |
| STAI-6 (6) | L `calme` · M `tendu` · N `emu` · O `decontracte` · P `satisfait` · Q `inquiet` |
| auto-efficacité (4) | **R:U** (se_q7 … se_q10) · V `conf_globale_q11` |

---

## 2. Onglet `scores_tableur` — composites (8 lignes) · **= export**

En-tête en **A1** (comma-split) :

```
participant,RTLX_AVEC,RTLX_SANS,STAI6_AVEC,STAI6_SANS,SELFEFF_AVEC,SELFEFF_SANS
```

Coller chaque bloc dans la **cellule du haut de sa colonne** (remplit les lignes 2–9). AVEC tire
les lignes **paires** de `raw` (2, 4 … 16), SANS les **impaires** (3, 5 … 17) — d'où le saut de 2.

**A2** — participant
```
=raw!A2
=raw!A4
=raw!A6
=raw!A8
=raw!A10
=raw!A12
=raw!A14
=raw!A16
```
**B2** — RTLX_AVEC · moyenne TLX (F:K)
```
=IFERROR(AVERAGE(raw!F2:K2),"")
=IFERROR(AVERAGE(raw!F4:K4),"")
=IFERROR(AVERAGE(raw!F6:K6),"")
=IFERROR(AVERAGE(raw!F8:K8),"")
=IFERROR(AVERAGE(raw!F10:K10),"")
=IFERROR(AVERAGE(raw!F12:K12),"")
=IFERROR(AVERAGE(raw!F14:K14),"")
=IFERROR(AVERAGE(raw!F16:K16),"")
```
**C2** — RTLX_SANS
```
=IFERROR(AVERAGE(raw!F3:K3),"")
=IFERROR(AVERAGE(raw!F5:K5),"")
=IFERROR(AVERAGE(raw!F7:K7),"")
=IFERROR(AVERAGE(raw!F9:K9),"")
=IFERROR(AVERAGE(raw!F11:K11),"")
=IFERROR(AVERAGE(raw!F13:K13),"")
=IFERROR(AVERAGE(raw!F15:K15),"")
=IFERROR(AVERAGE(raw!F17:K17),"")
```
**D2** — STAI6_AVEC · inversion calme/décontracté/satisfait (`5−x`) puis ×20/6
```
=IF(raw!L2="","",((5-raw!L2)+(5-raw!O2)+(5-raw!P2)+raw!M2+raw!N2+raw!Q2)*20/6)
=IF(raw!L4="","",((5-raw!L4)+(5-raw!O4)+(5-raw!P4)+raw!M4+raw!N4+raw!Q4)*20/6)
=IF(raw!L6="","",((5-raw!L6)+(5-raw!O6)+(5-raw!P6)+raw!M6+raw!N6+raw!Q6)*20/6)
=IF(raw!L8="","",((5-raw!L8)+(5-raw!O8)+(5-raw!P8)+raw!M8+raw!N8+raw!Q8)*20/6)
=IF(raw!L10="","",((5-raw!L10)+(5-raw!O10)+(5-raw!P10)+raw!M10+raw!N10+raw!Q10)*20/6)
=IF(raw!L12="","",((5-raw!L12)+(5-raw!O12)+(5-raw!P12)+raw!M12+raw!N12+raw!Q12)*20/6)
=IF(raw!L14="","",((5-raw!L14)+(5-raw!O14)+(5-raw!P14)+raw!M14+raw!N14+raw!Q14)*20/6)
=IF(raw!L16="","",((5-raw!L16)+(5-raw!O16)+(5-raw!P16)+raw!M16+raw!N16+raw!Q16)*20/6)
```
**E2** — STAI6_SANS
```
=IF(raw!L3="","",((5-raw!L3)+(5-raw!O3)+(5-raw!P3)+raw!M3+raw!N3+raw!Q3)*20/6)
=IF(raw!L5="","",((5-raw!L5)+(5-raw!O5)+(5-raw!P5)+raw!M5+raw!N5+raw!Q5)*20/6)
=IF(raw!L7="","",((5-raw!L7)+(5-raw!O7)+(5-raw!P7)+raw!M7+raw!N7+raw!Q7)*20/6)
=IF(raw!L9="","",((5-raw!L9)+(5-raw!O9)+(5-raw!P9)+raw!M9+raw!N9+raw!Q9)*20/6)
=IF(raw!L11="","",((5-raw!L11)+(5-raw!O11)+(5-raw!P11)+raw!M11+raw!N11+raw!Q11)*20/6)
=IF(raw!L13="","",((5-raw!L13)+(5-raw!O13)+(5-raw!P13)+raw!M13+raw!N13+raw!Q13)*20/6)
=IF(raw!L15="","",((5-raw!L15)+(5-raw!O15)+(5-raw!P15)+raw!M15+raw!N15+raw!Q15)*20/6)
=IF(raw!L17="","",((5-raw!L17)+(5-raw!O17)+(5-raw!P17)+raw!M17+raw!N17+raw!Q17)*20/6)
```
**F2** — SELFEFF_AVEC · moyenne se_q7..q10 (R:U)
```
=IFERROR(AVERAGE(raw!R2:U2),"")
=IFERROR(AVERAGE(raw!R4:U4),"")
=IFERROR(AVERAGE(raw!R6:U6),"")
=IFERROR(AVERAGE(raw!R8:U8),"")
=IFERROR(AVERAGE(raw!R10:U10),"")
=IFERROR(AVERAGE(raw!R12:U12),"")
=IFERROR(AVERAGE(raw!R14:U14),"")
=IFERROR(AVERAGE(raw!R16:U16),"")
```
**G2** — SELFEFF_SANS
```
=IFERROR(AVERAGE(raw!R3:U3),"")
=IFERROR(AVERAGE(raw!R5:U5),"")
=IFERROR(AVERAGE(raw!R7:U7),"")
=IFERROR(AVERAGE(raw!R9:U9),"")
=IFERROR(AVERAGE(raw!R11:U11),"")
=IFERROR(AVERAGE(raw!R13:U13),"")
=IFERROR(AVERAGE(raw!R15:U15),"")
=IFERROR(AVERAGE(raw!R17:U17),"")
```

> **Alternative à l'épreuve de l'ordre (si la règle de disposition gêne).** Ajouter à `raw` 3
> colonnes-relais par ligne — X `=IFERROR(AVERAGE(F2:K2),"")`, Y `=IF(L2="","",((5-L2)+(5-O2)+(5-P2)+M2+N2+Q2)*20/6)`,
> Z `=IFERROR(AVERAGE(R2:U2),"")` (tirées jusqu'à 17) — puis, dans `scores_tableur` (taper P01..P08 en A2:A9) :
> `=IFERROR(AVERAGEIFS(raw!$X$2:$X$17,raw!$A$2:$A$17,$A2,raw!$D$2:$D$17,"AVEC"),"")` (Y→STAI6, Z→SELFEFF ;
> "SANS" pour l'autre colonne). Cherche par participant + condition → insensible à l'ordre des lignes.

---

## 3. Onglets `wilcoxon_*` — un par mesure (3 onglets)

Trois onglets **identiques en structure**, un par mesure : `wilcoxon_nasaTLX`,
`wilcoxon_STAI`, `wilcoxon_SELFEFF`. Chacun (a) tire ses paires depuis `scores_tableur`,
(b) calcule W, T+/T−, r_rb tout seul, (c) reçoit le **p** lu sur le calculateur en ligne.
**La seule chose à taper à la main = la cellule jaune `p` (B20).** Tout le reste est formule.

### Gabarit d'un onglet (exemple `wilcoxon_nasaTLX`)

| Cellule | Contenu (texte à taper) |
|---|---|
| **A1** | `WILCOXON — NASA-TLX (RTLX) — charge cognitive` |
| **A2** | `H1 : AVEC < SANS   ·   calculateur : alternative = less   ·   mode EXACT` |

En-tête en **A4** : `participant · AVEC · SANS · d=AVEC−SANS · |d| · rang`

**Données (lignes 5–12)** — coller dans la cellule du haut, puis tirer jusqu'à la ligne 12 :
```
A5:  =scores_tableur!A2
B5:  =scores_tableur!B2
C5:  =scores_tableur!C2
D5:  =IF(OR(B5="",C5=""),"",B5-C5)
E5:  =IF(D5="","",ABS(D5))
F5:  =IF(OR(D5="",D5=0),"",RANK.AVG(E5,$E$5:$E$12))
```

**Synthèse (se calcule seule)** — libellé en colonne A, formule en colonne B :
```
A14 T+               B14: =SUMIF(D5:D12,">0",F5:F12)
A15 T−               B15: =SUMIF(D5:D12,"<0",F5:F12)
A16 W                B16: =MIN(B14,B15)
A17 n effectif       B17: =COUNT(F5:F12)
A18 r (rang-bisér.)  B18: =(B14-B15)/(B14+B15)
```

**Saisie manuelle (★ surligner B20 en jaune)** :
```
A20 p unilatéral     B20: ← COLLER la valeur lue sur le calculateur
A21 p bilatéral      B21: =B20*2
```

### Procédure (mêmes 3 étapes pour les 3 onglets)
1. Les colonnes AVEC/SANS se remplissent seules depuis `scores_tableur`.
2. Copier **AVEC (B5:B12)** et **SANS (C5:C12)** dans le calculateur en ligne (échantillons
   appariés, **mode exact**, `alternative` indiquée en A2). Contrôle : le **W du calculateur
   doit = B16** ; sinon une paire est inversée (cf. règle d'ordre §1).
3. Lire **p**, le saisir en **B20**.

### Ce qui change d'un onglet à l'autre (seulement 3 choses)

| Onglet | B5 (AVEC) | C5 (SANS) | A2 : H1 / alternative |
|---|---|---|---|
| `wilcoxon_nasaTLX` | `=scores_tableur!B2` | `=scores_tableur!C2` | AVEC < SANS / **less** |
| `wilcoxon_STAI` | `=scores_tableur!D2` | `=scores_tableur!E2` | AVEC < SANS / **less** |
| `wilcoxon_SELFEFF` | `=scores_tableur!F2` | `=scores_tableur!G2` | AVEC > SANS / **greater** ⚠️ |

---

## 4. Onglet `tlx_items_tableur` — vue « format long » de `raw` (16 lignes) · **= export**

> **Tu ne tapes RIEN dans cet onglet** (sauf l'en-tête). C'est une **vue 100 % formules** de
> l'onglet `raw` : elle reprend les **6 colonnes NASA-TLX déjà saisies** dans `raw` et les
> recopie telles quelles dans la forme « longue » (8 colonnes) attendue par `present.py`. Aucune
> nouvelle donnée, aucune moyenne, aucun score — juste un **sous-ensemble de `raw`** (on garde
> participant + condition + les 6 items, on jette niveau / morceau / ordre / STAI / self-eff).

**En-tête en A1** (texte, puis Data → Split text to columns → Comma) :

```
participant,condition,tlx_mental,tlx_physique,tlx_temporel,tlx_perf,tlx_effort,tlx_frustration
```

**Une seule formule, en A2** — elle se déverse toute seule sur 16 lignes × 8 colonnes (A2:H17) :

```
=ARRAYFORMULA({raw!A2:A17, raw!D2:D17, IF(raw!F2:K17="","",raw!F2:K17)})
```

Ce que cette formule assemble (de gauche à droite), depuis `raw` :

| Colonne ici | ← `raw` | contenu |
|---|---|---|
| A `participant` | `raw!A` | P01 … P08 |
| B `condition` | `raw!D` | AVEC / SANS |
| C → H (6 items) | `raw!F:K` | mental, physique, temporel, perf, effort, frustration |

Le `IF(…="","",…)` autour de `raw!F:K` garde les cellules TLX **vides à blanc** (et non à 0) tant
qu'une ligne n'est pas saisie — sinon un 0 fantôme fausserait les médianes de `present.py`.

> *Si la formule unique coince (séparateur `{}` selon la locale), version équivalente colonne par
> colonne :* `A2: =ARRAYFORMULA(raw!A2:A17)` · `B2: =ARRAYFORMULA(raw!D2:D17)` ·
> `C2: =ARRAYFORMULA(IF(raw!F2:F17="","",raw!F2:F17))` … jusqu'à `H2` (`raw!K2:K17`).

(Pas de pairage AVEC/SANS ici — `present.py` ne fait que des **médianes par condition** — donc
l'ordre des lignes n'a aucune importance pour cet onglet.)

---

## 5. Onglet `q0_profil` — profil participant (8 lignes) · **= export**

En-tête en **A1** (ou importer `data/q0_profil.csv`) :

```
participant,age,daltonisme,instrument_principal,annees_instrument,annees_piano,formation_piano,annees_jazz,lecture_grille,freq_impro,niveau_impro_1_7,defilement_difficile_1_7,usage_ireal,deja_piano_augmente,plus_difficile_texte
```

Saisie directe (pas de formule). Valeurs attendues :

| Colonne | Q | Valeurs |
|---|---|---|
| `age` | 1 | nombre |
| `daltonisme` | 2 | `Non` / `Oui` / `NSP` |
| `instrument_principal` | 3 | texte |
| `annees_instrument` | 3 | nombre |
| `annees_piano` | 4 | nombre |
| `formation_piano` | 5 | `Autodidacte` / `Cours particuliers` / `École de musique / conservatoire` / `Autre` |
| `annees_jazz` | 6 | nombre |
| `lecture_grille` | 7 | `Pas du tout` / `Avec difficulté` / `À l'aise` / `Très à l'aise` |
| `freq_impro` | 8 | `Jamais` / `Rarement` / `Quelques fois par mois` / `Chaque semaine` / `Presque chaque jour` |
| `niveau_impro_1_7` | 9 | entier **1–7** |
| `defilement_difficile_1_7` | 10 | entier **1–7** |
| `usage_ireal` | 13 | `Jamais` / `Occasionnellement` / `Régulièrement` |
| `deja_piano_augmente` | 14 | `Non` / `Oui` |
| `plus_difficile_texte` | 11 | texte libre |

Mettre une **liste déroulante** (Data → Data validation) sur les 6 colonnes catégorielles pour
fiabiliser les `COUNTIF` du tableau descriptif. Q12 (familiarité 14 morceaux) n'est **pas** ici :
son résultat (morceaux inconnus → choisis) vit dans la colonne `morceau` de `raw`.

---

## Export & exécution

Régler d'abord **File → Settings → Locale = United States** (CSV en décimale `.`). Puis, par
onglet : **File → Download → CSV**, enregistrer dans `rapport/stats/data/` :

| Onglet | → fichier |
|---|---|
| `scores_tableur` | `scores_tableur.csv` |
| `tlx_items_tableur` | `tlx_items_tableur.csv` |
| `q0_profil` | `q0_profil.csv` |
| `raw` *(facultatif, recoupement)* | `responses.csv` |

```bash
poetry run python rapport/stats/present.py        # slope_*.png ×3 + tlx_subscales.png
poetry run python rapport/stats/analyze_tests.py  # facultatif : recalcule depuis responses.csv, doit concorder
```
