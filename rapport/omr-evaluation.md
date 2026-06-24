# Annexe — Évaluation de l'OMR (support du §3.4)

> Matériel d'annexe pour la section 3.4 "L'ingestion de la grille : le rôle de l'OMR".
> Le corps du chapitre ne garde que l'essentiel (le constat, un exemple, le chiffre
> moyen) ; le détail de la métrique et les résultats complets vivent ici.
> Style : "nous" / "on", pas de tirets cadratins, guillemets droits, termes techniques
> anglais en *italique*, virgule décimale.

## Méthode d'évaluation

Nous comparons la sortie de l'*OMR* (fichiers `JM_MIR_*`) à une transcription de
référence établie à la main (fichiers `GT_MIR_*`), toutes deux au format *mir_eval*
(temps de début, temps de fin, chiffrage). Faute d'une métrique standard adaptée à notre
besoin précis, une grille jouable et fidèle temps par temps, nous avons défini une mesure
sur mesure, en trois temps.

D'abord, le déroulage : chaque grille est dépliée en une suite d'un symbole par temps
(*resolution* = 1,0), de sorte qu'un accord tenu quatre temps occupe quatre cases. Les
erreurs sont ainsi pondérées par la durée : un accord faux tenu longtemps coûte plus cher
qu'un accord faux de passage.

Ensuite, l'alignement : nous alignons les deux suites par une distance d'édition (un
*Levenshtein* pondéré) qui minimise le coût total. Chaque temps de référence est alors
soit correct, soit substitué (accord faux), soit supprimé (temps manquant dans la sortie),
tandis que les temps en trop dans la sortie sont des insertions (temps hallucinés). Le coût
d'une substitution est gradué selon la distance harmonique (table ci-dessous) : confondre
deux écritures d'un même accord coûte peu, confondre deux qualités fondamentales coûte
cher, se tromper de fondamentale coûte le maximum. Une insertion ou une suppression coûte
1,0, soit autant qu'un accord entièrement faux : une grille de la mauvaise longueur est
aussi inutilisable qu'une grille aux mauvais accords.

Enfin, le score : la précision pondérée vaut 1 moins le coût total divisé par le nombre de
temps de référence. Un repère structurel signale en outre, indépendamment du score, tout
écart entre le nombre de temps des deux grilles.

## Barème de la distance harmonique (coût d'une substitution)

Le coût s'applique par temps, il se multiplie donc par la durée de l'accord. La première
règle qui s'applique l'emporte (du moins grave au plus grave).

| Condition (même fondamentale sauf mention) | Coût | Exemple | Justification musicale |
|---|---:|---|---|
| Chiffrage identique | 0,00 | `D:min7` = `D:min7` | correspondance exacte |
| Extensions diatoniques ajoutées ou changées (sans b, #, alt) | 0,00 | `C:7` vs `C:7(13)` | couleur sans changement de fonction |
| Deux dominantes écrites sans parenthèses (7 / 9 / 11 / 13) | 0,00 | `D:7` vs `D:9` | même fonction dominante |
| Triade contre septième de même famille | 0,10 | `A:min` vs `A:min7`, `Eb:maj7` vs `Eb:6` | même couleur tonale |
| Tension altérée fausse ou manquée (b, #, alt) | 0,25 | `G:7` vs `G:7(b9)` | tension supérieure incorrecte |
| `min7` contre `minmaj7`, `hdim7` contre `dim` | 0,25 | `C:min7` vs `C:minmaj7` | une note de la couleur change |
| Conflit majeur / mineur / dominante (3ce ou 7e fausse) | 0,50 | `Bb:7` vs `Bb:maj7`, `C:maj7` vs `C:min7` | qualité fondamentale changée |
| Même fondamentale, toute autre qualité | 0,75 | `C:maj7` vs `C:dim7`, `C:maj7` vs `C:maj9` | qualité radicalement différente |
| Fondamentale différente | 1,00 | `Db:maj7` vs `D:maj7` | mauvaise note de basse |
| Un des deux est `N` (silence) | 1,00 | `A:min7` vs `N` | rien reconnu |
| Temps inséré (I) ou supprimé (D) | 1,00 | `***` contre `F:min7` | grille de la mauvaise longueur |

## Résultats par standard

Décomposition du coût total en part structurelle (temps faux : insertions + suppressions,
à 1,0 chacun) et part harmonique (accords faux : somme des substitutions). Comme
précision = 1 - coût total / temps de référence et coût total = structurel + harmonique,
les parts correcte, harmonique et structurelle somment exactement à 100 % des temps de
référence (figure `figures/solution-conceptuelle/omr_fiabilite.png`).

| Standard | Temps réf. | Temps OMR | Δ temps | Pén. struct. (D+I) | Pén. harm. (Σ S) | Pén. totale | Précision |
|---|---:|---:|---:|---:|---:|---:|---:|
| On the Sunny Side of the Street | 128 | 102 | -26 | 28 | 20,5 | 48,5 | 62,1 |
| Fly Me to the Moon | 128 | 129 | +1 | 1 | 49,5 | 50,5 | 60,6 |
| Autumn Leaves | 128 | 120 | -8 | 38 | 15,0 | 53,0 | 58,6 |
| Stella by Starlight | 128 | 127 | -1 | 7 | 55,5 | 62,5 | 51,2 |
| All The Things You Are | 144 | 149 | +5 | 23 | 49,0 | 72,0 | 50,0 |
| Satin Doll | 128 | 112 | -16 | 16 | 60,5 | 76,5 | 40,2 |
| Oleo | 128 | 86 | -42 | 42 | 34,5 | 76,5 | 40,2 |
| Misty | 128 | 169 | +41 | 41 | 37,75 | 78,75 | 38,5 |
| Take the "A" Train | 128 | 105 | -23 | 65 | 18,5 | 83,5 | 34,8 |
| Summertime | 64 | 86 | +22 | 22 | 21,2 | 43,2 | 32,5 |
| Sandu | 96 | 128 | +32 | 32 | 49,0 | 81,0 | 15,6 |
| **Total / moyenne** | **1328** | **1313** | **11/11 faux** | **315** | **411** | **726** | **44,0** |

Précision moyenne 44,0 sur 100, médiane 40,2, étendue de 15,6 (Sandu) à 62,1 (On the
Sunny Side of the Street). Sur les onze morceaux, les onze produisent un nombre de temps
erroné. À l'échelle du corpus, la pénalité se répartit en 315 points structurels (43 %) et
411 points harmoniques (57 %) : les deux modes d'échec sont sévères et indépendants.

## Ventilation des erreurs sur le corpus

| Coût unitaire | Type d'erreur | Temps concernés |
|---:|---|---:|
| 0,10 | triade contre septième de même famille | 2 |
| 0,25 | tension altérée fausse / `min7`↔`minmaj7`, `hdim7`↔`dim` | 6 |
| 0,50 | conflit majeur / mineur / dominante | 69 |
| 0,75 | autre qualité, même fondamentale | 137 |
| 1,00 | substitution de fondamentale fausse ou `N` | 272 |
| 1,00 | insertion (temps halluciné) | 150 |
| 1,00 | suppression (temps manquant) | 165 |

Les erreurs les plus lourdes dominent : 272 temps reçoivent la pénalité maximale en
substitution (mauvaise fondamentale ou silence reconnu à la place d'un accord), auxquels
s'ajoutent 315 temps de décalage structurel. Les erreurs vraiment bénignes (0,10 et 0,25)
ne pèsent presque rien : 8 temps sur l'ensemble.

## Limites de la mesure (à énoncer)

- La comparaison de fondamentale est textuelle, pas en classes de hauteur : `Gb` et `F#`
  compteraient comme deux fondamentales différentes (1,00) bien qu'identiques à l'oreille.
  Nos pires erreurs de fondamentale (`Db:maj7` lu `D:maj7`) sont de vrais demi-tons faux,
  donc la pénalité est juste ici, mais la mesure ne distingue pas une fondamentale fausse
  d'une réécriture enharmonique.
- Les extensions écrites sans parenthèses sont traitées de façon inégale : les dominantes
  inline (7 / 9 / 11 / 13) sont regroupées (0,00), mais `maj9`, `min9`, `min6` inline
  tombent dans le fourre-tout à 0,75. Seules les extensions entre parenthèses, comme
  `(b9)`, reçoivent le traitement gradué à 0,25.
- Une insertion ou une suppression coûte autant qu'un accord entièrement faux, si bien que
  le pourcentage mélange deux échecs de nature différente. C'est la raison de présenter la
  décomposition (structurel vs harmonique) plutôt que le seul chiffre.
- Le test reste indicatif : un seul outil (Martinez-Sevilla et al. [15]), onze grilles, une
  référence et une métrique établies par le concepteur. Le constat qui ne dépend d'aucun de
  ces choix reste le défaut structurel : onze transcriptions sur onze ont un nombre de temps
  erroné.

## Reproduire

- Figure : `poetry run python rapport/figures/solution-conceptuelle/omr_fiabilite.py`
  (police Plus Jakarta Sans partagée avec `rapport/stats/fonts`, largeur justification A4).
- Scores : script `evaluate_custom` sur les paires `GT_MIR_*` / `JM_MIR_*`, un rapport
  `REPORT_*.txt` par standard.
