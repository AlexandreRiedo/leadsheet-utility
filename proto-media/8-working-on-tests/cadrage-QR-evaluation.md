# Cadrage de la question de recherche & évaluation — points de discussion

*Document de travail préparé pour la discussion avec le superviseur (P. Roth).*
*Synthèse après lecture de : l'artefact (SPEC), l'interview du prof de jazz (Evaristo, « Canon+FP3 — merged »), et le rapport DS annoté du 2026-02-10.*

---

## But de ce document

Décider **(1)** d'une reformulation de la question de recherche (QR) qui soit réellement
**testable** dans le cadre d'un bachelor HCI, et **(2)** de ce qu'on mesure :
qualité musicale, confort AR, charge mentale, ou autre chose.

Les **4 décisions à trancher ensemble** sont rassemblées à la fin (§7).

---

## 1. Le constat : la QR actuelle n'est pas mesurable

QR actuelle du rapport :
> *« Comment favoriser des improvisations jazz plus créatives et bien conçues
> avec l'aide d'un piano augmenté ? »*

Cette formulation bute sur un problème de **mesure**, et c'est déjà signalé des deux côtés :

- **Annotation de P. Roth** en marge de la section Questions de recherche : *« bon désir à enrichir ».*
- **Dans l'interview**, je le dis moi-même : *« comment tu mesures ça ? C'est impossible, en fait. »*
  Le prof confirme : *« Nous, on n'a pas trouvé de méthode. »*

→ **« improvisation plus créative / mieux conçue » ne peut pas être la variable dépendante
principale.** C'est la motivation du projet, pas la mesure.

---

## 2. Le point d'ancrage : la charge mentale (triangulé)

Trois sources indépendantes pointent le même construit :

- **Roth** (annotation p.11) : *« Peut ajouter dans l'état de l'art de la théorie relative à la charge mentale. »*
- **Le prof de jazz**, sans qu'on l'y amène : *« ce dispositif permet de gommer tout ce côté
  psychologique compliqué […] plus on va directement à l'essentiel […] On peut juste jouer,
  puis se taire. »* Quand je résume l'hypothèse de charge cognitive, il répond :
  *« C'est ce que je suis en train de dire à l'instant. »*
- **La SPEC de l'artefact** : la proposition de valeur est explicitement de *décharger* la
  question « quelles notes sont justes maintenant ? » pour libérer l'attention.

→ Quand le superviseur, l'expert métier et la raison d'être de l'artefact convergent,
c'est **l'ancrage** de l'évaluation.

---

## 3. Ce que l'interview a apporté de neuf

- **Un plafond d'utilisabilité concret** : *« les lumières, quand il y a de la grille,
  elles vont beaucoup trop vite. Je n'arrive pas à les choper. »*
  → Si on ne peut pas suivre les lumières au tempo réel, le bénéfice de charge mentale s'effondre.
  Le **tempo (et la difficulté de la grille) doit donc être une variable contrôlée**, pas un détail.

- **Un proxy musical mesurable** qui contourne le piège de la « qualité » :
  est-ce que les notes pivots/cibles tombent sur les **upper structures (7/9/11/13)**
  plutôt que sur 1-3-5 ? *« Ça, c'est un critère avancé et mesurable. Même par un ordi. »*
  Il propose même un barème (1 → 1 pt, 3 → 3 pts, … 13 → 13 pts).

- **L'idée du « gincana » gradué** : transformer l'outil ouvert en une **échelle d'exercices
  de difficulté croissante** et mesurer **jusqu'où** l'apprenant monte.
  *« créer une série de Jinkana de plus en plus complexe et ça montrerait le niveau de progression. »*
  Métaphore du rat : *« Est-ce que le rat, il saute ? […] quand il tourne trop vite,
  il n'arrive plus à sortir. »* → convertit une « qualité » floue en **mesure ordinale** nette.

- **La question du transfert (« on éteint la lumière »)** : *« Est-ce qu'il y a une trace
  dedans quelque part ? Est-ce qu'il arrive à faire des impros [sans la projection] ? »*
  → la vraie question d'apprentissage, mais elle exige du **longitudinal** (plusieurs séances).

- **L'évaluation par « subjectivité croisée »** : *« je suis ancien doyen, j'ai tout évalué
  les élèves pendant 5 ans qu'avec de la subjectivité croisée »* — chaque collègue juge selon
  son propre biais, et le rôle du doyen est de **sentir où la ligne se croisait** :
  *« ça se croise, forcément, et là, c'était la zone, là, tu avais la réponse. »*
  → C'est la méthode du panel d'experts, légitime pour la qualité musicale.

---

## 4. Principe de reformulation proposé

Pratique standard en Design Science / HCI : **arrêter de mesurer le résultat distal**
(une meilleure impro, non mesurable) **et mesurer le mécanisme proximal qu'on revendique
réellement** : l'artefact réduit la charge de navigation harmonique en temps réel,
ce qui (a) libère de l'attention et (b) abaisse la barrière pour oser jouer.

La créativité / qualité **reste dans l'introduction** comme effet escompté en aval,
traitée uniquement en **exploratoire** (triangulation), jamais comme variable principale.

---

## 5. Proposition de QR reformulées

**Principale (confirmatoire) :**
> *La guidance projetée des notes en temps réel réduit-elle la charge cognitive perçue
> lors de l'improvisation sur une grille de jazz qui défile, comparé au jeu avec
> le backing track seul ?*
> → intra-sujet, projection **ON vs OFF**, **NASA-TLX**. Hypothèse directionnelle : ON < OFF.

**Secondaires / de soutien :**

| Axe | Question | Instrument |
|---|---|---|
| Confort AR / lisibilité | Peut-on suivre les lumières, et à quel tempo ça casse ? | SUS + items sur la vitesse des lumières (*« trop vite »*), confort visuel, latence ; **tempo manipulé** |
| Barrière d'entrée / *oser se lancer* (= ta 2ᵉ QR) | La guidance augmente-t-elle la confiance / l'envie de continuer plutôt que de bloquer ? | auto-évaluation de confiance ON/OFF + interview |
| Support à la créativité | Le système est-il vécu comme soutenant l'exploration créative ? | **CSI** (Creativity Support Index) |
| Effet musical (**EXPLORATOIRE**) | Le jeu se déplace-t-il vers des notes plus riches (upper structures) ? | proxy MIDI (ratio upper-structure / notes cibles) **et/ou** panel d'experts (subjectivité croisée) |

> *Note de continuité : NASA-TLX et CSI sont déjà les instruments cités dans la section
> Évaluation du rapport (repris d'ImproVisAR). On reste donc dans la méthodo annoncée.*

---

## 6. Réponse à « qu'est-ce qu'on teste ? » (classement)

1. **Charge mentale → la colonne vertébrale.** Instrument validé (NASA-TLX),
   demandé par le superviseur, nommé spontanément par l'expert, = ce que l'artefact fait par design.
2. **Confort AR / utilisabilité → 2ᵉ.** Peu coûteux à mesurer et **conditionne tout le reste**
   (le « lumières trop rapides »). Contribution HCI honnête en soi.
3. **Confiance / barrière d'entrée → 3ᵉ.** Récupère ta 2ᵉ QR ; c'est tout le fil
   « flux / impétuosité / arrête de te parler » du prof.
4. **Qualité musicale → PAS en mesure principale.** Seulement en proxy + panel, en exploratoire.
   En faire la VD principale est le **piège** que Roth ET le prof ont explicitement signalé.

---

## 7. Les 4 décisions à trancher avec le superviseur

> Pour chacune : options + ma recommandation. C'est ici que j'ai besoin de son avis HCI.

### Décision A — Portée de l'étude
*(J'avais visé juin ; aujourd'hui = début juin, mais le calendrier est flexible.)*

- **A1. Mono-séance A/B** *(recommandé pour le délai)* — 1 séance ~30-45 min/personne,
  projection ON vs OFF, n ≈ 8-12. Faisable maintenant. Mesure charge/expérience/confiance,
  **pas** l'apprentissage long terme ni le transfert « lumière éteinte ».
- **A2. Longitudinal multi-séances** — 3-5 séances courtes/personne sur quelques semaines ;
  permet de sonder la rétention et le transfert. Revendication d'apprentissage la plus forte,
  mais recrutement/planning difficiles d'ici juin.
- **A3. Hybride** — 1 séance A/B principale pour tous + 2-3 participants motivés en
  études de cas longitudinales (qualitatif).

### Décision B — Mesure principale (claim confirmatoire)

- **B1. Réduction de charge cognitive** *(recommandé)* — titre : la guidance AR baisse
  la charge mentale (NASA-TLX). Appuyé par Roth + le prof + la SPEC.
- **B2. Confiance / oser se lancer** — titre : la guidance abaisse la barrière à l'impro.
  Ranime directement la 2ᵉ QR. Mesuré par auto-efficacité/confiance + comportement.
- **B3. Support à la créativité (CSI en principal)** — plus risqué : au plus près du piège
  de la « qualité ».
- **B4. Profil équilibré** — pas de titre unique : charge + utilisabilité + confiance + CSI
  comme profil d'expérience. Plus sûr mais thèse moins tranchée.

### Décision C — Cadrage de l'artefact

- **C1. Garder l'outil ouvert** *(recommandé si délai serré)* — évaluer les 5 modes libres
  existants tels quels. Moins de dev ; la QR reste sur charge/utilisabilité/confiance.
- **C2. Construire une échelle graduée (« gincana »)** — concevoir une courte séquence
  d'exercices de notes-cibles de difficulté croissante ; VD = « niveau atteint ».
  Musicalement signifiant, contourne la mesure de qualité — mais plus de design + dev.
- **C3. Les deux** — modes ouverts pour le A/B de charge, **+** une petite échelle 3-5 paliers
  comme sonde de performance. Le plus complet, le plus de travail.

### Décision D — Mesure musicale objective (MIDI)

- **D1. Oui — MIDI + proxy** *(recommandé)* — faire l'éval sur un **clavier MIDI** ;
  calculer le ratio notes-cibles / upper-structures ON vs OFF. Peu coûteux, objectif, fondé musicalement.
  *(Attention : le pipeline actuel suppose un piano acoustique → il faut un clavier MIDI pour les séances de test.)*
- **D2. Panel d'experts seulement** — pas de MIDI ; enregistrer l'audio, faire noter 2-3 profs
  de jazz en « subjectivité croisée », chercher la convergence. La méthode des autres chercheurs.
- **D3. Les deux (proxy + panel)** — triangulation la plus forte de la question musicale (exploratoire).
- **D4. Pas de mesure musicale** — se concentrer sur charge + utilisabilité + confiance ;
  qualité musicale abordée seulement qualitativement en interview.

---

## 8. Ma recommandation par défaut (si on veut un fil cohérent)

**A1 + B1 + C1 + D1** : une **mono-séance intra-sujet ON/OFF**, **charge mentale** en mesure
principale (NASA-TLX), sur les **modes ouverts** existants, avec **logging MIDI** pour le proxy
upper-structure en exploratoire — le tout avec **le tempo comme variable contrôlée** pour
documenter le plafond « lumières trop rapides ».
C'est le chemin le plus **faisable** et le plus **défendable** d'ici juin.

Si le délai s'ouvre, **C2/C3 (échelle graduée)** est la plus belle idée du prof et donnerait
une mesure de progression nette ; **A3 (hybride)** ajouterait une amorce de question de transfert.

---

### Questions ouvertes pour le superviseur
1. Valide-t-il le pivot « résultat distal (qualité) → mécanisme proximal (charge/expérience) » ?
2. n ≈ 8-12 en mono-séance suffit-il pour son standard, ou faut-il viser l'hybride ?
3. Le proxy upper-structure (MIDI) est-il assez solide pour figurer, même en exploratoire,
   ou strictement panel d'experts ?
4. Faut-il restreindre l'artefact au « gincana » gradué pour avoir une VD propre,
   ou garder l'outil ouvert et assumer une étude d'expérience/charge ?
