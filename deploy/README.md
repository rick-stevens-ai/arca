# Deploying Arca on uicgpu

Arca runs as an always-on MCP service on uicgpu, reachable by every agent/model over
Tailscale.

## One-time setup

```bash
# on m1 (or wherever the repo lives), push to GitHub first, then on uicgpu:
ssh uicgpu
git clone https://github.com/rick-stevens-ai/arca.git ~/arca
bash ~/arca/deploy/bootstrap_uicgpu.sh      # makes ~/.arca-venv, installs arca + deps
```

`bootstrap_uicgpu.sh` needs a python ≥3.11 on uicgpu (system is 3.8). If none exists,
install via pyenv/conda first (`conda create -n arca python=3.11`), then point
`ARCA_VENV` at it or let the script find it.

## Launch (fixture mode — no corpus, proves the service)

```bash
ssh uicgpu 'bash ~/arca/deploy/launch_uicgpu.sh'
# → arca UP on 0.0.0.0:8890, MCP endpoint http://<uicgpu-tailscale-ip>:8890/mcp
```

## Build an index, then launch bound to it

```bash
ssh uicgpu
source ~/.arca-venv/bin/activate
# smoke on LUCID first (smallest corpus)
python -m arca.build_index --corpus lucid --name lucid --limit 500
# then launch bound to it
ARCA_INDEX_NAME=lucid bash ~/arca/deploy/launch_uicgpu.sh
```

Index artifacts land in `~/arca-index/<name>/` (git-ignored; host-local).

## Connectivity

- **Embeddings + generation** go to the Argo proxy at `100.86.220.115:44497/v1`
  (the m1 gateway, over Tailscale). Arca does NOT pull models from HF, so uicgpu's
  dead-DNS/Xet trap does not apply to the service itself.
- If you switch generation to a **uicgpu-local** model (Laguna/Ornith), set
  `ARCA_GEN_BACKEND=local`, `ARCA_GEN_BASE_URL=http://localhost:<port>/v1`, and pin
  `CUDA_VISIBLE_DEVICES` to a free GPU (check `nvidia-smi` — GPUs float).

## Registering Arca with an agent (Kukla example)

Add to the Hermes MCP client config (config.yaml `mcp.servers`):

```yaml
mcp:
  servers:
    arca:
      transport: streamable-http
      url: http://<uicgpu-tailscale-ip>:8890/mcp
```

Tools appear as `arca_search`, `arca_answer`, `arca_related_papers`, `arca_get_paper`.

## Supervision (durable)

For a restart-surviving service, wrap `launch_uicgpu.sh` in systemd (Linux uicgpu):
see `deploy/arca.service` (template). Until then, `launch_uicgpu.sh` detaches with
nohup and kills any prior instance on the port, so re-running it is the recycle path.
