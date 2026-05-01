"""Retrieval functions over the Wikivoyage RAG index."""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from rapidfuzz import fuzz, process

from trip_planner.embeddings import embed_query
from trip_planner.schemas import DestinationHit, SectionHit
from trip_planner.vectorstore import (
    DESTINATIONS_COLLECTION,
    SECTIONS_COLLECTION,
    get_collection,
)


@lru_cache(maxsize=1)
def _all_destination_names() -> list[str]:
    coll = get_collection(DESTINATIONS_COLLECTION)
    metas = coll.get()["metadatas"] or []
    return [m["destination_name"] for m in metas if "destination_name" in m]


def resolve_destination_name(user_input: str, threshold: int = 80) -> Optional[str]:
    """Map a user spelling -> canonical indexed name. None if no good match."""
    candidates = _all_destination_names()
    if not candidates:
        return None
    match = process.extractOne(user_input, candidates, scorer=fuzz.WRatio)
    if not match:
        return None
    name, score, _ = match
    return name if score >= threshold else None


def find_destinations(query: str, k: int = 8) -> list[DestinationHit]:
    """For brainstorm queries — retrieve destinations matching the user's vibe."""
    coll = get_collection(DESTINATIONS_COLLECTION)
    if coll.count() == 0:
        return []
    v = embed_query(query)
    res = coll.query(query_embeddings=[v], n_results=min(k, coll.count()))

    hits: list[DestinationHit] = []
    docs = res["documents"][0]
    metas = res["metadatas"][0]
    dists = res["distances"][0]
    for doc, meta, dist in zip(docs, metas, dists):
        hits.append(DestinationHit(
            name=meta["destination_name"],
            summary=doc,
            similarity=1.0 - dist,
        ))
    return hits


def get_destination_details(
    destination: str,
    query: Optional[str] = None,
    section_types: Optional[list[str]] = None,
    k: int = 8,
) -> list[SectionHit]:
    """For itinerary queries — retrieve relevant section chunks for a known destination."""
    canonical = resolve_destination_name(destination)
    if not canonical:
        return []

    coll = get_collection(SECTIONS_COLLECTION)
    where: dict = {"destination_name": canonical}
    if section_types:
        where = {"$and": [where, {"section_type": {"$in": section_types}}]}

    if query:
        v = embed_query(query)
        res = coll.query(
            query_embeddings=[v],
            n_results=k,
            where=where,
        )
        docs = res["documents"][0]
        metas = res["metadatas"][0]
        dists = res["distances"][0]
    else:
        raw = coll.get(where=where, limit=k)
        docs = raw["documents"]
        metas = raw["metadatas"]
        dists = [0.0] * len(docs)

    hits: list[SectionHit] = []
    for doc, meta, dist in zip(docs, metas, dists):
        hits.append(SectionHit(
            destination=meta["destination_name"],
            section_type=meta["section_type"],
            text=doc,
            similarity=1.0 - dist,
        ))
    return hits
