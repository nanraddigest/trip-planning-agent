from datetime import date
from urllib.parse import quote


def build_google_hotels_url(
    destination: str,
    check_in_date: date,
    check_out_date: date,
    guests: int = 2,
) -> str:
    """Build a Google Hotels search URL using natural-language query format.

    Mirrors the Google Flights URL pattern (a single ?q= query parameter
    containing a human-readable phrase) — the path-based /hotels/{dest} form
    returns a near-empty stub.
    """
    q = (
        f"Hotels in {destination} from {check_in_date.isoformat()} "
        f"to {check_out_date.isoformat()}"
    )
    return f"https://www.google.com/travel/hotels?q={quote(q)}"
