"""LangChain tool wrappers exposed to the trip-planner agent."""
from langchain_core.tools import tool

from trip_planner.retrieval import find_destinations, get_destination_details


@tool
def search_destinations(query: str) -> list[dict]:
    """
    Use this when the user does not yet have a destination — i.e., they're
    brainstorming where to go ("a relaxed coastal place", "somewhere with good
    food and history under 6 hours from NYC"). The query should describe the
    travel vibe, interests, constraints — not a city name.

    Returns up to 8 candidate destinations with summaries.
    """
    hits = find_destinations(query, k=8)
    return [h.model_dump() for h in hits]


@tool
def search_destination_content(
    destination: str,
    query: str = "",
    section_types: list[str] = [],
) -> list[dict]:
    """
    Use this when the user already has a destination and wants suggestions for
    things to do, see, eat, or where to stay there.

    Args:
      destination: The city or region name (e.g., "Lisbon", "Tokyo", "Tuscany").
        Misspellings will be auto-corrected.
      query: A natural-language description of what the user is asking about
        (e.g., "romantic restaurants", "quiet neighborhoods to stay in",
        "kid-friendly activities"). If empty, returns top general content.
      section_types: Optional filter. Choose from: ["Understand", "Get in",
        "Get around", "See", "Do", "Eat", "Drink", "Sleep", "Buy", "Go next"].
        Use ["Eat"] for food queries, ["See", "Do"] for activities, ["Sleep"]
        for accommodation, etc.

    Returns up to 8 relevant content chunks.
    """
    hits = get_destination_details(
        destination=destination,
        query=query or None,
        section_types=section_types or None,
        k=8,
    )
    return [h.model_dump() for h in hits]
