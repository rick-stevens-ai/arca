"""Retrieval dedup-by-doc: HybridRetriever must collapse multiple chunks of the
same paper to one hit (best-scoring), and top_k must count unique papers.

Regression for the fix where a single paper appeared 3-4x in search results.
"""
from __future__ import annotations

import pytest

from tests._helpers import build_store, make_cfg, patch_embedder

# Skip cleanly if faiss/numpy aren't importable in this env.
faiss = pytest.importorskip("faiss")
np = pytest.importorskip("numpy")


def _corpus():
    # doc A has 3 near-identical chunks; doc B and C one each. All 8-dim.
    return [
        ("docA", "Alpha paper", "alpha one",   [1, 0, 0, 0, 0, 0, 0, 0]),
        ("docA", "Alpha paper", "alpha two",   [1, 0, 0, 0, 0, 0, 0, 0.01]),
        ("docA", "Alpha paper", "alpha three", [1, 0, 0, 0, 0, 0, 0, 0.02]),
        ("docB", "Beta paper",  "beta text",   [0.9, 0.1, 0, 0, 0, 0, 0, 0]),
        ("docC", "Gamma paper", "gamma text",  [0.8, 0.2, 0, 0, 0, 0, 0, 0]),
    ]


def test_dedup_collapses_same_doc(tmp_path, monkeypatch):
    cfg = make_cfg(tmp_path)
    store = build_store(cfg, _corpus())
    patch_embedder(monkeypatch, [1, 0, 0, 0, 0, 0, 0, 0])  # closest to docA

    from arca.retrieve import HybridRetriever
    r = HybridRetriever(store, cfg)
    hits = r.search("alpha", top_k=3)

    doc_ids = [h.doc_id for h in hits]
    assert len(doc_ids) == len(set(doc_ids)), f"duplicate docs in results: {doc_ids}"
    assert "docA" in doc_ids
    # docA appears exactly once despite having 3 chunks
    assert doc_ids.count("docA") == 1


def test_top_k_counts_unique_papers(tmp_path, monkeypatch):
    cfg = make_cfg(tmp_path)
    store = build_store(cfg, _corpus())
    patch_embedder(monkeypatch, [1, 0, 0, 0, 0, 0, 0, 0])

    from arca.retrieve import HybridRetriever
    r = HybridRetriever(store, cfg)
    hits = r.search("alpha", top_k=3)
    # 3 unique docs exist (A, B, C) -> top_k=3 should return all 3, not 3 chunks of A
    assert len(hits) == 3
    assert set(h.doc_id for h in hits) == {"docA", "docB", "docC"}


def test_dedup_disabled_returns_multiple_chunks(tmp_path, monkeypatch):
    cfg = make_cfg(tmp_path)
    store = build_store(cfg, _corpus())
    patch_embedder(monkeypatch, [1, 0, 0, 0, 0, 0, 0, 0])

    from arca.retrieve import HybridRetriever
    r = HybridRetriever(store, cfg)
    hits = r.search("alpha", top_k=3, dedup_by_doc=False)
    # with dedup off, docA's multiple chunks may fill the results
    assert sum(1 for h in hits if h.doc_id == "docA") >= 2
