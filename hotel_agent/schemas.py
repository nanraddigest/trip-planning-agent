from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class HotelFormInput(BaseModel):
    destination: str
    check_in_date: date
    check_out_date: date
    guests: int = 2
    rooms: int = 1
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    min_rating: Optional[float] = None
    hotel_class: Optional[int] = None
    sort_by: str = "relevance"


class HotelOption(BaseModel):
    name: str
    address: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    price_per_night: float
    price_currency: str = "USD"
    total_price: Optional[float] = None
    amenities: list[str] = Field(default_factory=list)
    hotel_class: Optional[int] = None
    image_url: Optional[str] = None
    booking_url: Optional[str] = None
    check_in_date: str
    check_out_date: str
    cancellation_policy: Optional[str] = None


class HotelsResponse(BaseModel):
    hotels: list[HotelOption]
    notes: str = Field(description="One-line narration: what was searched, any caveats")
