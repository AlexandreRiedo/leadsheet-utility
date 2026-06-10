# Protocole de test — Piano augmenté

*Sessions du 12 au 19 juin 2026, ~1 h par personne.*

## L'essentiel

Chaque participant·e improvise (main droite, ~4 min) sur **deux morceaux** :
**un avec la projection, un sans**. Après chaque morceau : NASA-TLX + questionnaire
d'assurance. À la fin : entretien semi-ouvert. Tout est filmé (mains/clavier).

- **Hypothèse 1** : la charge cognitive (NASA-TLX) est plus basse AVEC projection.
- **Hypothèse 2** : l'assurance (auto-efficacité) est plus haute AVEC projection.
- En exploratoire : apprentissage, créativité, display de grille (entretien) ;
  qualité musicale via les vidéos (panel d'experts, plus tard).

| Condition | Le participant a |
|---|---|
| **SANS** | backing track + grille d'accords à l'écran |
| **AVEC** | pareil + les notes justes allumées sur les touches (Free Mode) |

## Morceaux

Une paire par niveau. Dans une paire, les deux morceaux se valent (32 mesures,
ii-V, 1 mineur + 1 majeur) — l'un se joue AVEC, l'autre SANS.

| Paire | Niveau | Morceaux (tempo) |
|---|---|---|
| **D** | Débutant | Autumn Leaves (110), Fly Me to the Moon (120) |
| **I** | Intermédiaire | Beautiful Love (110), How High the Moon (120) |

**Choix de la paire** : niveau auto-évalué au Q0 (item 10) : ≤ 3 → D, ≥ 4 → I.
On peut reclasser après la familiarisation si la personne est visiblement perdue
ou très à l'aise (le noter sur la feuille de session).

**Tempo** : fixe, identique dans les deux conditions. Si la personne est perdue au
1er morceau : −10 BPM, pour ses deux morceaux, et on le note.

## Contrebalancement

Dans chaque groupe de niveau, 4 cas, attribués dans l'ordre d'arrivée
(compteur séparé par groupe, sur les feuilles de session).

**Paire D (débutant) :**

| Cas | Morceau 1 | Morceau 2 |
|---|---|---|
| 1 | SANS — Autumn Leaves | AVEC — Fly Me to the Moon |
| 2 | SANS — Fly Me to the Moon | AVEC — Autumn Leaves |
| 3 | AVEC — Autumn Leaves | SANS — Fly Me to the Moon |
| 4 | AVEC — Fly Me to the Moon | SANS — Autumn Leaves |

**Paire I (intermédiaire) :**

| Cas | Morceau 1 | Morceau 2 |
|---|---|---|
| 1 | SANS — Beautiful Love | AVEC — How High the Moon |
| 2 | SANS — How High the Moon | AVEC — Beautiful Love |
| 3 | AVEC — Beautiful Love | SANS — How High the Moon |
| 4 | AVEC — How High the Moon | SANS — Beautiful Love |

Ainsi chaque morceau passe autant en AVEC qu'en SANS, en 1er qu'en 2e. n visé : 8–12.

**Analyse** : un score TLX et un score d'assurance par condition et par personne →
comparaison appariée AVEC vs SANS (Wilcoxon). Le niveau sert juste de variable descriptive.

## Réglages de l'app

- **Free Mode uniquement** (touche `1`) — ne jamais montrer les autres modes.
- RangeMode **R.HAND** (`B`), ChordToneMode OFF, Root OFF.
- Backing **FULL** (`G`), métronome OFF (`M`).
- Grille d'accords visible à l'écran **dans les deux conditions**.
- SANS = projecteur éteint.
- Calibration vérifiée avant la première session du jour.
- `form_repeats: 4` dans les `.meta.json` → ~4 min par morceau ; sinon arrêter avec `S`.

## Déroulé (~50 min)

Les *phrases en italique* sont le script — même formulation pour tout le monde,
neutre (ne jamais dire que la projection « devrait aider »).

**0. Avant l'arrivée** : app calibrée et réglée ; caméra sur trépied (mains/clavier
seulement) ; feuille de session pré-remplie ; questionnaires imprimés.

**1. Accueil + consentement (5 min)**
*« Merci de venir ! Je compare deux façons d'improviser au piano : avec et sans un
dispositif de projection. J'évalue le dispositif, pas ton niveau. La session est
filmée, mais seulement tes mains. Tu peux arrêter à tout moment. »*
→ signer `consentement.md`.

**2. Questionnaire initial (5 min)** → `q0`. À la fin, fixer la paire D ou I.

**3. Démo + familiarisation (8 min)**
*« Le dispositif allume les touches qui fonctionnent avec l'accord du moment. Je te montre. »*
Satin Doll (jamais utilisé en test) : montrer 30 s, puis laisser jouer ~2 min avec
projection et ~1 min sans. Puis : *« Pour chaque morceau : la grille à l'écran, un
count-in de 2 mesures, et tu improvises main droite environ 4 minutes. Pas besoin de
jouer tout le temps. Juste après, deux petits questionnaires. »*

**4. Morceau 1 (10 min)**
1. *« Prochain morceau : ___. Prends 30 secondes pour regarder la grille. »*
2. Caméra ON ; dire à voix haute : code, morceau, condition.
3. `Espace` → impro ~4 min. Ne pas intervenir. `S` pour arrêter.
4. Caméra OFF. Tout de suite : TLX (`q1`) puis assurance (`q2`).
   *« Réponds par rapport à ce morceau précis. »*

**5. Changement (2 min)** : *« Pour le prochain morceau, on passe [avec / sans] la projection. »*

**6. Morceau 2 (10 min)** : comme le morceau 1.

**7. Entretien (8–10 min)** → `q3`, enregistré en audio. Finir par un debriefing libre.

**8. Clôture** : code participant sur toutes les feuilles (jamais le nom) ; vidéo
déchargée en local (`P##_morceau_condition.mp4`) ; incidents notés.

## Données

- Codes `P01`–`P12` ; table nom↔code à part, détruite à la fin du travail.
- Vidéos en local seulement, supprimées après validation du travail.
- Saisie des questionnaires dans un tableur le soir même.

## Fichiers du dossier

| Fichier | Quand |
|---|---|
| `consentement.md` | accueil |
| `q0-questionnaire-initial.md` | début |
| `q1-nasa-tlx.md` | après chaque morceau |
| `q2-assurance.md` | après chaque morceau |
| `q3-entretien-semi-ouvert.md` | fin |
| `feuille-de-session.md` | toute la session |
| `testing-todo.md` | à faire avant le 12 juin |
