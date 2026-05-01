"""LangGraph trip-planner agent with memory + RAG tools."""
from __future__ import annotations

import os
import pathlib

from langchain_google_vertexai import ChatVertexAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from trip_planner.tools import search_destination_content, search_destinations

SYSTEM_PROMPT = pathlib.Path(__file__).parent.joinpath("prompts/system.md").read_text()


def build_trip_planner_agent():
    """Build a tool-calling Gemini agent with MemorySaver checkpointer.

    Memory is keyed on the LangGraph ``thread_id`` passed in ``config``. Same
    thread_id across calls -> conversation continuity. New thread_id -> fresh
    conversation.
    """
    llm = ChatVertexAI(
        model_name=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
        project=os.environ["GCP_PROJECT_ID"],
        location=os.environ.get("GCP_REGION", "us-central1"),
        temperature=0.4,  # slight creativity for itinerary phrasing
    )
    tools = [search_destinations, search_destination_content]
    return create_react_agent(
        model=llm,
        tools=tools,
        prompt=SYSTEM_PROMPT,
        checkpointer=MemorySaver(),
    )
