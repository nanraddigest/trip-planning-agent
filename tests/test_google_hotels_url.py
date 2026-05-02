from datetime import date

from hotel_agent.google_hotels import build_google_hotels_url


def test_basic_url():
    url = build_google_hotels_url("Lisbon", date(2026, 8, 15), date(2026, 8, 20), 2)
    assert "google.com/travel/hotels" in url
    assert "Lisbon" in url
    assert "2026-08-15" in url
    assert "2026-08-20" in url


def test_destination_with_spaces():
    url = build_google_hotels_url("New York", date(2026, 9, 1), date(2026, 9, 5), 1)
    assert "New%20York" in url or "New+York" in url


def test_url_contains_natural_query():
    url = build_google_hotels_url("Paris", date(2026, 7, 10), date(2026, 7, 14), 3)
    assert "Hotels" in url
    assert "Paris" in url
    assert "from" in url.lower()
    assert "to" in url.lower()
