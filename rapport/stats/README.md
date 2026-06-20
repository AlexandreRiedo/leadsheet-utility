# Analyse statistique des tests utilisateurs

La méthode et les sources sont dans [`../guide-interpretation-stats.md`](../guide-interpretation-stats.md).
Le plan du classeur Google Sheets (onglets, en-têtes, formules, saisie → export CSV) est dans
[`SHEETS-LAYOUT.md`](SHEETS-LAYOUT.md).

**Deux chemins, une seule source de vérité.**

1. **Tableur + calculateur en ligne (source de vérité, auditable).** Saisie des valeurs brutes
   → scores composites → Wilcoxon (W, W⁺/W⁻, p) via le calculateur en ligne → `r` rang-bisérial
   `(W⁺−W⁻)/(W⁺+W⁻)` à la main. C'est la version défendable au jury.
2. **`present.py` (présentation).** On exporte les **scores composites** du tableur vers
   `data/scores_tableur.csv`, et le script en tire les figures en pente (`slope_*.png`, ×3).
   Pour le détail NASA-TLX par dimension, on exporte en plus les **items bruts** vers
   `data/tlx_items_tableur.csv` (format long) → `tlx_subscales.png`. Le script ne (re)calcule
   **aucun** score et ne refait **aucun** test — il ne fait que dessiner les mêmes valeurs que
   le tableur, donc une figure ne peut pas contredire le test fait à la main.
3. **`analyze_tests.py` (recoupement, optionnel).** Refait tout depuis les réponses brutes
   (`responses.csv`) pour *vérifier* le tableur — à lancer une fois, confirmer que W, p et r_rb
   concordent, investiguer tout écart.

## Fichiers

| Fichier | Rôle |
|---|---|
| `data/responses.csv` | **À remplir** — 1 ligne par morceau joué (16 lignes : P01–P08 × AVEC/SANS). Valeurs **brutes**. |
| `data/q0_profil.csv` | **À remplir** — 1 ligne par participant (profil Q0, pour le tableau descriptif). |
| `analyze_tests.py` | **Recoupement** : scoring → Wilcoxon exact → r_rb + dz + k/n → tableaux + figures, depuis `responses.csv`. À ne lancer que pour *vérifier* le tableur. |
| `data/scores_tableur.csv` | **À remplir / exporter du tableur** — scores composites par participant (`<MESURE>_AVEC` / `_SANS`). Source de vérité de la présentation. |
| `data/tlx_items_tableur.csv` | *Facultatif* — items NASA-TLX bruts, **format long** (1 ligne par participant × condition) pour la figure par dimension. |
| `present.py` | **Présentation** : lit les deux CSV ci-dessus → `slope_*.png` (×3) + `tlx_subscales.png`. Ne (re)calcule rien. |
| `results/` | *Généré* : `scores.csv` (scores par personne) + `wilcoxon_summary.md` (tableau de résultats). |
| `figures/` | *Généré par `present.py`* : `slope_*.png` (×3) + `tlx_subscales.png` — **les figures insérées dans le rapport**. |
| `figures/_verify/` | *Généré par `analyze_tests.py`* : mêmes figures, **version recoupement jetable** (sous-dossier dédié + gitignoré, pour ne jamais écraser celles du rapport). |

## Remplir `data/responses.csv`

Saisir les **valeurs brutes**, ne **rien** pré-calculer (le script fait les moyennes, les
inversions STAI, les directions). Cellule vide = pas encore saisie (le script ignore les
lignes/mesures incomplètes — tu peux donc lancer au fur et à mesure).

| Colonnes | Échelle brute à saisir |
|---|---|
| `niveau, morceau, ordre` | contexte (difficulté du morceau S/E/M/P ; titre ; 1 ou 2) — facultatif |
| `tlx_*` (6) | **0–100** par pas de 5. Saisir Performance telle quelle (Réussie→Ratée), **sans inverser**. |
| `stai_*` (6) | **1–4** (Non=1, Plutôt non=2, Plutôt oui=3, Oui=4). **Ne pas inverser** : le script s'en charge. |
| `se_q7..se_q10` | **1–7** |
| `conf_globale_q11` | **0–10** (contrôle) |

## Installer & lancer

```bash
poetry install --with stats          # numpy + scipy + matplotlib
poetry run python rapport/stats/analyze_tests.py
```

Le test, le calcul des rangs et les figures s'appuient sur **scipy** et **matplotlib**
(groupe Poetry `stats` ; numpy est déjà dans les dépendances principales).

## Ce que fait le script (résumé)

- **Scores** : RTLX = moyenne des 6 dimensions ; STAI-6 = inversion calme/décontracté/satisfait
  puis somme ×20/6 ; auto-efficacité = moyenne items 7–10.
- **Test** : Wilcoxon des rangs signés via `scipy.stats.wilcoxon` (p **exacte** à n ≤ 50), dans
  la bonne direction par mesure (`less` pour TLX & STAI, `greater` pour l'auto-efficacité).
- **Sorties par mesure** : médiane (IQR) AVEC/SANS, W, p exact (uni + bi), corrélation
  rang-bisériale (taille d'effet) + dz, et le compte k/n dans le sens prédit.

> ⚠️ Direction des hypothèses : TLX et STAI → **AVEC < SANS** ; auto-efficacité → **AVEC > SANS**.
> Le script applique ça automatiquement ; ne pas le « corriger » à la main.
