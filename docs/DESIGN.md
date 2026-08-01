# Arca — Design & Decisions

Streamlined corpus RAG, exposed to the fleet as the MCP service `arca`.
Deploy target: **uicgpu** (8×A100-80GB). Reachable over Tailscale.

---

## 1. Goal (Rick, 2026-08-01)

> "A place for our corpus to be accessible to all our agents and models on demand."

One always-on network service. Any agent (Kukla, Ollie, tricksters) or model can call
Arca's MCP tools to search the corpus and get grounded, cited answers — no per-agent
re-derivation of corpus access.

Lineage: streamlined re-implementation of Ozan's **HiPerRAG** (arXiv 2505.04846:
Oreo parser + ColTrast encoder + distllm retriever over 3.6M articles on
Polaris/Sunspot/Frontier). Arca keeps the *pattern* (retriever + BYO-LLM generation)
and drops the HPC-scale training/serving machinery — sized for one node.

## 2. Decisions

| # | Decision | Value | Rationale |
|---|---|---|---|
| D1 | Transport | **Streamable HTTP over Tailscale** (+ stdio for dev) | Shared multi-agent service; must be network-reachable on demand. |
| D2 | Deploy host | **uicgpu** | 8×A100; local Laguna/Ornith available for generation; on tailnet. |
| D3 | Embedding model | **Argo `embedding-3-small`, dim 1536 — LOCKED** | Fleet standard (FALDA lock). Re-embedding a 280K-paper corpus is painful; lock forever. |
| D4 | Vector backend | **FAISS** (flat→IVF/HNSW as it grows) default; Qdrant optional | Zero-dependency, file-backed, fast enough at our scale; Qdrant if we need live upserts/filtering at scale. |
| D5 | Lexical | **BM25** (in-process, e.g. `bm25s` / rank_bm25) | Hybrid recall; papers need exact-term matching (gene names, IDs). |
| D6 | Fusion | **Reciprocal Rank Fusion (RRF)** over vector+BM25 | Robust, param-light hybrid; no score-scale calibration needed. |
| D7 | Generation | BYO-LLM, pluggable: **uicgpu-local (Laguna/Ornith) default**, Argo, CELS | Keep generation on-node; fall back to Argo/CELS proxies. |
| D8 | Corpus scope v1 | **LUCID first** (~45K, smallest, already scoped) → then SCOUT → OSTI | Smoke on the smallest corpus per smoke-before-scale rule; OSTI (280K) last. |
| D9 | Chunking | Heading-aware over `.md`/`.mmd`, ~1000-tok chunks w/ overlap | Marker/Nougat output is structured; respect section boundaries. |
| D10 | Package name | `arca`; service/MCP name `arca` | Rick's name. Repo `rick-stevens-ai/arca`. |

Defaults (D4/D7/D8) are reversible — chosen to unblock the scaffold, not final law.

## 3. Corpus ground truth (on SG-1-8TB, m1)

- OSTI catalog: `catalog/catalog.sqlite` (~282K papers), `.md` under `md/<year>/`, `.mmd` under `mmd/<year>/`.
- SCOUT: flat SHA-named `md/` + `mmd/`.
- LUCID: `~/Dropbox/LUCID-papers/` (TXT/PDF); GPI hypotheses + open problems already in `lucid.sqlite`.
- Embedding endpoint: Argo wrapper (m1 `localhost:44497`, `100.86.220.115:44497`) serves `embedding-3-small/large`, `embedding-ada-002`.

## 4. Data model

```python
Document  = {doc_id, corpus, title, authors, year, doi, path, metadata}
Chunk     = {chunk_id, doc_id, text, ordinal, section, n_tokens}
Hit       = {chunk_id, doc_id, score, text, metadata}
Answer    = {text, citations:[{doc_id, title, doi, chunk_ids}], model, hits}
```

## 5. MCP tool contract

| Tool | Args | Returns |
|---|---|---|
| `arca_search` | `query:str, top_k:int=20, corpus:str?=None, filters:dict?=None` | `list[Hit]` |
| `arca_answer` | `query:str, top_k:int=20, corpus:str?=None, model:str?=None` | `Answer` |
| `arca_related_papers` | `paper_id:str \| doi:str, k:int=10` | `list[Document]` |
| `arca_get_paper` | `paper_id:str \| doi:str` | `Document` (+ parsed-text path) |

## 6. Build plan (phased)

- **P0 — scaffold** (this commit): repo, package skeleton, module interfaces, MCP server that serves the tool surface against a tiny in-memory fixture. Runs end-to-end with zero corpus. ✅ target.
- **P1 — index LUCID**: corpus loader → chunk → embed (Argo 1536) → FAISS + BM25. Persist index artifacts. Smoke retrieval quality on known queries.
- **P2 — MCP live on uicgpu**: deploy service, expose over Tailscale, wire generation to uicgpu-local Laguna. Register with one agent (Kukla) as an MCP server; verify tool round-trip.
- **P3 — SCOUT + OSTI**: scale index to full corpora; IVF/HNSW; incremental index growth as parse queues fill.
- **P4 — polish**: auth/allowlist on the HTTP endpoint, related-papers via paper-level embeddings, caching, metrics.

## 7. uicgpu notes (from fleet memory)

- Python 3.8.10 system; use a dedicated venv (py3.11+) — FAISS/openai/fastmcp need modern typing.
- DNS is a dead stub (`127.0.0.53`); large HF pulls need the dnspython getaddrinfo shim + `HF_HUB_DISABLE_XET=1`. Arca embeds via Argo proxy (Tailscale IP), not HF, so this mostly doesn't bite — but pin any model pulls.
- GPU contention: resident llama-servers float across GPUs. Pin Arca generation to a free GPU via `CUDA_VISIBLE_DEVICES`; check `nvidia-smi` before launch.
- Long nested-`$()` SSH commands time out at ~60s — split into small ssh calls.
- Prefer `at now` / nohup-detach for long index builds so the ssh session can return.
