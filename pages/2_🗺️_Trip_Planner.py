"""v1 — chat-style trip planner over a Wikivoyage RAG corpus."""
import sys
import uuid
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
load_dotenv()

from async_runner import run_async  # noqa: E402
from trip_planner.agent import build_trip_planner_agent  # noqa: E402

st.set_page_config(page_title="Trip Planner", page_icon=":world_map:", layout="centered")
st.title(":world_map: Trip Planner")
st.caption("Brainstorm destinations or plan day-to-day itineraries. Grounded in Wikivoyage.")


# ---- Session state ----
if "tp_thread_id" not in st.session_state:
    st.session_state.tp_thread_id = str(uuid.uuid4())
if "tp_messages" not in st.session_state:
    st.session_state.tp_messages = []  # display-only history


# ---- Sidebar ----
with st.sidebar:
    st.subheader("Trip Planner")
    if st.button(":arrows_counterclockwise: New conversation"):
        st.session_state.tp_thread_id = str(uuid.uuid4())
        st.session_state.tp_messages = []
        st.rerun()
    st.caption(f"Thread: `{st.session_state.tp_thread_id[:8]}`")


# ---- Cached agent (survives Streamlit reruns within a process) ----
@st.cache_resource
def _get_agent():
    return build_trip_planner_agent()


agent = _get_agent()


# ---- Render history ----
for msg in st.session_state.tp_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ---- Input ----
prompt = st.chat_input("Where do you want to go, or what do you want to plan?")
if prompt:
    st.session_state.tp_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                config = {"configurable": {"thread_id": st.session_state.tp_thread_id}}
                result = run_async(agent.ainvoke(
                    {"messages": [{"role": "user", "content": prompt}]},
                    config=config,
                ))
                # Gemini 2.5 returns content as a list of {type, text, thought_signature}
                # blocks. AIMessage.text concatenates only the text parts for us.
                reply = str(result["messages"][-1].text)
            except Exception as e:  # noqa: BLE001
                reply = f":warning: Trip planner failed: `{e}`"
        st.markdown(reply)
        st.session_state.tp_messages.append({"role": "assistant", "content": reply})
