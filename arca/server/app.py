"""The ``arca`` MCP service.

Exposes the corpus to every agent/model as MCP tools over Streamable HTTP (Tailscale)
or stdio (local dev). Retrieval always works (fixture fallback when no index is built);
generation is best-effort.

Run:
    python -m arca.server                 # HTTP on ARCA_HOST:ARCA_PORT
    python -m arca.server --stdio         # stdio transport (local dev)
    python -m arca.server --index osti    # bind to a built index by name
"""

from __future__ import annotations

import argparse
import os
from typing import Optional

from arca.config import DEFAULT, Config
from arca.generate import Generator
from arca.retrieve import load_retriever

try:
    # mcp SDK >= 2.0 : high-level server is MCPServer (FastMCP was removed)
    from mcp.server import MCPServer
except ImportError:  # allow module import without mcp installed (tests/scaffold)
    MCPServer = None  # type: ignore


def build_app(cfg: Config = DEFAULT, index_name: Optional[str] = None):
    if MCPServer is None:
        raise SystemExit("mcp SDK required: pip install 'mcp>=2.0'")

    retriever = load_retriever(cfg, index_name or os.environ.get("ARCA_INDEX_NAME"))
    generator = Generator(cfg)
    mcp = MCPServer(cfg.service_name, version="0.1.0")

    @mcp.tool()
    def arca_search(query: str, top_k: int = 20, corpus: Optional[str] = None) -> list[dict]:
        """Search the corpus. Returns ranked passages with paper metadata.

        Args:
            query: natural-language or keyword query.
            top_k: number of passages to return.
            corpus: optional filter — one of "lucid", "scout", "osti".
        """
        hits = retriever.search(query, top_k=top_k, corpus=corpus)
        return [h.to_dict() for h in hits]

    @mcp.tool()
    def arca_answer(query: str, top_k: int = 20, corpus: Optional[str] = None,
                    model: Optional[str] = None) -> dict:
        """Answer a question grounded in the corpus, with inline [doc_id] citations.

        Args:
            query: the question.
            top_k: passages to retrieve for grounding.
            corpus: optional corpus filter ("lucid"|"scout"|"osti").
            model: optional generation model override.
        """
        hits = retriever.search(query, top_k=top_k, corpus=corpus)
        ans = generator.answer(query, hits, model=model)
        return ans.to_dict()

    @mcp.tool()
    def arca_related_papers(paper_id: str, k: int = 10) -> list[dict]:
        """Find papers semantically related to a given paper_id (or its title/text)."""
        doc = retriever.get_document(paper_id)
        seed = (doc.title if doc else "") or paper_id
        hits = retriever.search(seed, top_k=k * 3)
        seen: dict[str, dict] = {}
        for h in hits:
            if h.doc_id == paper_id or h.doc_id in seen:
                continue
            seen[h.doc_id] = h.metadata
            if len(seen) >= k:
                break
        return list(seen.values())

    @mcp.tool()
    def arca_get_paper(paper_id: str) -> dict:
        """Fetch a paper's metadata + parsed-text path by paper_id."""
        doc = retriever.get_document(paper_id)
        return doc.to_dict() if doc else {"error": f"not found: {paper_id}"}

    return mcp


def main(argv: Optional[list[str]] = None) -> None:
    ap = argparse.ArgumentParser(prog="arca.server")
    ap.add_argument("--stdio", action="store_true", help="use stdio transport (default: HTTP)")
    ap.add_argument("--index", default=None, help="built index name to bind (else fixture)")
    args = ap.parse_args(argv)

    app = build_app(DEFAULT, index_name=args.index)
    if args.stdio:
        app.run(transport="stdio")
    else:
        # Streamable HTTP — reachable over Tailscale at ARCA_HOST:ARCA_PORT
        app.run(transport="streamable-http", host=DEFAULT.host, port=DEFAULT.port)


if __name__ == "__main__":
    main()
