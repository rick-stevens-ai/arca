"""Arca — streamlined corpus RAG, exposed to the fleet as the MCP service ``arca``.

Public surface:
    from arca import Document, Chunk, Hit, Answer
    from arca.config import Config
"""

from __future__ import annotations

from arca.types import Answer, Chunk, Citation, Document, Hit

__all__ = ["Document", "Chunk", "Hit", "Answer", "Citation"]
__version__ = "0.1.0"
