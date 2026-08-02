"""Offline test helpers for Arca: build a tiny real FaissStore + stub the embedder.

Everything here avoids the network. faiss + numpy are project deps, so we build
a genuine flat index over hand-made vectors and monkeypatch Embedder so the
retriever never calls out to Argo.
"""
from __future__ import annotations

import numpy as np

from arca.config import Config
from arca.index.store import FaissStore
from arca.types import Chunk, Document


def make_cfg(tmp_path, **over) -> Config:
    """Config pointed at a temp index dir, small embed dim for cheap vectors."""
    params: dict = {"index_dir": tmp_path / "idx", "embed_dim": 8}
    params.update(over)
    return Config(**params)


def _unit(vec) -> list[float]:
    a = np.asarray(vec, dtype="float32")
    n = np.linalg.norm(a)
    return (a / n if n else a).tolist()


def build_store(cfg: Config, docs_chunks_vecs) -> FaissStore:
    """docs_chunks_vecs: list of (doc_id, title, chunk_text, vector)."""
    store = FaissStore("test", cfg)
    chunks, docs, vecs = [], [], []
    seen_docs = set()
    for i, (doc_id, title, text, vec) in enumerate(docs_chunks_vecs):
        chunks.append(Chunk(chunk_id=f"{doc_id}::{i}", doc_id=doc_id, text=text, ordinal=i))
        if doc_id not in seen_docs:
            docs.append(Document(doc_id=doc_id, corpus="test", title=title,
                                 metadata={"corpus": "test", "title": title}))
            seen_docs.add(doc_id)
        vecs.append(_unit(vec))
    store.build(chunks, docs, vecs)
    return store


def patch_embedder(monkeypatch, query_vec):
    """Force Embedder.embed_one to return a fixed query vector (no network)."""
    from arca.index.embedder import Embedder

    monkeypatch.setattr(Embedder, "embed_one", lambda self, text: _unit(query_vec))
    monkeypatch.setattr(Embedder, "embed", lambda self, texts, batch_size=64:
                        [_unit(query_vec) for _ in texts])
