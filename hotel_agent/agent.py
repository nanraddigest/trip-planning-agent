"""Hotel search agent: 4-node LangGraph StateGraph + Bright Data MCP + Vertex AI Gemini."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, StateGraph

from hotel_agent.google_hotels import build_google_hotels_url
from hotel_agent.schemas import HotelOption, HotelsResponse, HotelFormInput
from shared import _normalize_mcp_text, get_llm, get_scrape_tool

PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"

EXTRACTION_PROMPT = (PROMPT_DIR / "hotel_extraction.md").read_text()


class HotelAgentState(TypedDict, total=False):
    form: HotelFormInput
    url: str
    markdown: str
    response: HotelsResponse
    final: HotelsResponse


def _log(name: str, inputs: dict, output_summary: str) -> None:
    inp = json.dumps(inputs, default=str)
    if len(inp) > 200:
        inp = inp[:200] + "..."
    print(f"[hotel:{name}] input={inp} -> {output_summary}")


def build_url_node(state: HotelAgentState) -> dict:
    form = state["form"]
    url = build_google_hotels_url(
        form.destination,
        form.check_in_date,
        form.check_out_date,
        form.guests,
    )
    print(f"[hotel:build_url] {url}")
    return {"url": url}


async def scrape_node(state: HotelAgentState) -> dict:
    scrape = await get_scrape_tool()
    last_len = 0
    for attempt in (1, 2):
        raw = await scrape.ainvoke({"url": state["url"]})
        markdown = _normalize_mcp_text(raw)
        _log("scrape", {"url": state["url"], "attempt": attempt}, f"{len(markdown)} chars")
        last_len = len(markdown)
        if len(markdown) >= 3_000 and "verify you are human" not in markdown.lower():
            return {"markdown": markdown}
        if attempt == 1:
            print(f"[hotel:scrape] flake on attempt 1 ({last_len} chars), retrying in 1.5s...")
            await asyncio.sleep(1.5)
    raise ValueError(
        f"hotel scrape returned suspiciously little content after 2 "
        f"attempts (last={last_len} chars). Possible CAPTCHA."
    )


async def extract_node(state: HotelAgentState) -> dict:
    form = state["form"]
    llm = get_llm().with_structured_output(HotelsResponse)
    prompt = EXTRACTION_PROMPT.format(
        destination=form.destination,
        check_in_date=form.check_in_date.isoformat(),
        check_out_date=form.check_out_date.isoformat(),
        guests=form.guests,
        markdown=state["markdown"][:100_000],
    )
    response = await llm.ainvoke(prompt)
    print(
        f"[hotel:extract] structured -> {len(response.hotels)} options, "
        f"notes={response.notes!r}"
    )
    for h in response.hotels[:5]:
        print(f"    - {h.name} ${h.price_per_night}/night")
    return {"response": response}


def filter_node(state: HotelAgentState) -> dict:
    form = state["form"]
    response: HotelsResponse = state["response"]

    keep: list[HotelOption] = []
    for h in response.hotels:
        if h.price_per_night <= 0:
            continue
        if form.min_price is not None and h.price_per_night < form.min_price:
            continue
        if form.max_price is not None and h.price_per_night > form.max_price:
            continue
        if form.min_rating is not None and (h.rating or 0) < form.min_rating:
            continue
        if form.hotel_class is not None and (h.hotel_class or 0) < form.hotel_class:
            continue
        keep.append(h)

    if form.sort_by == "price":
        keep.sort(key=lambda h: h.price_per_night)
    elif form.sort_by == "rating":
        keep.sort(key=lambda h: -(h.rating or 0))

    final = HotelsResponse(hotels=keep[:10], notes=response.notes)
    print(f"[hotel:filter] {len(response.hotels)} -> {len(final.hotels)} after filters")
    return {"final": final}


def build_hotel_agent():
    g = StateGraph(HotelAgentState)
    g.add_node("build_url", build_url_node)
    g.add_node("scrape", scrape_node)
    g.add_node("extract", extract_node)
    g.add_node("filter", filter_node)
    g.set_entry_point("build_url")
    g.add_edge("build_url", "scrape")
    g.add_edge("scrape", "extract")
    g.add_edge("extract", "filter")
    g.add_edge("filter", END)
    return g.compile()


_compiled = None


def get_hotel_agent():
    global _compiled
    if _compiled is None:
        _compiled = build_hotel_agent()
    return _compiled


async def run_hotel_search(form: HotelFormInput) -> HotelsResponse:
    agent = get_hotel_agent()
    out = await agent.ainvoke({"form": form})
    return out["final"]
