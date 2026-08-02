"""Server wiring: load_retriever must pick the fixture when no index exists and
the real HybridRetriever when a built index is named. This is the exact bug that
made Arca 'healthy but empty' — the service defaulted to the fixture because
ARCA_INDEX_NAME was unset.

build_app is exercised only when the mcp SDK is installed (skipped otherwise);
the tool bodies themselves are thin wrappers already covered by the retriever
and generator tests.
"""
from __future__ import annotations

import pytest

from tests._helpers import build_store, make_cfg

faiss = pytest.importorskip("faiss")


def test_load_retriever_falls_back_to_fixture(tmp_path):
    from arca.retrieve import FixtureRetriever, load_retriever
    cfg = make_cfg(tmp_path)
    # no index_name -> fixture
    r = load_retriever(cfg, None)
    assert isinstance(r, FixtureRetriever)
    # a name that doesn't exist on disk -> still fixture (graceful)
    r2 = load_retriever(cfg, "nonexistent-index")
    assert isinstance(r2, FixtureRetriever)


def test_load_retriever_uses_real_index_when_present(tmp_path):
    from arca.retrieve import HybridRetriever, load_retriever
    cfg = make_cfg(tmp_path)
    # build a real 'test' index on disk
    build_store(cfg, [
        ("docA", "Alpha", "alpha text", [1, 0, 0, 0, 0, 0, 0, 0]),
        ("docB", "Beta", "beta text", [0, 1, 0, 0, 0, 0, 0, 0]),
    ])
    r = load_retriever(cfg, "test")
    assert isinstance(r, HybridRetriever), "should load the real index, not the fixture"


def test_build_app_wires_up_if_sdk_available():
    mcp_sdk = pytest.importorskip("mcp.server")
    from arca.server.app import build_app
    from arca.config import Config
    # Uses fixture retriever (no index_name); just proves the app assembles.
    app = build_app(Config(), index_name=None)
    assert app is not None
