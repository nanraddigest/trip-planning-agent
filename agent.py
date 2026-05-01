"""Flight search agent: LangGraph topology + Bright Data MCP + Vertex AI Gemini."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Optional, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_vertexai import ChatVertexAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import END, StateGraph

from google_flights import build_google_flights_url
from schemas import FlightOption, FlightsResponse, FormInput
from tools.airports import resolve_airport

load_dotenv()

PROMPT_DIR = Path(__file__).parent / "prompts"


# ---------------------------------------------------------------------------
# Shared utilities
# ---------------------------------------------------------------------------

def get_llm(temperature: float = 0) -> ChatVertexAI:
    return ChatVertexAI(
        model_name=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
        project=os.environ["GCP_PROJECT_ID"],
        location=os.environ.get("GCP_REGION", "us-central1"),
        temperature=temperature,
    )


def _normalize_mcp_text(result) -> str:
    """Coerce an MCP tool result into a single string.

    langchain-mcp-adapters >= 0.2 may return either a str or a list of MCP
    content blocks (dicts with 'text', or objects with a .text attribute).
    """
    if isinstance(result, str):
        return result
    if isinstance(result, list):
        parts = []
        for block in result:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                parts.append(block.get("text", ""))
            else:
                parts.append(getattr(block, "text", "") or str(block))
        return "\n".join(p for p in parts if p)
    return str(result)


# ---------------------------------------------------------------------------
# MCP client (process-singleton)
# ---------------------------------------------------------------------------

_scrape_tool = None


async def get_scrape_tool():
    global _scrape_tool
    if _scrape_tool is None:
        client = MultiServerMCPClient({
            "brightdata": {
                "command": "npx",
                "args": ["@brightdata/mcp"],
                "transport": "stdio",
                "env": {"API_TOKEN": os.environ["BRIGHTDATA_API_TOKEN"]},
            }
        })
        tools = await client.get_tools()
        _scrape_tool = next(t for t in tools if t.name == "scrape_as_markdown")
    return _scrape_tool


# ---------------------------------------------------------------------------
# Phase 3: extraction
# ---------------------------------------------------------------------------

EXTRACTION_PROMPT = """You are extracting flight data from a Google Flights page that has been scraped to markdown.

User's search:
- Origin airport(s): {origin}
- Destination airport(s): {destination}
- Departure date: {departure_date}
- Return date: {return_date}
- Cabin class: {cabin_class}

Scraped markdown follows. Extract every distinct flight option you can identify.

Rules:
- Do NOT fabricate any field. If a field is not clearly present, set it to null (where allowed).
- duration_minutes must be a total integer in minutes (e.g., "8h 25m" -> 505, "11 hr 50 min" -> 710).
- price_amount is the numeric price; strip currency symbols. Use the user-displayed price, not "from" estimates if both appear.
- stops = 0 means nonstop. layover_airports lists the IATA codes of any intermediate airports.
- Return up to 15 options. Drop any whose origin/destination don't match the user's search.
- The notes field should be one short sentence describing what you found.

--- MARKDOWN ---
{markdown}
"""


async def extract_flights(
    markdown: str,
    form: FormInput,
    origin_iatas: list[str],
    dest_iatas: list[str],
) -> FlightsResponse:
    llm = get_llm().with_structured_output(FlightsResponse)
    prompt = EXTRACTION_PROMPT.format(
        origin=", ".join(origin_iatas),
        destination=", ".join(dest_iatas),
        departure_date=form.departure_date.isoformat(),
        return_date=form.return_date.isoformat() if form.return_date else "(one-way)",
        cabin_class=form.cabin_class,
        markdown=markdown[:100_000],
    )
    return await llm.ainvoke(prompt)


# ---------------------------------------------------------------------------
# Phase 4: LangGraph topology
# ---------------------------------------------------------------------------

class AgentState(TypedDict, total=False):
    form: FormInput
    origin_iatas: list[str]
    dest_iatas: list[str]
    url: str
    markdown: str
    response: FlightsResponse
    final: FlightsResponse
    narration: str


def _log_tool_call(name: str, inputs: dict, output_summary: str) -> None:
    inp = json.dumps(inputs, default=str)
    if len(inp) > 200:
        inp = inp[:200] + "..."
    print(f"[{name}] input={inp} -> {output_summary}")


_JSON_RE = re.compile(r"\{[^{}]*\"origin_iatas\".*?\}", re.DOTALL)


async def resolve_node(state: AgentState) -> dict:
    """LLM with the resolve_airport tool. Looped until the LLM emits final JSON."""
    form = state["form"]
    system_text = (PROMPT_DIR / "system.md").read_text()
    llm = get_llm().bind_tools([resolve_airport])

    messages = [
        SystemMessage(system_text),
        HumanMessage(
            f"Resolve airport codes. Origin: {form.origin!r}. Destination: {form.destination!r}."
        ),
    ]

    for _ in range(5):
        ai = await llm.ainvoke(messages)
        messages.append(ai)
        if not ai.tool_calls:
            break
        for tc in ai.tool_calls:
            tool_msg = await resolve_airport.ainvoke(tc)
            _log_tool_call(
                "resolve_airport",
                tc["args"],
                f"{len(json.loads(tool_msg.content) if isinstance(tool_msg.content, str) else tool_msg.content)} match(es)",
            )
            messages.append(tool_msg)

    # Gemini 2.5 may return content as a list of {type, text, thought_signature}
    # blocks when "thinking" is engaged. AIMessage.text concatenates the text
    # parts for us regardless of the underlying shape.
    text = str(ai.text)
    m = _JSON_RE.search(text)
    if not m:
        # Last-ditch: try to parse the whole content
        m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise ValueError(f"resolve_node: LLM did not return JSON. Got: {text[:500]}")

    parsed = json.loads(m.group(0))
    origin_iatas = [c.upper() for c in parsed.get("origin_iatas", [])]
    dest_iatas = [c.upper() for c in parsed.get("destination_iatas", [])]

    if not origin_iatas or not dest_iatas:
        raise ValueError(
            f"resolve_node: empty IATA list. origin={origin_iatas} dest={dest_iatas}"
        )

    return {
        "origin_iatas": origin_iatas,
        "dest_iatas": dest_iatas,
        "narration": parsed.get("narration", ""),
    }


def build_url_node(state: AgentState) -> dict:
    # Google Flights' q= parameter doesn't parse comma-separated multi-airport
    # origins/destinations — passing them returns the generic landing page
    # instead of search results. Use the first (primary hub) on each side.
    primary_origin = state["origin_iatas"][:1]
    primary_dest = state["dest_iatas"][:1]
    url = build_google_flights_url(
        primary_origin,
        primary_dest,
        state["form"].departure_date,
        state["form"].return_date,
    )
    print(f"[build_url] {url}")
    return {"url": url}


async def scrape_node(state: AgentState) -> dict:
    scrape = await get_scrape_tool()
    raw = await scrape.ainvoke({"url": state["url"]})
    markdown = _normalize_mcp_text(raw)
    _log_tool_call(
        "scrape_as_markdown",
        {"url": state["url"]},
        f"{len(markdown)} chars",
    )
    if len(markdown) < 5_000 or "verify you are human" in markdown.lower():
        raise ValueError(
            f"scrape_node: scrape returned suspiciously little content "
            f"({len(markdown)} chars). Possible CAPTCHA. Try again."
        )
    return {"markdown": markdown}


async def extract_node(state: AgentState) -> dict:
    response = await extract_flights(
        state["markdown"],
        state["form"],
        state["origin_iatas"],
        state["dest_iatas"],
    )
    print(
        f"[extract_flights] structured -> {len(response.flights)} options, "
        f"notes={response.notes!r}"
    )
    return {"response": response}


def filter_node(state: AgentState) -> dict:
    """Apply airline / max_stops filters, drop garbage rows, sort by price, top 10."""
    form = state["form"]
    response: FlightsResponse = state["response"]

    keep: list[FlightOption] = []
    for f in response.flights:
        if f.price_amount <= 0 or f.duration_minutes <= 0:
            continue
        if form.max_stops == "Nonstop only" and f.stops != 0:
            continue
        if form.max_stops == "1 stop max" and f.stops > 1:
            continue
        if form.airlines:
            airline_blob = " ".join(f.airlines).lower()
            if not any(a.lower() in airline_blob for a in form.airlines):
                continue
        keep.append(f)

    keep.sort(key=lambda f: f.price_amount)
    final = FlightsResponse(flights=keep[:10], notes=response.notes)
    print(f"[filter] {len(response.flights)} -> {len(final.flights)} after filters")
    return {"final": final}


def build_agent():
    g = StateGraph(AgentState)
    g.add_node("resolve", resolve_node)
    g.add_node("build_url", build_url_node)
    g.add_node("scrape", scrape_node)
    g.add_node("extract", extract_node)
    g.add_node("filter", filter_node)
    g.set_entry_point("resolve")
    g.add_edge("resolve", "build_url")
    g.add_edge("build_url", "scrape")
    g.add_edge("scrape", "extract")
    g.add_edge("extract", "filter")
    g.add_edge("filter", END)
    return g.compile()


_compiled = None


def get_agent():
    global _compiled
    if _compiled is None:
        _compiled = build_agent()
    return _compiled


async def run_search(form: FormInput) -> FlightsResponse:
    agent = get_agent()
    out = await agent.ainvoke({"form": form})
    return out["final"]
