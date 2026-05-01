"""Phase 0 standalone MCP validation. Run before any agent code exists."""
import asyncio
import os

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()


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
    print("Available MCP tools:")
    for t in tools:
        desc = (t.description or "").strip().splitlines()[0] if t.description else ""
        print(f"  - {t.name}: {desc[:80]}")


if __name__ == "__main__":
    asyncio.run(main())
