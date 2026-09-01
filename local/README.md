# Arca — local deployment (ChromaDB, single machine)

This is the **local option** for Arca: one persistent, self-contained RAG service
that runs on a single machine (laptop / workstation) and serves **any number of
topic corpora** through a single MCP server. No remote DB, no HPC, no Tailscale —
just a local ChromaDB store and an OpenAI-compatible LLM endpoint.

It mirrors the tool surface of the server deployment (`../arca/`), so agents get
the same *search → answer → get_paper* workflow whether they hit the shared
uicgpu service or this local one. Each topic is a ChromaDB collection; every tool
takes a `corpus` argument.

> Same corpus-RAG contract, running entirely on your own box.

- **Vector store:** ChromaDB, one collection per corpus, persistent at `~/.corpus-rag/chroma`
- **Embeddings:** `argo:text-embedding-3-large` (3072-dim, LOCKED across corpora) via a local LiteLLM aggregator
- **Answers:** `argo:claude-sonnet-4.6` via the aggregator (cited RAG)
- **Interface:** MCP server (`server.py`) over stdio → tools `corpus_*`
- **Registry:** `corpora.yaml` — add a topic = add an entry + run the indexer

> **Note on embedding dim.** The local store locks embeddings at **3072-dim**
> (`text-embedding-3-large`), while the server deployment locks **1536-dim**
> (`embedding-3-small`). The two indexes are therefore not interchangeable — pick
> the deployment that matches your endpoint, or rebuild if you switch. Both are
> internally consistent.

## MCP tools
- `corpus_list()` — all registered corpora + chunk counts (**call first**)
- `corpus_search(query, corpus, top_k=8, year_min, year_max, type)` — ranked chunks
- `corpus_answer(question, corpus, ...)` — cited RAG answer
- `corpus_get_paper(corpus, paper_id)` — one paper's chunks/metadata
- `corpus_stats(corpus)` — stats for one corpus

`type` filter = `review` | `research`. Year filters inclusive.

## Layout
```
local/
  corpora.yaml     # the registry: one block per topic
  config.py        # paths, models, chunking, registry loader
  index.py         # chunk + embed + index (--corpus NAME [--rebuild] | --all)
  server.py        # multi-corpus MCP server (stdio)
  smoke_test.py    # in-process sanity check over the tools
  verify_mcp.py    # end-to-end MCP client check (lists + calls tools)
  migrate_flagellum.py  # one-time: old single-store -> corpus_flagellum
  meta/            # optional per-corpus paper_id -> year / review-label JSONs
  requirements.txt # locked, known-good deps for the local deployment
```

## Install
```bash
cd local
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Point it at your OpenAI-compatible endpoint (defaults target a LiteLLM aggregator
on the tailnet — override as needed):
```bash
export CORPUS_RAG_LLM_BASE="http://<host>:4000/v1"
export CORPUS_RAG_LLM_KEY="sk-..."
# optional overrides:
export CORPUS_RAG_CHROMA_DIR="$HOME/.corpus-rag/chroma"
export CORPUS_RAG_EMBED_MODEL="argo:text-embedding-3-large"
export CORPUS_RAG_ANSWER_MODEL="argo:claude-sonnet-4.6"
```

## Add a new corpus (the whole workflow)
1. Parse the topic's PDFs to `.md` (Marker) + `.mmd` (Nougat) into a source dir.
   One `.md`/`.mmd` per paper, basename = paper id.
2. (Optional) build `meta/<name>_years.json` (`{paper_id: year}`) and
   `meta/<name>_review_labels.json` (`{paper_id: {"type": "review"|"research"}}`)
   — LLM-classified, NOT regex.
3. Add a block to `corpora.yaml`:
   ```yaml
     <name>:
       title: "..."
       source_dir: /abs/path/to/parsed
       years: meta/<name>_years.json          # omit if none
       review_labels: meta/<name>_review_labels.json   # omit if none
   ```
4. `.venv/bin/python index.py --corpus <name>`   (~1-2s/paper embed via aggregator)
5. Reload MCP (or restart the gateway). The new corpus appears in `corpus_list()`.
   **No new code, no new config entry, no new process** — same 5 tools serve it.

## Rebuild / refresh
```bash
.venv/bin/python index.py --corpus <name> --rebuild   # after adding papers
.venv/bin/python index.py --all                       # build any not-yet-built
```

## Verify
```bash
.venv/bin/python smoke_test.py    # in-process: list / stats / search / answer
.venv/bin/python verify_mcp.py    # over MCP stdio: list tools + call corpus_list
```

## Wire into an MCP client (e.g. Hermes / any stdio MCP host)
Register a stdio server with `command = <venv python>`, `args = [server.py]`, and
the `CORPUS_RAG_*` env above. Tools register under the host's namespace
(e.g. `mcp_corpus_rag_*`).

## Notes
- Embedding dim LOCKED at 3072 — all local corpora share the model so
  cross-corpus search stays possible. Changing embed model = `--rebuild` every corpus.
- ChromaDB store is local (`~/.corpus-rag`), deliberately NOT in Dropbox.
- Corpora that ship only parsed text (no PDFs) work too — the indexer falls back
  to `.md`/`.mmd` basenames when no `*.pdf` are present.
