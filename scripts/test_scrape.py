"""Phase 0 — verify scrape_as_markdown returns usable Google Flights data."""
import asyncio
import os

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

# A known-good Google Flights URL: JFK → LIS, ~110 days out from 2026-04-28
TEST_URL = "https://www.google.com/travel/flights?q=Flights%20from%20JFK%20to%20LIS%20on%202026-08-15"


async def main():
    client = MultiServerMCPClient({
        "brightdata": {
            "command": "npx",
            "args": ["@brightdata/mcp"],
            "transport": "stdio",
            "env": {"API_TOKEN": os.environ["BRIGHTDATA_API_TOKEN"]},
        }
    })
    tools = await client.get_tools()
    scrape = next(t for t in tools if t.name == "scrape_as_markdown")

    result = await scrape.ainvoke({"url": TEST_URL})

    # langchain-mcp-adapters >= 0.2 may return either a str or a list of MCP
    # content blocks (e.g. [{"type": "text", "text": "..."}] or text objects).
    if isinstance(result, str):
        text = result
    elif isinstance(result, list):
        parts = []
        for block in result:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                parts.append(block.get("text", ""))
            else:
                parts.append(getattr(block, "text", "") or str(block))
        text = "\n".join(p for p in parts if p)
    else:
        text = str(result)

    print(f"Scraped {len(text)} characters (raw type: {type(result).__name__})")

    out_path = "scripts/sample_markdown.md"
    with open(out_path, "w") as f:
        f.write(text)
    print(f"Saved to {out_path}")
    print("\n--- First 2000 chars ---")
    print(text[:2000])


if __name__ == "__main__":
    asyncio.run(main())
