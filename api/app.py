"""FastAPI application — bridges the Python agent backend to the React frontend."""
from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    from shared import get_scrape_tool
    from agent import get_agent
    from hotel_agent.agent import get_hotel_agent
    from trip_planner.retrieval import _all_destination_names
    from api.routes.trip import _get_agent as _get_trip_agent

    # Warm up the chromadb client + RAG agent FIRST so the connection is
    # established before any concurrent request attempts to touch it.
    _all_destination_names()
    _get_trip_agent()
    print("[api] chromadb + trip planner agent warmed up")

    await get_scrape_tool()
    get_agent()
    get_hotel_agent()
    print("[api] MCP subprocess + flight/hotel agents warmed up")
    yield


app = FastAPI(title="Trip Planner API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from api.routes import search, trip  # noqa: E402

app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(trip.router, prefix="/api/trip", tags=["trip-planner"])


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Static frontend (production single-service deploy)
# ---------------------------------------------------------------------------
# Mounted AFTER the /api routers so API routes still take precedence. The
# guard means local dev (no `npm run build` yet) skips this entirely and the
# Vite dev server on :5173 talks to the API on :8000 via CORS instead.
if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount(
            "/assets",
            StaticFiles(directory=assets_dir),
            name="assets",
        )

    @app.get("/")
    async def index():
        return FileResponse(FRONTEND_DIST / "index.html")

    @app.get("/{path:path}")
    async def spa_fallback(path: str):
        # API routes are already registered above; this only fires for SPA
        # client-side routes and static files like favicon.ico.
        candidate = FRONTEND_DIST / path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
