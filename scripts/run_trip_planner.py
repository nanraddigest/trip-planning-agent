"""Phase 4 CLI smoke test: 3 turns, last one tests memory."""
import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
load_dotenv()

from trip_planner.agent import build_trip_planner_agent  # noqa: E402


async def main():
    agent = build_trip_planner_agent()
    config = {"configurable": {"thread_id": "demo-thread-1"}}

    queries = [
        "I have 5 days in late September and want a relaxed coastal European city with great seafood. Ideas?",
        "Tell me more about Lisbon — where should I eat seafood?",
        # Memory test: no destination named, agent must infer "Lisbon" from history.
        "What about a viewpoint to watch the sunset?",
    ]
    for q in queries:
        print(f"\n>>> USER: {q}")
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": q}]},
            config=config,
        )
        # Surface tool calls so we can verify the third turn really used Lisbon.
        for msg in result["messages"]:
            if getattr(msg, "tool_calls", None):
                for tc in msg.tool_calls:
                    print(f"    [tool] {tc['name']}({tc['args']})")
        # Gemini 2.5 returns list-of-blocks content; .text joins the text parts.
        reply = str(result["messages"][-1].text)
        print(f"<<< AGENT:\n{reply}\n{'-' * 60}")


if __name__ == "__main__":
    asyncio.run(main())
