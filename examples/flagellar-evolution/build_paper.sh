#!/usr/bin/env bash
# Step 4: two-pass pdflatex compile of the generated paper.
# Usage: bash build_paper.sh paper/flagellar-evolution.tex
set -euo pipefail
TEX="${1:-paper/flagellar-evolution.tex}"
DIR="$(cd "$(dirname "$TEX")" && pwd)"
BASE="$(basename "$TEX" .tex)"

# Discover pdflatex (often not on PATH on macOS). Prefer the real TeX Live cellar.
PDFLATEX="$(command -v pdflatex || true)"
if [ -z "$PDFLATEX" ]; then
  PDFLATEX="$(ls /usr/local/texlive/*/bin/*/pdflatex 2>/dev/null | head -1 || true)"
fi
[ -n "$PDFLATEX" ] || { echo "pdflatex not found (install TeX Live)"; exit 1; }
export PATH="$(dirname "$PDFLATEX"):$PATH"

cd "$DIR"
# Two passes so \cite / \ref / TOC resolve.
pdflatex -interaction=nonstopmode -halt-on-error "$BASE.tex"
pdflatex -interaction=nonstopmode -halt-on-error "$BASE.tex"

# Verify no unresolved references leaked into the PDF.
if command -v pdftotext >/dev/null 2>&1; then
  N=$(pdftotext "$BASE.pdf" - 2>/dev/null | grep -c '??' || true)
  [ "$N" = "0" ] || echo "WARNING: $N unresolved refs (??) — check the two-pass compile"
fi
echo "built $DIR/$BASE.pdf"
