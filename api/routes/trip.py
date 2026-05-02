"""POST /api/trip/* — RAG-powered itinerary generation and chat."""
from __future__ import annotations

import re
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.schemas import (
    ChatRequest,
    ChatResponse,
    ItineraryDay,
    ItineraryRequest,
    ItineraryResponse,
    NewConversationResponse,
)
from shared import get_llm
from trip_planner.agent import build_trip_planner_agent
from trip_planner.retrieval import get_destination_details


class _ItineraryStructured(BaseModel):
    """Structured-output target for the single-shot itinerary LLM call."""
    days: list[ItineraryDay] = Field(
        description="One entry per day, in order, each with 3-4 specific activities.",
    )

router = APIRouter()

_agent = None


def _get_agent():
    global _agent
    if _agent is None:
        _agent = build_trip_planner_agent()
    return _agent


def _extract_text(message) -> str:
    """Pull plaintext from an AIMessage, handling list-of-blocks content."""
    text_attr = getattr(message, "text", None)
    if text_attr:
        return str(text_attr)
    content = getattr(message, "content", "")
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                parts.append(block.get("text", ""))
            else:
                parts.append(getattr(block, "text", "") or str(block))
        return "\n".join(p for p in parts if p)
    return str(content)


_DAY_PATTERN = re.compile(
    r"(?:^|\n)\s*(?:#+\s*|\*\*\s*)?Day\s+(\d+)\s*[:.\-)]?\s*\*{0,2}",
    re.IGNORECASE,
)
_BULLET_PATTERN = re.compile(
    r"^\s*(?:[-*•]|\d+[.)])\s+(.+)",
    re.MULTILINE,
)


def _parse_itinerary(text: str) -> list[ItineraryDay] | None:
    """Try to extract structured itinerary from the agent's markdown response."""
    # Drop trailing follow-up sections so we don't pull questions in as activities.
    for marker in ("Suggested follow-ups", "Follow-up", "Suggested questions"):
        idx = text.find(marker)
        if idx > 0:
            text = text[:idx]

    matches = list(_DAY_PATTERN.finditer(text))
    if not matches:
        return None

    days = []
    for i, match in enumerate(matches):
        day_num = int(match.group(1))
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section = text[start:end]
        activities = []
        for m in _BULLET_PATTERN.finditer(section):
            activity = re.sub(r"\*+", "", m.group(1)).strip()
            if not activity or len(activity) < 4:
                continue
            # Skip bullet points that are clearly follow-up questions.
            if activity.endswith("?"):
                continue
            activities.append(activity)
        if activities:
            days.append(ItineraryDay(day=day_num, activities=activities[:6]))

    return days if days else None


@router.post("/new", response_model=NewConversationResponse)
async def new_conversation():
    return NewConversationResponse(thread_id=str(uuid.uuid4()))


@router.post("/itinerary", response_model=ItineraryResponse)
async def generate_itinerary(req: ItineraryRequest):
    """Single-shot itinerary builder: ONE RAG retrieval + ONE Gemini call."""
    print(
        f"[itinerary] destination={req.destination!r} "
        f"vibe={req.vibe!r} days={req.num_days}"
    )

    query = req.vibe.strip() if req.vibe else "things to see, do, and eat"

    try:
        hits = get_destination_details(
            destination=req.destination,
            query=query,
            section_types=["See", "Do", "Eat", "Drink"],
            k=15,
        )
        print(f"[itinerary] RAG retrieved {len(hits)} chunks for {req.destination}")

        if not hits:
            print(f"[itinerary] {req.destination} not in corpus — using fallback")
            return ItineraryResponse(
                days=[
                    ItineraryDay(
                        day=d + 1,
                        activities=[f"Explore {req.destination}"],
                    )
                    for d in range(req.num_days)
                ],
                thread_id=req.thread_id,
            )

        context = "\n\n".join(
            f"[{h.section_type}] {h.text[:600]}" for h in hits
        )

        prompt = (
            f"Build a {req.num_days}-day itinerary for {req.destination}.\n"
            f"Traveler's vibe: {req.vibe or '(no specific vibe)'}\n\n"
            f"Use ONLY the content below as your knowledge base — do not "
            f"invent places that aren't mentioned. Pick activities that match "
            f"the traveler's vibe. Output exactly {req.num_days} days, with "
            f"3-4 activities per day. Each activity should be a specific "
            f"place or experience plus a short context sentence.\n\n"
            f"--- WIKIVOYAGE CONTENT ---\n{context}"
        )

        llm = get_llm(temperature=0.4).with_structured_output(_ItineraryStructured)
        structured = await llm.ainvoke(prompt)
        print(f"[itinerary] generated {len(structured.days)} days")

        return ItineraryResponse(days=structured.days, thread_id=req.thread_id)

    except Exception as e:
        print(f"[itinerary] FAILED: {e}")
        raise HTTPException(500, f"Itinerary generation failed: {e}")


def _strip_markdown(text: str) -> str:
    """Best-effort stripping of common markdown so the chat reply renders cleanly."""
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        # Drop heading-only lines and horizontal rules
        if stripped.startswith("#") or stripped in ("---", "***"):
            continue
        # Strip bullet/numbered list markers at the start of a line
        line = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s+", "", line)
        lines.append(line)
    text = "\n".join(lines)
    # Remove inline emphasis markers (** __ * _ `)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"_([^_]+)_", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    # Markdown links [label](url) → label
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Collapse runs of blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    agent = _get_agent()
    config = {"configurable": {"thread_id": req.thread_id}}

    if req.destination:
        wrapped = (
            f"[Context: This conversation is strictly about the user's trip to "
            f"{req.destination}. Do NOT recommend or mention any other city. "
            f"If the user asks about beaches, food, neighborhoods, etc., your "
            f"answer must be about {req.destination} specifically — use the "
            f"search_destination_content tool with destination='{req.destination}'.]\n\n"
            f"[Style: Reply in plain text only. No markdown, no headers, no "
            f"bullet points, no asterisks, no numbered lists. Keep your reply "
            f"to 2-4 short sentences.]\n\n"
            f"User: {req.message}"
        )
    else:
        wrapped = (
            f"[Style: Reply in plain text only. No markdown, no headers, no "
            f"bullet points. Keep your reply to 2-4 short sentences.]\n\n"
            f"User: {req.message}"
        )

    try:
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": wrapped}]},
            config=config,
        )
        raw_reply = _extract_text(result["messages"][-1])
        reply_text = _strip_markdown(raw_reply)
        updated = _parse_itinerary(raw_reply)

        return ChatResponse(
            reply=reply_text,
            thread_id=req.thread_id,
            updated_itinerary=updated,
        )

    except Exception as e:
        raise HTTPException(500, f"Chat failed: {e}")
