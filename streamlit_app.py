"""Trip Planner — landing page.

Streamlit auto-discovers files in `pages/` and renders sidebar nav. This
top-level file is the default route shown when the app first opens.
"""
import streamlit as st

st.set_page_config(page_title="Trip Planner", page_icon=":airplane:", layout="centered")

st.title(":earth_africa: Trip Planner")
st.caption("Two agents — one for flights, one for destinations.")

st.markdown(
    """
### What's here

**:airplane: Flight Search** — pick origin, destination, and dates. An agent
resolves your city to airport codes, scrapes Google Flights via Bright Data
MCP, and extracts structured options with Gemini.

**:world_map: Trip Planner** — chat-style. Brainstorm where to go ("a relaxed
coastal trip with great food") or plan day-to-day in a known destination
("4 days in Tokyo, where do locals eat?"). Grounded in a Wikivoyage RAG corpus.

---

Pick a page from the sidebar on the left.
"""
)

with st.expander("Pilot corpus details"):
    st.write(
        "The Trip Planner currently indexes ~30 destinations across Europe, Asia, "
        "the Americas, Africa, the Middle East, and Oceania. To expand: add "
        "destinations to `data/destinations.txt` and re-run "
        "`python scripts/build_corpus.py`."
    )
