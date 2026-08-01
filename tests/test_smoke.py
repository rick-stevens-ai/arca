"""P0 smoke tests: package imports, fixture retrieval, MCP tool surface — no deps, no corpus."""

from __future__ import annotations


def test_imports():
    import arca
    from arca import Answer, Chunk, Document, Hit  # noqa
    from arca.config import DEFAULT

    assert arca.__version__ == "0.1.0"
    assert DEFAULT.embed_dim == 1536  # locked


def test_fixture_retrieval():
    from arca.retrieve import FixtureRetriever

    r = FixtureRetriever()
    hits = r.search("ATM DNA damage low-dose radiation", top_k=5)
    assert hits, "fixture retriever returned no hits"
    assert hits[0].doc_id == "fixture-1"
    assert hits[0].score > 0


def test_fixture_corpus_filter():
    from arca.retrieve import FixtureRetriever

    r = FixtureRetriever()
    hits = r.search("retrieval scientific articles", top_k=5, corpus="osti")
    assert all(h.metadata.get("corpus") == "osti" for h in hits)


def test_chunker():
    from arca.index import chunk_document

    text = "# Intro\n\nHello world.\n\n## Methods\n\nWe did things.\n\n" + ("x " * 3000)
    chunks = list(chunk_document("d1", text))
    assert len(chunks) >= 2
    assert chunks[0].doc_id == "d1"
    assert all(c.chunk_id.startswith("d1::") for c in chunks)


def test_generator_no_llm_graceful():
    """Generator must return an Answer even when the LLM endpoint is unreachable."""
    from arca.config import Config
    from arca.generate import Generator
    from arca.retrieve import FixtureRetriever

    cfg = Config(gen_base_url="http://127.0.0.1:1", gen_api_key="x")  # dead endpoint
    hits = FixtureRetriever().search("ATM radiation", top_k=3)
    ans = Generator(cfg).answer("What does ATM do?", hits)
    assert ans.hits, "must still return retrieved hits"
    assert ans.citations, "must build citations from hits"


def test_answer_serialization():
    from arca.types import Answer, Citation, Hit

    a = Answer(text="x", citations=[Citation("d1", "T")], hits=[Hit("d1::0", "d1", 1.0, "t")])
    d = a.to_dict()
    assert d["text"] == "x" and d["citations"][0]["doc_id"] == "d1"
