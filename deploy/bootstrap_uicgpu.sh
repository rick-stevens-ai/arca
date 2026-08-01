#!/usr/bin/env bash
# Arca — uicgpu bootstrap (verified path, 2026-08-01).
# uicgpu system python is 3.8; we use the existing miniforge3 (python 3.13).
# Private repo: sync the checkout from m1 with rsync FIRST (git clone can't auth here):
#   rsync -az --delete --exclude='.venv/' --exclude='arca-index/' --exclude='.git/' \
#         ~/code/arca/ uicgpu:~/arca/
set -euo pipefail

ARCA_HOME="${ARCA_HOME:-$HOME/arca}"
VENV="${ARCA_VENV:-$HOME/.arca-venv}"

echo "[arca] bootstrap on $(hostname)"

# 1. python >=3.11 — prefer the fleet miniforge, then miniconda, then any python3.1x
PY=""
for c in "$HOME/miniforge3/bin/python" "$HOME/miniconda3/bin/python" \
         python3.13 python3.12 python3.11; do
  if [ -x "$c" ] || command -v "$c" >/dev/null 2>&1; then
    ver=$("$c" -c 'import sys;print(sys.version_info>=(3,11))' 2>/dev/null || echo False)
    [ "$ver" = "True" ] && { PY="$c"; break; }
  fi
done
if [ -z "$PY" ]; then
  echo "[arca] ERROR: no python >=3.11 found (miniforge/miniconda/python3.1x)." >&2
  exit 1
fi
echo "[arca] using $($PY --version 2>&1) at $PY"

# 2. venv
[ -d "$VENV" ] || "$PY" -m venv "$VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"
pip install -q --upgrade pip

# 3. install locked deps THEN arca (editable). Locked reqs = verified-good pins.
if [ ! -d "$ARCA_HOME" ]; then
  echo "[arca] ERROR: repo not found at $ARCA_HOME (rsync it from m1 first)" >&2
  exit 1
fi
if [ -f "$ARCA_HOME/requirements.txt" ]; then
  pip install -q -r "$ARCA_HOME/requirements.txt"
fi
pip install -q -e "$ARCA_HOME"

# 4. verify — run from a NEUTRAL cwd so the source dir doesn't shadow the install
( cd /tmp && python -c "import arca, mcp, faiss, openai; print('[arca] deps OK', arca.__version__)" )
echo "[arca] bootstrap complete. venv=$VENV"
