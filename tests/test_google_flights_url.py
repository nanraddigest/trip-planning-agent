from datetime import date

from google_flights import build_google_flights_url


def test_one_way_single_airport():
    url = build_google_flights_url(["JFK"], ["LIS"], date(2026, 8, 15))
    assert url.startswith("https://www.google.com/travel/flights?q=")
    assert "Flights%20from%20JFK%20to%20LIS%20on%202026-08-15" in url
    assert "returning" not in url


def test_one_way_multi_airport():
    url = build_google_flights_url(
        ["JFK", "LGA", "EWR"], ["LIS"], date(2026, 8, 15)
    )
    assert "JFK%2CLGA%2CEWR" in url
    assert "to%20LIS" in url


def test_round_trip():
    url = build_google_flights_url(
        ["JFK"], ["LIS"], date(2026, 8, 15), date(2026, 8, 22)
    )
    assert "on%202026-08-15%20returning%202026-08-22" in url


def test_url_encoding_spaces_and_commas():
    url = build_google_flights_url(
        ["JFK", "LGA"], ["CDG", "ORY"], date(2026, 8, 15)
    )
    assert "%20" in url
    assert "%2C" in url
    assert " " not in url
    assert "," not in url.split("?q=", 1)[1]
