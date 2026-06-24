# Figures — Solution conceptuelle

Rendus PNG en **mode clair** (thème mermaid `default`, fond blanc, échelle 3) des
diagrammes du chapitre 3 "Solution conceptuelle" de `../../plan-solution-conceptuelle.md`.
Le plan reste la source de vérité ; les `.mmd` en sont une copie régénérable.

| Fichier | Diagramme (§3) | Destination |
|---|---|---|
| `3-2-flux-conceptuel-analyse-grille` | 3.2 Flux conceptuel analyse → grille (une source, deux sorties synchronisées) | corps |

Les autres figures de §3.2 ne sont pas des diagrammes Mermaid : le **diagramme des
exigences** (DS Fig.1) est déjà fait dans le DS, et le **schéma du système**
(projecteur / piano / ordinateur) reste à produire (il n'existe pas dans le DS) ou à
remplacer par une photo réelle du montage (cf. §3.9).

## Régénérer

Depuis la racine du dépôt, avec Node installé, un `puppeteer-config.json` pointant sur un
Chrome local (cf. `../../puppeteer-config.json`) :

```bash
export PUPPETEER_SKIP_DOWNLOAD=true
for f in rapport/figures/solution-conceptuelle/*.mmd; do
  npx -y @mermaid-js/mermaid-cli -i "$f" -o "${f%.mmd}.png" -t default -b white -s 3 -p rapport/puppeteer-config.json
done
```
