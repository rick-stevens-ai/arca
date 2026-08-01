"""Embedding client — Argo/OpenAI-compatible. Dim locked to config.embed_dim (1536)."""

from __future__ import annotations

from typing import Sequence

from arca.config import Config, DEFAULT


class Embedder:
    """Thin wrapper over an OpenAI-compatible /embeddings endpoint (Argo proxy)."""

    def __init__(self, cfg: Config = DEFAULT):
        self.cfg = cfg
        self._client = None

    def _client_lazy(self):
        if self._client is None:
            import openai  # lazy: keep import cost out of module load

            self._client = openai.OpenAI(
                api_key=self.cfg.embed_api_key, base_url=self.cfg.embed_base_url
            )
        return self._client

    def embed(self, texts: Sequence[str], batch_size: int = 64) -> list[list[float]]:
        """Embed a list of texts. Returns one 1536-d vector per text."""
        if not texts:
            return []
        client = self._client_lazy()
        out: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            batch = list(texts[i : i + batch_size])
            resp = client.embeddings.create(model=self.cfg.embed_model, input=batch)
            for item in resp.data:
                vec = item.embedding
                if len(vec) != self.cfg.embed_dim:
                    raise ValueError(
                        f"Embedding dim {len(vec)} != locked {self.cfg.embed_dim}. "
                        "Refusing to mix dims (would corrupt the index)."
                    )
                out.append(vec)
        return out

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]
