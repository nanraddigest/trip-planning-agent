import os
from functools import lru_cache

import pandas as pd
from langchain_core.tools import tool

METRO_AIRPORTS = {
    "new york": ["JFK", "LGA", "EWR"],
    "nyc": ["JFK", "LGA", "EWR"],
    "london": ["LHR", "LGW", "STN", "LTN"],
    "paris": ["CDG", "ORY"],
    "tokyo": ["HND", "NRT"],
    "bay area": ["SFO", "OAK", "SJC"],
    "san francisco bay area": ["SFO", "OAK", "SJC"],
    "washington": ["IAD", "DCA", "BWI"],
    "washington dc": ["IAD", "DCA", "BWI"],
    "chicago": ["ORD", "MDW"],
    "milan": ["MXP", "LIN"],
    "rome": ["FCO", "CIA"],
    "stockholm": ["ARN", "BMA"],
    "moscow": ["SVO", "DME", "VKO"],
    "houston": ["IAH", "HOU"],
    "dallas": ["DFW", "DAL"],
}

AIRPORTS_CSV = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "airports.csv",
)


@lru_cache(maxsize=1)
def _load_airports() -> pd.DataFrame:
    cols = ["airport_id", "name", "city", "country", "iata", "icao", "lat", "lon",
            "alt", "tz", "dst", "tzdb", "type", "source"]
    df = pd.read_csv(AIRPORTS_CSV, header=None, names=cols, na_values=["\\N"])
    df = df[df["iata"].notna() & (df["iata"].str.len() == 3)]
    return df


@tool
def resolve_airport(query: str) -> list[dict]:
    """
    Resolve a city name or partial airport name to IATA airport codes.
    Returns up to 5 matches. For multi-airport metros (NYC, London, etc.),
    returns all major hubs.

    Args:
        query: City name (e.g. "New York"), IATA code ("JFK"), or partial
               airport name.

    Returns:
        List of dicts with keys: iata, city, name, country.
    """
    df = _load_airports()
    q = query.strip().lower()

    if len(q) == 3 and q.upper() in df["iata"].values:
        row = df[df["iata"] == q.upper()].iloc[0]
        return [{"iata": row["iata"], "city": row["city"],
                 "name": row["name"], "country": row["country"]}]

    if q in METRO_AIRPORTS:
        codes = METRO_AIRPORTS[q]
        rows = df[df["iata"].isin(codes)]
        return rows[["iata", "city", "name", "country"]].to_dict("records")

    matches = df[df["city"].str.lower() == q]
    if len(matches) == 0:
        matches = df[df["city"].str.lower().str.contains(q, na=False) |
                     df["name"].str.lower().str.contains(q, na=False)]

    matches = matches.copy()
    matches["intl_rank"] = matches["name"].str.contains(
        "International", case=False, na=False
    ).astype(int)
    matches = matches.sort_values(["intl_rank", "name"], ascending=[False, True])
    return matches.head(5)[["iata", "city", "name", "country"]].to_dict("records")
