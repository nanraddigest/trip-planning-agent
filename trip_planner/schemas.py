from typing import Optional

from pydantic import BaseModel, Field


class DestinationHit(BaseModel):
    name: str
    summary: str
    similarity: float


class SectionHit(BaseModel):
    destination: str
    section_type: str
    text: str
    similarity: float


class TripPlanResponse(BaseModel):
    """Agent's final structured response (used for the chat reply)."""
    answer: str = Field(description="Markdown-formatted answer to the user")
    suggested_followups: list[str] = Field(
        default_factory=list,
        description="2-3 short follow-up prompts the user might want to ask",
    )
