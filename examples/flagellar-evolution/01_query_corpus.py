#!/usr/bin/env python3
"""Step 1: Ask the corpus a set of grounded, cited questions via Arca.

Uses Arca's programmatic API (retriever + generator) — the same path the
`arca_answer` MCP tool takes. Writes answers.json for the downstream paper build.

Agents hit the identical capability over MCP:
    result = await session.call_tool("arca_answer",
                 {"query": "...", "corpus": "flagellum", "top_k": 12})

Usage:
    python 01_query_corpus.py --index flagellum --out answers.json
"""
import argparse
import json
import sys

from arca.config import DEFAULT
from arca.generate import Generator
from arca.retrieve import load_retriever

# The four framing questions for the flagellar-evolution synthesis. Editing this
# list (and section titles) is how you retarget the example to another topic.
QUESTIONS = [
    ("t3ss_direction",
     "What is the evolutionary relationship between the flagellar export apparatus "
     "and the type III secretion system? Which came first, and what evidence bears "
     "on the direction of evolution?"),
    ("motor_origin",
     "How did the flagellar motor, its stator units (MotA/MotB, PomA/PomB), and "
     "torque generation evolve? What is known about the evolution of ion "
     "selectivity (proton vs sodium) and the diversity of stator systems?"),
    ("archaellum",
     "How do flagellar architectures differ across bacterial species and between "
     "bacteria and archaea (archaellum)? What does this imply about convergent "
     "evolution, a conserved core, and species-specific elaborations?"),
    ("minimal_ancestor",
     "What are the major unresolved questions about the evolutionary origin of the "
     "bacterial flagellum, including exaptation, a minimal ancestral machine, and "
     "the role of the ATPase?"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", default="flagellum", help="built index name")
    ap.add_argument("--corpus", default=None, help="optional corpus filter")
    ap.add_argument("--top-k", type=int, default=12)
    ap.add_argument("--out", default="answers.json")
    a = ap.parse_args()

    retriever = load_retriever(DEFAULT, a.index)
    generator = Generator(DEFAULT)

    out = {}
    for key, q in QUESTIONS:
        hits = retriever.search(q, top_k=a.top_k, corpus=a.corpus)
        ans = generator.answer(q, hits).to_dict()
        # keep the answer text + the set of cited doc ids for the paper builder
        out[key] = {
            "question": q,
            "answer": ans.get("answer", ""),
            "citations": ans.get("citations", []),
            "doc_ids": sorted(
                pid for pid in {h.to_dict().get("paper_id") for h in hits}
                if pid),
        }
        print(f"[{key}] {len(out[key]['doc_ids'])} docs cited", flush=True)

    with open(a.out, "w") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
