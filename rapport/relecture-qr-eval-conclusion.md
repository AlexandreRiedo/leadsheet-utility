# Relecture FINALE : QR + Évaluation + Conclusion

Relecture du PDF "Projet de Bachelor - Alexandre RIEDO (Pre ROTH review)".
Périmètre demandé : **Questions de recherche** (p.6-7), **Évaluation** (p.13-46), **Conclusion** (p.47).
Les numéros de page sont ceux imprimés en haut du PDF.

> Cette passe est un **delta** sur la relecture précédente : la version "Pre ROTH review" a déjà
> absorbé la plupart des points (citations, bilatéral, échelle auto-eff, Fig 10, etc.).
> Tout ce qui est listé en §0 a été **vérifié comme corrigé** dans ce PDF. Les §1+ ne listent
> que ce qui **reste** + le neuf trouvé cette passe.

Vérifs d'arithmétique refaites cette passe : T+/T-/W, rangs, médianes (4.4→4.2 ; 75→35),
r_rb des 3 mesures, comptages d'entretien (6/8 facilité, 6/7 charge, 6/8 sécurité, 6/8 3ème essai).
**Tout concorde.** Les problèmes restants sont de présentation / coquilles, pas d'analyse.

---

## 0. Corrigé depuis la dernière relecture (vérifié dans ce PDF)

- **Citations renumérotées + 3 sources ajoutées.** La biblio compte maintenant Bebop Vol.3 `[9]`,
  la revue pianos augmentés 2022 (Deja et al.) `[11]`, Sandnes/Eika `[12]`. Les appels QR/État de l'art
  pointent juste : Deja et al. `[11]`, ImproVisAR `[13]`, Chyu `[10]` partout, OMR `[15]`, Blues Scales `[16]`.
- **Passage au test bilatéral, justifié.** Méthodo p.20 : "nous retenons le p bilatéral... nous ne
  pouvons pas écarter a priori l'effet inverse... risque de surcharge que le professeur soulève et que
  nous observons chez P04 et P08." Prose et tables alignées (TLX 0.25, auto-eff 0.47). C'était le point
  le plus important : il est traité exactement comme recommandé.
- **Échelle auto-efficacité** : Table 6 dit bien "(échelle 1-7)".
- **Figure 10** correctement légendée ("Réponses libres à... le plus difficile").
- **Table 8** (entretiens participants) : numérotée + légendée. Marqueur "non abordé" écrit en clair.
- **Titres de figures sans tiret long** : "NASA-TLX (RTLX, 0-100) : charge", etc. (`:` au lieu de `—`).
  Vérifié dans `rapport/stats/present.py` l.93-95 : corrigé. (Restent des `—` dans des **commentaires**
  de code et messages console, jamais rendus dans le rapport : non bloquant.)
- **Protocole décrit les 3 tours** de la condition AVEC (base / chord tones / anticipation d'une noire),
  p.19 pt 4. La contradiction "uniquement le mode libre" vs entretiens est **levée** (voir 1.x résiduel).
- **Coquilles corrigées** : "mesure" (ex-"mensuration"), "inverser" (ex-"invertir"), "écartée",
  "motivé à proposer", "la semaine suivante", "Nous visons", "protocole", "question de recherche",
  parenthèses "(1 à 7)" fermées, "indicative", "petites roues de vélo" (ex-"trous"),
  double négation "On peut donc difficilement affirmer" (le "ne" parasite est parti).

---

## 1. RESTE À CORRIGER — important avant envoi

### 1.1 Décimales non arrondies dans les tableaux (le plus visible)
Inchangé depuis la dernière passe.
- **Table 2 (p.26)** : "60.83333333", "21.66666667", "8.333333333"…
- **Table 4 (p.28)** : mélange dans le **même tableau** "56.66666667" (8 déc.) et "-36.6667" / "-3.3333" (4 déc.).
- **Tables 5 / 7** : "r (rang-bisér.) -0.4444444444", "0.3571428571" (10 décimales).
➡ Composites à 1-2 décimales, r à 2 décimales, uniformiser. En l'état ça fait "export de tableur"
brut, et c'est le premier truc que l'œil d'un juré accroche dans une table.

### 1.2 STAI-6 : deux valeurs de p concurrentes + note en anglais
- **Table 5 (p.28)** : headline "p bilatéral **0.3258**" (calculateur en ligne) + note **anglaise**
  "NB: Scipy's exact gives p=0.156 since it handles ties differently".
- **p.40** (prose) : "p a une valeur de **0.31** (la valeur exacte)" → c'est le bilatéral **scipy** (2×0.156).
➡ Le lecteur voit 0.31 dans le texte et 0.3258 dans la table censée le sourcer. Choisir **un seul moteur**
(scipy OU calculateur) et l'appliquer à la table ET à la prose. Passer la note en **français**, en prose,
en expliquant la cause (gestion des ex-aequo) sans exposer deux chiffres rivaux. C'est la seule des 3
mesures où ce flottement subsiste (TLX et auto-eff sont propres).

### 1.3 Citation résiduelle p.41
- **p.41 (auto-efficacité)** : "C'est un effet moyen **[20]**" → `[20]` = Hart & Field (NASA-TLX).
  Le seuil de taille d'effet vient de Fritz et al. = **[24]** (comme p.40 STAI qui cite bien `[24]`).
➡ Remplacer `[20]` par `[24]`. Dernier reliquat de la renumérotation.

---

## 2. COHÉRENCE — à régler, moins urgent

### 2.1 Rangs ex-aequo incohérents (Table 2 vs 4/6)
- **Table 2 (TLX)** : les deux diffs à 8.333 (P02, P03) reçoivent **rangs 1 et 2**.
- **Tables 4 et 6** : rangs **moyens** corrects pour les ex-aequo (5/5/5, 7.5/7.5, 2.5/2.5, 5.5/5.5).
➡ Mettre **1.5 / 1.5** sur le TLX pour homogénéité. **W et r ne changent pas** (1+2 = 1.5+1.5, et les deux
sont du même côté), donc swap purement cosmétique, mais défendable face à un juré qui compare les 3 tables.

### 2.2 QR mère : Intro vs section QR
- **Intro p.2** (marquée TO EDIT) : "favoriser des improvisations jazz plus **créatives et bien conçues**".
- **QR p.6** : "**soutenir l'improvisation jazz mélodique** dans le contexte de grille de standards swing".
➡ Deux questions mères différentes. Tout le reste (QR1 charge / QR2 affect, conclusion) découle de
"soutenir", pas de "créatives". Aligner l'Intro quand tu la sortiras du TO EDIT.

### 2.3 "sous-question 1/2" vs "QR1/QR2"
- p.7 et p.40 : "sous-question 1", "sous-questions". Méthodo p.20 et conclusion : "QR1 / QR2".
➡ Fixer un vocabulaire : QR mère = "QR" ; sous-questions = "QR1" / "QR2" **partout** (y compris la
colonne "Lien avec la QR" du tableau prof, qui sinon laisse croire qu'on parle des sous-questions).

### 2.4 Séparateur décimal mixte
- Figure 5 : "médiane **24,5**" (virgule). Prose p.22 : "médiane : **24.5** ans" (point). Reste du chapitre :
  "r de 0.5", "27.5", "4.4" (point).
➡ En rapport FR, virgule décimale. A minima, cohérence figure ↔ prose (ici la même médiane est écrite
des deux façons à une ligne d'écart).

### 2.5 Labels de difficulté en anglais (p.18)
"4 niveaux de difficulté ('Super easy', 'easy', 'medium', 'pro')" : anglais + registre familier ("pro")
dans un texte FR. ➡ "Très facile / Facile / Moyen / Avancé", ou justifier les labels.

### 2.6 "Uniquement le mode libre" : reliquat de formulation
La contradiction est **levée** (le protocole décrit les 3 tours), mais p.18 dit encore "uniquement le mode
'libre'" alors que la condition AVEC enchaîne base → chord tones → anticipation.
➡ Une demi-phrase suffit : préciser que chord tones et anticipation sont des **surcouches du mode libre**
(pas d'autres exercices), montrées dans les tours AVEC. Sinon le lecteur attentif tique encore une seconde.

### 2.7 Redondance des trois sections de clôture (soft)
Interprétation (p.40-43), Croisement (p.44-46), Conclusion (p.47) répètent r=0.5/0.44/0.36, P04/P08 à
contre-sens, n=8 sous-puissant, petites roues de vélo. C'est en partie voulu, mais Croisement ↔ Conclusion
se recouvrent fort. ➡ Rôles distincts : Interprétation = mesure par mesure ; Croisement = mise en tension
des sources + lecture par profil ; Conclusion = réponse aux 2 QR + ouverture. Élaguer les redites.

---

## 3. STYLE MAISON

- **Guillemets « »** : Figure 10 garde le titre interne "« Ce qui est le plus difficile » : réponses libres".
  Le corps respecte les guillemets droits → incohérence figures/corps. ➡ Passer les figures aux droits.
- **Couverture** : "Leadsheet–Utility" semble utiliser un tiret demi-cadratin (–). Si c'est le cas,
  règle maison = jamais "–". ➡ Vérifier sur le fichier source du titre (logo stylisé : décision à assumer).

---

## 4. COQUILLES (nouvelles cette passe, avec page)

- **p.47 (Conclusion)** : "Son évaluation**,** ne donne que des tendances…" → **virgule parasite** à retirer.
  Même phrase : "…jamais significatives (n = 8)**..**" → **double point** final, en garder un.
- **p.15 et p.38** : "gamme **parton**" → "gamme **par ton(s)**" (whole-tone). Deux occurrences.
- **p.22** : "a tendance **d'être** plus élevé" → "tendance **à être**" ; "**au dessus**" → "**au-dessus**".
- **p.20** : "**Etant** donné que n=8" → "**Étant**" (accent sur la capitale).

---

## 5. MINEURS / À SURVEILLER

- **Ordre AVEC/SANS** : tables = AVEC puis SANS ; graphiques en pente = SANS (gauche) → AVEC (droite).
  Pas faux, mais expliciter la convention une fois éviterait un micro-trébuchement.
- **Asymétrie figures** : seul le NASA-TLX a un graphique par dimension (Fig 13). OK, mais à assumer.
- **Casse des thèmes** tableau prof p.14 : "Charge cognitive" vs "Charge cognitive, Pédagogie **J**azz".
  Uniformiser la casse.
- **"Ta gueule dedans quoi."** (verbatim prof, p.14) : à garder pour l'authenticité, mais c'est un choix de
  registre à assumer face au jury.
- **n effectif auto-eff = 7** (P03 d=0 retiré) : correct et déjà indiqué en Table 7. La conclusion parle
  de "n = 8" globalement : OK comme taille d'échantillon, juste garder en tête que la puissance auto-eff
  est encore plus faible (n=7).

---

## 6. CE QUI TIENT BIEN (ne pas toucher)

- **Arithmétique Wilcoxon recoupée** : T+/T-/W cohérents (TLX 9/27, STAI 10/26, auto-eff 19/9 à n=7),
  r_rb et médianes justes. Les comptages d'entretien (6/8, 6/7…) tombent juste sur la Table 8.
- **Honnêteté statistique exemplaire et constante** : "tendances", "indicatif et sous-puissant (n=8)",
  jamais de significativité revendiquée. Le passage au bilatéral retire au jury l'angle "pourquoi unilatéral ?"
  sans rien coûter aux conclusions (rien n'est significatif dans aucun sens).
- **Cadrage QR1 (charge) / QR2 (affect)** clair et tenu de bout en bout.
- **Croisement des regards** : reconnaît explicitement les confusions (ordre × difficulté × condition,
  lecture par profil ad-hoc, biais de désirabilité car le concepteur a mené les tests). Solide et défendable.
- **Le contre-récit P04/P08** est bien géré : profil (lecteurs de grille chevronnés), morceaux les plus durs
  (26-2, Giant Steps) confiés à AVEC, séance unique trop courte. Honnête sans s'auto-saboter.

---

## 7. HORS PÉRIMÈTRE mais à signaler (État de l'art / Solution conceptuelle)

- **p.9 / p.10 / Fig 2** : "**Sadnens**/Eika" → "**Sandnes**/Eika" (p.5 l'écrit bien "Sandnes" dans le corps,
  donc incohérence interne en plus de la faute). Très visible car répété 3 fois autour de la Figure 2.
- **p.13** : "Solution Technique (TODO) — TBD" : section vide. Connue, mais le prof la verra.
