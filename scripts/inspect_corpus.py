"""Query the RAG index by hand. Usage: python scripts/inspect_corpus.py

Uses the public retrieval functions so this script doubles as an end-to-end
smoke test of the retrieval layer (not just raw Chroma queries).
"""
from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
load_dotenv()

from trip_planner.retrieval import find_destinations, get_destination_details  # noqa: E402


def _print_dest_hits(hits, label):
    print(f"\n=== {label} ===")
    if not hits:
        print("  (no hits)")
        return
    for h in hits:
        print(f"\n[{h.name}]  similarity={h.similarity:.3f}")
        print(f"  {h.summary[:300]}{'...' if len(h.summary) > 300 else ''}")


def _print_section_hits(hits, label):
    print(f"\n=== {label} ===")
    if not hits:
        print("  (no hits)")
        return
    for h in hits:
        print(f"\n[{h.destination} / {h.section_type}]  similarity={h.similarity:.3f}")
        print(f"  {h.text[:300]}{'...' if len(h.text) > 300 else ''}")


def main():
    _print_dest_hits(
        find_destinations("relaxed coastal European city with great seafood", k=5),
        "Brainstorm: relaxed coastal European city with great seafood",
    )
    _print_dest_hits(
        find_destinations("art museums and pasta", k=5),
        "Brainstorm: art museums and pasta",
    )
    _print_section_hits(
        get_destination_details("Lisbon", query="romantic dinner spots", section_types=["Eat"], k=5),
        "Itinerary: Lisbon romantic dinner spots (Eat)",
    )
    _print_section_hits(
        get_destination_details("Tokyo", query="where to find ramen", section_types=["Eat"], k=5),
        "Itinerary: Tokyo where to find ramen (Eat)",
    )


if __name__ == "__main__":
    main()
