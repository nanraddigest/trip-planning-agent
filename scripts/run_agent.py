"""Phase 4 CLI smoke test for the flight search agent."""
import asyncio
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent import run_search  # noqa: E402
from schemas import FormInput  # noqa: E402


async def main():
    form = FormInput(
        origin="New York",
        destination="Lisbon",
        departure_date=date.today() + timedelta(days=60),
        cabin_class="Economy",
    )
    print(f"Searching: {form.origin} -> {form.destination} on {form.departure_date}\n")
    result = await run_search(form)
    print(f"\nNotes: {result.notes}")
    print(f"Found {len(result.flights)} options:\n")
    for f in result.flights:
        airlines = "/".join(f.airlines)
        stops = "nonstop" if f.stops == 0 else f"{f.stops} stop(s)"
        print(
            f"  ${f.price_amount:>5.0f}  {airlines:<30}  "
            f"{f.departure_datetime} -> {f.arrival_datetime}  "
            f"({f.duration_minutes}min, {stops})"
        )


if __name__ == "__main__":
    asyncio.run(main())
