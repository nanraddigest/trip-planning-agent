# Navio — Agentic Trip Planner

Navio is a multi-agent travel-planning application that combines real-time web scraping with retrieval-augmented generation. Three specialized agents — a flight search agent, a hotel search agent, and a RAG-grounded trip planner — sit behind a FastAPI orchestrator and a React frontend, letting the user describe a trip in natural language and receive curated flight + hotel packages with a day-by-day itinerary tailored to their vibe.

---

## Class concepts → implementation

| Class concept | Where it lives in Navio | How it's implemented |
|---|---|---|
| **Agent framework** | LangGraph throughout | `StateGraph` for the deterministic flight/hotel pipelines ([agent.py](agent.py), [hotel_agent/agent.py](hotel_agent/agent.py)). `create_react_agent` for the conversational RAG agent ([trip_planner/agent.py](trip_planner/agent.py)). Both use the same `langgraph` runtime. |
| **Tool calling** | LLMs choose and invoke `@tool`-decorated functions | `resolve_airport` in [tools/airports.py](tools/airports.py) is bound to the flight agent's `resolve_node` via `llm.bind_tools(...)`. `search_destinations` and `search_destination_content` in [trip_planner/tools.py](trip_planner/tools.py) are exposed to the chat agent's ReAct loop. The MCP `scrape_as_markdown` tool is invoked from the `scrape_node` of both scraping agents. |
| **MCP** | Bright Data scrape MCP server | A single `npx @brightdata/mcp` subprocess is launched via `MultiServerMCPClient` in [shared.py](shared.py)`get_scrape_tool()`, communicating over stdio. The returned `scrape_as_markdown` tool is reused by both the flight and hotel `scrape_node`s — one MCP connection serves the whole process. |
| **RAG** | ChromaDB over Wikivoyage articles | [data/destinations.txt](data/destinations.txt) lists the indexed cities. [trip_planner/corpus_build.py](trip_planner/corpus_build.py) fetches Wikivoyage wikitext, [trip_planner/chunking.py](trip_planner/chunking.py) splits sections, [trip_planner/embeddings.py](trip_planner/embeddings.py) embeds via Vertex, [trip_planner/vectorstore.py](trip_planner/vectorstore.py) persists in ChromaDB (cosine, two collections). [trip_planner/retrieval.py](trip_planner/retrieval.py)`get_destination_details` is the read path used by both the chat agent's `search_destination_content` tool and the single-shot itinerary endpoint. |
| **Multi-agent orchestration** | FastAPI route runs three agents in coordination | `POST /api/search` in [api/routes/search.py](api/routes/search.py): in Mode A, `asyncio.gather(run_search(flight), run_hotel_search(hotel))` runs the flight and hotel agents concurrently and the orchestrator merges their outputs into packages. In Mode B, the RAG agent's `find_destinations()` runs first to pick 3 cities, then 3 × (flight, hotel) pairs run in parallel. The FastAPI `lifespan` in [a
---

## Quick start

### Prerequisites

- Python 3.11+
- Node.js 18+ (the Bright Data MCP server runs as an `npx` subprocess; the React frontend uses `npm`)
- A Bright Data account with an API token
- A GCP project with Vertex AI enabled, plus `gcloud` Application Default Credentials (`gcloud auth application-default login` and `gcloud services enable aiplatform.googleapis.com`)

### Setup

```bash
# Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Environment variables
Create a .env file with: 
BRIGHTDATA_API_TOKEN = <user insert>
GCP_PROJECT_ID = <user insert>
GCP_REGION = <user insert> #us-central1
GEMINI_MODEL = <user insert> #gemini-2.5-flash

# Build the RAG corpus (~5 min, idempotent)
python scripts/build_corpus.py
```

### Run

In two terminals:

**Backend:**
```bash
uv run uvicorn api.app:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install   # first time only
npm run dev
```

Open the Vite URL it prints (defaults to `http://localhost:5173`).

---


## Architecture

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

The React UI talks to a FastAPI backend that orchestrates three agents. Live travel data comes from a Bright Data MCP server (one shared `npx` subprocess), and grounded destination knowledge comes from a ChromaDB index over Wikivoyage articles. Vertex AI Gemini 2.5 Flash drives every reasoning step; Vertex `text-embedding-005` powers the RAG retrieval.

---

## Pipeline

### Search modes

The `POST /api/search` endpoint in [api/routes/search.py](api/routes/search.py) chooses one of two flows based on the form input.

- **Mode A — known destination.** The user fills in the destination on the planner. The flight and hotel agents run in parallel for that city via `asyncio.gather` (2 Bright Data scrapes total). The orchestrator cross-products every scraped flight against every scraped hotel, sorts with a tiered key (nonstop flights first, then cheapest within tier), and returns the top 3 packages.
- **Mode B — brainstorm.** The user leaves the destination blank and only describes a vibe. The RAG agent's `find_destinations(vibe)` runs first to surface 3 candidate cities. Then 3 × (flight + hotel) pairs run in parallel (6 Bright Data scrapes total). The orchestrator returns the cheapest nonstop-preferred package per destination.

In both modes the response also includes `allFlights` and `allHotels` — the full scraped lists, tagged by destination, sorted by `(stops, price)` for flights and by price for hotels — which the UI exposes through a "Show all scraped flights and hotels" toggle.

### Itinerary + chat

Once the user selects a package, the React UI calls:

1. `POST /api/trip/new` to mint a fresh `thread_id` (UUID).
2. `POST /api/trip/itinerary` with the destination, number of days, and the user's original vibe text. The handler in [api/routes/trip.py](api/routes/trip.py) runs **one** RAG retrieval (`get_destination_details(destination, query=vibe, section_types=["See","Do","Eat","Drink"], k=15)`) and **one** Gemini call with `with_structured_output(_ItineraryStructured)`. The response is a list of days with 3–4 specific activities each.
3. `POST /api/trip/chat` for refinements ("add more beaches on day 3"). Every chat request carries the destination so the chat handler can wrap the user's message with a context guard, keeping the RAG agent locked to the selected city. The reply is post-processed to strip any markdown so the UI can render plain conversational text.

The chat thread is keyed on `thread_id` so consecutive messages share conversation history via LangGraph's `MemorySaver`.

---

## Agent implementations

### Flight Search Agent

A 5-node LangGraph `StateGraph` defined in [agent.py](agent.py).

```
resolve → build_url → scrape → extract → filter → END
```

- **`resolve`** — Gemini bound to the `resolve_airport` tool ([tools/airports.py](tools/airports.py)). Converts a city name like `"New York"` to IATA codes (`["JFK","LGA","EWR"]`) using a hardcoded multi-airport metro lookup plus the OpenFlights `airports.csv`.
- **`build_url`** — Pure Python in [google_flights.py](google_flights.py). Constructs a Google Flights search URL with a natural-language `?q=...` query.
- **`scrape`** — Calls `scrape_as_markdown` on the shared Bright Data MCP server. Retries once on a sub-5K-char or CAPTCHA response.
- **`extract`** — Gemini with `with_structured_output(FlightsResponse)` parses the markdown into a list of `FlightOption` objects ([schemas.py](schemas.py)).
- **`filter`** — Drops zero-priced/zero-duration rows, applies optional airline and max-stops filters, sorts by price, returns the top 10.

Entry point: `async def run_search(form: FormInput) -> FlightsResponse`.

### Hotel Search Agent

A 4-node LangGraph `StateGraph` defined in [hotel_agent/agent.py](hotel_agent/agent.py). No resolve step — hotels are searched by city name directly.

```
build_url → scrape → extract → filter → END
```

- **`build_url`** — [hotel_agent/google_hotels.py](hotel_agent/google_hotels.py) builds `https://www.google.com/travel/hotels?q=Hotels in {city} from {checkin} to {checkout}`.
- **`scrape`** — Reuses the same MCP scrape singleton as the flight agent (one shared subprocess for the whole process). Same retry-once behaviour.
- **`extract`** — Gemini with `with_structured_output(HotelsResponse)` and a strict prompt ([prompts/hotel_extraction.md](prompts/hotel_extraction.md)) that forbids using any hotel name not present verbatim in the markdown.
- **`filter`** — Applies optional price-range, rating, and star-class filters; sorts by relevance/price/rating; returns the top results.

Entry point: `async def run_hotel_search(form: HotelFormInput) -> HotelsResponse`.

### Trip Planner (RAG)

The RAG agent has two entry points serving the two patterns the UI needs:

**Itinerary generation (single-shot).** [api/routes/trip.py](api/routes/trip.py)`generate_itinerary` calls `get_destination_details` directly ([trip_planner/retrieval.py](trip_planner/retrieval.py)) — one embedding + one ChromaDB query — then hands the retrieved chunks to Gemini with `with_structured_output(_ItineraryStructured)`. This avoids the variable-latency ReAct loop for a flow where we already know exactly which retrieval we want.

**Chat refinement (ReAct loop with memory).** [trip_planner/agent.py](trip_planner/agent.py) builds a `create_react_agent` over Gemini and exposes two tools from [trip_planner/tools.py](trip_planner/tools.py):

- `search_destinations(query)` — for vibe-style brainstorm queries; also used by the orchestrator's Mode B.
- `search_destination_content(destination, query, section_types)` — for itinerary-style queries about a known city.

Both tools wrap the retrieval functions in [trip_planner/retrieval.py](trip_planner/retrieval.py). The chat agent uses a `MemorySaver` checkpointer keyed on `thread_id`, so consecutive `/api/trip/chat` calls share conversation history.

The corpus itself is built by [trip_planner/corpus_build.py](trip_planner/corpus_build.py) (fetches Wikivoyage wikitext per city and caches it on disk), [trip_planner/chunking.py](trip_planner/chunking.py) (parses articles with `mwparserfromhell` and splits relevant sections into ~1500-char chunks with 200-char overlap), [trip_planner/embeddings.py](trip_planner/embeddings.py) (Vertex `text-embedding-005`), and [trip_planner/vectorstore.py](trip_planner/vectorstore.py) (ChromaDB with cosine similarity, two collections: `destinations` for vibe matching, `sections` for content lookup).

pi/app.py](api/app.py) warms up every agent at startup so the first request is fast. |


---

## Repo layout

```
trip-planner/
├── README.md
├── requirements.txt
├── .env.example
│
├── shared.py                         # get_llm, get_scrape_tool, _normalize_mcp_text — shared by both scrape agents
│
├── agent.py                          # Flight agent: 5-node StateGraph
├── google_flights.py                 # Flight URL builder
├── schemas.py                        # FormInput, FlightOption, FlightsResponse
├── tools/airports.py                 # @tool resolve_airport + METRO_AIRPORTS
├── prompts/system.md                 # Flight resolve_node system prompt
│
├── hotel_agent/
│   ├── agent.py                      # Hotel agent: 4-node StateGraph
│   ├── google_hotels.py              # Hotel URL builder
│   └── schemas.py                    # HotelFormInput, HotelOption, HotelsResponse
├── prompts/hotel_extraction.md       # Hotel extraction prompt
│
├── trip_planner/
│   ├── agent.py                      # create_react_agent + MemorySaver
│   ├── corpus_build.py               # Wikivoyage fetch + cache
│   ├── chunking.py                   # parse_article, chunk_destination
│   ├── embeddings.py                 # singleton VertexAIEmbeddings (text-embedding-005)
│   ├── vectorstore.py                # singleton ChromaDB PersistentClient (cosine)
│   ├── retrieval.py                  # find_destinations, get_destination_details
│   ├── tools.py                      # @tool wrappers for the chat agent
│   ├── schemas.py                    # DestinationHit, SectionHit
│   └── prompts/system.md             # RAG agent system prompt
│
├── api/
│   ├── app.py                        # FastAPI app + CORS + lifespan warmup
│   ├── schemas.py                    # API request/response models
│   └── routes/
│       ├── search.py                 # POST /api/search — Mode A + Mode B
│       └── trip.py                   # POST /api/trip/{itinerary,chat,new}
│
├── frontend/                         # Navio React UI (Vite + Tailwind)
│   ├── package.json
│   └── src/app/
│       ├── App.tsx
│       └── components/
│           ├── Brand.tsx             # Navio logo + animated palm
│           ├── PlannerSection.tsx
│           ├── TravelResultCard.tsx
│           ├── FullResults.tsx
│           ├── ItineraryPage.tsx
│           └── Sidebar.tsx
│
├── data/
│   ├── airports.csv                  # OpenFlights IATA DB (gitignored)
│   ├── destinations.txt              # Indexed cities (tracked)
│   ├── chroma/                       # ChromaDB persistence (gitignored)
│   └── wikivoyage_cache/             # Raw wikitext per destination (gitignored)
│
└── scripts/
    ├── build_corpus.py               # Ingest pipeline
    ├── inspect_corpus.py             # Retrieval REPL
    ├── run_agent.py                  # Flight agent CLI smoke test
    ├── run_hotel_agent.py            # Hotel agent CLI smoke test
    └── run_trip_planner.py           # RAG agent CLI smoke test
```
