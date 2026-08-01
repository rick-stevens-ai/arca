"""Corpus loaders → normalized (Document, text) pairs for indexing.

Each loader yields (Document, full_text) tuples. Indexing (chunk+embed) is done by
arca.index against these. Loaders are lazy/streaming so a 280K-paper corpus doesn't
blow up memory.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterator

from arca.config import Config, DEFAULT
from arca.types import Document


def _read_text(path: str) -> str:
    try:
        return Path(path).read_text(errors="ignore")
    except Exception:
        return ""


def load_osti(cfg: Config = DEFAULT, limit: int | None = None) -> Iterator[tuple[Document, str]]:
    """Stream OSTI papers from catalog.sqlite that have a parsed .md/.mmd path."""
    con = sqlite3.connect(f"file:{cfg.osti_catalog}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    q = (
        "SELECT osti_id, title, doi, publication_year AS year, md_path, mmd_path "
        "FROM papers WHERE md_path IS NOT NULL OR mmd_path IS NOT NULL"
    )
    if limit:
        q += f" LIMIT {int(limit)}"
    for r in con.execute(q):
        path = r["md_path"] or r["mmd_path"]
        text = _read_text(path)
        if not text.strip():
            continue
        yield (
            Document(
                doc_id=f"osti:{r['osti_id']}",
                corpus="osti",
                title=r["title"] or "",
                year=r["year"],
                doi=r["doi"],
                path=path,
                metadata={"corpus": "osti", "title": r["title"] or "", "doi": r["doi"]},
            ),
            text,
        )
    con.close()


def load_lucid(cfg: Config = DEFAULT, limit: int | None = None) -> Iterator[tuple[Document, str]]:
    """Stream LUCID papers from lucid.sqlite (piago data spine)."""
    db = cfg.lucid_sqlite
    if not Path(db).exists():
        return
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    # schema: papers(paper_id, title, authors, year, doi, path_txt, corpus_tag, ...)
    try:
        cols = {r[1] for r in con.execute("PRAGMA table_info(papers)")}
    except sqlite3.Error:
        con.close()
        return
    path_col = "path_txt" if "path_txt" in cols else ("path_pdf" if "path_pdf" in cols else None)
    q = "SELECT * FROM papers"
    if limit:
        q += f" LIMIT {int(limit)}"
    for r in con.execute(q):
        d = dict(r)
        text = _read_text(d.get(path_col, "")) if path_col else ""
        if not text.strip():
            # fall back to title+abstract if no parsed text on disk
            text = (d.get("title", "") + "\n\n" + str(d.get("abstract", ""))).strip()
        if not text.strip():
            continue
        yield (
            Document(
                doc_id=f"lucid:{d.get('paper_id')}",
                corpus="lucid",
                title=d.get("title", "") or "",
                year=d.get("year"),
                doi=d.get("doi"),
                path=d.get(path_col) if path_col else None,
                metadata={"corpus": "lucid", "title": d.get("title", "") or "",
                          "doi": d.get("doi"), "corpus_tag": d.get("corpus_tag")},
            ),
            text,
        )
    con.close()


def load_scout(cfg: Config = DEFAULT, limit: int | None = None) -> Iterator[tuple[Document, str]]:
    """Stream SCOUT papers from flat SHA-named md/ (mmd/ fallback)."""
    root = Path(cfg.scout_root)
    md_dir = root / "md"
    mmd_dir = root / "mmd"
    src = md_dir if md_dir.exists() else mmd_dir
    if not src.exists():
        return
    n = 0
    for p in src.iterdir():
        if not p.is_file():
            continue
        text = _read_text(str(p))
        if not text.strip():
            continue
        sha = p.stem
        yield (
            Document(
                doc_id=f"scout:{sha}",
                corpus="scout",
                title="",  # SCOUT is SHA-named; title parsed from text later if needed
                path=str(p),
                metadata={"corpus": "scout"},
            ),
            text,
        )
        n += 1
        if limit and n >= limit:
            break


LOADERS = {"osti": load_osti, "lucid": load_lucid, "scout": load_scout}
