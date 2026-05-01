from tools.airports import resolve_airport


def _iatas(rows):
    return {r["iata"] for r in rows}


def test_direct_iata_jfk():
    rows = resolve_airport.invoke({"query": "JFK"})
    assert len(rows) == 1
    assert rows[0]["iata"] == "JFK"


def test_metro_new_york():
    rows = resolve_airport.invoke({"query": "New York"})
    assert _iatas(rows) == {"JFK", "LGA", "EWR"}


def test_metro_nyc_lowercase_matches_new_york():
    nyc = resolve_airport.invoke({"query": "nyc"})
    ny = resolve_airport.invoke({"query": "New York"})
    assert _iatas(nyc) == _iatas(ny)


def test_city_lisbon_returns_lis():
    rows = resolve_airport.invoke({"query": "Lisbon"})
    assert any(r["iata"] == "LIS" for r in rows)


def test_unknown_city_returns_empty():
    rows = resolve_airport.invoke({"query": "Atlantis"})
    assert rows == []
