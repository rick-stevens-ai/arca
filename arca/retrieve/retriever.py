"""Hybrid retriever: vector (FAISS) + BM25 lexical, fused with RRF.

Includes an in-memory ``FixtureRetriever`` so the MCP service runs end-to-end at P0
with zero corpus (tiny built-in doc set), and a ``HybridRetriever`` for the real index.
Both satisfy the same ``Retriever`` protocol used by the server + generator.
"""

from __future__ import annotations

import math
from typing import Optional, Protocol

from arca.config import Config, DEFAULT
from arca.index.embedder import Embedder
from arca.index.store import FaissStore
from arca.types import Document, Hit


class Retriever(Protocol):
    def search(self, query: str, top_k: int = 20, corpus: Optional[str] = None,
               filters: Optional[dict] = None) -> list[Hit]: ...
    def get_document(self, doc_id: str) -> Optional[Document]: ...


def _rrf(rank_lists: list[list[str]], k: int = 60) -> dict[str, float]:
    """Reciprocal Rank Fusion over lists of chunk_ids (best-first)."""
    scores: dict[str, float] = {}
    for lst in rank_lists:
        for rank, cid in enumerate(lst):
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank + 1)
    return scores


# --------------------------------------------------------------------------- #
#  Real hybrid retriever
# --------------------------------------------------------------------------- #
class HybridRetriever:
    def __init__(self, store: FaissStore, cfg: Config = DEFAULT):
        self.cfg = cfg
        self.store = store
        self.embedder = Embedder(cfg)
        self._bm25 = None
        self._bm25_ids: list[str] = []
        self._build_bm25()

    def _build_bm25(self):
        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            self._bm25 = None
            return
        corpus_tokens = [c["text"].lower().split() for c in self.store.chunks]
        self._bm25_ids = [c["chunk_id"] for c in self.store.chunks]
        self._bm25 = BM25Okapi(corpus_tokens) if corpus_tokens else None

    def _bm25_search(self, query: str, top_k: int) -> list[str]:
        if self._bm25 is None:
            return []
        scores = self._bm25.get_scores(query.lower().split())
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        return [self._bm25_ids[i] for i in ranked[:top_k]]

    def search(self, query: str, top_k: int = 20, corpus: Optional[str] = None,
               filters: Optional[dict] = None) -> list[Hit]:
        pool = max(top_k * 3, 30)
        qvec = self.embedder.embed_one(query)
        vec_hits = self.store.search(qvec, pool)
        by_id = {h.chunk_id: h for h in vec_hits}
        vec_ids = [h.chunk_id for h in vec_hits]
        bm_ids = self._bm25_search(query, pool)
        # ensure bm25-only hits have a Hit object
        for cid in bm_ids:
            if cid not in by_id:
                row = next((c for c in self.store.chunks if c["chunk_id"] == cid), None)
                if row:
                    meta = dict(self.store.docs.get(row["doc_id"], {}))
                    by_id[cid] = Hit(cid, row["doc_id"], 0.0, row["text"], meta)
        fused = _rrf([vec_ids, bm_ids], self.cfg.rrf_k)
        out: list[Hit] = []
        for cid, s in sorted(fused.items(), key=lambda kv: kv[1], reverse=True):
            h = by_id.get(cid)
            if not h:
                continue
            if corpus and h.metadata.get("corpus") != corpus:
                continue
            if filters and not all(h.metadata.get(k) == v for k, v in filters.items()):
                continue
            h.score = s
            out.append(h)
            if len(out) >= top_k:
                break
        return out

    def get_document(self, doc_id: str) -> Optional[Document]:
        d = self.store.get_doc(doc_id)
        return Document(**{k: v for k, v in d.items() if k in Document.__dataclass_fields__}) if d else None


# --------------------------------------------------------------------------- #
#  Fixture retriever (P0: runs with zero corpus)
# --------------------------------------------------------------------------- #
_FIXTURE_DOCS = [
    Document("fixture-1", "lucid", "Low-dose radiation and DNA damage response",
             ["A. Author"], 2024, "10.0000/fixture1",
             metadata={"corpus": "lucid"}),
    Document("fixture-2", "osti", "High-performance retrieval for scientific corpora",
             ["B. Researcher"], 2025, "10.0000/fixture2",
             metadata={"corpus": "osti"}),
]
_FIXTURE_CHUNKS = {
    "fixture-1::0": "ATM kinase governs the DNA damage response after low-dose ionizing radiation, modulating repair pathway choice between HR and NHEJ.",
    "fixture-2::0": "Retrieval-augmented generation scales to millions of scientific articles using HPC-backed embedding and hybrid retrieval.",
}


class FixtureRetriever:
    """Keyword-overlap retriever over a tiny built-in doc set. No deps, no corpus."""

    def __init__(self, cfg: Config = DEFAULT):
        self.cfg = cfg
        self._docs = {d.doc_id: d for d in _FIXTURE_DOCS}

    def search(self, query: str, top_k: int = 20, corpus: Optional[str] = None,
               filters: Optional[dict] = None) -> list[Hit]:
        q = set(query.lower().split())
        scored: list[Hit] = []
        for cid, text in _FIXTURE_CHUNKS.items():
            doc_id = cid.split("::")[0]
            doc = self._docs[doc_id]
            if corpus and doc.corpus != corpus:
                continue
            overlap = len(q & set(text.lower().split()))
            score = overlap / (math.sqrt(len(q) + 1))
            scored.append(Hit(cid, doc_id, score, text, doc.to_dict()))
        scored.sort(key=lambda h: h.score, reverse=True)
        return scored[:top_k]

    def get_document(self, doc_id: str) -> Optional[Document]:
        return self._docs.get(doc_id)


def load_retriever(cfg: Config = DEFAULT, index_name: Optional[str] = None) -> Retriever:
    """Load the real hybrid retriever if an index exists, else the fixture."""
    if index_name:
        try:
            store = FaissStore(index_name, cfg).load()
            return HybridRetriever(store, cfg)
        except Exception:
            pass
    return FixtureRetriever(cfg)
