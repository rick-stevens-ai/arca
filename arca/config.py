"""Central configuration for Arca. Env-overridable, sane defaults for uicgpu."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _env(key: str, default: str) -> str:
    return os.environ.get(key, default)


@dataclass
class Config:
    # --- embedding (LOCKED: fleet standard, do not change without re-embedding) ---
    embed_model: str = _env("ARCA_EMBED_MODEL", "embedding-3-small")
    embed_dim: int = int(_env("ARCA_EMBED_DIM", "1536"))
    embed_base_url: str = _env("ARCA_EMBED_BASE_URL", "http://100.86.220.115:44497/v1")
    embed_api_key: str = _env("ARCA_EMBED_API_KEY", "stevens")

    # --- generation (BYO-LLM, pluggable) ---
    gen_backend: str = _env("ARCA_GEN_BACKEND", "argo")  # argo | openai | vllm | local
    gen_model: str = _env("ARCA_GEN_MODEL", "gpt4o")
    gen_base_url: str = _env("ARCA_GEN_BASE_URL", "http://100.86.220.115:44497/v1")
    gen_api_key: str = _env("ARCA_GEN_API_KEY", "stevens")

    # --- index / storage ---
    index_dir: Path = field(
        default_factory=lambda: Path(_env("ARCA_INDEX_DIR", str(Path.home() / "arca-index")))
    )
    vector_backend: str = _env("ARCA_VECTOR_BACKEND", "faiss")  # faiss | qdrant

    # --- retrieval ---
    default_top_k: int = int(_env("ARCA_TOP_K", "20"))
    rrf_k: int = int(_env("ARCA_RRF_K", "60"))  # RRF constant

    # --- chunking ---
    chunk_tokens: int = int(_env("ARCA_CHUNK_TOKENS", "1000"))
    chunk_overlap: int = int(_env("ARCA_CHUNK_OVERLAP", "150"))

    # --- server (MCP over Streamable HTTP) ---
    host: str = _env("ARCA_HOST", "0.0.0.0")
    port: int = int(_env("ARCA_PORT", "8890"))
    service_name: str = _env("ARCA_SERVICE_NAME", "arca")

    # --- corpus roots (m1 SG-1-8TB defaults; overridden per host) ---
    osti_catalog: str = _env("ARCA_OSTI_CATALOG", "/Volumes/SG-1-8TB/osti/catalog/catalog.sqlite")
    lucid_sqlite: str = _env(
        "ARCA_LUCID_SQLITE", str(Path.home() / "Dropbox/XFER/piago-lucid-site/lucid.sqlite")
    )
    scout_root: str = _env("ARCA_SCOUT_ROOT", "/Volumes/SG-1-8TB/scout-corpus")

    def index_path(self, name: str) -> Path:
        self.index_dir.mkdir(parents=True, exist_ok=True)
        return self.index_dir / name


DEFAULT = Config()
