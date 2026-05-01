"""Phase 3 retrieval tests. Hits Vertex AI for query embeddings.

Marked `integration` — deselect with `-m "not integration"` to skip.
"""
import pytest
from dotenv import load_dotenv

load_dotenv()

from trip_planner.retrieval import (  # noqa: E402
    _all_destination_names,
    find_destinations,
    get_destination_details,
)
from trip_planner.vectorstore import (  # noqa: E402
    DESTINATIONS_COLLECTION,
    SECTIONS_COLLECTION,
    get_collection,
)


def _index_is_populated() -> bool:
    return (
        get_collection(DESTINATIONS_COLLECTION).count() > 0
        and get_collection(SECTIONS_COLLECTION).count() > 0
    )


pytestmark = pytest.mark.integration


def test_brainstorm_returns_pilot_european_coastals():
    if not _index_is_populated():
        pytest.skip("corpus not yet ingested — run scripts/build_corpus.py first")

    hits = find_destinations("relaxed coastal European city with great seafood", k=5)
    names = {h.name for h in hits}
    expected = {"Lisbon", "Porto", "Barcelona"}
    overlap = names & expected
    assert len(overlap) >= 2, f"top 5 brainstorm hits: {names} (expected ≥2 of {expected})"


def test_itinerary_for_lisbon_eat_returns_chunks():
    if not _index_is_populated():
        pytest.skip("corpus not yet ingested")
    hits = get_destination_details(
        "Lisbon", query="seafood and tavernas", section_types=["Eat"], k=5
    )
    assert len(hits) >= 1
    assert all(h.destination == "Lisbon" for h in hits)
    assert all(h.section_type == "Eat" for h in hits)


def test_fuzzy_resolves_lisboa_to_lisbon():
    if not _index_is_populated():
        pytest.skip("corpus not yet ingested")
    hits = get_destination_details(
        "Lisboa", query="viewpoints over the city", section_types=["See", "Do"], k=3
    )
    assert hits, "Lisboa should fuzzy-match Lisbon"
    assert all(h.destination == "Lisbon" for h in hits)


def test_unknown_destination_returns_empty():
    if not _index_is_populated():
        pytest.skip("corpus not yet ingested")
    assert get_destination_details("Atlantis") == []


def test_known_pilot_destinations_present():
    if not _index_is_populated():
        pytest.skip("corpus not yet ingested")
    names = set(_all_destination_names())
    # Spot check a few we put in destinations.txt
    for expected in ["Lisbon", "Tokyo", "Marrakech"]:
        assert expected in names, f"{expected} missing from corpus: {names}"
