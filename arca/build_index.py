"""CLI to build an Arca index from a corpus.

Usage:
    python -m arca.build_index --corpus lucid --name lucid --limit 500
    python -m arca.build_index --corpus osti  --name osti

Streams the loader → chunk → embed (Argo 1536) → FAISS store. Persists under
ARCA_INDEX_DIR/<name>/.
"""

from __future__ import annotations

import argparse
import sys
import time

from arca.config import DEFAULT
from arca.corpus import LOADERS
from arca.index import Embedder, FaissStore, chunk_document
from arca.types import Chunk, Document


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="arca.build_index")
    ap.add_argument("--corpus", required=True, choices=list(LOADERS.keys()))
    ap.add_argument("--name", required=True, help="index name (dir under ARCA_INDEX_DIR)")
    ap.add_argument("--limit", type=int, default=None, help="cap docs (smoke tests)")
    ap.add_argument("--embed-batch", type=int, default=64)
    args = ap.parse_args(argv)

    cfg = DEFAULT
    loader = LOADERS[args.corpus]
    embedder = Embedder(cfg)

    docs: list[Document] = []
    chunks: list[Chunk] = []
    t0 = time.time()
    n_docs = 0
    for doc, text in loader(cfg, limit=args.limit):
        doc_chunks = list(chunk_document(doc.doc_id, text, cfg))
        if not doc_chunks:
            continue
        docs.append(doc)
        chunks.extend(doc_chunks)
        n_docs += 1
        if n_docs % 200 == 0:
            print(f"  loaded {n_docs} docs / {len(chunks)} chunks "
                  f"({time.time()-t0:.0f}s)", file=sys.stderr)

    if not chunks:
        raise SystemExit(f"no chunks produced for corpus={args.corpus} (check paths)")

    print(f"embedding {len(chunks)} chunks (dim {cfg.embed_dim})...", file=sys.stderr)
    vectors = embedder.embed([c.text for c in chunks], batch_size=args.embed_batch)

    store = FaissStore(args.name, cfg)
    store.build(chunks, docs, vectors)
    print(f"OK: index '{args.name}' — {n_docs} docs, {len(chunks)} chunks → {store.dir}")


if __name__ == "__main__":
    main()
