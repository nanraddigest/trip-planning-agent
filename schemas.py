from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class FormInput(BaseModel):
    origin: str
    destination: str
    departure_date: date
    return_date: Optional[date] = None
    airlines: list[str] = Field(default_factory=list)  # IATA codes, optional filter
    passengers: int = 1
    cabin_class: str = "Economy"
    max_stops: str = "Any"  # "Any" | "Nonstop only" | "1 stop max"


class FlightOption(BaseModel):
    airlines: list[str] = Field(
        description="Operating carrier names, e.g. ['TAP Air Portugal']"
    )
    flight_numbers: Optional[list[str]] = Field(
        default=None, description="e.g. ['TP 204']; null if not visible"
    )
    origin_iata: str
    destination_iata: str
    departure_datetime: str = Field(
        description="ISO 8601 if timezone visible, else local time string"
    )
    arrival_datetime: str
    duration_minutes: int = Field(
        description="Total trip duration including layovers, in minutes"
    )
    stops: int = Field(description="0 for nonstop")
    layover_airports: list[str] = Field(
        default_factory=list, description="IATA codes of layover airports"
    )
    price_amount: float
    price_currency: str = "USD"
    cabin_class: str
    booking_url: Optional[str] = None


class FlightsResponse(BaseModel):
    flights: list[FlightOption]
    notes: str = Field(description="One-line narration: what was searched, any caveats")
