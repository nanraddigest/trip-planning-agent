"""ChromaDB persistent client and collection helpers."""
from __future__ import annotations

import chromadb

CHROMA_PATH = "data/chroma"
DESTINATIONS_COLLECTION = "destinations"
SECTIONS_COLLECTION = "sections"

_client: chromadb.api.ClientAPI | None = None


def get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=CHROMA_PATH)
    return _client


def get_collection(name: str):
    """Return a Chroma collection with cosine similarity space.

    We always pass our own (Vertex) embeddings, so we override Chroma's default
    embedding function with a no-op-style passthrough by passing
    ``embedding_function=None`` is NOT allowed in 1.x — instead we just never
    call ``add(texts=...)`` and only use ``add(embeddings=...)`` / ``query(query_embeddings=...)``.
    """
    return get_client().get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )
