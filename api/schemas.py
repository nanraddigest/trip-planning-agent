"""API request/response schemas — shaped to match the React frontend's expectations."""
from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# /api/search
# ---------------------------------------------------------------------------

class TravelerPref(BaseModel):
    id: int
    vibe: str = ""
    flexibleDates: bool = False
    budgetFriendly: bool = False


class TripSearchRequest(BaseModel):
    departure: str
    destination: str = ""
    start_date: date = Field(alias="startDate")
    end_date: date = Field(alias="endDate")
    traveler_count: int = Field(default=1, alias="travelerCount")
    chat_message: str = Field(default="", alias="chatMessage")
    travelers: list[TravelerPref] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class PackageFlightInfo(BaseModel):
    airline: str
    departure: str
    arrival: str
    duration: str
    price: float
    stops: int


class PackageHotelInfo(BaseModel):
    name: str
    rating: float
    location: str
    amenities: list[str]
    pricePerNight: float


class TravelPackage(BaseModel):
    destination: str
    flightInfo: PackageFlightInfo
    hotelInfo: PackageHotelInfo
    totalPrice: float


class RawFlightOption(BaseModel):
    destination: str
    airline: str
    departure: str
    arrival: str
    duration: str
    price: float
    stops: int


class RawHotelOption(BaseModel):
    destination: str
    name: str
    rating: float
    location: str
    amenities: list[str]
    pricePerNight: float


class TripSearchResponse(BaseModel):
    packages: list[TravelPackage]
    allFlights: list[RawFlightOption] = []
    allHotels: list[RawHotelOption] = []
    notes: str = ""


# ---------------------------------------------------------------------------
# /api/trip
# ---------------------------------------------------------------------------

class ItineraryRequest(BaseModel):
    destination: str
    num_days: int
    vibe: str = ""
    thread_id: str


class ItineraryDay(BaseModel):
    day: int
    activities: list[str]


class ItineraryResponse(BaseModel):
    days: list[ItineraryDay]
    thread_id: str


class ChatRequest(BaseModel):
    message: str
    thread_id: str
    destination: str = ""


class ChatResponse(BaseModel):
    reply: str
    thread_id: str
    updated_itinerary: Optional[list[ItineraryDay]] = None


class NewConversationResponse(BaseModel):
    thread_id: str
