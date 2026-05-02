# Navio — Agentic Trip Planner

A multi-agent travel-planning app built for *Agentic AI for Analytics*. Three specialized agents — flight search, hotel search, and a RAG-grounded trip planner — exposed through a FastAPI backend and a React frontend (the **Navio** UI). A legacy Streamlit MVP is also kept around for quick CLI-style demos.

| Agent | Pattern | What it does |
|---|---|---|
| **Flight Search** | LangGraph StateGraph + MCP tool calling | City/IATA → Google Flights via Bright Data MCP → Gemini extracts a structured ranked list |
| **Hotel Search** | LangGraph StateGraph + MCP tool calling | City → Google Hotels via Bright Data MCP → Gemini extracts a structured ranked list |
| **Trip Planner (RAG)** | LangGraph `create_react_agent` + RAG + memory | Itinerary generation + chat refinement, grounded in a ChromaDB index of Wikivoyage articles, with conversation memory via `MemorySaver` |

Class concepts demonstrated end-to-end: **agent framework, tool calling, MCP, hosted models, RAG, memory, multi-agent orchestration.**

---

## Architecture overview

```
                         ┌──────────────────────────────────────┐
                         │     Navio React UI (Vite, :5173)     │
                         │   PlannerSection → Matches → Itinerary
                         └──────────────────┬───────────────────┘
                                            │ fetch() JSON
                                            ▼
                         ┌──────────────────────────────────────┐
                         │   FastAPI bridge (uvicorn, :8000)    │
                         │  CORS + lifespan warmup of all deps  │
                         └──────┬─────────────────┬─────────────┘
                                │                 │
        POST /api/search        │                 │      POST /api/trip/{itinerary,chat,new}
        (Mode A or Mode B)      │                 │
                                ▼                 ▼
        ┌────────────────────────────┐   ┌────────────────────────────┐
        │  Orchestrator: Mode A      │   │ Trip Planner (RAG agent)   │
        │  asyncio.gather(           │   │ create_react_agent + memory│
        │    flight_agent,           │   │ ChromaDB (Wikivoyage)      │
        │    hotel_agent             │   │ Vertex text-embedding-005  │
        │  ) → pair packages         │   └────────────────────────────┘
        │                            │
        │  Mode B (no destination):  │
        │  RAG.find_destinations →   │
        │  3× parallel (flight+hotel)│
        └─────┬────────────────┬─────┘
              │                │
              ▼                ▼
   ┌──────────────────┐ ┌──────────────────┐
   │  Flight agent    │ │  Hotel agent     │
   │  StateGraph (5n) │ │  StateGraph (4n) │
   │  resolve_airport │ │  build_url       │
   │  → build_url     │ │  → scrape (MCP)  │
   │  → scrape (MCP)  │ │  → extract       │
   │  → extract       │ │  → filter        │
   │  → filter        │ │                  │
   └────────┬─────────┘ └────────┬─────────┘
            │ Bright Data MCP    │ Bright Data MCP
            └─────────┬──────────┘
                      ▼
              scrape_as_markdown
              (single npx subprocess, shared singleton)
```

### Two search modes

- **Mode A — known destination.** User fills in the destination on the planner. Flight + hotel agents run in parallel for that city → 2 Bright Data scrapes → cross-product all flights × all hotels → return cheapest 3 packages with **nonstop flights preferred** over flights with stops.
- **Mode B — brainstorm.** User leaves the destination blank and only describes a vibe. The RAG agent runs `find_destinations(vibe)` first to surface 3 candidate cities, then 3× (flight + hotel) scrapes run in parallel → 6 Bright Data scrapes total → return the best package per destination.

### Itinerary + chat flow

1. User selects a package → React calls `POST /api/trip/new` to get a fresh `thread_id`, then `POST /api/trip/itinerary` to generate a day-by-day plan via the RAG agent.
2. The trip planner replies with a structured `## Day 1` / `## Day 2` markdown block which the API parses into `{ days: [{ day, activities[] }] }`.
3. User refines via the in-page chat (`POST /api/trip/chat`). The chat is **locked to the destination** (the API wraps the user's message with a context guard) and **plain-text only** (no markdown leaks into the UI).

---

## Repo layout

```
trip-planner/
├── README.md                         # ← you are here
├── requirements.txt
├── .env.example
│
├── shared.py                         # get_llm, get_scrape_tool, _normalize_mcp_text — shared by both scrape agents
│
├── agent.py                          # Flight agent: 5-node StateGraph (resolve→build_url→scrape→extract→filter)
├── google_flights.py                 # Flight URL builder
├── schemas.py                        # FormInput, FlightOption, FlightsResponse
├── tools/airports.py                 # @tool resolve_airport + METRO_AIRPORTS
├── prompts/system.md                 # Flight resolve_node system prompt
│
├── hotel_agent/
│   ├── agent.py                      # Hotel agent: 4-node StateGraph (build_url→scrape→extract→filter)
│   ├── google_hotels.py              # Hotel URL builder (Google Hotels natural-language ?q=)
│   └── schemas.py                    # HotelFormInput, HotelOption, HotelsResponse
├── prompts/hotel_extraction.md       # Hotel extraction prompt
│
├── trip_planner/
│   ├── agent.py                      # create_react_agent + MemorySaver
│   ├── corpus_build.py               # Wikivoyage fetch + cache
│   ├── chunking.py                   # parse_article, chunk_destination
│   ├── embeddings.py                 # singleton VertexAIEmbeddings (text-embedding-005)
│   ├── vectorstore.py                # singleton ChromaDB PersistentClient (cosine)
│   ├── retrieval.py                  # find_destinations, get_destination_details, fuzzy resolver
│   ├── tools.py                      # @tool wrappers exposed to the RAG agent
│   ├── schemas.py                    # DestinationHit, SectionHit, TripPlanResponse
│   └── prompts/system.md             # RAG agent system prompt
│
├── api/
│   ├── app.py                        # FastAPI app + CORS + lifespan warmup (chromadb, agents, MCP)
│   ├── schemas.py                    # API request/response models (TripSearchRequest, TravelPackage, ...)
│   └── routes/
│       ├── search.py                 # POST /api/search — Mode A + Mode B + package pairing + allFlights/allHotels
│       └── trip.py                   # POST /api/trip/{itinerary,chat,new}
│
├── frontend/                         # Navio React UI (Vite + Tailwind)
│   ├── package.json
│   └── src/app/
│       ├── App.tsx                   # Top-level state, fetch() to FastAPI, view router
│       └── components/
│           ├── Brand.tsx             # Navio logo + animated palm tree
│           ├── PlannerSection.tsx    # Initial form
│           ├── TravelResultCard.tsx  # Package card
│           ├── FullResults.tsx       # Toggle: full scraped flights/hotels grouped by destination
│           ├── ItineraryPage.tsx     # Day-by-day itinerary + destination-locked chat
│           └── Sidebar.tsx           # Sticky search-summary + nav (after first search)
│
├── streamlit_app.py                  # Legacy MVP UI (still works)
├── pages/                            # Streamlit pages (auto-discovered)
│   ├── 1_✈️_Flight_Search.py
│   └── 2_🗺️_Trip_Planner.py
├── async_runner.py                   # Streamlit-only thread-based async runner
│
├── data/
│   ├── airports.csv                  # OpenFlights IATA DB (gitignored)
│   ├── destinations.txt              # Pilot list of cities (tracked)
│   ├── chroma/                       # ChromaDB persistence (gitignored)
│   └── wikivoyage_cache/             # Raw wikitext per destination (gitignored)
│
├── scripts/
│   ├── test_mcp.py / test_scrape.py / test_embeddings.py / test_chroma.py / test_wikivoyage.py
│   ├── build_corpus.py               # Ingest pipeline: --limit N, --parse-only, --reembed-all
│   ├── inspect_corpus.py             # Retrieval REPL
│   ├── run_agent.py                  # Flight agent CLI smoke test
│   ├── run_hotel_agent.py            # Hotel agent CLI smoke test
│   └── run_trip_planner.py           # RAG agent CLI smoke test (3 turns; last tests memory)
│
└── tests/
    ├── test_airports.py
    ├── test_google_flights_url.py
    ├── test_google_hotels_url.py
    ├── test_chunking.py
    ├── test_extraction.py            # @integration (Vertex)
    └── test_retrieval.py             # @integration (Vertex + Chroma)
```

---

## Prerequisites

- **Python 3.11+** (developed on 3.13)
- **Node.js 18+** — Bright Data MCP server runs as an `npx` subprocess; the React frontend uses npm
- **Bright Data account** with a token. Free tier (5,000 requests/month) is enough for development. Both flight and hotel agents share one MCP subprocess, so a single search costs ~2 requests (Mode A) or ~6 requests (Mode B).
- **GCP project** with Vertex AI enabled
- **gcloud CLI** with Application Default Credentials: `gcloud auth application-default login` and `gcloud services enable aiplatform.googleapis.com --project=YOUR_PROJECT`

---

## Quick start

```bash
cd trip-planner

# 1. Python venv + deps (~3 min)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Environment
cp .env.example .env
# Edit .env: BRIGHTDATA_API_TOKEN, GCP_PROJECT_ID, GCP_REGION, GEMINI_MODEL

# 3. OpenFlights airport DB (~1 MB, gitignored)
mkdir -p data
curl -L -o data/airports.csv \
  https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat

# 4. Phase 0 sanity checks
python scripts/test_mcp.py          # MCP tools list — must include scrape_as_markdown
python scripts/test_embeddings.py   # Vertex embed: 768-dim vector
python scripts/test_chroma.py       # Chroma round-trip
python scripts/test_wikivoyage.py   # Lisbon article: ≥6 sections

# 5. RAG corpus — ingest the pilot destinations (~5 min, idempotent)
python scripts/build_corpus.py
```

### Run the full app (FastAPI + React)

Open two terminals.

**Terminal 1 — backend:**
```bash
cd trip-planner
source .venv/bin/activate
python -m uvicorn api.app:app --reload --port 8000
```

You should see:
```
[api] chromadb + trip planner agent warmed up
[api] MCP subprocess + flight/hotel agents warmed up
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**Terminal 2 — frontend:**
```bash
cd trip-planner/frontend
npm install   # first time only
npm run dev
```

Open the Vite URL it prints (usually `http://localhost:5173`). The CORS config in `api/app.py` already allows `localhost:5173` and `localhost:3000`.

### Or run the legacy Streamlit MVP

```bash
streamlit run streamlit_app.py
```

---

## API reference

### `POST /api/search` — combined flight + hotel search

```json
// Request — Mode A (known destination)
{
  "departure": "New York",
  "destination": "Lisbon",
  "startDate": "2026-07-01",
  "endDate": "2026-07-08",
  "travelerCount": 2,
  "chatMessage": "summer trip with sightseeing and nightlife"
}

// Request — Mode B (brainstorm: leave destination blank)
{
  "departure": "New York",
  "destination": "",
  "startDate": "2026-07-01",
  "endDate": "2026-07-08",
  "travelerCount": 2,
  "chatMessage": "relaxed beach vacation in Southeast Asia"
}

// Response
{
  "packages": [
    {
      "destination": "Lisbon",
      "flightInfo": { "airline": "TAP", "departure": "JFK", "arrival": "LIS", "duration": "8h 5m", "price": 612, "stops": 0 },
      "hotelInfo": { "name": "Hotel ...", "rating": 4.4, "location": "Baixa", "amenities": ["WiFi","Breakfast"], "pricePerNight": 110 },
      "totalPrice": 1382
    }
  ],
  "allFlights": [],
  "allHotels":  [],
  "notes": "Found 7 flights and 10 hotels for Lisbon."
}
```

Packages are picked with a **tiered preference**: nonstop flights first (cheapest within tier), only falling through to 1-stop / 2-stop options if no nonstops exist. The `allFlights` / `allHotels` lists hold every scraped option (sorted, tagged with destination) so the UI's "Show all scraped flights and hotels" toggle can render them grouped.

### `POST /api/trip/new` — start a new chat thread

Returns `{ "thread_id": "<uuid>" }`. The frontend persists this for the duration of the itinerary view and sends it with every chat / itinerary request.

### `POST /api/trip/itinerary` — generate the day-by-day plan

```json
{
  "destination": "Lisbon",
  "num_days": 5,
  "vibe": "summer trip with sightseeing and nightlife",
  "thread_id": "<uuid>"
}

// Response
{
  "days": [
    { "day": 1, "activities": ["Visit Castelo de São Jorge", "..."] },
    { "day": 2, "activities": [] }
  ],
  "thread_id": "<uuid>"
}
```

### `POST /api/trip/chat` — refine the itinerary

```json
{
  "message": "Can you add more beach time on day 3?",
  "thread_id": "<uuid>",
  "destination": "Lisbon"
}

// Response
{
  "reply": "Plain-text reply, 2-4 sentences, no markdown.",
  "thread_id": "<uuid>",
  "updated_itinerary": null
}
```

The chat handler **wraps the user's message with a destination guard** so the RAG agent stays focused on the selected city (no drifting into other cities), and **strips any markdown** that leaks through into the reply.

---

## Testing

```bash
# Fast unit tests only (~3s)
pytest -m "not integration"

# Everything, including Vertex- and Chroma-touching tests (~4 min)
pytest

# Just one file
pytest tests/test_chunking.py -v

# CLI smoke tests
python scripts/run_agent.py            # Flight agent
python scripts/run_hotel_agent.py      # Hotel agent
python scripts/run_trip_planner.py     # RAG agent (3 turns)
```

---

## Roadmap

1. **Scale the corpus** from ~30 to ~300 destinations. `build_corpus.py` is idempotent — only embeds new chunks.
2. **Streaming responses** in the chat (`agent.astream_events` instead of `ainvoke`).
3. **Persistent chat memory** — swap `MemorySaver` for `SqliteSaver` so chat history survives FastAPI restarts.
4. **Migrate `ChatVertexAI` → `ChatGoogleGenerativeAI`** (deprecated, currently emits warnings).
5. **Hotel agent improvements** — pull amenities and exact rating from a dedicated Bright Data Web Data API endpoint instead of scrape-and-extract, once the customer's account is activated.
6. **Multi-agent orchestrator** — top-level agent that does intent classification (search vs. chat vs. brainstorm) and routes to the appropriate sub-agent. Currently this routing lives in the FastAPI route handlers.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Could not connect to tenant default_tenant` | ChromaDB connection wasn't established before a concurrent request hit the agent. | Already fixed — `lifespan()` in `api/app.py` warms up ChromaDB and the trip planner agent before the MCP subprocess. Restart uvicorn (lifespan only runs on full boot, not on `--reload`). |
| Hotel scrape returns 31 chars / "Possible CAPTCHA" | The path-based `/travel/hotels/{city}` URL returns a stub. | Already fixed — `build_google_hotels_url` uses the natural-language `?q=Hotels in {city} from {date} to {date}` form, mirroring Google Flights. |
| Hotels show up as US chains for a Lisbon search | Gemini hallucinating from generic prompt. | Already fixed — `prompts/hotel_extraction.md` strictly forbids using anything not verbatim in the markdown and drops obviously-wrong city names. |
| Frontend shows wrong destination on itinerary page | `selectedPackage.hotelInfo.location` is the neighborhood, not the city. | Already fixed — packages carry an explicit `destination` field stamped by the API. |
| Chat replies with bullet points / `**bold**` / headings | RAG agent's default style is markdown. | Already fixed — `/api/trip/chat` wraps the user message with a plain-text style instruction and strips residual markdown server-side before responding. |
| Chat drifts to other cities | Agent's MemorySaver retains broad context. | Already fixed — chat handler injects `[Context: stay focused on {destination}]` into every user turn, and the frontend sends `destination` with each message. |
| `npx @brightdata/mcp` hangs on first call | First-run package download. | Pre-install: `npm install -g @brightdata/mcp`. |
| Trip Planner replies "I don't have information about X" | Destination isn't in the corpus. | Add it to `data/destinations.txt` and re-run `python scripts/build_corpus.py` (idempotent). |
| `aiplatform.googleapis.com` 403 | API not enabled on the GCP project. | `gcloud services enable aiplatform.googleapis.com --project=$GCP_PROJECT_ID` |
| `data/airports.csv` not found in worktree | Working in a git worktree where the gitignored data dir wasn't copied. | Symlink: `ln -s ../../../data/airports.csv data/airports.csv` (and similarly for `data/chroma`, `data/wikivoyage_cache`). |
