"""Grounded synthesis — BYO-LLM over retrieved chunks, returns Answer + citations.

Backends (config.gen_backend): argo | openai | vllm | local — all OpenAI-compatible,
so one client path covers them. Generation is optional: if the LLM call fails, the
service still returns hits (retrieval never depends on generation being up).
"""

from __future__ import annotations

from typing import Optional

from arca.config import Config, DEFAULT
from arca.types import Answer, Citation, Hit

_SYSTEM = (
    "You are Arca, a scientific literature assistant. Answer ONLY from the provided "
    "context passages. Cite sources inline as [doc_id]. If the context does not "
    "support an answer, say so plainly. Be concise and precise."
)


def _format_context(hits: list[Hit]) -> str:
    blocks = []
    for h in hits:
        title = h.metadata.get("title", "")
        blocks.append(f"[{h.doc_id}] {title}\n{h.text}")
    return "\n\n---\n\n".join(blocks)


class Generator:
    def __init__(self, cfg: Config = DEFAULT):
        self.cfg = cfg
        self._client = None

    def _client_lazy(self):
        if self._client is None:
            import openai

            self._client = openai.OpenAI(
                api_key=self.cfg.gen_api_key, base_url=self.cfg.gen_base_url
            )
        return self._client

    def answer(self, query: str, hits: list[Hit], model: Optional[str] = None) -> Answer:
        model = model or self.cfg.gen_model
        if not hits:
            return Answer(text="No relevant passages found in the corpus.", model=model, hits=[])
        context = _format_context(hits)
        prompt = f"Context passages:\n\n{context}\n\nQuestion: {query}\n\nAnswer (cite [doc_id]):"
        try:
            client = self._client_lazy()
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": _SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                max_tokens=1500,
            )
            text = resp.choices[0].message.content or ""
        except Exception as exc:  # generation is best-effort; retrieval still returned
            text = f"[generation unavailable: {exc}] Returning retrieved passages only."

        # Build citations from the hits actually provided (dedupe by doc)
        cite_map: dict[str, Citation] = {}
        for h in hits:
            c = cite_map.setdefault(
                h.doc_id,
                Citation(doc_id=h.doc_id, title=h.metadata.get("title", ""),
                         doi=h.metadata.get("doi")),
            )
            c.chunk_ids.append(h.chunk_id)
        return Answer(text=text, citations=list(cite_map.values()), model=model, hits=hits)
