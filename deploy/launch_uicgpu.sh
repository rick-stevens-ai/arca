#!/usr/bin/env bash
# Arca — launch the MCP service on uicgpu (Streamable HTTP over Tailscale).
# Detached, logged; safe to re-run (kills prior instance on the same port).
set -euo pipefail

VENV="${ARCA_VENV:-$HOME/.arca-venv}"
ARCA_HOME="${ARCA_HOME:-$HOME/arca}"
LOG="${ARCA_LOG:-$HOME/arca.log}"

# --- service config (override via env before calling) ---
export ARCA_HOST="${ARCA_HOST:-0.0.0.0}"
export ARCA_PORT="${ARCA_PORT:-8890}"
export ARCA_INDEX_NAME="${ARCA_INDEX_NAME:-}"     # empty → fixture; set once index built
# embeddings + generation via Argo proxy (Tailscale IP of the gateway host)
export ARCA_EMBED_BASE_URL="${ARCA_EMBED_BASE_URL:-http://100.86.220.115:44497/v1}"
export ARCA_EMBED_API_KEY="${ARCA_EMBED_API_KEY:-stevens}"
export ARCA_GEN_BASE_URL="${ARCA_GEN_BASE_URL:-http://100.86.220.115:44497/v1}"
export ARCA_GEN_API_KEY="${ARCA_GEN_API_KEY:-stevens}"
export ARCA_INDEX_DIR="${ARCA_INDEX_DIR:-$HOME/arca-index}"

# --- pin generation GPU if using a local model (skip for argo/proxy) ---
# export CUDA_VISIBLE_DEVICES="2"   # a free GPU; check nvidia-smi first

# shellcheck disable=SC1091
source "$VENV/bin/activate"

# kill any prior instance on this port
if command -v lsof >/dev/null 2>&1; then
  OLD=$(lsof -ti tcp:"$ARCA_PORT" 2>/dev/null || true)
  [ -n "$OLD" ] && { echo "[arca] killing prior pid(s): $OLD"; kill $OLD || true; sleep 1; }
fi

IDX_ARG=""
[ -n "$ARCA_INDEX_NAME" ] && IDX_ARG="--index $ARCA_INDEX_NAME"

echo "[arca] launching on ${ARCA_HOST}:${ARCA_PORT} (index='${ARCA_INDEX_NAME:-fixture}')"
nohup python -m arca.server $IDX_ARG > "$LOG" 2>&1 &
PID=$!
echo "[arca] pid=$PID log=$LOG"
sleep 3
if kill -0 "$PID" 2>/dev/null; then
  echo "[arca] UP. MCP endpoint: http://<uicgpu-tailscale-ip>:${ARCA_PORT}/mcp"
  tail -n 15 "$LOG" || true
else
  echo "[arca] FAILED to start — log tail:" >&2
  tail -n 30 "$LOG" >&2
  exit 1
fi
