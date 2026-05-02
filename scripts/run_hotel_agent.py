"""CLI smoke test for the hotel search agent."""
import asyncio
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hotel_agent.agent import run_hotel_search
from hotel_agent.schemas import HotelFormInput


async def main():
    form = HotelFormInput(
        destination="Lisbon",
        check_in_date=date.today() + timedelta(days=60),
        check_out_date=date.today() + timedelta(days=65),
        guests=2,
    )
    result = await run_hotel_search(form)
    print(f"\n{result.notes}")
    for h in result.hotels:
        stars = f" {'★' * h.hotel_class}" if h.hotel_class else ""
        rating = f" ({h.rating}/5)" if h.rating else ""
        amenities = ", ".join(h.amenities[:4]) if h.amenities else ""
        print(
            f"  ${h.price_per_night:.0f}/night{stars}{rating}  "
            f"{h.name}  [{amenities}]"
        )


if __name__ == "__main__":
    asyncio.run(main())
