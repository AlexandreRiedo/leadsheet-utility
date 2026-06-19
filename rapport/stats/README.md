# Analyse statistique des tests utilisateurs

Pipeline minimal : on tape les **réponses brutes** dans un CSV, une commande sort les
**scores composites, les tests de Wilcoxon exacts, les tailles d'effet et les figures**.
La méthode et les sources sont dans [`../guide-interpretation-stats.md`](../guide-interpretation-stats.md).

## Fichiers

| Fichier | Rôle |
|---|---|
| `data/responses.csv` | **À remplir** — 1 ligne par morceau joué (16 lignes : P01–P08 × AVEC/SANS). Valeurs **brutes**. |
| `data/q0_profil.csv` | **À remplir** — 1 ligne par participant (profil Q0, pour le tableau descriptif). |
| `analyze_tests.py` | Le script : scoring → Wilcoxon exact → r_rb + dz + k/n → tableaux + figures. |
| `results/` | *Généré* : `scores.csv` (scores par personne) + `wilcoxon_summary.md` (tableau de résultats). |
| `figures/` | *Généré* : `slope_*.png` (×3) + `tlx_subscales.png`. |

## Remplir `data/responses.csv`

Saisir les **valeurs brutes**, ne **rien** pré-calculer (le script fait les moyennes, les
inversions STAI, les directions). Cellule vide = pas encore saisie (le script ignore les
lignes/mesures incomplètes — tu peux donc lancer au fur et à mesure).

| Colonnes | Échelle brute à saisir |
|---|---|
| `niveau, cas, morceau, ordre` | contexte (S/E/M/P ; cas 1-4 ; titre ; 1 ou 2) — facultatif |
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
