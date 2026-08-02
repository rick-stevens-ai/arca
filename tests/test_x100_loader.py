"""X-100 corpus loader: reads <root>/<SET>/*.mmd, tags domain in metadata.set,
builds doc_id = x100:<set>:<stem>. Skips empty files, honors limit.
"""
from __future__ import annotations

from tests._helpers import make_cfg


def _seed_x100(root):
    (root / "BVBRC-100").mkdir(parents=True)
    (root / "OSTI-100").mkdir(parents=True)
    (root / "PDE-100").mkdir(parents=True)  # empty dir -> contributes nothing
    (root / "BVBRC-100" / "abc123.mmd").write_text("# Cytoscape\n\nNetwork visualization software.")
    (root / "BVBRC-100" / "def456.mmd").write_text("# SPAdes\n\nGenome assembly algorithm.")
    (root / "OSTI-100" / "ghi789.mmd").write_text("# Quantum ESPRESSO\n\nDFT materials modeling.")
    (root / "OSTI-100" / "empty.mmd").write_text("   \n\n")  # whitespace-only -> skipped


def test_x100_loads_and_tags_domain(tmp_path):
    root = tmp_path / "X-100"
    _seed_x100(root)
    cfg = make_cfg(tmp_path, x100_root=str(root))

    from arca.corpus.loaders import load_x100
    items = list(load_x100(cfg))

    # 3 real docs (empty.mmd skipped, PDE-100 empty)
    assert len(items) == 3, [d.doc_id for d, _ in items]

    by_id = {d.doc_id: (d, text) for d, text in items}
    assert "x100:BVBRC-100:abc123" in by_id
    assert "x100:OSTI-100:ghi789" in by_id
    assert "x100:OSTI-100:empty" not in by_id  # whitespace-only skipped

    doc, text = by_id["x100:BVBRC-100:abc123"]
    assert doc.corpus == "x100"
    assert doc.metadata.get("set") == "BVBRC-100"
    assert doc.metadata.get("stem") == "abc123"
    assert "Cytoscape" in doc.title
    assert "visualization" in text


def test_x100_limit(tmp_path):
    root = tmp_path / "X-100"
    _seed_x100(root)
    cfg = make_cfg(tmp_path, x100_root=str(root))

    from arca.corpus.loaders import load_x100
    items = list(load_x100(cfg, limit=2))
    assert len(items) == 2


def test_x100_missing_root_is_empty(tmp_path):
    cfg = make_cfg(tmp_path, x100_root=str(tmp_path / "does-not-exist"))
    from arca.corpus.loaders import load_x100
    assert list(load_x100(cfg)) == []


def test_x100_registered_in_loaders():
    from arca.corpus.loaders import LOADERS
    assert "x100" in LOADERS
