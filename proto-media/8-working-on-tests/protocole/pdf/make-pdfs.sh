#!/usr/bin/env bash
# Regénère tous les PDF depuis les .md du dossier parent, puis le PDF combiné.
# Usage (Git Bash) : cd protocole/pdf && bash make-pdfs.sh
cd "$(dirname "$0")"
EDGE="/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
# Profil isolé : sans lui, msedge délègue au navigateur déjà ouvert. Mais même
# isolé, msedge peut rendre la main AVANT d'avoir fini d'imprimer — il faut donc
# attendre que le PDF apparaisse avant de supprimer le .html (sinon PDF
# "File not found").
PROFILE="$(cygpath -w "${TEMP:-/tmp}/edge-pdf-profile")"

print_pdf() {  # print_pdf <fichier.html> <fichier.pdf>
  rm -f "$2"
  "$EDGE" --headless --disable-gpu --no-pdf-header-footer --user-data-dir="$PROFILE" \
    --print-to-pdf="$(cygpath -w "$PWD/$2")" "file:///$(cygpath -m "$PWD/$1")" 2>/dev/null
  local i=0
  while [ ! -s "$2" ] && [ $i -lt 120 ]; do sleep 0.5; i=$((i+1)); done
  if [ -s "$2" ]; then sleep 0.5; echo "OK: $2"; else echo "ECHEC: $2"; fi
}

# --- PDFs individuels ---
for f in ../*.md; do
  base="$(basename "${f%.md}")"
  { echo "<!DOCTYPE html><html><head><meta charset='utf-8'><style>$(cat style.css)</style></head><body>"
    npx --yes marked --gfm < "$f"
    echo "</body></html>"; } > "$base.html"
  print_pdf "$base.html" "$base.pdf"
  rm "$base.html"
done

# --- PDF combiné (ordre de session ; Q1/Q2 dupliqués en A = 1er morceau, B = 2e morceau) ---
emit() {  # emit <fichier-md-sans-ext> <suffixe A|B|-> <classe css>
  local name=$1 pass=$2 cls=$3 sedexpr=""
  if [ "$pass" = "A" ]; then sedexpr='s/^# Q([0-9]+) —/# Q\1A —/; s/___ \/ 2/1 \/ 2/'
  elif [ "$pass" = "B" ]; then sedexpr='s/^# Q([0-9]+) —/# Q\1B —/; s/___ \/ 2/2 \/ 2/'
  fi
  echo "<div class='$cls'>"
  sed -E "$sedexpr" "../$name.md" | npx --yes marked --gfm | sed 's|<style>td:empty { width: 65%; }</style>||'
  echo "</div>"
}
{ echo "<!DOCTYPE html><html><head><meta charset='utf-8'><style>$(cat style.css)"
  echo ".doc { page-break-after: always; } .q3 td:empty { width: 65%; }</style></head><body>"
  emit info1-PROTOCOLE          - doc
  emit s0-consentement          - doc
  emit s1-feuille-de-session    - doc
  emit q0-questionnaire-initial - doc
  emit q1-nasa-tlx              A doc
  emit q2-assurance-hybride     A doc
  emit q1-nasa-tlx              B doc
  emit q2-assurance-hybride     B doc
  emit q3-entretien-semi-ouvert - "doc q3"
  echo "</body></html>"
} > protocole-complet.html
print_pdf protocole-complet.html protocole-complet.pdf
rm protocole-complet.html
