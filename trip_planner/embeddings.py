"""Vertex AI embedding helpers (process-singleton)."""
from __future__ import annotations

import os

from langchain_google_vertexai import VertexAIEmbeddings

EMBED_MODEL = "text-embedding-005"

_emb: VertexAIEmbeddings | None = None


def get_embedder() -> VertexAIEmbeddings:
    global _emb
    if _emb is None:
        _emb = VertexAIEmbeddings(
            model_name=EMBED_MODEL,
            project=os.environ["GCP_PROJECT_ID"],
            location=os.environ.get("GCP_REGION", "us-central1"),
        )
    return _emb


def embed_documents(texts: list[str]) -> list[list[float]]:
    return get_embedder().embed_documents(texts)


def embed_query(text: str) -> list[float]:
    return get_embedder().embed_query(text)
