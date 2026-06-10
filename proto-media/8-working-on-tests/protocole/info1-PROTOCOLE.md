# Protocole de test — Piano augmenté

*Sessions du 12 au 19 juin 2026, ~1 h par personne.*

Chaque participant·e improvise (main droite, ~4 min) sur **deux morceaux** :
**un avec la projection, un sans**. Après chaque morceau : NASA-TLX + questionnaire
d'assurance. À la fin : entretien semi-ouvert. Tout est filmé (mains/clavier).

- **SANS** = backing track + grille d'accords à l'écran.
- **AVEC** = pareil + les notes justes allumées sur les touches (Free Mode).
- **Hypothèses** : AVEC < SANS en charge cognitive (NASA-TLX) ; AVEC > SANS en assurance.
- En exploratoire : apprentissage, créativité, display de grille (entretien).

## Morceaux

Une paire par niveau ; les deux morceaux d'une paire se valent (32 mesures, ii-V).
Choix : niveau auto-évalué au Q0 item 10 — ≤ 3 → D, ≥ 4 → I (reclassement possible
après la familiarisation, à noter). Tempo fixe, lent (déchiffrage à vue) ; si la
personne est perdue au 1er morceau : −10 BPM pour ses deux morceaux, à noter.

| Paire | Niveau | Morceaux | Tempo |
|---|---|---|---|
| **D** | Débutant | Autumn Leaves, Fly Me to the Moon | 90 |
| **I** | Intermédiaire | Beautiful Love, How High the Moon | 100 |

## Contrebalancement

4 cas par groupe de niveau, attribués dans l'ordre d'arrivée (compteur par groupe).
Chaque morceau passe ainsi autant en AVEC qu'en SANS, en 1er qu'en 2e. n visé : 8–12.

| Cas | Morceau 1 (paire D / paire I) | Morceau 2 |
|---|---|---|
| 1 | SANS — Autumn Leaves / Beautiful Love | AVEC — Fly Me to the Moon / How High the Moon |
| 2 | SANS — Fly Me to the Moon / How High the Moon | AVEC — Autumn Leaves / Beautiful Love |
| 3 | AVEC — Autumn Leaves / Beautiful Love | SANS — Fly Me to the Moon / How High the Moon |
| 4 | AVEC — Fly Me to the Moon / How High the Moon | SANS — Autumn Leaves / Beautiful Love |

**Analyse** : un score TLX et un score d'assurance par condition et par personne →
comparaison appariée AVEC vs SANS (Wilcoxon).

## Réglages de l'app

- **Free Mode uniquement** (`1`), RangeMode **R.HAND** (`B`), ChordToneMode OFF, Root OFF.
- Backing **FULL** (`G`), métronome OFF (`M`).
- Grille d'accords à l'écran **dans les deux conditions** ; SANS = projecteur éteint.
- Calibration vérifiée avant la première session du jour.
- `form_repeats: 3` → ~4 min par morceau (32 mesures à 90–100 BPM) ; sinon arrêter avec `S`.

## Déroulé (~50 min)

Les *phrases en italique* sont le script — même formulation pour tout le monde,
neutre (ne jamais dire que la projection « devrait aider »).

**1. Accueil + consentement (5 min)**
*« Merci de venir ! Je compare deux façons d'improviser au piano : avec et sans un
dispositif de projection. J'évalue le dispositif, pas ton niveau. La session est
filmée, mais seulement tes mains. Tu peux arrêter à tout moment. »*
→ signer `s0-consentement.md`.

**2. Questionnaire initial (5 min)** → `q0`. À la fin, fixer la paire D ou I.

**3. Démo + familiarisation (8 min)**
*« Le dispositif allume les touches qui fonctionnent avec l'accord du moment. Je te montre. »*
Satin Doll : montrer 30 s, laisser jouer ~2 min avec projection, ~1 min sans.
*« Pour chaque morceau : la grille à l'écran, un count-in de 2 mesures, et tu improvises
main droite environ 4 minutes. Juste après, deux petits questionnaires. »*

**4. Morceau 1 (6 min)**
*« Prochain morceau : ___. Prends 30 secondes pour regarder la grille. »*
Caméra ON (dire : code, morceau, condition) → `Espace` → impro ~4 min sans
intervenir → `S`, caméra OFF.

**5. NASA-TLX puis assurance (4 min)** — *« Réponds par rapport à ce morceau précis. »*

**6. Morceau 2 (6 min)** : comme le morceau 1, dans l'autre condition.
*« Pour ce morceau, on passe [avec / sans] la projection. »*

**7. NASA-TLX puis assurance (4 min)**

**8. Entretien semi-ouvert (8–10 min)** → `q3`, audio enregistré. Debriefing libre à la fin.

**9. Clôture** : code participant (jamais le nom) sur toutes les feuilles ; vidéo
en local (`P##_morceau_condition.mp4`) ; incidents notés sur la feuille de session.

## Données

Codes `P01`–`P12` ; table nom↔code à part, détruite à la fin du travail. Vidéos en
local seulement.

## Fichiers du dossier

| Fichier | Quand |
|---|---|
| `s0-consentement.md` | accueil |
| `q0-questionnaire-initial.md` | début |
| `q1-nasa-tlx.md` | après chaque morceau |
| `q2-assurance-hybride.md` | après chaque morceau |
| `q3-entretien-semi-ouvert.md` | fin |
| `s1-feuille-de-session.md` | toute la session |