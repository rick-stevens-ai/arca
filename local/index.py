#!/usr/bin/env python3
"""Chunk + embed + index one corpus into its ChromaDB collection.

Usage:
    python index.py --corpus flagellum            # build (skip if populated)
    python index.py --corpus flagellum --rebuild  # wipe + rebuild
    python index.py --all                         # build every registered corpus

Embeds via the LiteLLM aggregator; persists to a per-corpus collection.
Reads source .md/.mmd from the corpus's source_dir (registry: corpora.yaml).
"""
import os, sys, glob, re, json, time, argparse
import tiktoken
import chromadb
from openai import OpenAI
import config as C

enc = tiktoken.get_encoding("cl100k_base")
client = OpenAI(base_url=C.LLM_BASE, api_key=C.LLM_KEY)


def load_meta(cfg):
    years = json.load(open(cfg["years"])) if cfg.get("years") and os.path.exists(cfg["years"]) else {}
    reviews = json.load(open(cfg["review_labels"])) if cfg.get("review_labels") and os.path.exists(cfg["review_labels"]) else {}
    return years, reviews


def extract_title(text):
    for line in text.splitlines():
        s = line.strip().lstrip("#").strip()
        if len(s) > 8 and not s.lower().startswith(("http", "doi", "![")):
            return s[:200]
    return ""


def section_chunks(text, max_tokens=C.CHUNK_TOKENS, overlap=C.CHUNK_OVERLAP):
    """Split on markdown headers, then token-budget each section with overlap."""
    parts = re.split(r'(?m)^(#{1,4}\s+.*)$', text)
    blocks = []
    cur_header = ""
    buf = ""
    def flush():
        nonlocal buf
        if buf.strip():
            blocks.append((cur_header, buf.strip()))
        buf = ""
    for seg in parts:
        if re.match(r'^#{1,4}\s+', seg or ""):
            flush(); cur_header = seg.strip()
        else:
            buf += (seg or "")
    flush()

    chunks = []
    for header, body in blocks:
        toks = enc.encode(body)
        if len(toks) <= max_tokens:
            chunks.append((header, body)); continue
        start = 0
        while start < len(toks):
            window = toks[start:start + max_tokens]
            chunks.append((header, enc.decode(window)))
            if start + max_tokens >= len(toks):
                break
            start += max_tokens - overlap
    return [(h, c) for h, c in chunks if len(c.strip()) > 40]


def embed_batch(texts, retries=4):
    for a in range(retries):
        try:
            r = client.embeddings.create(model=C.EMBED_MODEL, input=texts)
            return [d.embedding for d in r.data]
        except Exception:
            if a == retries - 1:
                raise
            time.sleep(2 * (a + 1))


def build_corpus(corpus, rebuild=False):
    cfg = C.corpus_cfg(corpus)
    src = cfg["source_dir"]
    if not src or not os.path.isdir(src):
        print(f"[{corpus}] source_dir missing: {src}"); return
    years, reviews = load_meta(cfg)
    os.makedirs(C.CHROMA_DIR, exist_ok=True)
    chroma = chromadb.PersistentClient(path=C.CHROMA_DIR)
    cname = C.collection_name(corpus)
    if rebuild:
        try:
            chroma.delete_collection(cname); print(f"[{corpus}] deleted existing collection")
        except Exception:
            pass
    coll = chroma.get_or_create_collection(cname, metadata={"hnsw:space": "cosine"})
    if coll.count() > 0 and not rebuild:
        print(f"[{corpus}] already has {coll.count()} chunks; use --rebuild to redo"); return

    pdfs = sorted(glob.glob(os.path.join(src, "*.pdf")))
    # allow corpora that ship only parsed text (no PDFs): fall back to .md/.mmd basenames
    if not pdfs:
        stems = {os.path.splitext(os.path.basename(f))[0]
                 for f in glob.glob(os.path.join(src, "*.md")) + glob.glob(os.path.join(src, "*.mmd"))}
        pdfs = [os.path.join(src, s + ".pdf") for s in sorted(stems)]
    print(f"[{corpus}] {len(pdfs)} papers")

    ids, docs, metas = [], [], []
    n_papers = 0
    for p in pdfs:
        pid = os.path.basename(p)[:-4]
        txt, source = "", ""
        for ext in (".md", ".mmd"):
            fp = os.path.join(src, pid + ext)
            if os.path.exists(fp):
                txt = open(fp, errors="ignore").read(); source = ext[1:]; break
        if not txt.strip():
            continue
        n_papers += 1
        title = extract_title(txt)
        yr = years.get(pid)
        rtype = (reviews.get(pid) or {}).get("type", "unknown")
        for ci, (header, chunk) in enumerate(section_chunks(txt)):
            ids.append(f"{pid}::{ci}")
            docs.append(chunk)
            metas.append({
                "paper_id": pid, "title": title,
                "year": yr if yr is not None else -1,
                "type": rtype, "section": header[:120],
                "chunk_idx": ci, "source": source,
            })
    print(f"[{corpus}] papers with text: {n_papers} | chunks: {len(docs)}")

    B = 64; added = 0
    for i in range(0, len(docs), B):
        bd = docs[i:i+B]
        coll.add(ids=ids[i:i+B], documents=bd, embeddings=embed_batch(bd), metadatas=metas[i:i+B])
        added += len(bd)
        print(f"[{corpus}]   indexed {added}/{len(docs)}", flush=True)
    print(f"[{corpus}] DONE. '{cname}' now has {coll.count()} chunks from {n_papers} papers")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--rebuild", action="store_true")
    a = ap.parse_args()
    if a.all:
        for name in C.load_registry():
            build_corpus(name, a.rebuild)
    elif a.corpus:
        build_corpus(a.corpus, a.rebuild)
    else:
        print("registered corpora:", ", ".join(C.load_registry()) or "(none)")
        print("use --corpus <name> [--rebuild]  or  --all")


if __name__ == "__main__":
    main()
