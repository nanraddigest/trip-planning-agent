"""Shared utilities used by both the flight and hotel agents."""
from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_google_vertexai import ChatVertexAI
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()


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
