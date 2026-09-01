#!/usr/bin/env python3
"""Smoke test for corpus-rag multi-corpus service."""
import server as S
print("=== corpus_list ==="); print(S.corpus_list())
print("\n=== corpus_stats(flagellum) ==="); print(S.corpus_stats("flagellum"))
print("\n=== corpus_search (bad corpus name) ==="); print(S.corpus_search("x", "nope")[:120])
print("\n=== corpus_search(flagellum, torque, 2015+) ===")
print(S.corpus_search("cryo-EM flagellar motor structure", "flagellum", top_k=2, year_min=2015))
print("\n=== corpus_answer(flagellum) ===")
print(S.corpus_answer("How is switching between CW and CCW rotation controlled?", "flagellum", top_k=6))
