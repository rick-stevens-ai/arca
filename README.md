# Arca

**Arca** is a streamlined retrieval-augmented-generation (RAG) service over Rick's
scientific corpora (OSTI + SCOUT + LUCID), exposed to every agent and model in the
fleet **as an MCP service** named `arca`.

It is a lean re-implementation of the HiPerRAG pattern (distllm retriever + BYO-LLM
generation) without the multi-thousand-GPU HPC machinery.

> One corpus endpoint the whole agent family can hit on demand.

## Two deployment options

Arca ships **two interchangeable ways to run the same corpus-RAG contract**
(*search → answer → related_papers → get_paper*, over MCP). Pick the one that fits
where you want the index to live:

| | **Server / remote** (default) | **Local** |
|---|---|---|
| Where | always-on service on **uicgpu**, reachable over Tailscale | a single machine (laptop / workstation) |
| Vector store | FAISS (+ BM25 hybrid, RRF fusion) | ChromaDB, one collection per corpus |
| Transport | MCP over Streamable HTTP | MCP over stdio |
| Embeddings | `embedding-3-small`, **1536-dim** locked | `text-embedding-3-large`, **3072-dim** locked |
| Multi-corpus | corpus filter over one index | one collection per topic, registry-driven |
| Best for | shared, whole-fleet endpoint | private / offline / single-user, no remote DB |
| Code | `arca/` (this package) — see below | [`local/`](local/) — see [`local/README.md`](local/README.md) |

Both expose the same conceptual tools, so an agent's workflow is identical either
way; only the tool prefix differs (`arca_*` for the server, `corpus_*` for the
local service). The two indexes use different embedding dimensions and are not
interchangeable at the file level — choose the deployment that matches your
endpoint.

The rest of this document describes the **server** deployment. For the **local**
deployment (ChromaDB, stdio, single machine) see [`local/README.md`](local/README.md).

## Why

We have ~280K OSTI papers, a SCOUT corpus, and the ~45K-paper LUCID set, all parsed to
`.md` (Marker) and `.mmd` (Nougat) on `SG-1-8TB`. Today each agent re-derives access.
Arca makes the corpus a **shared retrieval tool**: `search`, `answer` (grounded, with
citations), `related_papers`, and `get_paper`, over MCP, from anywhere on the tailnet.

## Architecture

```
                       MCP clients (agents + models)
                                  │  MCP (Streamable HTTP over Tailscale)
                    ┌─────────────┴─────────────┐
                    │   arca.server  (MCP)       │   FastMCP app; tools:
                    │   search / answer /        │   arca.search, arca.answer,
                    │   related_papers / get_paper│   arca.related_papers, arca.get_paper
                    └─────────────┬─────────────┘
                    ┌─────────────┴─────────────┐
                    │   arca.retrieve            │   hybrid: vector (FAISS/Qdrant)
                    │   vector + BM25 + filter   │   + BM25 lexical + metadata filter
                    └──────┬──────────────┬──────┘
             ┌─────────────┴──┐    ┌──────┴──────────────┐
             │  arca.index    │    │  arca.generate      │
             │  embed+build   │    │  grounded synthesis │
             │  (Argo embed)  │    │  (uicgpu-local /    │
             │  dim=1536 lock │    │   Argo / CELS)      │
             └───────┬────────┘    └─────────────────────┘
                     │
             ┌───────┴────────┐
             │  arca.corpus   │   loaders: OSTI catalog / SCOUT / LUCID
             │  .md/.mmd →    │   → chunk → (id, text, metadata)
             │  chunks        │
             └────────────────┘
```

## Layout

| Path | Purpose |
|---|---|
| `arca/corpus/` | Corpus loaders: OSTI catalog, SCOUT, LUCID → normalized `Document`/`Chunk` |
| `arca/index/` | Chunking + embedding (Argo, **dim 1536 locked**) + vector index build |
| `arca/retrieve/` | Hybrid retriever: vector + BM25 + metadata filter, RRF fusion |
| `arca/generate/` | BYO-LLM grounded synthesis (uicgpu-local / Argo / CELS) |
| `arca/server/` | **The `arca` MCP service** — FastMCP app exposing the tools |
| `local/` | **Local deployment** — ChromaDB + stdio MCP, single machine (see `local/README.md`) |
| `deploy/` | uicgpu launch + supervision (nohup/systemd), Tailscale exposure |
| `tests/` | Unit + smoke tests |
| `docs/DESIGN.md` | Full design + decisions log |

## MCP tools

| Tool | Signature (conceptual) | Returns |
|---|---|---|
| `arca_search` | `(query, top_k=20, corpus=None, filters=None)` | ranked chunks + paper metadata |
| `arca_answer` | `(query, top_k=20, corpus=None, model=None)` | grounded answer + inline citations |
| `arca_related_papers` | `(paper_id \| doi, k=10)` | semantic-neighbor papers |
| `arca_get_paper` | `(paper_id \| doi)` | full metadata + parsed-text path |

## Status

**Scaffold + live on uicgpu** — 2026-08-01. MCP service running on uicgpu
(`100.81.132.121:8890/mcp`, HTTP 200 verified over Tailscale) in fixture mode.
Environment locked (`requirements.txt` + `environment.yml`). Next: build the LUCID
index and bind the service to it.

See `docs/DESIGN.md` for decisions, defaults, and the build plan.

## Reproduce the environment

Verified-good pins live in `requirements.txt` (frozen from the running uicgpu env).

```bash
# any host with python >=3.11
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt      # locked, known-good
pip install -e .                     # arca itself
python -m pytest tests/ -q           # 6 smoke tests, no corpus needed

# uicgpu (conda path): uses the fleet miniforge3 python 3.13
mamba env create -f environment.yml && conda activate arca && pip install -e .
```

Regenerate the lock after a deliberate dep bump + re-verify:
`pip freeze | grep -ivE '^-e |arca==' | sort > requirements.txt`


## Examples

- [`examples/flagellar-evolution/`](examples/flagellar-evolution/) — a complete,
  reproducible workflow: **build an index over a paper corpus → query it with
  grounded, cited answers → assemble a short, properly-referenced paper (LaTeX →
  PDF)**. Showcase: a 516-paper flagellum/ATP corpus producing *"Open Questions in
  the Evolution of the Bacterial Flagellum"* (finished PDF included). Uses Arca's
  own `search`/`answer` API, so it doubles as a template for any corpus.
