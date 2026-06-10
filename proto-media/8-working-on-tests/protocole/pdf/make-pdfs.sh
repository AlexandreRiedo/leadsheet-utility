#!/usr/bin/env bash
# Regénère tous les PDF depuis les .md du dossier parent.
# Usage (Git Bash) : cd protocole/pdf && bash make-pdfs.sh
cd "$(dirname "$0")"
EDGE="/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
for f in ../*.md; do
  base="$(basename "${f%.md}")"
  { echo "<!DOCTYPE html><html><head><meta charset='utf-8'><style>$(cat style.css)</style></head><body>"
    npx --yes marked --gfm < "$f"
    echo "</body></html>"; } > "$base.html"
  "$EDGE" --headless --disable-gpu --no-pdf-header-footer \
    --print-to-pdf="$(cygpath -w "$PWD/$base.pdf")" "file:///$(cygpath -m "$PWD/$base.html")" 2>/dev/null
  rm "$base.html"
  echo "OK: $base.pdf"
done
