"""Shared config + corpus registry loader for corpus-rag (multi-corpus RAG)."""
import os, yaml

BASE = os.path.dirname(__file__)

# Persistent ChromaDB location (local, survives restarts; one collection per corpus)
CHROMA_DIR = os.environ.get("CORPUS_RAG_CHROMA_DIR", "/Users/stevens/.corpus-rag/chroma")

# LiteLLM aggregator (m1)
LLM_BASE = os.environ.get("CORPUS_RAG_LLM_BASE", "http://100.86.220.115:4000/v1")
LLM_KEY = os.environ.get("CORPUS_RAG_LLM_KEY", "sk-1234")

# Models (embedding dim is LOCKED across all corpora)
EMBED_MODEL = os.environ.get("CORPUS_RAG_EMBED_MODEL", "argo:text-embedding-3-large")  # 3072-dim
EMBED_DIM = 3072
ANSWER_MODEL = os.environ.get("CORPUS_RAG_ANSWER_MODEL", "argo:claude-sonnet-4.6")

# Chunking
CHUNK_TOKENS = 900
CHUNK_OVERLAP = 150
DEFAULT_TOP_K = 8

REGISTRY = os.environ.get("CORPUS_RAG_REGISTRY", os.path.join(BASE, "corpora.yaml"))


def load_registry():
    with open(REGISTRY) as f:
        return (yaml.safe_load(f) or {}).get("corpora", {})


def collection_name(corpus):
    return f"corpus_{corpus}"


def resolve_path(p):
    """Registry paths may be relative to the project dir."""
    if not p:
        return None
    return p if os.path.isabs(p) else os.path.join(BASE, p)


def corpus_cfg(corpus):
    reg = load_registry()
    if corpus not in reg:
        raise KeyError(f"unknown corpus '{corpus}'. Known: {sorted(reg)}")
    c = dict(reg[corpus])
    c["source_dir"] = resolve_path(c.get("source_dir"))
    c["years"] = resolve_path(c.get("years"))
    c["review_labels"] = resolve_path(c.get("review_labels"))
    return c
