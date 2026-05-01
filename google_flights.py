from datetime import date
from urllib.parse import quote


def build_google_flights_url(
    origin_iatas: list[str],
    destination_iatas: list[str],
    departure_date: date,
    return_date: date | None = None,
) -> str:
    """
    Build a Google Flights search URL. Multi-airport origins/destinations are
    comma-separated. Round trip is encoded by appending 'returning {date}'.
    """
    origin = ",".join(origin_iatas)
    dest = ",".join(destination_iatas)

    if return_date:
        q = (
            f"Flights from {origin} to {dest} on {departure_date.isoformat()} "
            f"returning {return_date.isoformat()}"
        )
    else:
        q = f"Flights from {origin} to {dest} on {departure_date.isoformat()}"

    return f"https://www.google.com/travel/flights?q={quote(q)}"
