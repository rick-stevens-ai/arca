"""Core data types for Arca. Plain dataclasses, JSON-serializable."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class Document:
    """A corpus paper (not a chunk)."""

    doc_id: str
    corpus: str  # "lucid" | "scout" | "osti"
    title: str = ""
    authors: list[str] = field(default_factory=list)
    year: Optional[int] = None
    doi: Optional[str] = None
    path: Optional[str] = None  # parsed-text (.md/.mmd) path on disk
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Chunk:
    """A retrievable text span from a Document."""

    chunk_id: str
    doc_id: str
    text: str
    ordinal: int = 0
    section: Optional[str] = None
    n_tokens: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Hit:
    """A retrieval result: a chunk with a relevance score + surfaced metadata."""

    chunk_id: str
    doc_id: str
    score: float
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Citation:
    doc_id: str
    title: str = ""
    doi: Optional[str] = None
    chunk_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Answer:
    """A grounded RAG answer with citations."""

    text: str
    citations: list[Citation] = field(default_factory=list)
    model: Optional[str] = None
    hits: list[Hit] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "citations": [c.to_dict() for c in self.citations],
            "model": self.model,
            "hits": [h.to_dict() for h in self.hits],
        }
