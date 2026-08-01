#!/usr/bin/env bash
# Arca — launch the MCP service on uicgpu (Streamable HTTP over Tailscale).
# Fully detached (setsid + </dev/null) so an ssh session closing can NOT kill it
# — the classic uicgpu-launcher trap. Safe to re-run (kills prior port holder).
set -euo pipefail

VENV="${ARCA_VENV:-$HOME/.arca-venv}"
LOG="${ARCA_LOG:-$HOME/arca.log}"
RUN="${ARCA_RUN:-$HOME/arca-run.sh}"

# --- service config (override via env before calling) ---
export ARCA_HOST="${ARCA_HOST:-0.0.0.0}"
export ARCA_PORT="${ARCA_PORT:-8890}"
export ARCA_INDEX_NAME="${ARCA_INDEX_NAME:-}"     # empty → fixture; set once index built
export ARCA_INDEX_DIR="${ARCA_INDEX_DIR:-$HOME/arca-index}"
export ARCA_EMBED_BASE_URL="${ARCA_EMBED_BASE_URL:-http://100.86.220.115:44497/v1}"
export ARCA_EMBED_API_KEY="${ARCA_EMBED_API_KEY:-stevens}"
export ARCA_GEN_BASE_URL="${ARCA_GEN_BASE_URL:-http://100.86.220.115:44497/v1}"
export ARCA_GEN_API_KEY="${ARCA_GEN_API_KEY:-stevens}"
# export CUDA_VISIBLE_DEVICES="2"   # only if generation runs on a local uicgpu model

# kill any prior instance on this port
if command -v lsof >/dev/null 2>&1; then
  OLD=$(lsof -ti tcp:"$ARCA_PORT" 2>/dev/null || true)
  [ -n "$OLD" ] && { echo "[arca] killing prior pid(s): $OLD"; kill $OLD 2>/dev/null || true; sleep 1; }
else
  pkill -f "arca.server" 2>/dev/null || true; sleep 1
fi

# write a standalone runner that carries the env, then launch it fully detached.
IDX_ARG=""
[ -n "$ARCA_INDEX_NAME" ] && IDX_ARG="--index $ARCA_INDEX_NAME"
cat > "$RUN" <<EOF
#!/usr/bin/env bash
export ARCA_HOST='$ARCA_HOST' ARCA_PORT='$ARCA_PORT'
export ARCA_INDEX_NAME='$ARCA_INDEX_NAME' ARCA_INDEX_DIR='$ARCA_INDEX_DIR'
export ARCA_EMBED_BASE_URL='$ARCA_EMBED_BASE_URL' ARCA_EMBED_API_KEY='$ARCA_EMBED_API_KEY'
export ARCA_GEN_BASE_URL='$ARCA_GEN_BASE_URL' ARCA_GEN_API_KEY='$ARCA_GEN_API_KEY'
cd /tmp
exec "$VENV/bin/python" -m arca.server $IDX_ARG
EOF
chmod +x "$RUN"

echo "[arca] launching on ${ARCA_HOST}:${ARCA_PORT} (index='${ARCA_INDEX_NAME:-fixture}')"
setsid bash "$RUN" > "$LOG" 2>&1 < /dev/null &
disown || true
sleep 4
if pgrep -f "arca.server" >/dev/null 2>&1; then
  echo "[arca] UP. MCP endpoint: http://<uicgpu-tailscale-ip>:${ARCA_PORT}/mcp"
  tail -n 12 "$LOG" || true
else
  echo "[arca] FAILED to start — log tail:" >&2
  tail -n 30 "$LOG" >&2
  exit 1
fi
