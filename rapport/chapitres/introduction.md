# Introduction

## Contexte

Improviser de belles lignes mélodiques est au cœur de la pratique du jazz : c'est sans doute la compétence la plus emblématique du genre, et l'une des plus convoitées. Cette aspiration ne se limite d'ailleurs pas aux seuls jazzmen : de nombreux pianistes issus du monde classique souhaitent eux aussi aborder l'improvisation, et se heurtent au même obstacle. En effet, l'improvisation jazz n'a rien d'évident. La grille harmonique défile vite, les gammes associées à chaque accord ne sont pas immédiates, et produire un discours cohérent et intéressant, c'est-à-dire une mélodie qui ne se réduise pas à des gammes montées et descendues, demeure un défi particulièrement ardu.

Parallèlement, l'apprentissage musical s'ouvre de plus en plus aux outils numériques. À côté des méthodes traditionnelles (livres d'exercices, transcriptions de solos, *play-alongs*), un courant de recherche explore l'augmentation de l'instrument lui-même : visualisations, retours en temps réel, dispositifs interactifs venant épauler l'élève au moment précis où il joue. Le piano, par sa disposition régulière et entièrement visible, se prête particulièrement bien à ce type d'augmentation, et la littérature recense déjà un nombre conséquent de prototypes de pianos augmentés à visée pédagogique.

## Problématique

Plus précisément, ce qui rend l'improvisation sur une grille jazz si exigeante tient en grande partie à la charge mentale qu'elle impose dans l'instant. Tout se joue en tempo et en même temps, sans pouvoir s'arrêter pour réfléchir : la mémoire de travail est vite saturée, et c'est souvent là que l'improvisation se grippe, se réduisant à des gammes mécaniques ou se bloquant tout court.

Cette surcharge a une conséquence affective directe : faute de pouvoir tout gérer à la fois, l'élève n'ose pas se lancer. La barrière n'est donc pas seulement technique, elle est aussi psychologique, et elle touche jusqu'à des instrumentistes classiques pourtant aguerris. Or les ressources pédagogiques existantes (méthodes, recueils de *patterns*, *backing tracks*) fournissent surtout de la matière à travailler hors-ligne : elles n'allègent guère cette charge au moment précis où l'élève improvise. Du côté des dispositifs technologiques, les pianos augmentés qui traitent réellement de l'improvisation jazz, et dans un contexte musical réaliste, restent rares. Il y a donc un espace pour interroger la façon dont on pourrait soutenir l'improvisateur pendant l'acte même d'improviser.

## Question de recherche

Ce travail se concentre sur l'improvisation mélodique jazz assistée : l'accent est donc mis sur la main droite. Il vise avant tout des musiciens d'un niveau plutôt intermédiaire, à l'aise au piano, et cherche à stimuler une improvisation créative dans plusieurs tonalités, à la différence de certains systèmes existants limités à la seule gamme de do majeur. Le contexte se veut réaliste : une vraie grille qui tourne en boucle, accompagnée d'un *backing track* et tirée de *lead sheets* de morceaux existants. Enfin, le projet reste ancré dans les méthodes d'enseignement traditionnelles du jazz, ses jeux d'improvisation s'inspirant directement de la littérature pédagogique.

Dans ce cadre, la question de recherche mère de ce travail est de savoir

> *si l'usage de la réalité augmentée et diminuée sur un piano peut soutenir l'improvisation jazz mélodique dans le contexte de grille de standards swing.*

L'augmentation s'entend ici dans les deux sens : on peut aussi bien ajouter de l'information (éclairer des touches) que la retirer (en masquer pour contraindre le jeu).

Sous cette forme, la question reste difficilement soluble : il faut lui trouver un angle d'attaque. La clé tient dans une hypothèse, née de notre propre expérience de musicien jazz amateur : parmi tous les éléments qui troublent la production d'une improvisation sur une grille jazz, il y a la nécessité de calculer mentalement la gamme associée à chaque accord chiffré. À cette charge cognitive liée au calcul des gammes se couplent l'anticipation de l'accord suivant, la construction d'une phrase qui ait un fil conducteur et du sens musical, la synchronisation avec le tempo, et la gestion du stress propre à une performance improvisée.

Comme ce travail relève également de la Design Science Research, nous en avons dérivé deux sous-questions, posées dans un ordre qui n'est pas neutre :

> *SQ1 : l'augmentation, et la diminution, de la réalité sur le piano aide-t-elle à réduire la charge cognitive perçue lors d'une improvisation sur une grille de jazz qui défile ?*
>
> *SQ2 : en réduisant cette charge, peut-on aussi abaisser la barrière affective (moins d'anxiété, plus de confiance, plus d'envie d'oser) lors de cette même improvisation ?*

La première sous-question constitue le cœur du travail : elle énonce le mécanisme le plus direct et le plus aisément testable. La seconde en est le prolongement logique, car décharger la mémoire ne vaut que si cela aide réellement à franchir le pas. L'ordre encode ainsi une chaîne causale, la baisse de charge cognitive de SQ1 étant l'explication attendue de l'allègement affectif de SQ2.

L'évaluation menée dans ce travail vise principalement à répondre à ces deux sous-questions ; la question mère, plus large, ne pourra en recevoir que des éléments de réponse. Pour y parvenir, nous nous appuyons d'abord sur l'état de l'art : la manière dont on travaille habituellement l'improvisation mélodique jazz, les pianos augmentés existants, et les notions de charge cognitive et d'anxiété dans l'apprentissage de l'improvisation. Nous présentons ensuite la solution proposée, d'abord sur le plan conceptuel puis sur le plan technique. Enfin, nous la mettons à l'épreuve à travers un entretien avec un professeur de piano jazz et une série de tests menés auprès de participants, avant de conclure.

---

## Variantes et notes de rédaction (à filtrer, ne pas inclure dans le rendu)

**Ce qui a été déplacé / coupé en intégrant ta section "Questions de recherches" :**
- Les appuis bibliographiques explicites (Deja et al. pour "les prototypes sont rares", la comparaison nominale avec ImproVisAR) sont **renvoyés à l'état de l'art** : dans l'intro, ils précèdent le chapitre qui les établit. La substance est conservée sous forme allusive ("restent rares", "à la différence de certains systèmes limités à la seule gamme de do majeur"), à recibler/citer dans l'état de l'art.
- La parenthèse DSR ("circonscription d'un état intermédiaire de l'artefact… une autre sous-question écartée car non évaluable") a été **retirée** : elle mentionne l'artefact deux fois (consigne de Patrick) et reste opaque pour un lecteur qui n'a pas encore vu le système. À replacer éventuellement dans le chapitre Méthodologie / Solution.
- Le mot **"artefact"** est absent du corps de l'intro : les deux sous-questions disent désormais "l'augmentation et la diminution de la réalité sur le piano" / "peut-on", au lieu de "un artefact de piano augmenté/diminué" / "l'artefact".
- L'énumération de la charge cognitive (lire les chiffrages, rappeler la gamme, anticiper, construire la phrase, tempo, stress) n'apparaît **qu'une fois**, dans le paragraphe d'hypothèse, pour ne pas doublonner avec la Problématique (qui reste sur la surcharge vécue, sans liste).

**Variantes de la QR mère** (ta formulation est la version 1, retenue) :
1. *Si l'usage de la réalité augmentée et diminuée sur un piano peut soutenir l'improvisation jazz mélodique dans le contexte de grille de standards swing.* (retenue, tes mots exacts)
2. *Dans quelle mesure la réalité augmentée et diminuée appliquée à un piano peut-elle soutenir l'improvisation jazz mélodique sur une grille de standards swing qui défile ?* (forme interrogative directe)

**Variante des sous-questions (forme affirmative, plus proche de `question-de-recherche.md`)** :
- SQ1 : *La projection réduit la charge cognitive perçue par rapport à une improvisation sans assistance.*
- SQ2 : *Cette baisse de charge abaisse la barrière affective : moins d'anxiété, plus d'auto-efficacité, plus d'envie de poursuivre.*

**Points ouverts (à trancher) :**
- Garder les libellés "SQ1 / SQ2" (cohérents avec ton plan d'analyse) ou repasser aux deux puces sans étiquette comme dans ton texte d'origine.
- Garder le paragraphe "chaîne causale" (SQ1 → SQ2) ici, ou le renvoyer au chapitre Évaluations avec le tableau des instruments, pour une intro purement conceptuelle.
- Maintenir la mention "Design Science Research" dans l'intro, ou la réserver à un chapitre Méthodologie.
