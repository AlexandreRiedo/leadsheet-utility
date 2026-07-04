# Figures — Solution technique

Rendus PNG en **mode clair** (thème mermaid `default`, fond blanc, échelle 3) des
diagrammes du §2 de `../../plans/plan-solution-technique.md`. Les fichiers `.mmd` sont les
sources extraites du plan : **le plan reste la source de vérité**, ces `.mmd` en sont
une copie régénérable.

| Fichier | Diagramme (§2) | Destination |
|---|---|---|
| `2A-pipeline-flux-de-donnees-hau` | 2.A Pipeline / flux de données | corps |
| `2B-dependances-entre-modules` | 2.B Dépendances entre modules | corps |
| `2C-phase-de-chargement-et-de-re` | 2.C Séquence de chargement et de rendu | corps |
| `2D-boucle-de-jeu-60-fps` | 2.D Boucle de jeu (60 FPS) | corps (1er levier de coupe) |
| `2Dbis-pipeline-d-overlays-dans-ren` | 2.D bis Pipeline d'overlays (deux colonnes A4) | corps (2e levier de coupe) |
| `2E-machine-a-etats-de-la-calibr` | 2.E Machine à états de la calibration | annexe |
| `2F-resolution-de-gamme-le-syste` | 2.F Résolution de gamme (échelle de priorité, harmonie) | corps |
| `2G-generation-du-backing-une-co` | 2.G Génération du backing (vue d'ensemble) | corps |
| `2H-walking-bass-construction-pa` | 2.H Walking bass (détail par mesure) | annexe |
| `2I-comping-fenetre-2-mesures-vo` | 2.I Comping (fenêtre 2 mesures + voicing) | annexe |
| `2J-batterie-swing-motif-par-mes` | 2.J Batterie swing (motif par mesure) | annexe |
| `2K-synchronisation-fire-and-for` | 2.K Synchronisation fire-and-forget (audio libre / visuel re-ancré) | corps |

Pour le corps du rapport : **2.A, 2.B, 2.C, 2.F, 2.G** et, selon la place, **2.D bis** puis
**2.D** (cf. plan §6). Le détail backing par instrument (**2.H / 2.I / 2.J**) et **2.E**
partent en annexe (en remonter un en corps pour illustrer si la place le permet). La projection
(photo) et l'interface (captures d'écran) ne sont pas des diagrammes Mermaid et ne vivent pas ici.

## Régénérer

Depuis la racine du dépôt, avec Node installé :

1. Réextraire les `.mmd` depuis le plan (resynchronise figures et doc) :
   ```bash
   python rapport/plans/_extract_mmd.py
   ```
2. Créer un `puppeteer-config.json` pointant sur un Chrome/Edge local (évite le
   téléchargement de Chromium par puppeteer) :
   ```json
   { "executablePath": "C:/Program Files/Google/Chrome/Application/chrome.exe", "args": ["--no-sandbox"] }
   ```
3. Rendre chaque diagramme (thème clair, fond blanc, haute résolution) :
   ```bash
   export PUPPETEER_SKIP_DOWNLOAD=true
   for f in rapport/figures/solution-technique/*.mmd; do
     npx -y @mermaid-js/mermaid-cli -i "$f" -o "${f%.mmd}.png" -t default -b white -s 3 -p puppeteer-config.json
   done
   ```

> Note : les labels de nœuds de décision `{...}` doivent être entre guillemets
> (`{"texte = ? "}`) quand ils contiennent `=`, `?` ou `/`, sinon mermaid échoue au parse.
