"""v0 — Streamlit form + flight result rendering."""
import sys
from datetime import date, timedelta
from pathlib import Path

import streamlit as st

# Streamlit launches each page with its own working directory; ensure the
# repo root is on sys.path so top-level modules (agent, schemas) resolve.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent import get_agent, run_search  # noqa: E402
from async_runner import run_async  # noqa: E402
from schemas import FormInput  # noqa: E402

AIRLINE_OPTIONS = [
    "TAP", "United", "Delta", "American", "British Airways", "Lufthansa",
    "Air France", "KLM", "Iberia", "Emirates", "Qatar Airways", "Turkish Airlines",
    "JetBlue", "Aer Lingus",
]

st.set_page_config(page_title="Flight Search", page_icon=":airplane:", layout="centered")
st.title(":airplane: Flight Search")
st.caption("Powered by Bright Data MCP -> Google Flights -> Gemini")


@st.cache_resource
def _warm_agent():
    """Build and cache the LangGraph agent (with its MCP subprocess) per process."""
    return get_agent()


_warm_agent()


with st.form("search"):
    c1, c2 = st.columns(2)
    with c1:
        origin = st.text_input("Origin", value="New York", help="City name or IATA code")
    with c2:
        destination = st.text_input("Destination", value="Lisbon", help="City name or IATA code")

    c3, c4 = st.columns(2)
    with c3:
        round_trip = st.checkbox("Round trip", value=False)
        departure_date = st.date_input(
            "Departure",
            value=date.today() + timedelta(days=60),
            min_value=date.today(),
        )
    with c4:
        passengers = st.number_input("Passengers", min_value=1, max_value=9, value=1)
        return_date = (
            st.date_input(
                "Return",
                value=departure_date + timedelta(days=7),
                min_value=departure_date,
            )
            if round_trip
            else None
        )

    c5, c6 = st.columns(2)
    with c5:
        cabin_class = st.selectbox(
            "Cabin", ["Economy", "Premium Economy", "Business", "First"]
        )
    with c6:
        max_stops = st.selectbox("Max stops", ["Any", "Nonstop only", "1 stop max"])

    airlines = st.multiselect("Filter by airline (optional)", AIRLINE_OPTIONS)

    submitted = st.form_submit_button(":mag: Search")

if submitted:
    form = FormInput(
        origin=origin,
        destination=destination,
        departure_date=departure_date,
        return_date=return_date,
        airlines=airlines,
        passengers=passengers,
        cabin_class=cabin_class,
        max_stops=max_stops,
    )
    with st.spinner("Resolving airports, scraping Google Flights, extracting options..."):
        try:
            result = run_async(run_search(form))
        except Exception as e:  # noqa: BLE001
            st.error(f"Search failed: {e}")
            st.stop()

    st.info(result.notes or "Done.")

    if not result.flights:
        st.warning("No flights matched your filters. Try widening the criteria or pick a different date.")
    else:
        st.subheader(f"{len(result.flights)} option(s)")
        for f in result.flights:
            airlines_label = " / ".join(f.airlines)
            stops_label = "Nonstop" if f.stops == 0 else f"{f.stops} stop(s)"
            hours, minutes = divmod(f.duration_minutes, 60)
            duration_label = f"{hours}h {minutes}m"
            header = (
                f"${f.price_amount:.0f}  -  {airlines_label}  -  "
                f"{f.departure_datetime} -> {f.arrival_datetime}  -  "
                f"{duration_label}  -  {stops_label}"
            )
            with st.expander(header):
                st.write(f"**Origin:** {f.origin_iata}")
                st.write(f"**Destination:** {f.destination_iata}")
                st.write(f"**Cabin:** {f.cabin_class}")
                st.write(f"**Currency:** {f.price_currency}")
                if f.flight_numbers:
                    st.write(f"**Flight numbers:** {', '.join(f.flight_numbers)}")
                if f.layover_airports:
                    st.write(f"**Layover airports:** {', '.join(f.layover_airports)}")
                if f.booking_url:
                    st.markdown(f"[Open booking page]({f.booking_url})")
