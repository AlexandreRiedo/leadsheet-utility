# Plan de rédaction — Rapport de bachelor

> But de ce document : savoir **quoi écrire, où, et avec quoi**, section par section.
> Sources croisées : structure convenue (notes réunion finale Roth), brouillon DS annoté
> par Patrick (`rapport/ds/DS … 2026-02-10.pdf`), thèse de référence Carusi
> (`rapport/refs/bachelor-carusi.pdf`), code (`src/leadsheet_utility/`, CLAUDE.md, SPEC.md).
> Cible : **40–60 pages**. Style : "nous" (pas "je" — annotation Patrick p.3).

---

## 0. Consignes transversales (à garder en tête partout)

Corrections récurrentes de Patrick + notes de réunion qui s'appliquent à TOUT le rapport :

- **"nous" et non "je"** (annotation p.3).
- **Toujours revenir à la Question de Recherche (QR).** Patrick l'écrit deux fois
  ("évaluation : que par rapport à la QR !", "arrivez-vous à répondre à vos QR ?").
  Chaque chapitre doit pouvoir répondre : *en quoi ceci sert la QR ?*
- **Expliquer le PRINCIPE, pas juste les pièces.** Annotations : "quels sont les
  objectifs / quel est le principe de base ?", "plus d'explication sur le principe",
  "mieux formuler le système". → Toujours une vue top-down avant le détail.
- **Vocabulaire "réalité augmentée / réalité diminuée"** (annotations p.5, p.8, p.9).
  Patrick veut qu'on cadre le projet comme de la **RA** ; et il introduit la **réalité
  diminuée** = éteindre des touches est aussi un outil pédagogique (Contour, Flow,
  Start&End filtrent/retirent des notes — c'est de la réalité *diminuée*).
- **Reformuler la QR** : il a barré "bien conçues" et écrit "de la réalité" → la QR
  doit parler d'improvisations *ancrées dans la réalité* (contexte jazz réaliste).
  Les QR sont un "bon début à enrichir".

---

## 1. Introduction  — viser ~3-4 pages

**Modèle Carusi : Contexte → Problématique → Question de recherche.** On garde ça.

| Sous-section | Quoi écrire | Réutiliser du DS | À corriger / ajouter |
|---|---|---|---|
| Contexte | Le jazz et l'improvisation ; la difficulté pour débutants/intermédiaires ; pianistes classiques qui veulent improviser | §Introduction du DS (p.2) | "plus clair" — rendre le but explicite |
| Problématique | La grille défile vite, gammes difficiles, produire un discours cohérent ≠ gammes montantes/descendantes ; **charge cognitive** élevée | §Introduction du DS | Introduire ici le terme charge cognitive (relié à l'état de l'art) |
| Question de recherche | Les 2 QR, reformulées | QR du DS (p.6) | Intégrer corrections Patrick (cf. §0) + annoncer qu'on y répond au ch. Évaluation |

**QR (proposition reformulée, à valider avec Patrick) :**
1. *Comment favoriser des improvisations jazz plus créatives et ancrées dans la
   réalité (contexte jazz réaliste) à l'aide d'un piano augmenté ?*
2. *Quelles sont les raisons qui rendent l'improvisation jazz difficile, et comment
   promouvoir l'improvisation pour une personne qui n'ose pas se lancer ?*

Terminer l'intro par un **paragraphe "plan du rapport"** (1 phrase par chapitre) — Carusi le fait.

---

## 2. État de l'art  — viser ~10-14 pages (chapitre lourd)

**Note de réunion : "restructurer par thématique" + "mentionner charge cognitive, anxiété".**
Carusi organise son état de l'art en 3 thèmes avec sous-titres → faire pareil.

### Thème A — Apprendre l'improvisation jazz (pédagogie)
- La revue de Spice [1] : les 5 frameworks + notre 6e catégorie (jeux créatifs).
- Exploration des livres (Reeves [2], Drury [3], Patterns [4][5], Bass Method [6],
  How to Play Bebop I/II/III [7][8][9]) — déjà rédigé dans le DS (p.3-4), à condenser.
- Thèse de Chyu [10] : lecture créative, questions-réponses, impro autour d'accords.
- **Renvoyer à l'annexe** "Revue de quelques livres de jazz".

### Thème B — Charge cognitive et anxiété dans l'apprentissage de l'impro  ← NOUVEAU
> C'est le thème explicitement demandé (réunion + annotation p.11 "ajouter de la
> théorie relative à la charge mentale"). **Bloc à écrire de zéro** — voir prompts §10.
- Cognitive Load Theory (Sweller) appliquée à une tâche temps-réel comme l'impro.
- Anxiété de performance / blocage de l'improvisateur (lien avec QR2 "n'ose pas se lancer").
- Comment la visualisation peut décharger la mémoire de travail → justifie la projection.
- **Effet d'inversion d'expertise (Kalyuga & Sweller) + effet de redondance** : un
  échafaudage utile au débutant devient surcharge chez l'expert (info redondante = charge
  extrinsèque). ← **à poser ICI pour cadrer d'avance l'anomalie experts du ch. Évaluations**
  (§6.4) : les improvisateurs les plus chevronnés ont vécu la projection comme un fardeau.
- *Besoin de chercher 3-5 références académiques ici (à ajouter à la biblio).*

### Thème C — Pianos augmentés & Réalité Augmentée  ← reframer en "RA" (annotation p.5)
- Revue 2022 des pianos augmentés, Deja et al. [11] : 56 prototypes, seulement 16
  avec module d'impro, seulement 3 attaquent le jazz → **le créneau / le gap**.
- Sandnes & Eika [12] : projection couleur des voicings (inspiration couleurs).
- ImproVisAR, Deja et al. [13] : piano roll en RA — notre point de comparaison direct
  (eux = main droite, do majeur uniquement ; nous = plusieurs tonalités, contexte réaliste).
- "ism" Improvisation Supporting Systems [14] : correction MIDI temps réel.
- OMR des lead sheets [15] : Martinez-Sevilla et al. 2025 (code MIT) — à mentionner ici
  mais surtout exploité au ch. Solution conceptuelle.

**Fin de chapitre : formuler le GAP** explicitement → ça justifie la QR.

---

## 3. Méthodologie (DSR)  — viser ~1-2 pages

Carusi a un court chapitre **Design Science Research** [22] juste avant la Proposition.
On l'ajoute (le titre du brouillon est même "Projet de recherche en Design Science").
- Citer DSR comme cadre.
- Le cycle suivi : état de l'art → formulation problème → exigences/objectifs → design
  → instanciation → évaluation → conclusion (mappe sur nos chapitres).
- C'est ici qu'on peut placer les **étiquettes de Patrick** : "OCR → Interprétation →
  Focalisation → Présentation" et "Éléments de présentation" (étapes du processus
  de design de l'artefact — à clarifier avec lui, puis poser le vocabulaire ici).

---

## 4. Solution conceptuelle de l'artefact  — viser ~8-10 pages

> = "Proposition" du DS, mais Patrick veut MUSCLER le principe. Notes de réunion :
> "montrer le diagramme / analyse automatique → grille / montrer la force de l'OMR /
> indiquer tout ce qui a été fait".

### 4.1 Objectifs et principe de base  ← répond directement aux annotations p.8
- **Démarrer par les objectifs** (les "Objectif BI 1/2" du diagramme d'exigences).
- **Le principe de base en un paragraphe** : lire une grille → analyser l'harmonie →
  projeter l'info utile sur les touches en temps réel, synchronisé à un backing track.
- **Réalité augmentée vs réalité diminuée** : augmentée = on éclaire des notes utiles ;
  diminuée = on en retire pour contraindre (Contour, Flow, Start&End). Cadre conceptuel fort.

### 4.2 Diagramme d'ensemble de l'artefact  ← "ajouter un diagramme qui explique l'ensemble"
- Reprendre/refaire le **schéma du système** (Fig.3 du DS : projecteur / piano / ordi).
- Ajouter le **diagramme des exigences** (Fig.1 du DS) — déjà fait, le réutiliser.
- Diagramme de flux **analyse automatique → grille** (lead sheet → parser → harmonie → projection).

### 4.3 Le contexte musical : pourquoi un backing track
- Justification pédagogique (le jazz n'a de sens que dans une grille qui tourne).
- Mentionner basse + batterie + comping (répond à l'annotation p.12 "et l'ajout de
  la basse + du drum ?").

### 4.4 L'OMR et la lecture de la grille  ← "montrer la force de l'OMR (les tests)"
- Expliquer le rôle de l'OMR [15] : photo/scan d'un lead sheet → grille numérique.
- **Mettre en avant les tests** réalisés (cf. proto-media) qui démontrent sa valeur.
- Statut réel : intégré ? ou MusicXML/TSV préconçus ? → dire ce qui a été fait.

### 4.5 Les 5 exercices (cœur conceptuel)  ← "indiquer tout ce qui a été fait"
Pour chacun : justification pédagogique + catégorie (classification 6 frameworks) +
augmentée/diminuée. Déjà bien décrits dans le DS p.10-11, à reprendre + photos réelles
(Fig.4 du DS = Start&End sur Gm7). Les 5 : **Mode libre** (cat.1), **Guide Tone** (cat.2),
**Contour** (cat.6), **Flow** (cat.6), **Start & End Note** (cat.6).

---

## 5. Solution technique  — viser ~8-12 pages  ← chapitre "prompter Claude Code souvent"

> Notes de réunion : "architecture du code / expliquer les éléments techniques /
> regarder Carusi / diagramme de phase haut niveau".
> Modèle Carusi "Implémentation" : Architecture (modélisation + déploiement + structure
> fichiers) → Backend → Frontend (cas d'usage + interface).

### 5.1 Architecture générale
- **Diagramme de modules** (les 8 modules du pipeline — voir CLAUDE.md "Module Pipeline").
- **Structure des fichiers/dossiers** (comme Carusi p.25) — `src/leadsheet_utility/`.
- Choix techniques clés + **justification** (pygame-ce multi-fenêtres, FluidSynth
  offline, harmonie pure-python, homographie OpenCV).

### 5.2 Tableau de la stack technique  ← annotation p.13 "interprétez le tableau, vos choix"
> Patrick refuse le tableau "LLM recommande X". **Remplacer** par : ce qu'on a CHOISI
> et POURQUOI. Le vrai stack final (≠ spéculation du DS) :
> Python 3.13, pygame-ce, FluidSynth + SoundFont, OpenCV (homographie), numpy,
> harmonie maison (pas music21), Poetry. → 1 tableau "besoin → choix → justification".

### 5.3 Diagrammes de phase / séquence haut niveau  ← demande explicite Patrick
- Diagramme de **phases** : démarrage → chargement grille → analyse → rendu audio
  parallèle (4 couches) → count-in → boucle de jeu (projection+HUD+chart).
- Diagramme de **séquence** de la synchro : timeline (perf_counter) → projection menée
  par `_PROJECTION_LEAD_SECONDS - audio_delay_ms`.
- Style de référence : Carusi (diagramme de déploiement / cas d'usage).

### 5.4 Sous-systèmes (un bloc chacun, prompter le code pour les détails)
- **Harmonie** : table qualité→gamme, arithmétique mod-12, guide tones, 7 règles de contexte.
- **Backing** : walking bass algorithmique, drums swing, comping drop-2/3 voice-leadé,
  rendu par couches parallèles (GIL libéré), mix numpy.
- **Projection / calibration** : layout 88 touches, homographie, UI calibration 5 phases.
- **Exercices** : pipeline d'overlays composables (base → chord-tone → root → start&end ;
  Contour en pré-filtre).
- **Timeline & mode boucle** : horloge wall-clock, wrap-around, forme temporaire.

---

## 6. Évaluations  — viser ~8-12 pages (incl. résultats)

> Note de réunion la plus stricte : "QUE par rapport à la QR ! répondre à la QR".
> Modèle Carusi : **séparer Déroulement (protocole) et Résultats (analyse)**.
> Reprendre les méthodes d'ImproVisAR [13] (déjà prévu dans le DS).
>
> **Sources des résultats (sous-projet stats, déjà produit et vérifié) :**
> - Plan d'analyse détaillé + intendance des entretiens : `rapport/plans/plan-analyse-tests.md`.
> - Méthodo statistique (scoring, Wilcoxon exact, tailles d'effet, limites n=8) : `rapport/plans/guide-interpretation-stats.md`.
> - Données + scripts + figures : `rapport/stats/` (`README.md`, `SHEETS-LAYOUT.md`,
>   `data/*.csv`, `results/wilcoxon_summary.md`, `figures/*.png`).
>
> ⚠️ **Deux corrections vs DS** (le dispositif réellement administré a changé) :
> 1. **Pas de CSI.** Le protocole a été resserré (anti-fatigue, ~1 h) à **3 mesures
>    directement reliées aux QR** : charge (RTLX), anxiété (STAI-6), confiance (auto-eff.).
>    C'est mieux cadré pour Patrick ("que par rapport à la QR") — STAI-6 opérationnalise
>    en plus le **thème anxiété** du Thème B (état de l'art).
> 2. **n = 8** (corriger partout le "9 participants" du planning).

### 6.1 Déroulement de l'évaluation (protocole)
- **Design intra-sujet AVEC/SANS**, n = 8. **AVEC** = Free Mode projeté (R.HAND) ;
  **SANS** = projecteur éteint. **Grille (fenêtre chart iReal) + backing track dans les
  DEUX conditions.** 2 morceaux/personne, **inconnus** et de **difficulté comparable**
  (1 par condition), ~4 min main droite, séance ~1 h.
- **Protocole resserré vs cadrage initial** (anti-fatigue questionnaire) : ne subsistent
  que les instruments reliés aux QR — à **dire et justifier** (répond à "que par rapport à la QR").
- **Le tableau QR → construit → instrument → hypothèse** (= LA figure que Patrick veut) :

  | Construit | Instrument | Échelle | H1 | QR |
  |---|---|---|---|---|
  | Charge cognitive perçue | **NASA-TLX brut (RTLX)**, 6 dim. | 0–100 | AVEC < SANS | QR1 (charge) |
  | Anxiété-état | **STAI-6** | 20–80 | AVEC < SANS | QR2 (oser / blocage) |
  | Auto-efficacité tâche | **Bandura ad hoc** (items 7–10) | 1–7 | AVEC > SANS | QR2 (confiance) |
  | Vécu / apprentissage / créativité | **entretien semi-structuré** | — | analyse thématique | QR1 + QR2 |
  | Profil (descriptif) | **Q0** | — | caractérisation échantillon | — |

- **Méthodologie statistique** : Wilcoxon des rangs signés apparié, **p EXACT** (n ≤ 50),
  **unilatéral** dans la direction prédite, **taille d'effet r_rb (Kerby) + dz**, compteur
  **k/n**. **Deux chemins, une seule source de vérité** : (1) **tableur Google Sheets +
  calculateur en ligne = source auditable défendable au jury** (saisie brute → composites →
  W/p/r_rb à la main, cf. `SHEETS-LAYOUT.md`) ; (2) `present.py` = **figures uniquement**
  (ne recalcule rien) ; (3) `analyze_tests.py` = **recoupement** (concorde, à lancer une fois).

### 6.2 Partie 1 — Évaluation experte (interview Patrick Roth)  ← "les highlights"
- Patrick a testé l'artefact ; restituer son point de vue **pédagogique et cognitif**.
- Cadrer ses retours autour de la QR (note réunion : "tourner autour de la QR").

### 6.3 Partie 2 — Tests utilisateurs (résultats)

**Ce qu'on présente, et où (ne PAS tout mettre dans le corps) :**
- **Profil des participants** (Q0, tableau P01–P08 anonymisé) + synthèse **médiane/étendue**
  (n=8 → **pas** de moyenne±ET) + effectifs catégoriels + **2-3 verbatim de l'item 11**
  ("le plus difficile dans l'impro") — c'est de l'or pour relier au problème de charge / oser.
  Source : `data/q0_profil.csv`.
- **Pas le brut item-level dans le corps.** On présente les **scores composites appariés**
  (8 lignes × 3 mesures, AVEC/SANS/d) — `data/scores_tableur.csv`. Les feuilles de saisie
  brutes (16 lignes × ~22 items) **et** les onglets Wilcoxon du tableur → **annexe** (auditable).
- **Tableau de résultats Wilcoxon** (= `results/wilcoxon_summary.md`, condensé des onglets
  `wilcoxon_*`) — **chiffres réels, vérifiés et reproductibles** :

  | Mesure | H1 | Mdn AVEC | Mdn SANS | W | p (uni) | r_rb | dz | k/n |
  |---|---|---|---|---|---|---|---|---|
  | **RTLX** (charge) | AVEC < SANS | 33.3 | 54.2 | 9 | .125 | **−0.50** (grand) | −0.44 | 6/8 |
  | **STAI-6** (anxiété) | AVEC < SANS | 33.3 | 46.7 | 10 | .156 | **−0.44** (moyen) | −0.47 | 5/8 |
  | **Auto-eff.** (confiance) | AVEC > SANS | 4.2 | 4.4 | 9 | .234 | **+0.36** (moyen) | +0.23 | 4/7 (1 nul) |

  > ⚠️ **Cadrer en TENDANCES de taille d'effet dans le sens prédit — PAS en "significatif".**
  > p > .05 partout : étude **sous-puissante à n=8**. Message honnête (cf. CLAUDE.md) :
  > effets **moyens-à-grands, cohérents, tous dans le sens prédit**. La taille d'effet et la
  > cohérence individuelle portent le résultat, pas le p. **La confiance (auto-eff.) bouge
  > le moins** (+.36, 4/7, 1 nul) → résultat nuancé à assumer.
- **4 figures** (générées par `present.py` → `rapport/stats/figures/`) :
  - `slope_rtlx.png` · `slope_stai6.png` · `slope_selfeff.png` — **un trait par participant
    (SANS→AVEC)**, **vert** si dans le sens H1, **rouge** à contre-sens, médiane en gras.
    Avec n=8 **plus honnête qu'un barplot moyen** : on voit **qui** bouge et **dans quel
    sens** — on peut **pointer les 2-3 traits rouges** (cf. §6.4).
  - `tlx_subscales.png` — **médianes des 6 dimensions NASA-TLX** (AVEC vs SANS) : montre
    **quelle** charge baisse (mentale / effort / frustration) → triangulation avec STAI-6.
- **Analyse thématique des entretiens** : matrice **thème × participant** (framework
  analysis) — les "tendances thématiques" demandées. Grille de codage + procédure :
  `plan-analyse-tests.md` §7. Pour chaque thème : **combien de participants, direction,
  1-2 verbatim**.
- **Vidéos** : support, "pas si important" — seulement si ça sert la QR (montage 2-3 testeurs).

### 6.4 Discussion — réponse aux QR (+ l'anomalie experts = effet d'inversion d'expertise)

- **QR1 (charge)** : RTLX baisse AVEC (r_rb **−.50**, 6/8), porté par les dimensions
  **mentale / effort / frustration** (`tlx_subscales`). **QR2 (oser)** : anxiété STAI-6
  baisse (**−.44**, 5/8) ; auto-efficacité monte mais **faiblement** (+.36, 4/7).
- **L'anomalie EST le résultat le plus intéressant (et il confirme l'intuition terrain) :**
  les participants **à contre-sens sont systématiquement les improvisateurs jazz les plus
  expérimentés** — **P04** (impro quasi quotidienne, niveau auto-éval 6/7, "défilement
  difficile" **1/7**), **P07** (20 ans de jazz, iReal régulier), **P08** (iReal régulier).
  À l'inverse, les **plus gros bénéficiaires** sont les **moins expérimentés** / ceux qui
  trouvent la grille la plus dure — **P01, P05, P06** (niveau impro 1-2/7, défilement 6-7/7).
- **Explication théorique (← renvoie au Thème B de l'état de l'art) :**
  - **Effet d'inversion d'expertise** (*expertise reversal effect*, Kalyuga & Sweller) : un
    échafaudage qui décharge le débutant devient **redondant** chez l'expert — traiter
    l'info redondante **ajoute** de la charge extrinsèque. P04 note que la grille ne lui est
    **pas** difficile (1/7) : rien à décharger → les lumières = surcharge pure.
  - **Effet de redondance / partage d'attention** : la fenêtre **chart iReal** est présente
    dans les **deux** conditions ; les experts (P07/P08 = lecteurs iReal réguliers) **lisent
    les chiffrages** qu'ils maîtrisent → le balisage clavier devient un **canal visuel
    concurrent**. La projection est alors un **fardeau**, pas une aide. ← exactement le constat.
  - **Triangulation quanti ↔ quali** (ce que Patrick demande) : taguer dans les entretiens
    "lumières trop rapides / je lisais la grille / je connais déjà les accords" et
    **superposer ces verbatim aux traits rouges** des slope plots.
- **Lecture "modérateur" (descriptive, n=8 → on DÉCRIT, on ne TESTE pas)** : trier P01–P08
  par années de jazz / niveau d'impro rend l'inversion **visible à l'œil** (bénéfice ↘ quand
  expertise ↗). **Motif descriptif**, pas corrélation testée (pas de p sur n=8).
- **Limites** : n=8 sous-puissant ; **morceau différent entre conditions sans
  contrebalancement** (effet-morceau / ordre non neutralisés, seulement atténués par
  l'appariement intra-sujet + difficulté comparable) ; auto-efficacité ad hoc non validée ;
  STAI-6 à chaud rétrospectif ; mono-séance (pas de mesure de transfert).

---

## 7. Conclusion  — viser ~2-3 pages

- Synthèse : ce qui a été construit + ce que l'évaluation montre vs la QR.
- Reprendre des éléments du DS (motivation perso jazz/CPMDT, lien fort avec le sujet Roth).
- **Limites** (honnête) : OMR partiellement intégré, planéité homographie touches noires,
  échantillon de test réduit.
- **Travaux futurs** = stretch goals SPEC §12 : calibration caméra automatique, piste
  comping piano séparée.

---

## 8. Bibliographie + Annexes

- Biblio : 15 réfs déjà présentes [1]-[15]. **À enrichir** : refs charge cognitive /
  anxiété (thème B), réf DSR (comme Carusi [22]).
- Annexes (modèle Carusi) : "Revue de quelques livres de jazz", guides d'interview,
  questionnaires (Q0, NASA-TLX, STAI-6 + auto-efficacité Q2, guide d'entretien),
  **feuilles de saisie brutes + onglets Wilcoxon du tableur** (source auditable),
  transcriptions/tendances, captures du système.
- Ajouter **Table des figures** et **Table des tableaux** (Carusi les a).

---

## 9. Budget de pages (cible 40-60)

| Chapitre | Pages |
|---|---|
| Introduction | 3-4 |
| État de l'art | 10-14 |
| Méthodologie (DSR) | 1-2 |
| Solution conceptuelle | 8-10 |
| Solution technique | 8-12 |
| Évaluations (+ résultats) | 8-12 |
| Conclusion | 2-3 |
| **Total (hors annexes/biblio)** | **40-57** |

---

## 10. Bibliothèque de prompts Claude Code (à copier-coller pendant la rédaction)

Le code est la source de vérité. Prompts utiles à me redonner section par section :

**Pour la Solution technique :**
- « Décris l'architecture de `<module>` (rôle, entrées/sorties, fichiers clés) pour
  un paragraphe de rapport, niveau ingénieur, en français. »
- « Génère un diagramme Mermaid de phases du démarrage à la boucle de jeu de `main.py`. »
- « Génère un diagramme de séquence Mermaid de la synchronisation projection/audio. »
- « Liste le stack technique réel avec, pour chaque techno, le besoin et la justification
  du choix (format : besoin → choix → pourquoi). »
- « Explique le rendu audio en couches parallèles et pourquoi le GIL n'est pas un goulot. »

**Pour la Solution conceptuelle :**
- « Pour chaque exercice (Mode libre, Guide Tone, Contour, Flow, Start&End), donne :
  justification pédagogique, catégorie de framework, et si c'est de la réalité
  augmentée ou diminuée. »
- « Résume le rôle réel de l'OMR dans le projet et le statut d'intégration. »

**Pour l'état de l'art (thème B, à compléter par de la vraie recherche) :**
- « Donne les concepts clés de la Cognitive Load Theory pertinents pour une tâche
  temps réel comme l'improvisation, et comment la visualisation décharge la mémoire
  de travail. » *(puis vérifier/citer de vraies sources académiques)*

**Vérifs :**
- « Le brouillon dit X sur `<sous-système>` — est-ce que ça correspond au code actuel ? »

---

## 11. Ordre de rédaction conseillé

1. **Solution technique** (le code est frais et stable — facile à écrire, gros volume).
2. **Solution conceptuelle** (s'appuie sur le DS déjà rédigé + corrections Patrick).
3. **État de l'art** (réutiliser DS + écrire le thème B charge cognitive/anxiété).
4. **Évaluations** (dès que l'analyse initiale des tests est prête → à envoyer à Patrick).
5. **Introduction + Conclusion** en dernier (plus faciles une fois le corps écrit).
6. **Méthodologie** (court, à caler n'importe quand).

> Rappel réunion : envoyer le rapport à Patrick **mercredi soir** ; il renvoie un
> document annoté et tu réponds. Tu peux lui laisser des feedbacks/questions en marge,
> il y répond (comme ce cycle DS).

---

## 12. Planning jour par jour — deadline mercredi 24 juin (soir)

7 jours, en **blocs du soir** la semaine, **week-end plus chargé**. Le brouillon DS et le
code couvrent ~50% du contenu → surtout de l'assemblage.
**Capacité réelle** : jeu soir = interview prof ; ven soir = questionnaires + sessions de
test (données dispo dès 16h) ; sam/dim = grosses journées (chapitres techniques) ;
lun/mar soir = blocs plus courts ; mer = finalisation. Cible quotidienne pour suivre 40-60 p.

| Jour | Date | Bloc | Focus | Livrable | ~p cumul. |
|---|---|---|---|---|---|
| **Jeu** | 18/06 | soir | **Setup + Évaluations (1/2)** : créer le Google Doc (toutes sections) ; rédiger l'**interview enseignant** (highlights pédago/cognitif de Patrick, cadrés sur la QR) | Squelette + section interview prof | ~3 |
| **Ven** | 19/06 | soir (données 16h) | **Évaluations (2/2)** : protocole AVEC/SANS mappé aux QR, **résultats questionnaires** (RTLX / STAI-6 / auto-efficacité — pas CSI), **analyse thématique des sessions** (8 participants), interprétation + discussion QR (anomalie experts) → **envoyer à Patrick** | Chapitre éval fini (~11 p) + envoi | ~11 |
| **Sam** | 20/06 | journée | **Solution technique** : archi + structure fichiers + tableau stack justifié + diagrammes phase/séquence + 5 sous-systèmes | Chapitre technique fini (~10 p) | ~21 |
| **Dim** | 21/06 | journée | **Solution conceptuelle** : objectifs+principe, diagramme d'ensemble, RA/réalité diminuée, contexte musical, OMR+tests, 5 exercices (DS p.10-11 + photos) | Chapitre conceptuel fini (~9 p) | ~30 |
| **Lun** | 22/06 | soir | **État de l'art — thèmes A & C** (condenser DS p.2-6) + **recherche thème B** (3-5 réfs charge cognitive/anxiété) | Thèmes A+C + biblio thème B repérée | ~37 |
| **Mar** | 23/06 | soir | **État de l'art — thème B** (rédiger) + **Méthodologie (DSR)** + **Introduction** + **Conclusion** + intégrer retour Patrick sur l'éval | Tout rédigé | ~47 |
| **Mer** | 24/06 | soir | **Finalisation** : relecture, passage "nous", légendes figures, table des figures/tableaux, biblio, mise en page, export PDF → **ENVOI le soir** | PDF envoyé ✅ | 40-57 |

### Jalons / dépendances
- **Données de test = vendredi 16h (fixe).** L'éval s'écrit jeu (interview prof, sans
  données) + ven soir (questionnaires + sessions, avec données). Une *analyse initiale*
  suffit (note réunion).
- **Boucle de feedback Patrick** : éval envoyée ven soir → retour week-end/lundi → intégré
  mardi. C'est le but de sa demande ("voir comment tu interprètes les résultats").
- **Préparer JEUDI la grille de codage thématique** (thèmes à repérer dans les interviews :
  charge cognitive réduite, confiance à se lancer, découverte créative, distraction/surcharge…)
  → vendredi soir = taguer les citations sur une grille prête, pas inventer les catégories à 17h.
- **Figures à préparer** (en avance, le soir) : diagramme d'ensemble artefact, diagramme
  modules, diagramme phases, diagramme séquence synchro, photos système.

### Coussin / gestion du risque
- Pas de vraie journée tampon → **mar = la marge**. Si retard, rogner d'abord l'état de
  l'art (condenser thème A) et la profondeur des sous-systèmes techniques, jamais l'éval.
- Les 2 gros chapitres (technique, conceptuel) sont placés sam/dim (journées pleines) :
  c'est là qu'est le gros volume, ne pas le repousser en semaine.
- Cible minimale mercredi : **40 p cohérentes** > 55 p inégales. Patrick renvoie des
  annotations et tu réponds → complet mais perfectible suffit.
