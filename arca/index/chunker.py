"""Heading-aware chunker for Marker (.md) / Nougat (.mmd) parsed output."""

from __future__ import annotations

import re
from typing import Iterator

from arca.config import Config, DEFAULT
from arca.types import Chunk

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)


def _approx_tokens(text: str) -> int:
    # cheap heuristic ~4 chars/token; avoids a tokenizer dep in the hot path
    return max(1, len(text) // 4)


def _split_sections(text: str) -> list[tuple[str, str]]:
    """Split markdown into (section_title, body) pairs by headings."""
    matches = list(_HEADING.finditer(text))
    if not matches:
        return [("", text)]
    sections: list[tuple[str, str]] = []
    # preamble before first heading
    if matches[0].start() > 0:
        pre = text[: matches[0].start()].strip()
        if pre:
            sections.append(("", pre))
    for i, m in enumerate(matches):
        title = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if body:
            sections.append((title, body))
    return sections


def chunk_document(
    doc_id: str, text: str, cfg: Config = DEFAULT
) -> Iterator[Chunk]:
    """Yield Chunks: split by heading, then window long sections with overlap."""
    max_tok = cfg.chunk_tokens
    overlap = cfg.chunk_overlap
    ordinal = 0
    for section, body in _split_sections(text):
        if _approx_tokens(body) <= max_tok:
            yield Chunk(
                chunk_id=f"{doc_id}::{ordinal}",
                doc_id=doc_id,
                text=body,
                ordinal=ordinal,
                section=section or None,
                n_tokens=_approx_tokens(body),
            )
            ordinal += 1
            continue
        # window on paragraph boundaries
        paras = [p for p in re.split(r"\n\s*\n", body) if p.strip()]
        buf: list[str] = []
        buf_tok = 0
        for para in paras:
            pt = _approx_tokens(para)
            if buf and buf_tok + pt > max_tok:
                joined = "\n\n".join(buf)
                yield Chunk(
                    chunk_id=f"{doc_id}::{ordinal}",
                    doc_id=doc_id,
                    text=joined,
                    ordinal=ordinal,
                    section=section or None,
                    n_tokens=buf_tok,
                )
                ordinal += 1
                # overlap: keep tail paragraphs summing ~overlap tokens
                tail: list[str] = []
                tail_tok = 0
                for p in reversed(buf):
                    tail.insert(0, p)
                    tail_tok += _approx_tokens(p)
                    if tail_tok >= overlap:
                        break
                buf, buf_tok = tail, tail_tok
            buf.append(para)
            buf_tok += pt
        if buf:
            joined = "\n\n".join(buf)
            yield Chunk(
                chunk_id=f"{doc_id}::{ordinal}",
                doc_id=doc_id,
                text=joined,
                ordinal=ordinal,
                section=section or None,
                n_tokens=buf_tok,
            )
            ordinal += 1
