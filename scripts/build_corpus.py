"""Run the full Wikivoyage ingest pipeline. Idempotent — safe to re-run.

By default skips chunks/destinations whose IDs are already in Chroma — this
saves the costly Vertex embedding call on iterative re-runs. Pass
``--reembed-all`` to bypass the skip and re-embed everything.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from tqdm import tqdm

# Ensure repo root is on path so trip_planner.* imports work when launched as a script.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
load_dotenv()

from trip_planner.chunking import chunk_destination, parse_article  # noqa: E402
from trip_planner.corpus_build import fetch_wikitext  # noqa: E402
from trip_planner.embeddings import embed_documents  # noqa: E402
from trip_planner.vectorstore import (  # noqa: E402
    DESTINATIONS_COLLECTION,
    SECTIONS_COLLECTION,
    get_collection,
)

DESTINATIONS_FILE = Path("data/destinations.txt")
BATCH = 32
PACE_SECONDS = 0.25  # stay under 250 instances/min Vertex free-tier ceiling


def _batched_upsert(coll, ids, vectors, docs, metas, label):
    """Batch upsert with tqdm + rate pacing."""
    for i in tqdm(range(0, len(ids), BATCH), desc=label):
        coll.upsert(
            ids=ids[i:i + BATCH],
            embeddings=vectors[i:i + BATCH],
            documents=docs[i:i + BATCH],
            metadatas=metas[i:i + BATCH],
        )


def _embed_in_batches(texts, label):
    out: list[list[float]] = []
    for i in tqdm(range(0, len(texts), BATCH), desc=label):
        batch = texts[i:i + BATCH]
        out.extend(embed_documents(batch))
        time.sleep(PACE_SECONDS)
    return out


def main(limit: int | None, parse_only: bool, reembed_all: bool):
    if not DESTINATIONS_FILE.exists():
        print(f"Missing {DESTINATIONS_FILE}. Create it (one destination per line).")
        sys.exit(1)

    destinations = [
        line.strip()
        for line in DESTINATIONS_FILE.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]
    if limit:
        destinations = destinations[:limit]

    dest_coll = get_collection(DESTINATIONS_COLLECTION)
    sec_coll = get_collection(SECTIONS_COLLECTION)

    existing_dest_ids: set[str] = set()
    existing_sec_ids: set[str] = set()
    if not reembed_all:
        existing_dest_ids = set(dest_coll.get()["ids"])
        existing_sec_ids = set(sec_coll.get()["ids"])
        if existing_dest_ids or existing_sec_ids:
            print(
                f"Will skip {len(existing_dest_ids)} dest + {len(existing_sec_ids)} "
                f"section IDs already in the index. Use --reembed-all to override."
            )

    dest_buffer: list[str] = []
    dest_ids: list[str] = []
    dest_metas: list[dict] = []
    sec_buffer: list[str] = []
    sec_ids: list[str] = []
    sec_metas: list[dict] = []

    skipped: list[str] = []
    section_count_by_dest: list[int] = []

    for name in tqdm(destinations, desc="Fetch + parse"):
        fetched = fetch_wikitext(name)
        if not fetched:
            skipped.append(name)
            continue
        canonical, wikitext = fetched
        parsed = parse_article(canonical, wikitext)
        section_count_by_dest.append(len(parsed.sections))
        dest_doc, chunks = chunk_destination(parsed)

        if dest_doc["id"] not in existing_dest_ids and dest_doc["text"]:
            dest_buffer.append(dest_doc["text"])
            dest_ids.append(dest_doc["id"])
            dest_metas.append(dest_doc["metadata"])

        for c in chunks:
            if c["id"] in existing_sec_ids:
                continue
            sec_buffer.append(c["text"])
            sec_ids.append(c["id"])
            sec_metas.append(c["metadata"])

    if skipped:
        print(f"\nSkipped (page not found): {skipped}")

    if section_count_by_dest:
        avg = sum(section_count_by_dest) / len(section_count_by_dest)
        print(
            f"\nParsed {len(section_count_by_dest)} destinations. "
            f"Avg {avg:.1f} sections/destination. "
            f"{len(dest_ids)} new dest docs, {len(sec_ids)} new section chunks."
        )

    if parse_only:
        print("(parse-only mode — nothing embedded or indexed.)")
        return

    if dest_buffer:
        print(f"\nEmbedding {len(dest_buffer)} destination summaries...")
        dest_vectors = _embed_in_batches(dest_buffer, label="Embed dest")
        _batched_upsert(dest_coll, dest_ids, dest_vectors, dest_buffer, dest_metas,
                        label="Upsert dest")

    if sec_buffer:
        print(f"Embedding {len(sec_buffer)} section chunks...")
        sec_vectors = _embed_in_batches(sec_buffer, label="Embed sections")
        _batched_upsert(sec_coll, sec_ids, sec_vectors, sec_buffer, sec_metas,
                        label="Upsert sections")

    print(
        f"\nDone. Total in index: {dest_coll.count()} destinations, "
        f"{sec_coll.count()} section chunks."
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=None,
                   help="Process only the first N destinations.")
    p.add_argument("--parse-only", action="store_true",
                   help="Fetch & parse but don't embed/index. Useful for chunking iteration.")
    p.add_argument("--reembed-all", action="store_true",
                   help="Re-embed every chunk even if its ID is already indexed.")
    args = p.parse_args()
    main(args.limit, args.parse_only, args.reembed_all)
