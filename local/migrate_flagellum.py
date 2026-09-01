#!/usr/bin/env python3
"""One-time migration: copy flagellum_papers (old single-corpus store) into
corpus_flagellum (new multi-corpus store) without re-embedding."""
import chromadb

OLD_DIR = "/Users/stevens/.flagellum-rag/chroma"
OLD_COLL = "flagellum_papers"
NEW_DIR = "/Users/stevens/.corpus-rag/chroma"
NEW_COLL = "corpus_flagellum"

old = chromadb.PersistentClient(path=OLD_DIR).get_collection(OLD_COLL)
n = old.count()
print(f"source {OLD_COLL}: {n} chunks")

new_client = chromadb.PersistentClient(path=NEW_DIR)
try:
    new_client.delete_collection(NEW_COLL)
except Exception:
    pass
new = new_client.get_or_create_collection(NEW_COLL, metadata={"hnsw:space": "cosine"})

B = 512
moved = 0
# pull with embeddings + docs + metadata, page through by offset
while moved < n:
    batch = old.get(limit=B, offset=moved,
                    include=["documents", "metadatas", "embeddings"])
    if not batch["ids"]:
        break
    new.add(ids=batch["ids"], documents=batch["documents"],
            embeddings=batch["embeddings"], metadatas=batch["metadatas"])
    moved += len(batch["ids"])
    print(f"  migrated {moved}/{n}", flush=True)

print(f"DONE. {NEW_COLL} now has {new.count()} chunks (source had {n})")
