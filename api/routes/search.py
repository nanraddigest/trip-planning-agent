"""POST /api/search — combined flight + hotel search with package pairing."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException

from agent import run_search
from api.schemas import (
    PackageFlightInfo,
    PackageHotelInfo,
    RawFlightOption,
    RawHotelOption,
    TravelPackage,
    TripSearchRequest,
    TripSearchResponse,
)
from hotel_agent.agent import run_hotel_search
from hotel_agent.schemas import HotelFormInput, HotelsResponse
from schemas import FlightsResponse, FormInput
from trip_planner.retrieval import find_destinations

router = APIRouter()


def _format_duration(minutes: int) -> str:
    h, m = divmod(minutes, 60)
    return f"{h}h {m}m"


def _pair_packages(
    flights: FlightsResponse,
    hotels: HotelsResponse,
    num_nights: int,
    destination: str,
) -> list[TravelPackage]:
    """Cross-product all flights × all hotels, return cheapest 3 with nonstop preference."""
    packages = []
    for f in flights.flights:
        for h in hotels.hotels:
            total = f.price_amount + (h.price_per_night * num_nights)
            packages.append(TravelPackage(
                destination=destination,
                flightInfo=PackageFlightInfo(
                    airline=" / ".join(f.airlines),
                    departure=f.origin_iata,
                    arrival=f.destination_iata,
                    duration=_format_duration(f.duration_minutes),
                    price=f.price_amount,
                    stops=f.stops,
                ),
                hotelInfo=PackageHotelInfo(
                    name=h.name,
                    rating=h.rating or 0.0,
                    location=h.address or h.name,
                    amenities=h.amenities[:6],
                    pricePerNight=h.price_per_night,
                ),
                totalPrice=round(total, 2),
            ))
    # Tiered sort: nonstops first, then cheapest within each stop tier.
    packages.sort(key=lambda p: (p.flightInfo.stops, p.totalPrice))
    return packages[:3]


def _to_raw_flights(flights: FlightsResponse, destination: str) -> list[RawFlightOption]:
    return [
        RawFlightOption(
            destination=destination,
            airline=" / ".join(f.airlines),
            departure=f.origin_iata,
            arrival=f.destination_iata,
            duration=_format_duration(f.duration_minutes),
            price=f.price_amount,
            stops=f.stops,
        )
        for f in flights.flights
    ]


def _to_raw_hotels(hotels: HotelsResponse, destination: str) -> list[RawHotelOption]:
    return [
        RawHotelOption(
            destination=destination,
            name=h.name,
            rating=h.rating or 0.0,
            location=h.address or h.name,
            amenities=h.amenities[:6],
            pricePerNight=h.price_per_night,
        )
        for h in hotels.hotels
    ]


@router.post("", response_model=TripSearchResponse)
async def combined_search(req: TripSearchRequest):
    num_nights = (req.end_date - req.start_date).days
    if num_nights <= 0:
        raise HTTPException(400, "end_date must be after start_date")

    try:
        if req.destination.strip():
            # MODE A — known destination: 2 Bright Data calls
            flight_form = FormInput(
                origin=req.departure,
                destination=req.destination,
                departure_date=req.start_date,
                return_date=req.end_date,
            )
            hotel_form = HotelFormInput(
                destination=req.destination,
                check_in_date=req.start_date,
                check_out_date=req.end_date,
                guests=req.traveler_count,
            )
            flight_result, hotel_result = await asyncio.gather(
                run_search(flight_form),
                run_hotel_search(hotel_form),
            )
            packages = _pair_packages(
                flight_result, hotel_result, num_nights, req.destination,
            )
            all_flights = _to_raw_flights(flight_result, req.destination)
            all_hotels = _to_raw_hotels(hotel_result, req.destination)
            notes = (
                f"Found {len(flight_result.flights)} flights and "
                f"{len(hotel_result.hotels)} hotels for {req.destination}."
            )
        else:
            # MODE B — brainstorm: RAG first, then 6 Bright Data calls
            if not req.chat_message.strip():
                raise HTTPException(
                    400,
                    "Either destination or chatMessage is required.",
                )
            destinations = find_destinations(req.chat_message, k=3)
            if not destinations:
                return TripSearchResponse(
                    packages=[],
                    notes="No matching destinations found for your description.",
                )

            async def _search_one(dest_name: str):
                flight_form = FormInput(
                    origin=req.departure,
                    destination=dest_name,
                    departure_date=req.start_date,
                    return_date=req.end_date,
                )
                hotel_form = HotelFormInput(
                    destination=dest_name,
                    check_in_date=req.start_date,
                    check_out_date=req.end_date,
                    guests=req.traveler_count,
                )
                fr, hr = await asyncio.gather(
                    run_search(flight_form),
                    run_hotel_search(hotel_form),
                )
                pkgs = _pair_packages(fr, hr, num_nights, dest_name)
                return {
                    "package": pkgs[0] if pkgs else None,
                    "flights": _to_raw_flights(fr, dest_name),
                    "hotels": _to_raw_hotels(hr, dest_name),
                }

            results = await asyncio.gather(
                *[_search_one(d.name) for d in destinations]
            )
            packages = [r["package"] for r in results if r["package"] is not None]
            all_flights = [f for r in results for f in r["flights"]]
            all_hotels = [h for r in results for h in r["hotels"]]
            dest_names = ", ".join(d.name for d in destinations)
            notes = f"Brainstorm results for: {dest_names}"

        all_flights.sort(key=lambda f: (f.stops, f.price))
        all_hotels.sort(key=lambda h: h.pricePerNight)

        return TripSearchResponse(
            packages=packages,
            allFlights=all_flights,
            allHotels=all_hotels,
            notes=notes,
        )

    except HTTPException:
        raise
    except ValueError as e:
        msg = str(e)
        if "suspiciously little content" in msg or "CAPTCHA" in msg.upper():
            print(f"[search] scrape flake after retries — surfacing friendly error: {msg}")
            return TripSearchResponse(
                packages=[],
                allFlights=[],
                allHotels=[],
                notes=(
                    "We hit a temporary scraping hiccup (likely a CAPTCHA from "
                    "the upstream travel site). Please try the search again — "
                    "this almost always resolves on the next attempt."
                ),
            )
        raise HTTPException(500, f"Search failed: {e}")
    except Exception as e:
        raise HTTPException(500, f"Search failed: {e}")
