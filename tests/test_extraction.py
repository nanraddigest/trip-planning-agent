"""Phase 3 — extraction against the saved sample markdown. Hits Vertex AI."""
import asyncio
from datetime import date
from pathlib import Path

import pytest

from agent import extract_flights
from schemas import FormInput

SAMPLE = Path(__file__).parent.parent / "scripts" / "sample_markdown.md"


@pytest.mark.integration
def test_extract_jfk_lis_from_saved_markdown():
    if not SAMPLE.exists():
        pytest.skip("scripts/sample_markdown.md missing — run scripts/test_scrape.py first")

    markdown = SAMPLE.read_text()
    form = FormInput(
        origin="New York",
        destination="Lisbon",
        departure_date=date(2026, 8, 15),
        cabin_class="Economy",
    )
    result = asyncio.run(extract_flights(markdown, form, ["JFK"], ["LIS"]))

    assert len(result.flights) >= 3, f"Expected >=3 flights, got {len(result.flights)}"
    for f in result.flights:
        assert f.airlines, f"Missing airlines on {f}"
        assert f.price_amount > 0, f"Bad price on {f}"
        assert f.duration_minutes > 0, f"Bad duration on {f}"
        assert f.origin_iata in {"JFK", "LGA", "EWR", "NYC"}, f"Unexpected origin {f.origin_iata}"
        assert f.destination_iata in {"LIS"}, f"Unexpected destination {f.destination_iata}"
