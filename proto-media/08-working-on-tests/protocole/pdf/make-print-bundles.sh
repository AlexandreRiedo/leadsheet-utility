#!/usr/bin/env bash
# Assemble les deux liasses d'impression recto-verso d'une session :
#   session-experimentateur.pdf : info1-PROTOCOLE + s1-feuille-de-session + q3-entretien
#   session-participant.pdf     : s0-consentement + q0 + q1A + q2A + q1B + q2B
# Chaque document est complété d'une page blanche s'il a un nombre impair de pages,
# pour qu'en recto-verso chaque feuille n'appartienne qu'à un seul document.
# Prérequis : bash make-pdfs.sh d'abord (PDF individuels à jour) ; pypdf (poetry, groupe dev).
# Usage (Git Bash) : cd protocole/pdf && bash make-print-bundles.sh
cd "$(dirname "$0")"
ROOT="$(cd ../../../.. && pwd)"
EDGE="/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
PROFILE="$(cygpath -w "${TEMP:-/tmp}/edge-pdf-profile")"

print_pdf() {  # print_pdf <fichier.html> <fichier.pdf>
  rm -f "$2"
  "$EDGE" --headless --disable-gpu --no-pdf-header-footer --user-data-dir="$PROFILE" \
    --print-to-pdf="$(cygpath -w "$PWD/$2")" "file:///$(cygpath -m "$PWD/$1")" 2>/dev/null
  local i=0
  while [ ! -s "$2" ] && [ $i -lt 120 ]; do sleep 0.5; i=$((i+1)); done
  if [ -s "$2" ]; then sleep 0.5; echo "OK: $2"; else echo "ECHEC: $2"; exit 1; fi
}

for f in info1-PROTOCOLE.pdf s1-feuille-de-session.pdf q3-entretien-semi-ouvert.pdf \
         s0-consentement.pdf q0-questionnaire-initial.pdf; do
  [ -s "$f" ] || { echo "Manquant : $f — lancer d'abord : bash make-pdfs.sh"; exit 1; }
done

# --- Variantes A/B de q1/q2 (mêmes transformations sed que dans make-pdfs.sh) ---
for name in q1-nasa-tlx q2-assurance-hybride; do
  for pass in A B; do
    if [ "$pass" = A ]; then sedexpr='s/^# Q([0-9]+) —/# Q\1A —/; s/___ \/ 2/1 \/ 2/'
    else sedexpr='s/^# Q([0-9]+) —/# Q\1B —/; s/___ \/ 2/2 \/ 2/'
    fi
    { echo "<!DOCTYPE html><html><head><meta charset='utf-8'><style>$(cat style.css)</style></head><body>"
      sed -E "$sedexpr" "../$name.md" | npx --yes marked --gfm
      echo "</body></html>"; } > "$name-$pass.html"
    print_pdf "$name-$pass.html" "$name-$pass.pdf"
    rm "$name-$pass.html"
  done
done

# --- Fusion avec padding pour recto-verso ---
PDFDIR="$PWD" poetry --directory "$ROOT" run python - <<'EOF'
import os
from pypdf import PdfReader, PdfWriter

os.chdir(os.environ["PDFDIR"])

def bundle(out, files):
    writer = PdfWriter()
    for f in files:
        reader = PdfReader(f)
        for page in reader.pages:
            writer.add_page(page)
        if len(reader.pages) % 2:  # page blanche -> le doc suivant commence sur un recto
            writer.add_blank_page()
    with open(out, "wb") as fh:
        writer.write(fh)
    print(f"OK: {out} ({len(writer.pages)} pages, {len(files)} documents)")

bundle("session-experimentateur.pdf", [
    "info1-PROTOCOLE.pdf",
    "s1-feuille-de-session.pdf",
    "q3-entretien-semi-ouvert.pdf",
])
bundle("session-participant.pdf", [
    "s0-consentement.pdf",
    "q0-questionnaire-initial.pdf",
    "q1-nasa-tlx-A.pdf",
    "q2-assurance-hybride-A.pdf",
    "q1-nasa-tlx-B.pdf",
    "q2-assurance-hybride-B.pdf",
])
EOF
