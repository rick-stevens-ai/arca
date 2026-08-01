#!/usr/bin/env bash
# Arca — uicgpu bootstrap. Creates a py3.11 venv and installs arca.
# uicgpu system python is 3.8; we need a modern one for mcp/faiss/typing.
set -euo pipefail

ARCA_HOME="${ARCA_HOME:-$HOME/arca}"
VENV="${ARCA_VENV:-$HOME/.arca-venv}"

echo "[arca] bootstrap on $(hostname)"

# 1. find a python >=3.11 (uicgpu: try common locations)
PY=""
for c in python3.13 python3.12 python3.11 /opt/homebrew/bin/python3.13; do
  if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
done
if [ -z "$PY" ]; then
  echo "[arca] ERROR: no python >=3.11 found. Install one (pyenv/conda) first." >&2
  exit 1
fi
echo "[arca] using $($PY --version) at $(command -v $PY)"

# 2. venv
if [ ! -d "$VENV" ]; then
  "$PY" -m venv "$VENV"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"
pip install -q --upgrade pip

# 3. install arca (editable) from the repo checkout
if [ -d "$ARCA_HOME" ]; then
  pip install -q -e "$ARCA_HOME"
else
  echo "[arca] ERROR: repo not found at $ARCA_HOME (clone it first)" >&2
  exit 1
fi

# 4. verify
python -c "import arca, mcp, faiss, openai; print('[arca] deps OK', arca.__version__)"
echo "[arca] bootstrap complete. venv=$VENV"
