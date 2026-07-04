# Cadrage de la question de recherche & évaluation — points de discussion

*Document de travail préparé pour la discussion avec le superviseur (P. Roth).*
*Synthèse après lecture de : l'artefact (SPEC), l'interview du prof de jazz (Evaristo, « Canon+FP3 — merged »), et le rapport DS annoté du 2026-02-10.*

---

## But de ce document

Décider **(1)** d'une reformulation de la question de recherche (QR) qui soit réellement
**testable** dans le cadre d'un bachelor HCI, et **(2)** de ce qu'on mesure :
qualité musicale, confort AR, charge mentale, ou autre chose.

Les **4 décisions à trancher ensemble** sont rassemblées à la fin (§8).

> **Démarche globale retenue** : interview de l'expert *d'abord* (cf. `INTERVIEW SCRIPT V2.md`)
> → en extraire le cadre d'enseignement → *puis* construire les tests utilisateurs pour répondre
> à ce cadre. Ce document est l'étape charnière entre les deux.

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
  On part de **morceaux-jouets / études** (le ii-V-I dans toutes les tonalités, un accord isolé)
  plutôt que d'un vrai morceau, et on s'appuie sur le **looping de bouts de forme** déjà
  implémenté. → **développé en détail au §7.**

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

**Cadre général (parapluie) :** *existe-t-il des moyens technologiques pour assister
l'enseignement du jazz ?* — décliné côté **élève** (comment il utilise l'outil, ce qu'il y gagne)
et côté **enseignant** (en quoi l'outil soutient son travail). Le **cœur mesurable** reste l'effet
proximal côté élève ; le soutien à l'enseignant est traité en cadrage / exploratoire (cf. §6 et Q5).

**Principale (confirmatoire) :**
> *La guidance projetée des notes en temps réel réduit-elle la charge cognitive perçue
> lors de l'improvisation sur une grille de jazz qui défile, comparé au jeu avec
> le backing track seul ?*
> → intra-sujet, projection **ON vs OFF**, **NASA-TLX mesuré avant ET après** chaque condition.
> Hypothèse directionnelle : ON < OFF.
> Opérationnalisation concrète (depuis le protocole) : la condition canonique ON/OFF se joue sur
> **Guide Tone sans projection vs avec projection**.

**Variante clé — « faut-il tout montrer ? »**
> Le bénéfice de charge n'est pas forcément monotone : trop de lumières (surtout « trop vite » sur
> grille rapide, cf. §3) peut *augmenter* la charge plutôt que la réduire. On teste donc aussi une
> **dose** d'information : **mode fenêtre (Contour) vs affichage complet** → la charge est-elle plus
> basse quand on montre *moins* ? C'est la jonction directe entre le plafond « lumières trop vite »
> du prof et le mode Contour de l'artefact.

**Secondaires / de soutien :**

| Axe | Question | Instrument |
|---|---|---|
| Confort AR / lisibilité | Peut-on suivre les lumières, et à quel tempo ça casse ? | SUS + items vitesse des lumières (*« trop vite »*) / confort visuel / latence ; **tempo manipulé** |
| Quantité d'information (*« faut-il tout montrer ? »*) | Montrer *moins* (Contour / fenêtre) réduit-il la charge vs tout afficher ? | **NASA-TLX comparé entre densités** (full vs Contour) |
| Acceptation & expérience | L'outil est-il jugé utile, utilisable, désirable ? | **TAM** (acceptation) + **AttrakDiff** (qualité pragmatique + hédonique) |
| Barrière d'entrée / motivation / *oser se lancer* (= ta 2ᵉ QR) | La guidance augmente-t-elle la confiance, la **motivation**, l'envie de continuer plutôt que de bloquer ? | auto-évaluation confiance/motivation ON/OFF + ressenti ouvert + interview |
| Support à la créativité | Le système est-il vécu comme soutenant l'exploration créative ? | **CSI** (Creativity Support Index) |
| Soutien à l'enseignant | L'outil assiste-t-il le prof dans son enseignement du jazz ? | interview expert + observation (**exploratoire**) |
| Effet musical (**EXPLORATOIRE**) | Le jeu se déplace-t-il vers des notes plus riches (upper structures) ? | proxy MIDI (ratio upper-structure / notes cibles) **et/ou** panel d'experts (subjectivité croisée) |

**Batterie d'instruments (questionnaire cobaye) :**

1. **Questions initiales** — âge, nombre d'années de pratique (instrument / jazz).
2. **Ressenti / feeling face à l'outil** — question ouverte.
3. **NASA-TLX** — charge de travail, **avant et après** (et comparé ON/OFF + full/Contour).
4. **AttrakDiff** — qualité hédonique + pragmatique.
5. **TAM** — acceptation de la technologie.
6. **SUS** — utilisabilité / confort AR.
7. **CSI** — support à la créativité.

> *Note de continuité : NASA-TLX et CSI étaient déjà cités dans la section Évaluation du rapport
> (repris d'ImproVisAR) ; AttrakDiff et TAM viennent du protocole de test et complètent le volet
> « expérience / acceptation ». On reste dans la méthodo annoncée, en l'étoffant.*

---

## 6. Réponse à « qu'est-ce qu'on teste ? » (classement)

1. **Charge mentale → la colonne vertébrale.** Instrument validé (NASA-TLX),
   demandé par le superviseur, nommé spontanément par l'expert, = ce que l'artefact fait par design.
   Inclut la variante **« faut-il tout montrer ? »** (full vs Contour), pas seulement ON/OFF.
2. **Confort AR / utilisabilité → 2ᵉ.** Peu coûteux à mesurer et **conditionne tout le reste**
   (le « lumières trop rapides »). Contribution HCI honnête en soi.
3. **Confiance / barrière d'entrée → 3ᵉ.** Récupère ta 2ᵉ QR ; c'est tout le fil
   « flux / impétuosité / arrête de te parler » du prof. Inclut l'**aspect motivation**
   (l'outil donne-t-il envie de continuer ?).
4. **Qualité musicale → PAS en mesure principale.** Seulement en proxy + panel, en exploratoire.
   En faire la VD principale est le **piège** que Roth ET le prof ont explicitement signalé.

---

## 7. Zoom : la piste « gincana » (curriculum gradué d'études)

*Développement de l'idée la plus forte du prof (§3) et de mon envie, formulée en interview, de
« figer des morceaux-exercices à l'avance » plutôt que de tout laisser ouvert.*

### 7.1 Le principe : un jouet ouvert → des exercices fermés

Le prof résume le rapport entre l'outil et le curriculum :
> *« ça c'est ton jouet ; et de ce jouet, tu prends un truc et tu fais une chose précise avec. »*

L'artefact actuel est un **bac à sable** (5 modes ouverts, n'importe quel standard). La piste
gincana consiste à **tailler dans ce bac à sable une séquence d'études courtes, fermées, de
difficulté croissante** — pas besoin de se lancer direct dans un vrai morceau. Moi, en interview :
*« ça me donne envie de figer les choses, de faire des morceaux-exercices figés à l'avance… un
curriculum cadré. »*

### 7.2 Pas besoin d'un vrai morceau : on a déjà les « morceaux-jouets »

Le dépôt contient **déjà** les briques de départ :

- `ii_v_i_all_keys` — le ii-V-I qui monte par quartes dans les 12 tonalités (l'étude canonique).
- `ii_v_i_minor_all_keys` — sa version mineure.
- `Eb7` — un seul accord de dominante tenu (vamp), pour isoler **une seule couleur**.

Le prof valide exactement cette progression :
> *« Peut-être sur une séquence, les deux-cinq, ça va très bien, sur une séquence déjà basique…
> puis après, dans le contexte d'un morceau pas trop compliqué — Beautiful Love, How High the
> Moon — des trucs moins avancés que Beatrice. »*

→ **Échelle de support harmonique** (du plus simple au plus dur) :

1. **Un seul accord tenu** (`Eb7`) — viser une extension sur une couleur figée.
2. **Une cadence isolée** (ii-V, puis ii-V-I) dans une tonalité.
3. **ii-V-I dans les 12 tonalités** (`ii_v_i_all_keys`) — même geste, transposé partout.
4. **Un standard facile** (Beautiful Love, How High the Moon…).
5. *(plus tard)* un standard plus avancé.

### 7.3 Le looping sur des bouts de forme = le moteur d'entraînement

Cette échelle se branche directement sur une feature **déjà implémentée** : la **sélection de
boucle** (touche `L` → bande de mesures → `Enter`) qui transforme quelques mesures en une
mini-forme qui tourne indéfiniment, avec backing re-généré à chaque passe. En interview :
> *« Tu peux dire : je veux juste travailler ces deux changements. En boucle, comme ça, tu n'as
> pas toute la grille, toute la base d'informations. »*

→ Le gincana n'est donc **pas un nouveau moteur** : c'est **boucle + notes-cibles graduées**. On
boucle un ii-V, on vise la cible ; quand c'est acquis, on monte d'un palier (plus de tonalités,
ou cibles plus exigeantes).

### 7.4 La double gradation : support ↓ et exigence ↑

Deux axes de difficulté **orthogonaux** :

| Axe | Facile → Difficile |
|---|---|
| **Support harmonique** (ce qui tourne) | 1 accord → 1 cadence → 12 tonalités → standard |
| **Exigence de cible** (ce qu'on demande de viser) | 1-3-5 → 7 → 9/11/13 (upper structures) ; et **fermé** (1 note cible) → **ouvert** (2-3 cibles acceptées) |

Le prof, sur l'exigence :
> *« rouge qui va résoudre sur rouge ; ou orange qui va vers rouge et vert vers bleu — là, tu as
> tes deux extensions. »* Et : *« ça peut être fermé ou ouvert, avec une seule note d'arrivée, ou
> deux, ou trois. »*

Ces deux axes s'expriment **déjà** avec les briques existantes : le mode **Start & End Note** pour
la cible d'arrivée, **Chord-Tone OVERLAY** pour pousser vers les upper structures, **Contour** pour
la fenêtre. Le travail de dev se réduit à **scripter une séquence de paliers** par-dessus.

### 7.5 La mesure : « jusqu'où monte le rat »

C'est ici que le gincana résout le problème de mesure du §1. Plutôt qu'une « qualité » floue, on
mesure une **variable ordinale nette : le palier le plus haut atteint**. Métaphore du prof :
> *« Est-ce que le rat, il saute ? Quand il tourne trop vite, il n'arrive plus à sortir. À partir
> de quand il n'arrive plus à sortir. »*

→ VD candidate : **niveau atteint** (palier 1…N) et/ou **tempo de décrochage** par palier — lien
direct avec le plafond « lumières trop vite » du §3. Mesurable *« même par un ordi »* via le
logging MIDI (la cible est-elle touchée dans la fenêtre ?). Le prof : *« si le gars couvre jusqu'à
l'exercice 15, c'est intéressant. »*

### 7.6 Ce que ça coûte / ce que ça rapporte

- **Rapporte** : une VD propre et défendable (niveau / tempo de décrochage), musicalement
  signifiante, qui contourne le piège « qualité » sans le nier ; et un récit clair pour le rapport.
- **Coûte** : le design pédagogique des paliers — le prof propose explicitement de **co-concevoir**
  cette échelle : *« ça c'est pure pédagogie, là je me sens concerné, je peux t'aider »* — plus un
  peu de dev pour enchaîner les paliers et logger la réussite. Le **moteur** (boucle, cibles, MIDI)
  existe déjà.
- **Risque délai** : c'est la branche **C2 / C3** du §8 — la plus belle, mais plus lourde que le
  simple A/B ON/OFF. À arbitrer selon le calendrier (Décision A).

---

## 8. Les 4 décisions à trancher avec le superviseur

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
  existants tels quels. Moins de dev ; la QR reste sur charge/utilisabilité/confiance. Les modes
  ouverts fournissent déjà une manipulation de **dose** clé en main (Guide Tone ON/OFF, Contour vs
  full) pour le test « faut-il tout montrer ? ».
- **C2. Construire une échelle graduée (« gincana »)** *(détaillée au §7)* — concevoir une courte
  séquence d'études de notes-cibles de difficulté croissante, à partir des morceaux-jouets
  existants (`Eb7`, `ii_v_i_all_keys`) bouclés ; VD = « niveau atteint » / tempo de décrochage.
  Musicalement signifiant, contourne la mesure de qualité — mais plus de design + dev (le prof
  propose de co-concevoir les paliers).
- **C3. Les deux** — modes ouverts pour le A/B de charge, **+** une petite échelle 3-5 paliers
  (§7) comme sonde de performance. Le plus complet, le plus de travail.

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

## 9. Ma recommandation par défaut (si on veut un fil cohérent)

**A1 + B1 + C1 + D1** : une **mono-séance intra-sujet ON/OFF**, **charge mentale** en mesure
principale (NASA-TLX, avant/après), sur les **modes ouverts** existants, avec **logging MIDI** pour
le proxy upper-structure en exploratoire — le tout avec **le tempo comme variable contrôlée** pour
documenter le plafond « lumières trop rapides ». Questionnaire complet :
NASA-TLX + AttrakDiff + TAM + SUS + CSI + questions démographiques et ressenti ouvert. On glisse
une **comparaison de dose** (full vs Contour) dans le même protocole pour traiter
« faut-il tout montrer ? ».
C'est le chemin le plus **faisable** et le plus **défendable** d'ici juin.

Si le délai s'ouvre, **C2/C3 (échelle graduée, détaillée au §7)** est la plus belle idée du prof
et donnerait une mesure de progression nette ; **A3 (hybride)** ajouterait une amorce de question
de transfert.

---

### Questions ouvertes pour le superviseur
1. Valide-t-il le pivot « résultat distal (qualité) → mécanisme proximal (charge/expérience) » ?
2. n ≈ 8-12 en mono-séance suffit-il pour son standard, ou faut-il viser l'hybride ?
3. Le proxy upper-structure (MIDI) est-il assez solide pour figurer, même en exploratoire,
   ou strictement panel d'experts ?
4. Faut-il restreindre l'artefact au « gincana » gradué pour avoir une VD propre,
   ou garder l'outil ouvert et assumer une étude d'expérience/charge ?
5. Quel poids donner au volet **soutien à l'enseignant** (cadre parapluie) vs un cadrage
   strictement élève/charge ? Ici mesurable seulement en interview/observation exploratoire.
6. La batterie complète (NASA-TLX + AttrakDiff + TAM + SUS + CSI, avant *et* après) est-elle
   trop lourde pour une mono-séance, ou faut-il en couper pour éviter la fatigue questionnaire ?
