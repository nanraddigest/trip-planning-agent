"""Thread-based async runner for Streamlit pages.

Streamlit 1.57+ ships uvloop as a transitive dep, and ``nest_asyncio`` cannot
patch uvloop event loops. To run an async coroutine from a sync Streamlit
callback, dispatch to a worker thread; that thread gets a fresh stdlib asyncio
loop via ``asyncio.run`` and stays out of Streamlit's main loop entirely.
"""
from __future__ import annotations

import asyncio
import threading
from typing import Any, Awaitable


def run_async(coro: Awaitable[Any]) -> Any:
    """Block until ``coro`` finishes and return its result.

    Re-raises whatever the coroutine raised so callers see normal Python
    tracebacks.
    """
    box: dict[str, Any] = {}

    def _target() -> None:
        try:
            box["value"] = asyncio.run(coro)
        except BaseException as e:  # noqa: BLE001
            box["error"] = e

    t = threading.Thread(target=_target, daemon=True)
    t.start()
    t.join()
    if "error" in box:
        raise box["error"]
    return box["value"]
