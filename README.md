# Trip Planner

A two-agent travel-planning app built for *Agentic AI for Analytics*. Both agents share one Streamlit UI (multi-page, sidebar nav) and one Vertex AI / Bright Data setup.

| Agent | Pattern | What it does |
|---|---|---|
| **v0 — Flight Search** | LangGraph + MCP tool calling | Form input → resolve city to IATA → scrape Google Flights via Bright Data MCP → Gemini extracts a structured ranked list |
| **v1 — Trip Planner** | LangGraph `create_react_agent` + RAG + memory | Chat input → ReAct loop with two RAG tools over a ChromaDB index of Wikivoyage articles → Gemini answers grounded in retrieved chunks; conversation memory via `MemorySaver` |

Class concepts demonstrated end-to-end: **agent framework, tool calling, MCP, hosted models, RAG, memory.**

---

## Architecture

### v0 Flight Search graph

```
  ┌────────────┐  LLM picks resolve_airport(query) for origin and dest
  │  resolve   │  Auto-handles multi-airport metros (NYC, London, ...).
  └─────┬──────┘
        ▼
  ┌────────────┐  Pure Python: build_google_flights_url(...)
  │ build_url  │  (Single primary IATA per side — multi-IATA URLs
  └─────┬──────┘   return Google's landing page, not search results.)
        ▼
  ┌────────────┐  MCP scrape_as_markdown via Bright Data
  │   scrape   │  ~5–10s per request. Fails closed on <5K chars.
  └─────┬──────┘
        ▼
  ┌────────────┐  ChatVertexAI + with_structured_output(FlightsResponse)
  │  extract   │  ~3.5 min — bottleneck of the pipeline.
  └─────┬──────┘
        ▼
  ┌────────────┐  Drop $0/0min rows, apply airline / max_stops filters,
  │   filter   │  sort by price, top 10.
  └─────┬──────┘
        ▼
       END
```

### v1 Trip Planner graph

```
  ┌──────────────┐
  │ chat input   │  st.chat_input
  └──────┬───────┘
         ▼
  ┌──────────────────────────────────┐
  │  create_react_agent (Gemini)     │  prompt=trip_planner/prompts/system.md
  │                                  │  thread_id keys conversation memory
  │   tools:                         │
  │   • search_destinations(query)   │  brainstorm — embeds query, hits
  │     → top-k destination summaries   destinations Chroma collection
  │   • search_destination_content(  │  itinerary — fuzzy-resolves city,
  │       destination, query,        │  filters by section_type, embeds
  │       section_types)             │  query, hits sections collection
  │     → top-k section chunks       │
  └──────┬───────────────────────────┘
         ▼
  ┌──────────────┐  Markdown reply (extracted via AIMessage.text to drop
  │  st.markdown │  Gemini 2.5's thought_signature blocks)
  └──────────────┘
         ▼
  state persists for next turn (MemorySaver, in-process)
```

---

## Prerequisites

- **Python 3.11+** (developed on 3.13)
- **Node.js 18+** — Bright Data MCP server runs as an npx subprocess
- **Bright Data account** with a token. The free tier (5,000 requests/month) is enough for development. Hotel search additionally needs the *Web Data API / Datasets* product activated — see [Roadmap](#roadmap).
- **GCP project** with Vertex AI enabled
- **gcloud CLI** with Application Default Credentials: `gcloud auth application-default login` and `gcloud services enable aiplatform.googleapis.com --project=YOUR_PROJECT`

---

## Quick start

```bash
cd "Agentic AI for Analytics/trip-planner"

# 1. Python venv + deps (~3 min)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Environment
cp .env.example .env
# Edit .env to set BRIGHTDATA_API_TOKEN, GCP_PROJECT_ID, GCP_REGION, GEMINI_MODEL

# 3. v0 dataset — OpenFlights airport IATA codes (~1 MB)
mkdir -p data
curl -L -o data/airports.csv \
  https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat

# 4. Phase 0 sanity checks (each ~10s, except chroma's first run downloads ~80 MB ONNX)
python scripts/test_mcp.py          # MCP tools list — must include scrape_as_markdown
python scripts/test_embeddings.py   # Vertex embed: 768-dim vector
python scripts/test_chroma.py       # Chroma round-trip
python scripts/test_wikivoyage.py   # Lisbon article: ≥6 sections

# 5. v1 corpus — ingest the 31 pilot destinations (~5 min, idempotent)
python scripts/build_corpus.py

# 6. Launch the app
streamlit run streamlit_app.py
# Open http://localhost:8501; switch pages from the left sidebar.
```

---

## Project structure

```
trip-planner/
├── .env                              # local secrets, gitignored
├── .env.example                      # template
├── .gitignore
├── pyproject.toml                    # registers pytest.mark.integration
├── requirements.txt
├── README.md                         # ← you are here
│
├── streamlit_app.py                  # landing page (sidebar nav lives here)
├── async_runner.py                   # run_async() — thread-based async runner
│
├── agent.py                          # v0 LangGraph: resolve→build_url→scrape→extract→filter
├── google_flights.py                 # v0 URL builder (deterministic, pure Python)
├── schemas.py                        # v0 Pydantic: FormInput, FlightOption, FlightsResponse
├── prompts/system.md                 # v0 resolve_node system prompt
├── tools/
│   ├── __init__.py
│   └── airports.py                   # v0 @tool resolve_airport + METRO_AIRPORTS
│
├── trip_planner/                     # v1 RAG agent module
│   ├── __init__.py
│   ├── agent.py                      # v1 create_react_agent factory + MemorySaver
│   ├── corpus_build.py               # fetch_wikitext: cache + retry + canonical-title capture
│   ├── chunking.py                   # parse_article, chunk_destination, _split_text
│   ├── embeddings.py                 # singleton VertexAIEmbeddings (text-embedding-005)
│   ├── vectorstore.py                # singleton ChromaDB PersistentClient (cosine)
│   ├── retrieval.py                  # find_destinations, get_destination_details, fuzzy resolver
│   ├── tools.py                      # @tool wrappers exposed to the agent
│   ├── schemas.py                    # DestinationHit, SectionHit, TripPlanResponse
│   └── prompts/system.md             # v1 BRAINSTORM/ITINERARY system prompt
│
├── pages/                            # Streamlit auto-discovers these into sidebar
│   ├── 1_✈️_Flight_Search.py        # v0 form UI
│   └── 2_🗺️_Trip_Planner.py         # v1 chat UI
│
├── data/
│   ├── airports.csv                  # OpenFlights airport DB (gitignored)
│   ├── destinations.txt              # 31 cities for the v1 pilot (tracked)
│   ├── chroma/                       # ChromaDB on disk (gitignored)
│   └── wikivoyage_cache/             # raw wikitext per destination (gitignored)
│
├── scripts/
│   ├── test_mcp.py                   # Phase 0 v0: MCP tool listing
│   ├── test_scrape.py                # Phase 0 v0: live Google Flights scrape (saves sample_markdown.md)
│   ├── test_embeddings.py            # Phase 0 v1: Vertex embedding round-trip
│   ├── test_chroma.py                # Phase 0 v1: persistent collection round-trip
│   ├── test_wikivoyage.py            # Phase 0 v1: API + parser
│   ├── build_corpus.py               # v1 ingest: --limit N, --parse-only, --reembed-all
│   ├── inspect_corpus.py             # v1 retrieval REPL (uses public functions, doubles as smoke test)
│   ├── run_agent.py                  # v0 CLI smoke test (NYC → Lisbon, +60d)
│   └── run_trip_planner.py           # v1 CLI smoke test (3 turns, last tests memory)
│
└── tests/
    ├── __init__.py
    ├── test_airports.py              # 5 unit tests
    ├── test_google_flights_url.py    # 4 unit tests
    ├── test_chunking.py              # 5 unit tests
    ├── test_extraction.py            # 1 integration (Vertex)
    └── test_retrieval.py             # 5 integration (Vertex + Chroma)
```

---

## v0 — Flight Search

**What it does.** User fills a form (origin city/IATA, destination, departure date, optional return, cabin, max stops, airline filter). The agent resolves city names to IATA codes (handles NYC → JFK/LGA/EWR via a hardcoded metro lookup), constructs a Google Flights search URL, scrapes the page through Bright Data MCP's `scrape_as_markdown`, sends the markdown to Gemini 2.5 Flash with `with_structured_output(FlightsResponse)`, then filters and sorts.

**Per-search cost.** ~1 Bright Data scrape + ~1 Gemini call. Wall time dominated by the Gemini extraction (~3.5 min on a 13K-char scrape).

**Bug we fixed.** Google Flights does **not** parse comma-separated multi-IATA URLs (`Flights from EWR,LGA,JFK to LIS`) — it returns the generic Google Flights landing page instead of search results. `build_url_node` therefore scrapes only the first (primary) airport on each side, even though the resolved-IATA list flows through state for future per-airport fan-out.

**How to test in isolation.**

```bash
python scripts/test_mcp.py          # MCP connectivity
python scripts/test_scrape.py       # Live scrape, saves scripts/sample_markdown.md
pytest tests/test_airports.py tests/test_google_flights_url.py
python scripts/run_agent.py         # End-to-end CLI smoke test
```

---

## v1 — Trip Planner (RAG)

**What it does.** Chat-style assistant. Two modes the LLM detects from the message:

- **Brainstorm** — user describes a vibe (`"a relaxed coastal place with great seafood"`). Agent calls `search_destinations(query)` → top-k destinations → recommends 3–5 with one-paragraph rationales.
- **Itinerary** — user names a place (`"4 days in Tokyo, where do locals eat?"`). Agent calls `search_destination_content(destination, query, section_types=["Eat"])` → top-k chunks → synthesises a focused answer.

**Memory.** Each Streamlit session gets a UUID `thread_id`. LangGraph's `MemorySaver` keys conversation state on that ID, so turn 3 can ask `"What about a viewpoint to watch the sunset?"` and the agent infers Lisbon from prior turns. "🔄 New conversation" in the sidebar issues a fresh UUID.

**Pilot corpus.** 31 destinations spanning Europe, Asia, the Americas, Africa, the Middle East, Oceania, and a few broad regions ("Tuscany", "Bali"). Curated in `data/destinations.txt`.

```
ChromaDB collections (cosine):
  destinations  — 31 docs, one summary per city (~500–1500 chars)
  sections      — 2,023 chunks, one per relevant Wikivoyage section
                  (Understand, Get in, Get around, See, Do, Eat, Drink,
                   Sleep, Buy, Go next), max_chars=1500, overlap=200
```

**Expanding the corpus.** Add cities to `data/destinations.txt`, re-run `python scripts/build_corpus.py`. The script reads existing IDs from Chroma and **only embeds new chunks** — re-runs are near-free. Pass `--reembed-all` to override.

**Testing.**

```bash
pytest tests/test_chunking.py             # unit tests, no network
pytest tests/test_retrieval.py            # integration: hits Vertex + Chroma
python scripts/inspect_corpus.py          # eyeball brainstorm + itinerary results
python scripts/run_trip_planner.py        # 3-turn CLI smoke test
```

---

## Async runner

`async_runner.run_async(coro)` runs a coroutine in a worker thread (where `asyncio.run` gets a fresh stdlib event loop) and blocks until it returns.

We dropped `nest_asyncio` after Streamlit 1.57 transitively pulled in `uvloop`. `nest_asyncio` can only patch stdlib asyncio loops, not uvloop, so calling `nest_asyncio.apply()` raised `ValueError: Can't patch loop of type <class 'uvloop.Loop'>` on every page load. Routing through a worker thread sidesteps the main-loop type entirely — both pages just call `run_async(...)` instead of `asyncio.run(...)`.

---

## Testing

```bash
# Fast unit tests only (14 tests, ~3s) — recommended default
pytest -m "not integration"

# Everything, including Vertex- and Chroma-touching tests (20 tests, ~4 min)
pytest

# Just one file
pytest tests/test_chunking.py -v
```

Custom `integration` mark is registered in `pyproject.toml`. v1 retrieval tests skip themselves cleanly if the Chroma corpus hasn't been ingested yet (`scripts/build_corpus.py` not run).

---

## Roadmap

1. **Hotel search via Booking.com — blocked.** Investigated. Bright Data exposes `web_data_booking_hotel_listings` (returns structured JSON, no Gemini extraction needed) when the MCP server is launched with `TOOLS=scrape_as_markdown,web_data_booking_hotel_listings`. The tool is in the active tool list but **calls return `HTTP 400: Customer is not active`** — the *Web Data API / Datasets* product isn't activated on the user's Bright Data subscription. Two paths forward:
   - **Activate the Web Data API product** on the Bright Data dashboard, then implement against the structured JSON. Faster searches, cleaner data.
   - **Fallback**: scrape `https://www.booking.com/searchresults.html?ss=...&checkin=...&checkout=...&group_adults=...&selected_currency=USD` via `scrape_as_markdown` and extract via Gemini, mirroring the flight pattern. Works today, ~3 min slower per search.
2. **Phase 6 polish** for both agents — console event streaming via `agent.astream_events`, full demo-flow validation per the v0/v1 plan documents.
3. **Migrate `ChatVertexAI` → `ChatGoogleGenerativeAI`** and `VertexAIEmbeddings` → `GoogleGenerativeAIEmbeddings` (both are deprecated in `langchain-google-vertexai`, currently emit warnings on every call). Set `GOOGLE_GENAI_USE_VERTEXAI=true` to keep the Vertex backend. One combined pass across v0+v1.
4. **Scale the corpus** from 31 to ~300 destinations (~30–60 min ingest at the current Vertex throughput). Already supported by `build_corpus.py`.
5. **Streaming responses** in the Trip Planner chat (`agent.astream_events` instead of `ainvoke`).
6. **v2 multi-agent orchestrator** — a top-level agent that calls flight + RAG agents and synthesises a combined trip plan.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ValueError: Can't patch loop of type <class 'uvloop.Loop'>` | Streamlit 1.57 uses `uvloop`; `nest_asyncio` can't patch it. | Already fixed — pages use `async_runner.run_async()` instead of `asyncio.run()`. Don't add `nest_asyncio.apply()` back. |
| Trip Planner replies with `[{'type':'text','text':'...','thought_signature':'...'}]` | Gemini 2.5 returned content as a list of "thinking" blocks. | Already fixed — pages render `str(message.text)`, which uses LangChain's `AIMessage.text` accessor to concatenate just the text parts. |
| Flight search returns 0 options for a multi-airport metro | Google Flights doesn't parse comma-separated IATAs. | Already fixed — `build_url_node` passes only the first IATA per side. The full resolved list still flows through state. |
| Hotel search returns `HTTP 400: Customer is not active` | Bright Data Web Data API product not activated on the account. | See Roadmap item 1. |
| `npx @brightdata/mcp` hangs on first call | First-run package download. | Pre-install: `npm install -g @brightdata/mcp`. |
| `403` from Wikivoyage | Missing/empty User-Agent. | Already set in `trip_planner/corpus_build.py`. Don't strip it. |
| `aiplatform.googleapis.com` 403 | API not enabled on the GCP project even though ADC works. | `gcloud services enable aiplatform.googleapis.com --project=$GCP_PROJECT_ID` |
| `data/airports.csv` not found | Step 3 of Quick start was skipped. | Run the curl command. File is gitignored. |
| Trip Planner replies "I don't have information about X" | Destination isn't in the corpus. | Add it to `data/destinations.txt` and re-run `python scripts/build_corpus.py` (idempotent — only embeds new content). |
