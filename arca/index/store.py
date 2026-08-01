"""FAISS-backed vector store. File-backed, flat by default (IVF/HNSW as it grows).

Persists three artifacts under index_dir/<name>/:
  - vectors.faiss   the FAISS index
  - chunks.jsonl    chunk_id -> {doc_id, text, section, ...} (row order == faiss id)
  - docs.jsonl      doc_id  -> Document metadata
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from arca.config import Config, DEFAULT
from arca.types import Chunk, Document, Hit


class FaissStore:
    def __init__(self, name: str, cfg: Config = DEFAULT):
        self.cfg = cfg
        self.name = name
        self.dir = cfg.index_path(name)
        self.dir.mkdir(parents=True, exist_ok=True)
        self._index = None
        self._chunks: list[dict] = []  # row order == faiss vector id
        self._docs: dict[str, dict] = {}

    # ---- build ----
    def build(self, chunks: list[Chunk], docs: list[Document], vectors: list[list[float]]):
        import faiss  # lazy
        import numpy as np

        if len(chunks) != len(vectors):
            raise ValueError("chunks/vectors length mismatch")
        arr = np.asarray(vectors, dtype="float32")
        faiss.normalize_L2(arr)  # cosine via inner product
        index = faiss.IndexFlatIP(self.cfg.embed_dim)
        index.add(arr)
        self._index = index
        self._chunks = [c.to_dict() for c in chunks]
        self._docs = {d.doc_id: d.to_dict() for d in docs}
        self.save()

    def save(self):
        import faiss

        faiss.write_index(self._index, str(self.dir / "vectors.faiss"))
        with open(self.dir / "chunks.jsonl", "w") as f:
            for c in self._chunks:
                f.write(json.dumps(c) + "\n")
        with open(self.dir / "docs.jsonl", "w") as f:
            for d in self._docs.values():
                f.write(json.dumps(d) + "\n")

    def load(self) -> "FaissStore":
        import faiss

        self._index = faiss.read_index(str(self.dir / "vectors.faiss"))
        self._chunks = [json.loads(l) for l in open(self.dir / "chunks.jsonl")]
        self._docs = {
            (d := json.loads(l))["doc_id"]: d for l in open(self.dir / "docs.jsonl")
        }
        return self

    # ---- query ----
    def search(self, query_vec: list[float], top_k: int) -> list[Hit]:
        import faiss
        import numpy as np

        if self._index is None:
            return []
        q = np.asarray([query_vec], dtype="float32")
        faiss.normalize_L2(q)
        scores, idxs = self._index.search(q, top_k)
        hits: list[Hit] = []
        for score, i in zip(scores[0], idxs[0]):
            if i < 0:
                continue
            c = self._chunks[i]
            meta = dict(self._docs.get(c["doc_id"], {}))
            meta["section"] = c.get("section")
            hits.append(
                Hit(chunk_id=c["chunk_id"], doc_id=c["doc_id"], score=float(score),
                    text=c["text"], metadata=meta)
            )
        return hits

    def get_doc(self, doc_id: str) -> Optional[dict]:
        return self._docs.get(doc_id)

    @property
    def chunks(self) -> list[dict]:
        return self._chunks

    @property
    def docs(self) -> dict[str, dict]:
        return self._docs
