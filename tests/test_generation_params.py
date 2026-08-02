"""Generation request shaping: the Argo wrapper 502s on Claude models when an
explicit `temperature` is sent. Generator must OMIT temperature by default, and
include it only when cfg.gen_temperature is set.

We inject a fake OpenAI-compatible client that records the create() kwargs, so
no network is touched.
"""
from __future__ import annotations

from arca.config import Config
from arca.generate import Generator
from arca.types import Hit


class _FakeCompletions:
    def __init__(self, sink):
        self._sink = sink

    def create(self, **kwargs):
        self._sink["kwargs"] = kwargs

        # minimal OpenAI-shaped response object
        class _Msg:
            content = "Grounded answer [docX]."

        class _Choice:
            message = _Msg()

        class _Resp:
            choices = [_Choice()]

        return _Resp()


class _FakeChat:
    def __init__(self, sink):
        self.completions = _FakeCompletions(sink)


class _FakeClient:
    def __init__(self, sink):
        self.chat = _FakeChat(sink)


def _hits():
    return [Hit("docX::0", "docX", 1.0, "some passage text", {"title": "X", "corpus": "test"})]


def _generator_with_fake_client(cfg, sink):
    gen = Generator(cfg)
    gen._client = _FakeClient(sink)  # bypass _client_lazy (no openai import/network)
    return gen


def test_temperature_omitted_by_default():
    sink: dict = {}
    cfg = Config(gen_temperature=None)
    gen = _generator_with_fake_client(cfg, sink)
    gen.answer("what is X?", _hits())
    assert "kwargs" in sink, "create() was never called"
    assert "temperature" not in sink["kwargs"], \
        "temperature must be omitted (Argo wrapper 502s on Claude with it)"


def test_temperature_included_when_configured():
    sink: dict = {}
    cfg = Config(gen_temperature=0.2)
    gen = _generator_with_fake_client(cfg, sink)
    gen.answer("what is X?", _hits())
    assert sink["kwargs"].get("temperature") == 0.2


def test_answer_carries_citations_and_hits():
    sink: dict = {}
    cfg = Config(gen_temperature=None)
    gen = _generator_with_fake_client(cfg, sink)
    ans = gen.answer("what is X?", _hits())
    assert ans.text.startswith("Grounded")
    assert ans.citations and ans.citations[0].doc_id == "docX"
    assert ans.hits
