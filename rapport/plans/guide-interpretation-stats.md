# Guide d'interprétation statistique — tests utilisateurs (n = 8, intra-sujet AVEC/SANS)

> But : savoir **calculer**, **tester**, **lire** et **rédiger** chaque résultat, sans
> erreur de scoring ni de direction. Complète `plan-analyse-tests.md` (§4–7).
> **Implémenté** dans `rapport/stats/analyze_tests.py` (scoring, direction, p exact, r_rb,
> dz, k/n) — voir `rapport/stats/README.md`. Toutes les sources sont en fin de document.

---

## 0. Les trois mesures et leur calcul (à faire AVANT tout test)

On obtient **un score par mesure, par condition (AVEC / SANS), par personne** → 3 mesures × 2
conditions × 8 personnes. Le test compare ensuite, pour chaque mesure, les 8 paires AVEC vs SANS.

| Mesure | Items | Calcul du score | Étendue | Sens |
|---|---|---|---|---|
| **NASA-TLX (RTLX)** | 6 dimensions, 0–100 | **MOYENNE** des 6 (pas la somme). **Aucune inversion** (Performance déjà orientée Réussie→Ratée). | 0–100 | ↑ = charge élevée |
| **STAI-6** (anxiété) | 6 items Likert 1–4 | **Inverser** calme/décontracté/satisfait (`5−x`), puis **somme × 20/6** | 20–80 | ↑ = anxiété élevée |
| **Auto-efficacité** (« confiance ») | items 7–10, Likert 1–7 | **MOYENNE** des 4 items (aucune inversion) | 1–7 | ↑ = confiance élevée |
| *(contrôle)* Confiance globale | item 11, 0–10 | tel quel ; **pas un 4ᵉ test**, sert à valider l'auto-efficacité | 0–10 | ↑ = confiance |

> **Erreurs de scoring les plus fréquentes** : (1) sommer le TLX au lieu de moyenner ;
> (2) oublier l'inversion STAI ; (3) inverser Performance par réflexe (ne PAS le faire).

---

## 1. Hypothèses — nulle (H₀) et directionnelle (H₁), mesure par mesure

Le test de Wilcoxon porte sur la **médiane des différences appariées** `d = score_AVEC − score_SANS`.

- **H₀ (nulle, identique pour les 3)** : la projection ne change rien → la médiane des
  différences appariées = 0 (autant de hausses que de baisses, de même ampleur). C'est le
  « monde où l'artefact est inutile » dont le test mesure la plausibilité.

- **H₁ (alternative, DIRECTIONNELLE, ≠ selon la mesure)** :

| Mesure | H₁ | `d = AVEC − SANS` | `alternative` (scipy / web) |
|---|---|---|---|
| NASA-TLX | **AVEC < SANS** (charge plus basse avec projection) | < 0 | **`less`** |
| STAI-6 | **AVEC < SANS** (moins anxieux avec projection) | < 0 | **`less`** |
| Auto-efficacité | **AVEC > SANS** (plus confiant avec projection) | > 0 | **`greater`** |

> ⚠️ **L'auto-efficacité va dans l'AUTRE sens.** Régler les trois sur `less` répondrait
> à la mauvaise question pour la confiance. Vérifier la direction avant chaque test.

**Unilatéral justifié** : les trois hypothèses sont prédites *à l'avance* et *directionnelles*
(le protocole l'annonce). Si un·e relecteur·rice est puriste, mentionner aussi le bilatéral
(p simplement ×2) — c'est l'option conservatrice (Field, 2018).

---

## 2. Le test : Wilcoxon des rangs signés (apparié), version EXACTE

- **Pourquoi ce test** : 2 échantillons appariés, mesures au moins ordinales (Likert), pas
  d'hypothèse de normalité, n petit → non paramétrique apparié (Wilcoxon, 1945 ; Field, 2018).
- **Statistique W** : on classe les |différences|, on somme les rangs des d positifs (T⁺) et
  des d négatifs (T⁻) ; `W = min(T⁺, T⁻)`. Un W très petit = quasi toutes les différences
  vont dans le même sens (signal fort).
- **p EXACT, pas l'approximation z** : à n = 8, l'approximation normale (z = (W−μ_W)/σ_W) est
  imprécise ; utiliser le **calcul exact**. Le script `rapport/stats/analyze_tests.py` l'obtient
  via **`scipy.stats.wilcoxon`** (méthode par défaut « auto » → p **exacte** tant que n ≤ 50, par
  énumération des configurations de signes) ; un calculateur convient aussi en **mode
  petit-échantillon / exact**. Ne **pas** rapporter de z-score à n = 8.
- **Exact vs approximation — écart attendu** : un outil réglé sur l'**approximation normale**
  (DATAtab, ou MetricGate par défaut) donne un p légèrement différent (vérifié : .344 exact vs
  .312 approx sur un même jeu). À n = 8, **l'exact est le bon** ; ne pas s'inquiéter de l'écart.
- **Différences nulles (d = 0)** : exclues → n effectif diminue ; **le
  noter** si ça arrive (ex. « un score nul, n effectif = 7 »).

### 2.1 Table de p exacte (n = 8 et n = 7) — pour le calcul à la main

> **Pourquoi une table.** Un tableur (Sheets/Excel) calcule nativement W (`RANK.AVG` + `SUMIF`),
> r_rb, dₙ, médiane/IQR, mais **n'a pas de fonction Wilcoxon** : on lit donc p ici. Faire le
> calcul à la main évite *par construction* le piège de l'approximation z (§2 ; DATAtab/MetricGate
> y basculent par défaut) et rend chaque étape auditable → plus défendable qu'un appel `scipy` à n = 8.

**Dérivation (exacte, par énumération — vérifiable à la main).** Sous H₀, chacun des rangs
{1,…,n} reçoit un signe ± au hasard → **2ⁿ** configurations équiprobables (256 à n = 8, 128 à
n = 7). T⁺ = somme des rangs positifs. Alors :

```
p unilatéral = (nb de sous-ensembles de {1..n} de somme ≤ W) / 2ⁿ
p bilatéral  = 2 × p unilatéral          (distribution symétrique)
```

Aucune intégrale ni approximation normale : un simple **comptage de sommes de sous-ensembles**.
**On rejette H₀ quand le W observé ≤ W de la ligne.** (Recoupé avec `scipy.stats.wilcoxon` ;
l'exemple §4 « W = 1, p = .016 » est la ligne n = 7, W = 1 unilatéral.)

**n = 8** (aucun nul exclu) :

| W | p unilatéral | p bilatéral |
|--:|--:|--:|
| 0 | .004 | .008 |
| 1 | .008 | .016 |
| 2 | .012 | .023 |
| 3 | .020 | .039 |
| 4 | .027 | .055 |
| 5 | .039 | .078 |
| 6 | .055 | .109 |

**n = 7** (un nul exclu) :

| W | p unilatéral | p bilatéral |
|--:|--:|--:|
| 0 | .008 | .016 |
| 1 | .016 | .031 |
| 2 | .023 | .047 |
| 3 | .039 | .078 |
| 4 | .055 | .109 |

> **Plancher de puissance à n = 8** : le plus petit p unilatéral atteignable est **.004** (les 8
> différences dans le sens prédit, W = 0) ; bilatéral **.008**. Pour α = .05 unilatéral il faut
> **W ≤ 5** → une seule paire à contre-sens peut faire basculer p au-dessus de .05 ; d'où le choix
> (§3.3) de la **taille d'effet comme mesure principale, p en appui**.
> **Ex æquo** : des |différences| égales modifient légèrement la distribution nulle ; cette table
> suppose l'absence d'ex æquo → les noter (§5) et, le cas échéant, s'appuyer sur le recoupement `scipy`.

---

## 3. Comment lire chaque sortie

### 3.1 W (et T⁺ / T⁻)
Indicateur de **direction et de concentration** : si l'hypothèse est AVEC < SANS, on s'attend
à beaucoup de différences négatives → **T⁻ grand, T⁺ (donc W) petit**. W seul ne se lit pas en
absolu : il sert à calculer p et la taille d'effet.

### 3.2 La valeur p (exacte, unilatérale)
« Si l'artefact n'avait aucun effet, quelle est la probabilité d'obtenir un écart **au moins
aussi marqué** que le mien ? »
- **p < 0,05** → résultat **statistiquement significatif** (on rejette H₀) — *pas* « bon » ou
  « mauvais », juste « peu compatible avec le hasard ».
- **p ≥ 0,05** → on **ne rejette pas** H₀ ; **n'écrit JAMAIS « il n'y a pas d'effet »** : à
  n = 8 c'est très souvent un manque de puissance (Field, 2018 ; Amrhein et al., 2019).
- À n = 8, p est **discret et instable** (un·e participant·e qui change de sens peut le faire
  traverser 0,05) → **p est un appui, pas le cœur de la preuve.**

### 3.3 La taille d'effet (le cœur de la lecture à n = 8)
**Mesure principale : corrélation rang-bisériale appariée** (Kerby, 2014) :
```
r = (T⁺ − T⁻) / (T⁺ + T⁻)        étendue −1 … +1
```
Signe = direction ; |valeur| = ampleur. Indépendante de p, robuste, sans approximation
normale → adaptée à n = 8.

**Interprétation (barème de Cohen, 1988 — repère approximatif)** :

| |r| | Interprétation |
|---|---|
| ≈ 0,10 | petit |
| ≈ 0,30 | moyen |
| ≈ 0,50 | grand |

> Nuance : ces seuils ont été pensés pour le r de Pearson ; la rang-bisériale tend à
> être **plus grande**. Les présenter comme **repères**, pas comme une loi (Fritz et al., 2012).

**Compagnon optionnel pour le RTLX** (quasi-continu, 0–100) : **d de Cohen apparié (dₙ)** =
`moyenne(d) / écart-type(d)` ; seuils 0,2 / 0,5 / 0,8 (Cohen, 1988). Pour STAI/auto-efficacité
(dérivés d'ordinal) → s'en tenir à la rang-bisériale.

> Alternative connue `r = Z / √N` (Rosenthal, 1991 ; Field, 2018) : populaire mais s'appuie
> sur le Z de l'approximation normale → moins fiable à n = 8. La citer en second, pas en
> principal.

### 3.4 Le slope plot apparié (figure obligatoire)
Deux positions en x (SANS, AVEC), une **ligne par participant**. On lit en un coup d'œil :
**cohérence** (lignes parallèles dans un sens ?), **ampleur** (pentes), **exceptions** (qui va
à contre-sens → à discuter : niveau avancé ? daltonisme ? plafond « lumières trop vite » ?).
Plus honnête qu'un barplot de moyennes, qui efface l'appariement (Weissgerber et al., 2015).

### 3.5 Le compte k/n dans le sens prédit
« k participants sur 8 vont dans le sens attendu » (1 ex æquo exclu → k/7). Sans hypothèse,
lisible par tout jury, et c'est un **test des signes** déguisé (le plus conservateur). Quand
compte, taille d'effet et Wilcoxon concordent → résultat **triangulé**.

---

## 4. Comment rédiger un résultat (gabarit, style APA 7)

Un résultat = **descriptif + test + taille d'effet + figure + compte**, jamais p seul.

> *En condition AVEC, le RTLX était plus faible (Mdn = 55, IQR = 18) qu'en condition SANS
> (Mdn = 68, IQR = 15). Le test de Wilcoxon des rangs signés (exact, unilatéral) indique une
> réduction significative, W = 1, p = .016, avec une taille d'effet importante (r_rb = −.93) ;
> 6 des 7 paires exploitables vont dans le sens attendu (un score nul exclu) [voir Fig. X].*

Variante non significative (à assumer, pas à cacher) :

> *Aucune différence significative n'a été détectée pour l'auto-efficacité (Mdn_AVEC = 4,5 ;
> Mdn_SANS = 4,0 ; W = 9, p = .19), bien que la tendance aille dans le sens attendu
> (5/8 ; r_rb = +.31, effet moyen). Au vu de l'effectif réduit (n = 8), ce résultat est
> indicatif et insuffisamment puissant pour conclure à l'absence d'effet.*

Règles APA : p en italique sans 0 initial (`p = .016`), `p < .001` si très petit, médiane +
IQR pour des données non normales / petit n (APA, 2020 ; Field, 2018).

---

## 5. Pièges & garde-fous (checklist avant d'envoyer à Patrick)

- [ ] **Direction** : `less` pour TLX & STAI, `greater` pour l'auto-efficacité.
- [ ] **Scoring** : TLX = moyenne ; STAI = inversions + ×20/6 ; auto-eff = moyenne ; pas
      d'inversion de Performance.
- [ ] **p exact** (pas le z) ; ex æquo notés.
- [ ] **Taille d'effet + slope plot + compte** systématiques (pas p seul).
- [ ] **Primaire vs exploratoire** : les 3 mesures = **confirmatoires** (pré-spécifiées) ; les
      **6 sous-dimensions TLX** et l'**item 11** = **exploratoires** (descriptif, pas de
      sur-correction de multiplicité qui rendrait tout illisible). Le **dire** explicitement.
- [ ] **Ne jamais** écrire « prouve qu'il n'y a pas d'effet » pour un p non significatif.
- [ ] **Médiane/IQR**, pas moyenne ± écart-type (n = 8, non normal).

---

## 6. Triangulation (la discussion qui répond à la QR)

Croiser les trois mesures entre elles **et** avec l'entretien :
- **TLX ↓ + STAI ↓ + auto-eff ↑** AVEC → récit cohérent « moins de charge, moins d'anxiété,
  plus de confiance » → appuie QR1 (charge) et QR2 (oser).
- **Exigence temporelle TLX qui ne baisse pas** + verbatim « lumières trop vite » → corrobore
  le plafond d'utilisabilité (cohérence quanti/quali).
- **Pari d'auto-évaluation (entretien Q8)** vs RTLX/Performance mesurés → écart subjectif/objectif.
- Relier **STAI ↔ Frustration (TLX)** et **auto-efficacité ↔ « j'ai osé » (entretien Q9)**.

---

## 7. Sources

**Instruments**
- Hart, S. G., & Staveland, L. E. (1988). Development of NASA-TLX (Task Load Index): Results of
  empirical and theoretical research. *Advances in Psychology, 52*, 139–183.
- Hart, S. G. (2006). NASA-Task Load Index (NASA-TLX); 20 years later. *Proceedings of the Human
  Factors and Ergonomics Society Annual Meeting, 50*(9), 904–908. *(justifie le RTLX brut/moyenné)*
- Cegarra, J., & Morgado, N. (2009). Étude des propriétés de la version française de la NASA-TLX.
  *(traduction FR utilisée)*
- Spielberger, C. D. (1983). *Manual for the State-Trait Anxiety Inventory (STAI)*. Consulting
  Psychologists Press.
- Marteau, T. M., & Bekker, H. (1992). The development of a six-item short-form of the state scale
  of the Spielberger State-Trait Anxiety Inventory (STAI). *British Journal of Clinical
  Psychology, 31*(3), 301–306. *(STAI-6 + cotation × 20/6)*
- Schweitzer, M. B., & Paulhan, I. (1990). *Adaptation française du STAI-Y de Spielberger*.
  Université de Bordeaux II. *(formulations FR)*
- Bandura, A. (2006). Guide for constructing self-efficacy scales. In F. Pajares & T. Urdan (Eds.),
  *Self-Efficacy Beliefs of Adolescents* (pp. 307–337). Information Age Publishing.
- Ritchie, L., & Williamon, A. (2011). Measuring distinct types of musical self-efficacy.
  *Psychology of Music, 39*(3), 328–344.

**Test & statistiques**
- Wilcoxon, F. (1945). Individual comparisons by ranking methods. *Biometrics Bulletin, 1*(6), 80–83.
- Cohen, J. (1988). *Statistical Power Analysis for the Behavioral Sciences* (2nd ed.). Erlbaum.
  *(barèmes : r .10/.30/.50 ; d .20/.50/.80)*
- Rosenthal, R. (1991). *Meta-Analytic Procedures for Social Research*. Sage. *(r = Z/√N)*
- Fritz, C. O., Morris, P. E., & Richler, J. J. (2012). Effect size estimates: Current use,
  calculations, and interpretation. *Journal of Experimental Psychology: General, 141*(1), 2–18.
- Kerby, D. S. (2014). The simple difference formula: An approach to teaching nonparametric
  correlation. *Comprehensive Psychology, 3*, 11.IT.3.1. *(corrélation rang-bisériale appariée)*
- Field, A. (2018). *Discovering Statistics Using IBM SPSS Statistics* (5th ed.). Sage.
  *(Wilcoxon, p exact vs approximation, taille d'effet, médiane/IQR, unilatéral vs bilatéral)*
- Amrhein, V., Greenland, S., & McShane, B. (2019). Retire statistical significance.
  *Nature, 567*, 305–307. *(ne pas conclure « pas d'effet » d'un p non significatif)*

**Présentation des données**
- Weissgerber, T. L., Milic, N. M., Winham, S. J., & Garovic, V. D. (2015). Beyond bar and line
  graphs: Time for a new data presentation paradigm. *PLoS Biology, 13*(4), e1002128.
  *(montrer les points/appariements individuels → slope plot)*
- American Psychological Association (2020). *Publication Manual of the APA* (7th ed.).
  *(format de report : p, tailles d'effet, statistiques descriptives)*

**Ressources pratiques (tutoriels & calculateurs — compréhension et vérification)**
- numiqo — *Wilcoxon Test* (tutoriel + vidéo). https://numiqo.com/tutorial/wilcoxon-test
  *(explication pas-à-pas : arbre paramétrique/non-paramétrique, rangs, W, p ; support des captures utilisées ici)*
- MetricGate — *Wilcoxon Signed-Rank Test for Median Difference*.
  https://metricgate.com/docs/wilcoxon-signed-rank-test-for-median-difference/
  *(calculateur en ligne : échantillons appariés, p exact en petit échantillon, IC de la médiane ; sert à recouper les sorties du script)*
- MetricGate — *Rank-Biserial Correlation*. https://metricgate.com/docs/rank-biserial-correlation/
  *(définition et calcul de la taille d'effet rang-bisériale)*
- Investopedia — *Wilcoxon Test*. https://www.investopedia.com/terms/w/wilcoxon-test.asp
  *(définition grand public : signed-rank vs rank-sum ; utile pour une formulation accessible)*

> *Conseil de rédaction : pour la section Méthode, citer la référence primaire (Wilcoxon 1945,
> Kerby 2014…) en note de bas de page, et ces ressources pratiques comme appui de compréhension /
> vérification des calculs — les deux sont complémentaires, pas concurrentes.*

> *Vérifier l'année/pagination exacte de Cegarra & Morgado et de Schweitzer & Paulhan dans les
> PDF de `proto-media/08-working-on-tests/protocole/refs/` avant l'export final de la biblio.*
