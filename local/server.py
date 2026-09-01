#!/usr/bin/env python3
"""corpus-rag MCP server — multi-corpus local RAG.

One service, many topic corpora (one ChromaDB collection each). Every tool
takes a `corpus` argument; `corpus_list` shows what's available.

Tools:
  corpus_list()                                   -> registered corpora + stats
  corpus_search(query, corpus, top_k, year_min, year_max, type) -> ranked chunks
  corpus_answer(question, corpus, top_k, ...)     -> cited RAG answer
  corpus_get_paper(corpus, paper_id)              -> one paper's chunks/metadata
  corpus_stats(corpus)                            -> stats for one corpus

Vector store: persistent ChromaDB on m1. Embeddings + answers via the m1
LiteLLM aggregator. Runs over stdio (MCP).
"""
import json
from collections import Counter
import chromadb
from openai import OpenAI
from mcp.server.fastmcp import FastMCP
import config as C

mcp = FastMCP("corpus-rag")
_client = OpenAI(base_url=C.LLM_BASE, api_key=C.LLM_KEY)
_chroma = chromadb.PersistentClient(path=C.CHROMA_DIR)


def _coll(corpus):
    return _chroma.get_collection(C.collection_name(corpus))


def _embed(text):
    return _client.embeddings.create(model=C.EMBED_MODEL, input=[text]).data[0].embedding


def _where(year_min, year_max, type_filter):
    conds = []
    if year_min is not None:
        conds.append({"year": {"$gte": int(year_min)}})
    if year_max is not None:
        conds.append({"year": {"$lte": int(year_max)}})
    if type_filter in ("review", "research"):
        conds.append({"type": {"$eq": type_filter}})
    if not conds:
        return None
    return conds[0] if len(conds) == 1 else {"$and": conds}


def _retrieve(corpus, query, top_k, year_min=None, year_max=None, type_filter=None):
    res = _coll(corpus).query(
        query_embeddings=[_embed(query)], n_results=top_k,
        where=_where(year_min, year_max, type_filter),
        include=["documents", "metadatas", "distances"])
    hits = []
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        hits.append({"paper_id": meta.get("paper_id"), "title": meta.get("title"),
                     "year": meta.get("year"), "type": meta.get("type"),
                     "section": meta.get("section"), "score": round(1 - dist, 4),
                     "text": doc})
    return hits


@mcp.tool()
def corpus_list() -> str:
    """List all registered RAG corpora with their titles and chunk counts.
    Call this first to see which topics are available to search/answer."""
    reg = C.load_registry()
    lines = [f"{len(reg)} corpora registered:\n"]
    for name, meta in reg.items():
        try:
            cnt = _coll(name).count()
            state = f"{cnt} chunks" if cnt else "EMPTY (needs indexing)"
        except Exception:
            state = "NOT INDEXED"
        lines.append(f"  {name}: {meta.get('title','')} [{state}]")
    return "\n".join(lines)


@mcp.tool()
def corpus_search(query: str, corpus: str, top_k: int = 8, year_min: int = None,
                  year_max: int = None, type: str = None) -> str:
    """Semantic search within one corpus. Returns ranked text chunks with paper
    id, title, year, similarity score. Filters: year_min, year_max, type
    ('review'|'research'). Use corpus_list() to see available corpus names."""
    try:
        hits = _retrieve(corpus, query, top_k, year_min, year_max, type)
    except Exception as e:
        return f"Error (bad corpus name?): {e}. Use corpus_list() for valid names."
    if not hits:
        return "No matching passages found."
    out = [f"{len(hits)} results in '{corpus}' for: {query}\n"]
    for i, h in enumerate(hits, 1):
        out.append(f"[{i}] {h['paper_id']} ({h['year']}, {h['type']}) score={h['score']}\n"
                   f"    {h['title']}\n    § {h['section']}\n    {h['text'][:500]}...\n")
    return "\n".join(out)


@mcp.tool()
def corpus_answer(question: str, corpus: str, top_k: int = 8, year_min: int = None,
                  year_max: int = None, type: str = None) -> str:
    """Answer a question grounded in one corpus (RAG): retrieve relevant passages,
    then synthesize a cited answer ([paper_id] citations). Use corpus_list() for
    valid corpus names."""
    try:
        hits = _retrieve(corpus, question, top_k, year_min, year_max, type)
    except Exception as e:
        return f"Error (bad corpus name?): {e}. Use corpus_list() for valid names."
    if not hits:
        return "No relevant passages found to answer this question."
    context = "\n\n".join(f"[{h['paper_id']} ({h['year']})] {h['title']}\n{h['text']}" for h in hits)
    prompt = ("You are a research assistant. Answer the question using ONLY the "
              "passages below. Cite every claim with the paper id in square "
              "brackets, e.g. [Sowa-2008]. If the passages do not contain the "
              f"answer, say so plainly.\n\nPASSAGES:\n{context}\n\n"
              f"QUESTION: {question}\n\nCited answer:")
    r = _client.chat.completions.create(model=C.ANSWER_MODEL,
                                        messages=[{"role": "user", "content": prompt}])
    srcs = ", ".join(sorted({h["paper_id"] for h in hits}))
    return f"{r.choices[0].message.content}\n\n---\nRetrieved from [{corpus}]: {srcs}"


@mcp.tool()
def corpus_get_paper(corpus: str, paper_id: str) -> str:
    """Return all indexed chunks + metadata for one paper in a corpus.
    Use corpus_search first to find paper ids."""
    try:
        res = _coll(corpus).get(where={"paper_id": {"$eq": paper_id}},
                                include=["documents", "metadatas"])
    except Exception as e:
        return f"Error: {e}. Use corpus_list() for valid corpus names."
    if not res["ids"]:
        return f"No paper '{paper_id}' in '{corpus}'. Use corpus_search to find ids."
    metas = res["metadatas"]; m0 = metas[0]
    order = sorted(range(len(res["ids"])), key=lambda i: metas[i].get("chunk_idx", 0))
    body = "\n\n".join(f"§ {metas[i].get('section','')}\n{res['documents'][i]}" for i in order)
    return (f"{paper_id} | {m0.get('title')}\nyear={m0.get('year')} "
            f"type={m0.get('type')} chunks={len(res['ids'])}\n\n{body[:6000]}")


@mcp.tool()
def corpus_stats(corpus: str) -> str:
    """Statistics for one corpus: papers, chunks, year distribution, and
    review-vs-research breakdown."""
    try:
        coll = _coll(corpus)
        all_meta = coll.get(include=["metadatas"])["metadatas"]
    except Exception as e:
        return f"Error: {e}. Use corpus_list() for valid corpus names."
    papers = {}
    for m in all_meta:
        papers.setdefault(m["paper_id"], m)
    yrs = Counter(m["year"] for m in papers.values() if m["year"] and m["year"] > 0)
    types = Counter(m["type"] for m in papers.values())
    dec = Counter((y // 10) * 10 for y in
                  (m["year"] for m in papers.values() if m["year"] and m["year"] > 0))
    lines = [f"[{corpus}] {len(papers)} papers, {coll.count()} chunks",
             "Types: " + ", ".join(f"{k}={v}" for k, v in types.items()),
             "By decade: " + ", ".join(f"{d}s:{dec[d]}" for d in sorted(dec))]
    if yrs:
        lines.append(f"Year range: {min(yrs)}-{max(yrs)}")
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
