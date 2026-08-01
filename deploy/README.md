# Deploying Arca on uicgpu

Arca runs as an always-on MCP service on uicgpu, reachable by every agent/model over
Tailscale.

## One-time setup

Arca is a **private** repo — uicgpu has no GitHub creds, so `git clone` there fails.
Push from m1, then **rsync the checkout** to uicgpu (not `git clone`):

```bash
# from m1 (repo at ~/code/arca):
rsync -az --delete \
  --exclude='.venv/' --exclude='arca-index/' --exclude='__pycache__/' \
  --exclude='*.pyc' --exclude='.git/' \
  ~/code/arca/ uicgpu:~/arca/

# on uicgpu — use the existing miniforge python 3.13 (system python is 3.8):
ssh uicgpu '~/miniforge3/bin/python -m venv ~/.arca-venv && \
  ~/.arca-venv/bin/pip install -e ~/arca'
```

uicgpu already has **miniforge3 (python 3.13.12)** at `~/miniforge3` — no python
install needed. `bootstrap_uicgpu.sh` will also find it, but the rsync+miniforge path
above is the proven one for this private repo.

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

## Supervision (durable — survives reboot)

**uicgpu uses a systemd USER unit** (no sudo; stevens has `Linger=yes` so user
services start at boot and survive logout). This is the installed, verified path:

```bash
# unit template in repo: deploy/arca.user.service
ssh uicgpu 'export XDG_RUNTIME_DIR=/run/user/$(id -u)
  mkdir -p ~/.config/systemd/user
  cp ~/arca/deploy/arca.user.service ~/.config/systemd/user/arca.service
  systemctl --user daemon-reload
  systemctl --user enable --now arca.service'
```

Manage it:

```bash
ssh uicgpu 'export XDG_RUNTIME_DIR=/run/user/$(id -u); systemctl --user status arca'
ssh uicgpu 'export XDG_RUNTIME_DIR=/run/user/$(id -u); systemctl --user restart arca'
ssh uicgpu 'export XDG_RUNTIME_DIR=/run/user/$(id -u); journalctl --user -u arca -n 50'
```

`Restart=always` recovers it on crash (verified: `kill -9` → respawned with new PID).
To bind to a built index, uncomment `Environment=ARCA_INDEX_NAME=<name>` in the unit,
`daemon-reload`, `restart`.

The system-level `deploy/arca.service` (needs sudo) and `launch_uicgpu.sh` (manual
`setsid` detach, no supervision) remain as alternatives.
