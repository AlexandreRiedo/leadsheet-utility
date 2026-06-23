# Figures — Solution technique

Rendus PNG en **mode clair** (thème mermaid `default`, fond blanc, échelle 3) des
diagrammes du §2 de `../../plan-solution-technique.md`. Les fichiers `.mmd` sont les
sources extraites du plan : **le plan reste la source de vérité**, ces `.mmd` en sont
une copie régénérable.

| Fichier | Diagramme (§2) | Destination |
|---|---|---|
| `2A-pipeline-flux-de-donnees-hau` | 2.A Pipeline / flux de données | corps |
| `2B-dependances-entre-modules` | 2.B Dépendances entre modules | corps |
| `2C-phase-de-chargement-et-de-re` | 2.C Séquence de chargement et de rendu | corps |
| `2D-boucle-de-jeu-60-fps` | 2.D Boucle de jeu (60 FPS) | annexe / au choix |
| `2Dbis-pipeline-d-overlays-dans-ren` | 2.D bis Pipeline d'overlays | annexe (figure très haute) |
| `2E-machine-a-etats-de-la-calibr` | 2.E Machine à états de la calibration | annexe |

Pour le corps du rapport : **2.A, 2.B, 2.C** (cf. plan §6). Les autres en annexe.

## Régénérer

Depuis la racine du dépôt, avec Node installé :

1. Réextraire les `.mmd` depuis le plan (resynchronise figures et doc) :
   ```bash
   python rapport/_extract_mmd.py
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
