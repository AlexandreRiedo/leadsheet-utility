# Plan d'analyse des tests utilisateurs (8 participants)

> But de ce document : savoir **comment dépouiller, présenter et analyser** les
> données des sessions de test (12–19 juin 2026), section par section du chapitre
> *Évaluations* (cf. `plan-redaction.md` §6).
> Sources : le protocole réellement administré (`proto-media/8-working-on-tests/protocole/`),
> les notes méthodo de chaque questionnaire, le cadrage QR (`cadrage-QR-evaluation.md`),
> les notes de réunion finale Roth.
> Répond aux 4 questions posées : (1) présenter le Q0, (2) présenter les questionnaires +
> guide + protocole, (3) analyser NASA-TLX et l'assurance, (4) valider l'idée d'entretien.

---

## 0. Le dispositif réellement administré (à poser noir sur blanc)

Le `cadrage-QR-evaluation.md` explorait une grosse batterie (NASA-TLX + AttrakDiff + TAM
+ SUS + CSI + proxy MIDI…). **Ce n'est pas ce qui a tourné.** Le protocole final
(`info1-PROTOCOLE.md`) est volontairement resserré — il faut le **dire et le justifier**
dans le rapport (anti-fatigue questionnaire sur une session d'~1 h, cf. question ouverte 6
du cadrage). Le set d'instruments qui a survécu :

| Construit | Instrument | Quand | Hypothèse |
|---|---|---|---|
| Charge cognitive perçue | **NASA-TLX brut (RTLX)**, 6 dimensions | après chaque morceau | AVEC < SANS |
| Anxiété-état | **STAI-6** (Partie A de Q2) | après chaque morceau | AVEC < SANS |
| Auto-efficacité tâche | **Bandura ad hoc** (Partie B de Q2, items 7–10 + item 11 global) | après chaque morceau | AVEC > SANS |
| Vécu / apprentissage / créativité (exploratoire) | **entretien semi-ouvert** (Q3) | fin de session | analyse thématique |
| Profil (descriptif) | **Q0** | début | caractérisation de l'échantillon |

**Design** : intra-sujet, 2 conditions **AVEC** (Free Mode projeté, R.HAND) vs **SANS**
(projecteur éteint, grille + backing dans les deux cas). 2 morceaux/personne, choisis pour
être **inconnus du participant** et de **difficulté comparable** (niveau S/E/M/P du morceau).
Le contrebalancement formel à 4 cas prévu au cadrage **n'a pas été appliqué** (pas de rotation
systématique morceau↔condition ni de l'ordre). **n = 8.** → un score par instrument **par
condition et par personne** → **comparaison appariée AVEC vs SANS (Wilcoxon)** pour chaque mesure.

> **À écrire dans 6.1 :** « Le protocole a été resserré par rapport au cadrage initial pour
> tenir en une séance d'~1 h sans fatigue questionnaire ; ne subsistent que les instruments
> directement reliés aux deux QR (charge cognitive ; anxiété + auto-efficacité) plus
> l'entretien exploratoire. » Cela répond à Patrick (« que par rapport à la QR ! »).

---

## 1. Workflow de dépouillement (tes 3 idées, validées et précisées)

Tes trois idées sont bonnes ; voici le réglage fin.

### 1.1 Transcription des entretiens — Whisper ✅

- **Modèle** : `large-v3` si la machine suit, sinon `medium`. En-dessous, le français
  d'oral spontané (hésitations, jargon jazz) décroche. → `faster-whisper` (4–8× plus
  rapide, même qualité) ou **WhisperX** si tu veux des **timestamps mot-à-mot** et une
  **diarisation** (séparer expérimentateur / participant·e — utile, le guide est en
  question-réponse).
- **Langue forcée** : `--language fr` (ne pas laisser l'auto-détection hésiter).
- **Sortie** : un `.txt` (ou `.srt` horodaté) **par participant**, nommé `P01_entretien.txt`
  … `P08_entretien.txt`. Garde le `.srt` : un timestamp à côté d'une citation = tu
  retrouves l'extrait vidéo en 2 s pour le montage demandé par Patrick.
- **Relecture obligatoire** : Whisper invente sur les noms propres et le vocabulaire jazz
  (« ii-V-I », « upper structures », noms de morceaux). Passe rapide au casque, corrige
  juste les passages que tu comptes citer.

### 1.2 Saisie des questionnaires chiffrés — scanner 1 feuille de réf + Excel ✅

Pour n=8 × 2 conditions = **16 instances**, chacune ~10 valeurs numériques : la saisie
manuelle est la bonne approche (un OCR de 16 feuilles cochées à la main coûterait plus en
correction qu'en frappe). **Scanne UNE feuille remplie** (une de chaque : NASA-TLX,
assurance) comme référence visuelle/annexe, puis saisis dans **un seul classeur**.

**Schéma recommandé — format « large » (1 ligne = 1 morceau joué), lisible à l'œil :**

```
participant | niveau | morceau | condition | ordre
| tlx_mental | tlx_physique | tlx_temporel | tlx_perf | tlx_effort | tlx_frustration
| stai_calme | stai_tendu | stai_emu | stai_decontracte | stai_satisfait | stai_inquiet
| se_q7 | se_q8 | se_q9 | se_q10 | conf_globale_q11
```

- 16 lignes (P01-AVEC, P01-SANS, …, P08-SANS).
- Saisis les **valeurs brutes** (TLX 0–100 par pas de 5 ; STAI 1–4 ; auto-eff 1–7 ;
  q11 0–10). **Ne calcule rien à la main** : les scores composites (RTLX, STAI-6,
  auto-eff) et les inversions se font par formule (cf. §4–5). Saisir du brut = traçable
  et ré-analysable.
- **Q0** : `rapport/stats/data/q0_profil.csv` — 1 ligne par participant avec les champs du §2
  (item 11 texte libre = colonne `plus_difficile_texte`).
- **Écarts/incidents** (feuille `s1` : tempo réduit ? reclassé ? morceau C/D ?) : les colonnes
  de contexte de `responses.csv` (`niveau`, `morceau`, `ordre`) les portent en partie ;
  le reste va dans le **tableau « écarts au protocole »** du rapport (§8).

> **✅ FAIT — décision retenue : CSV + script CLI.** Le scaffolding est construit dans
> `rapport/stats/` (voir §10) : tu remplis `data/responses.csv` (valeurs brutes), tu lances
> `poetry run python rapport/stats/analyze_tests.py`, et il sort scores composites, table
> appariée, Wilcoxon **exact**, tailles d'effet et figures. **Zéro calcul manuel.** Le détail
> méthodo (lire/rédiger chaque sortie) est dans `guide-interpretation-stats.md`.

### 1.3 Entretiens — capture ≠ analyse (corrige l'idée du tableau unique)

Ton idée « questions → réponses → analyse » en un seul tableau **mélange deux couches**.
Sépare-les (détaillé au §7) :

- **Couche capture** (Google Docs OK) : par participant, la transcription nettoyée, qu'on
  peut effectivement ranger par question du guide.
- **Couche analyse** : une **matrice thème × participant** (analyse de cadre / *framework
  analysis*). C'est elle qui produit les **« tendances thématiques »** demandées par
  Patrick — on lit **une colonne-thème en travers des 8 personnes**, pas les réponses
  d'une personne en travers des questions.

---

## 2. QUESTION 1 — Présenter les données du Q0 (profil de l'échantillon)

C'est la **caractérisation de l'échantillon** (Carusi : un tableau « participants » en
début de Résultats). Deux objets :

### 2.1 Tableau « Profil des participants » (anonymisé P01–P08)

Une ligne par participant, colonnes tirées du Q0 :

| Col | Source Q0 | Type |
|---|---|---|
| Code | — | P01…P08 |
| Âge | item 1 | continu |
| Instrument principal (années) | item 3 | texte + n |
| Années de piano | item 4 | continu |
| Années de jazz | item 6 | continu |
| Lecture de grille | item 7 | ordinal (4 niveaux) |
| Fréquence d'impro | item 8 | ordinal (5 niveaux) |
| Niveau impro auto-évalué | item 9 (1–7) | ordinal |
| « Grille qui défile = difficile » | item 10 (1–7) | ordinal |
| Usage iReal Pro | item 13 | ordinal |
| Déjà essayé piano augmenté | item 14 | oui/non |
| **Niveau assigné** | S/E/M/P (feuille session) | catégoriel |

### 2.2 Synthèse agrégée (sous le tableau)

- **Continus** (âge, années piano/jazz, items 9 & 10) : **médiane + étendue (min–max)**.
  Avec n=8 on **ne fait pas de moyenne±écart-type** comme si c'était gaussien ; médiane
  + étendue est honnête. Un petit nuage de points ou un strip-plot suffit si tu veux du
  visuel.
- **Catégoriels/ordinaux** (formation, lecture de grille, fréquence d'impro, iReal,
  piano augmenté) : **effectifs** (« 5/8 lisent une grille “à l'aise” ou + »).
- **Répartition par niveau** S/E/M/P : compte (« 1 S, 4 E, 2 M, 1 P »).

### 2.3 Item 11 (texte libre : « le plus difficile dans l'impro jazz »)

Mini-analyse thématique (3–4 catégories : *trouver les notes justes / suivre le tempo qui
défile / oser-bloquer / cohérence du discours*). **C'est de l'or pour l'intro et la
discussion** : ça montre, dans les mots des participants, le problème de **charge
cognitive** et le **« oser se lancer »** — exactement les deux QR. Cite 2–3 verbatim.

### 2.4 À quoi sert le Q0 dans l'analyse (pas juste décoratif)

- **Validité** : item 2 (daltonisme). La projection code l'info en **rouge/orange/vert/
  bleu** → si un·e participant·e est daltonien·ne, c'est un **caveat de validité** à
  signaler, et un point d'interprétation pour son cas.
- **Modérateur descriptif** : items 9 (niveau) et 10 (difficulté perçue) servent à lire
  **qui** profite de l'aide. Avec n=8 on **ne teste pas** une interaction, mais on
  **décrit** le motif (« les 3 participants les moins expérimentés montrent la plus
  grosse baisse de charge AVEC ; le participant P du niveau avancé montre l'effet inverse,
  cohérent avec le plafond “lumières trop vite” signalé par l'expert »). Ça relie
  directement à l'interview Evaristo (§3 du cadrage).
- **Familiarité** (item 12) : justifie les substitutions morceau C/D et écarte le biais de
  familiarité dans l'interprétation.

---

## 3. QUESTION 2 — Présenter les 2 questionnaires, le guide d'entretien et le protocole

Principe Carusi (et demande de Patrick) : **séparer Déroulement (protocole) et Résultats
(analyse)**, et **toujours mapper sur la QR**. Règle de placement :

> **Corps du rapport = description + justification + renvoi.
> Annexes = les formulaires intégraux.** (Carusi met les questionnaires en annexe.)

### 3.1 Dans le corps (§6.1 « Déroulement de l'évaluation »)

1. **Le design en un paragraphe** : intra-sujet AVEC/SANS, 2 morceaux de difficulté
   comparable, main droite ~4 min, grille + backing dans les deux conditions, ~1 h.
2. **Le choix des morceaux** : explique que chaque participant a joué 2 morceaux **inconnus
   de lui** et de **difficulté comparable**, un par condition. Précise que le contrebalancement
   formel à 4 cas (prévu au cadrage) **n'a pas été appliqué** : l'effet d'ordre et l'effet-morceau
   ne sont donc **pas** neutralisés au niveau du groupe — à porter en **limite** (§6.4), atténués
   seulement par le design intra-sujet apparié et par la difficulté comparable des morceaux.
3. **Les instruments**, chacun en 2–3 phrases avec **la source validée** :
   - NASA-TLX **brut/RTLX** (Hart & Staveland 1988 ; version non pondérée justifiée par
     Hart 2006 ; traduction FR Cegarra & Morgado 2009). Adaptation musicale = uniquement
     les exemples entre parenthèses (à signaler).
   - **STAI-6** (Marteau & Bekker 1992 ; FR Schweitzer & Paulhan 1990). Signale les 2
     adaptations : consigne « pendant que vous jouiez » (mesure à chaud rétrospective) et
     imparfait.
   - **Auto-efficacité** : 4 items construits selon **Bandura (2006)**, items 7 & 10
     inspirés de Ritchie & Williamon (2011) ; **ad hoc, non validée** → à assumer comme
     limite. Item 8 = le mécanisme revendiqué par l'artefact ; item 9 = le « oser se
     lancer ».
4. **Le tableau QR → construit → instrument → hypothèse** (= le tableau du §0 ci-dessus).
   **C'est LA figure que Patrick veut voir** (« arrivez-vous à répondre à vos QR ? »).
5. **Profil des participants** (le tableau §2) et **écarts au protocole** (tempos réduits,
   reclassements, substitutions, daltonisme) — honnêteté méthodologique.
6. **Renvois** : « le détail des formulaires figure en annexe X (Q0, NASA-TLX, Q2 hybride,
   guide d'entretien) ».

### 3.2 Le guide d'entretien dans le corps

Ne recopie pas les 9 questions ; **décris la structure thématique** (incident critique →
comparaison avec/sans → agentivité → attention → gêne/lisibilité → rétention → image du
dispositif → pari d'auto-évaluation → clôture) et **justifie 2 choix de conception** (cf.
§7.1). Le guide complet va en annexe.

### 3.3 En annexe

Formulaires intégraux Q0 / NASA-TLX / Q2 / Q3 + feuille de session + consentement. Tu les
as déjà en PDF propres dans `protocole/pdf/` → prêts à coller.

---

## 4. QUESTION 3a — Analyser le NASA-TLX

### 4.1 Du brut au score (RTLX)

- Chaque dimension est lue **0–100** (21 graduations, pas de 5). Une croix entre deux
  graduations → arrondir au pas de 5 le plus proche.
- **Performance** est orientée **Réussie→Ratée** : un score élevé = mauvaise perf =
  **charge élevée**, cohérent avec les 5 autres dimensions. **Aucune inversion à la
  saisie** (la note méthodo le dit).
- **RTLX = moyenne non pondérée des 6 dimensions** (pas de comparaisons par paires).
  En tableur : `=MOYENNE(tlx_mental:tlx_frustration)` pour chaque ligne.

→ un RTLX par (participant × condition). Différence appariée `d = RTLX_AVEC − RTLX_SANS`
(hypothèse : d < 0).

### 4.2 Ce qu'on présente

1. **Tableau apparié** : P01…P08 × {RTLX AVEC, RTLX SANS, d}.
2. **Synthèse** : **médiane (IQR)** de RTLX par condition + médiane des d.
3. **Test** : **Wilcoxon des rangs signés apparié** (AVEC vs SANS), **p exact**
   (pas l'approximation normale — n trop petit), **unilatéral** justifié par l'hypothèse
   directionnelle (ou bilatéral + mention de la direction, plus prudent).
4. **Taille d'effet** : **corrélation rang-bisériale appariée** `r = (W+ − W−)/ΣW`
   (ou `r = Z/√N`). **Indispensable avec n=8** : c'est elle qui porte le résultat, pas p.
5. **Compteur direction** : « k/8 participants vont dans le sens prédit » (lecture immédiate).
6. **Figure clé** : **slope plot apparié** (une ligne par participant reliant son SANS à
   son AVEC). Avec n=8, c'est **plus honnête qu'un barplot moyen** : on voit qui bouge,
   et dans quel sens.

### 4.3 La décomposition par dimension (analyse fine, à valoriser)

Ne te limite pas au RTLX global : **3 dimensions racontent la QR**.

- **Exigence mentale** = le cœur du claim (l'artefact décharge « quelles notes jouer ? »).
- **Exigence temporelle** = le **plafond « lumières trop vite »** signalé par Evaristo.
  Si AVEC ne baisse pas (voire monte) sur grille rapide / niveau avancé, c'est **le
  résultat le plus intéressant du mémoire**, pas un échec.
- **Frustration** = relie à l'anxiété (triangulation avec STAI-6).

→ **Barres groupées AVEC vs SANS sur les 6 dimensions (médianes)** : une figure très
parlante. Mais traite les tests par-dimension comme **exploratoires** (cf. §6, multiplicité).

---

## 5. QUESTION 3b — Analyser le questionnaire d'assurance (DEUX scores, séparés)

> ⚠️ **Le piège n°1.** « L'assurance » n'est **pas un score unique**. C'est **deux
> construits distincts**, de **valence opposée**. Les rapporter séparément (la note méthodo
> l'exige). Ne **jamais** moyenner STAI-6 et auto-efficacité ensemble.

### 5.1 Score A — STAI-6 (anxiété-état, validé)

- Réponses **Non / Plutôt non / Plutôt oui / Oui = 1 / 2 / 3 / 4**.
- **Inverser** les items **positifs** (calme = item 1, décontracté = item 4, satisfait =
  item 5) : `valeur_corrigée = 5 − x`. Les négatifs (tendu, ému, inquiet) restent tels quels.
- **Score STAI-6 = (somme des 6 items corrigés) × 20/6** → étendue **20–80**, comparable
  au STAI-S complet. **Élevé = anxieux.** Hypothèse : **AVEC < SANS**.
- En tableur : `=(stai_tendu + stai_emu + stai_inquiet + (5-stai_calme) + (5-stai_decontracte) + (5-stai_satisfait)) * 20/6`.

### 5.2 Score B — Auto-efficacité tâche (ad hoc Bandura)

- Items **7–10**, échelle **1–7**, **aucune inversion**. **Score = moyenne(7..10).**
  Élevé = confiant. Hypothèse : **AVEC > SANS**.
- En tableur : `=MOYENNE(se_q7:se_q10)`.
- **Item 11** (0–10, confiance globale) = **mesure de contrôle** : sert de validation
  croisée du score B (ils doivent corréler) et de chiffre « grand public » facile à citer.

### 5.3 Ce qu'on présente

- **Deux tableaux appariés** (STAI-6 ; auto-efficacité), **deux Wilcoxon**, **deux tailles
  d'effet**, **deux slope plots** — exactement comme le RTLX (§4.2).
- **Triangulation** dans la discussion : si STAI-6 baisse **et** auto-efficacité monte
  AVEC, le récit « moins anxieux + plus capable » est solide. Si l'un bouge et pas l'autre,
  c'est **un résultat nuancé intéressant** (p. ex. « rassure sans rendre plus capable »).
- Relie **STAI-6 ↔ frustration TLX** et **auto-efficacité ↔ items 9 (oser) de l'entretien**.

---

## 6. Statistiques avec n=8 : ce qu'il faut faire (et dire)

- **Test** : **Wilcoxon des rangs signés apparié**, **p exact**, par mesure. C'est ce que
  le protocole a annoncé.
- **n=8 n'est pas désespéré** : si l'effet est **cohérent** (tous dans le même sens), le p
  exact bilatéral minimal est ≈ 0,008 → la significativité est **atteignable**. En
  revanche, un effet faible/irrégulier sera **sous-puissant** : c'est attendu, à assumer.
- **Ex æquo** : une différence nulle (d=0) est **retirée** → n effectif baisse (8→6 réduit
  la puissance). Note-le si ça arrive.
- **Mesures primaires pré-spécifiées** (3) : RTLX (QR1), STAI-6 et auto-efficacité (QR
  « oser »). Les **6 sous-dimensions TLX, l'item 11, les analyses par niveau** =
  **exploratoires** — présentées en descriptif, **pas** noyées sous une correction de
  Bonferroni qui tuerait toute lecture. Dis-le explicitement (« confirmatoire vs
  exploratoire »).
- **Compagnon paramétrique optionnel** : RTLX est quasi-continu (0–100) → tu **peux**
  ajouter un t apparié + **Cohen's dz** en appui. Pour STAI/auto-eff (dérivés d'ordinal),
  reste sur Wilcoxon.
- **Toujours : taille d'effet + figure appariée + compteur k/8.** Avec n=8, **l'effet et
  la cohérence individuelle priment sur le p.**
- **Limites à écrire** (§6.4 / conclusion) : petit échantillon, auto-efficacité non
  validée, **morceau différent entre conditions sans contrebalancement** (effet-morceau et
  effet d'ordre non neutralisés ; seulement atténués par l'appariement intra-sujet et le choix
  de morceaux inconnus de difficulté comparable), mesure à chaud rétrospective pour STAI, pas
  de mesure de transfert (mono-séance).

---

## 7. QUESTION 4 — L'idée du contenu d'entretien : validation + méthode d'analyse

### 7.1 Le guide lui-même est bien conçu (le dire dans le rapport)

Deux choix de conception **à mettre en valeur** (ils crédibilisent la méthodo) :

- **Incident critique en premier** (Q1) et **sonde de rétention avant tout debriefing**
  (Q6) : la mémoire des moments précis s'efface et les jugements globaux la recouvrent →
  poser le concret avant le global est une **bonne pratique d'entretien rétrospectif**.
- **Cadre neutre** : ne jamais dire que la projection « devrait aider », ne pas annoncer la
  comparaison → limite la **demande caractéristique** (biais de complaisance). À expliciter.
- **Le pari d'auto-évaluation (Q8)** est malin : la réponse « je pense avoir mieux joué
  avec/sans » se **confronte ensuite aux enregistrements** et au RTLX/perf → triangulation
  objective/subjective. (Tu ne peux plus changer le guide — les données sont prises — donc
  ici « valider » = **savoir quoi en tirer**.)

### 7.2 La méthode d'analyse : matrice thème × participant (PAS le tableau Q→R→analyse)

Patrick demande des **« tendances thématiques »**. Procédure légère type Braun & Clarke /
framework analysis :

1. **Grille de codage a priori** (déductive, dérivée du guide + des QR), à figer **avant**
   de te noyer dans les transcriptions. **13 thèmes, chacun ancré sur une question du guide
   Q3** : le recoupement thèmes ↔ questions a été fait (tout thème a une question source,
   toute question a une destination). Codes repris tels quels dans
   `templates/matrice-thematique.md` :
   - **T1** *Charge réduite / « je pensais à moins de choses »* : Q2 relance *charge* (QR1, TLX)
   - **T2** *Anticipation des changements d'accord* (vu venir vs subi) : Q2 relance *anticipation*
   - **T3** *Confiance / oser / prise de risque* : Q2 relance *assurance* + Q3 (QR2, auto-eff)
   - **T4** *Anxiété / blocage / sécurité* : Q2 relance *assurance* + Q1 incident (STAI-6)
   - **T5** *Agentivité : suggestion vs règle, transgression* (touche éteinte) : Q3 (dédiée)
   - **T6** *Partage de l'attention : yeux & oreilles, conflit lumière/oreille* : Q4 (dédiée)
   - **T7** *Gêne / lisibilité : trop vite, trop de touches, couleurs, latence* : Q5 (plafond Evaristo)
   - **T8** *Trace / rétention / formes sur le clavier* : Q6 (dédiée, transfert)
   - **T9** *Image / métaphore du dispositif* (partition / jeu vidéo / petites roues / GPS, prof) : Q7 + relance *prof*
   - **T10** *Désétayage / autonomie / s'en passer* (l'aide qui s'efface) : Q7 relance *détachement* **[ajout]**
   - **T11** *Motivation / envie de pratiquer* : Q7 relance *usage* **[scindé de l'ancien « image »]**
   - **T12** *Préférence avec / sans* : Q2 relance *préférence*
   - **T13** *Améliorations souhaitées / wishlist* : Q9 clôture (baguette magique) **[ajout]**
   + zone **émergente** (inductive). **À surveiller** : *Découverte créative / exploration*
   (l'ancien thème) **n'a pas de question dédiée** dans Q3, alors que la créativité est un
   construit déclaré au §0 : il restera **mince**, codé seulement depuis Q1 / Q3. Le rapporter
   en émergent, pas en colonne pleine, et l'assumer en limite si la matière manque.

   > **Recoupement guide Q3 ↔ thèmes (fait)** : les questions à colonne dédiée (Q3→T5, Q4→T6,
   > Q5→T7, Q6→T8, Q7→T9/T10/T11) sont bien couvertes. **T1-T4 + T12 dépendent des relances de
   > Q2** (posées « seulement si nécessaire ») : leur remplissage peut être **inégal** selon les
   > participants, à noter. **Q1 (incident critique)** n'a pas de colonne : son contenu se code
   > dans les thèmes (souvent T1/T3/T4) ou en émergent. **Q8 (pari)** n'est pas un thème : il va
   > dans le *tableau des paris* de la matrice (triangulation, cf. pt 4).
2. **Matrice** : **lignes = P01…P08, colonnes = thèmes**. Cellule = **verbatim codés**
   (citation courte + code participant). C'est ça qui remplace ton tableau unique : on lit
   **une colonne en travers des 8** = la tendance.
3. **Pour chaque thème** : *combien de participants l'évoquent*, *la direction*
   (positif/négatif/mitigé), *1–2 verbatim représentatifs*. → c'est le texte du §6.3.
4. **Triangulation quantitatif ↔ qualitatif** : superpose les thèmes aux scores. Ex. :
   « la charge temporelle ne baisse pas AVEC sur les morceaux rapides (TLX) **et** 5/8
   participants disent les lumières “trop rapides” (entretien) » → les deux se confirment.
   Confronte aussi le **pari Q8** au RTLX/perf mesuré (colonne *Concordance* du **tableau des
   paris** de la matrice).

> **Garde quand même une couche capture par question** (ton Google Doc, rangé par
> question) comme matériau brut horodaté — mais **l'analyse vit dans la matrice
> thématique**, pas dans le tableau Q→R.

### 7.3 Ce qu'on envoie à Patrick ce soir

Note de réunion : *« essayer de faire une analyse initiale et l'envoyer »* + *« tendances
thématiques »*. Donc, même incomplet : le **tableau de profil (Q0)**, les **slope plots +
Wilcoxon** des 3 mesures, et la **matrice thématique** avec 4–5 tendances et leurs verbatim.
L'objectif explicite de Patrick est de voir **comment tu interprètes** — une analyse
**initiale** suffit, il renvoie ses annotations.

---

## 8. Livrables figures/tableaux pour le chapitre Évaluations (checklist)

- [ ] **Tab. profil participants** (Q0) + synthèse médiane/étendue + effectifs
- [ ] **Tab. QR → construit → instrument → hypothèse**
- [ ] **Tab. assignation morceaux↔conditions** (par participant : morceau, condition, ordre)
- [ ] **Tab. données appariées scorées** (RTLX, STAI-6, auto-eff, conf q11) × condition
- [ ] **Fig. slope plots** ×3 (RTLX, STAI-6, auto-eff)
- [ ] **Fig. barres 6 dimensions TLX** AVEC vs SANS (médianes)
- [ ] **Tab. résultats Wilcoxon** (mesure, médiane AVEC, médiane SANS, W, p exact, taille
      d'effet, k/8)
- [ ] **Matrice thème × participant** (13 thèmes T1-T13 + Tcr, `templates/matrice-thematique.md`)
      + tableau de synthèse (thème, n, direction, verbatim) + **tableau des paris Q8**
- [ ] **Tab. écarts au protocole** (tempos, reclassements, substitutions, daltonisme)
- [ ] (support) **montage vidéo 2–3 testeurs** — « pas si important », seulement si ça sert la QR

---

## 9. Raccord avec la structure du rapport

Le chapitre **Évaluations** contient deux sections sœurs : l'**interview de Patrick**
(évaluation experte, *déjà rédigée*) et **« Sessions de tests avec 8 participants »**
(ci-dessous). Correspondance entre chaque sous-section du rapport, ce qui l'alimente dans
ce document (+ `guide-interpretation-stats.md`), et le §6 de `plan-redaction.md` :

| Sous-section du rapport | Alimentée par | `plan-redaction.md` |
|---|---|---|
| **À propos du protocole et des statistiques** | | §6.1 |
| └ Le protocole | §0 + §3 (+ profil §2) ; **inclure le tableau QR→instrument→hypothèse (§0)** + écarts au protocole | §6.1 |
| └ Méthodologie statistique | §6 + `guide` §1–3 et §6 (Wilcoxon exact, taille d'effet, directions par mesure, limites n=8) | §6.1 |
| **Résultats** | | §6.3 |
| └ Profil des participants | §2 (tableau + médianes/effectifs + item 11 texte libre) | §6.3 |
| └ NASA-TLX | §4 — RTLX global (§4.2) **+ 6 dimensions** (§4.3) | §6.3 |
| └ STAI-6 | §5.1 — anxiété ; hypothèse **AVEC < SANS** | §6.3 |
| └ Questionnaire de confiance | §5.2 — auto-efficacité ; hypothèse **AVEC > SANS** (+ item 11 contrôle) | §6.3 |
| └ Interviews semi-structurées post-expérimentales | §7 — matrice thème × participant, tendances | §6.3 |
| **Discussion — triangulation et réponse aux QR** *(à ajouter)* | §5.3 + §6 (triangulation) + §7.2 pt 4 — croise les 4 résultats, répond **QR1 (charge) / QR2 (oser)** | §6.4 |

> **Deux points à ne pas oublier** (cf. retour sur la structure) :
> 1. le **tableau QR → construit → instrument → hypothèse** (§0) doit figurer dans « Le protocole » ;
> 2. prévoir la sous-section **« Discussion — triangulation et réponse aux QR »** — ici, ou au
>    niveau du chapitre Évaluations (où elle peut aussi intégrer l'interview de Patrick). Sans
>    elle, la section s'arrête sur les interviews **sans répondre à la QR** (demande n°1 de Patrick).
>
> *Nommage : « STAI-6 » + « Questionnaire de confiance » sont les **deux parties du même
> formulaire Q2 (assurance)**, de valence opposée — le signaler d'une phrase ; envisager
> « Auto-efficacité (confiance) » pour l'homogénéité avec NASA-TLX / STAI-6.*

---

## 10. Scaffolding `rapport/stats/` (CONSTRUIT et vérifié)

Décision retenue : **CSV + script CLI**, saisie en **CSV brut**. Arborescence :

```
rapport/stats/
├── data/
│   ├── responses.csv     # ✅ 16 lignes P01-P08 × AVEC/SANS, valeurs brutes (à remplir)
│   └── q0_profil.csv     # ✅ 8 lignes, profil Q0 (item 11 = colonne plus_difficile_texte)
├── analyze_tests.py      # ✅ scoring + Wilcoxon EXACT + r_rb + dz + k/n + figures
├── README.md             # ✅ comment remplir + lancer
├── results/              # généré : scores.csv, wilcoxon_summary.md
└── figures/              # généré : slope_*.png ×3, tlx_subscales.png

rapport/templates/
└── matrice-thematique.md # ✅ matrice thème × participant (T1-T13 + Tcr), tableau des paris
                          #    Q8, synthèse par thème ; ancrée sur le guide Q3 (cf. §7.2)
```

- **Lancer** : `poetry run python rapport/stats/analyze_tests.py`.
- **Dépendances** : **numpy seul** (déjà installé) ; le p exact est calculé par **énumération
  des 2^n configurations de signes** (pas scipy). **matplotlib optionnel** → sans lui, tableaux
  OK, figures ignorées (`poetry run pip install matplotlib` pour les activer).
- **Directions encodées** : `less` pour TLX & STAI, `greater` pour l'auto-efficacité (le
  script applique la bonne direction par mesure — ne pas « corriger » à la main).
- **Vérifié** : reproduit l'exemple travaillé (W=1, p=.016, r_rb=−.93) et l'exemple DATAtab
  (T⁺=31, T⁻=14 ; p exact .344 vs .312 par approximation normale — écart attendu, l'exact est
  le bon à petit n).
- **Note git** : `rapport/stats/` n'est **pas** gitignoré → script et CSV sont suivis ; à toi
  de décider si tu committes les `data/*.csv` remplis (données anonymisées P01–P08).

**Fait** :
- ✅ `templates/matrice-thematique.md` : matrice thème × participant (13 thèmes T1-T13 + Tcr
  émergent, ancrés sur le guide Q3), tableau des paris Q8, synthèse par thème, prête pour
  Google Docs. Recoupement guide ↔ thèmes intégré (cf. §7.2).

**Reste optionnel (dis « oui »)** :
- générateur du **tableau de profil Q0** (lit `q0_profil.csv` → tableau + médianes/effectifs du §2).
