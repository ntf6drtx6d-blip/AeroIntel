import streamlit as st
import time
from db import init_db, cleanup_old
from scraper import fetch_news
from radar import generate_opportunities
from config import FETCH_INTERVAL_MINUTES

init_db()
st.set_page_config(layout="wide")
st.title("🧠 AeroIntel")

if "last_fetch_ts" not in st.session_state:
    st.session_state.last_fetch_ts = 0.0

now = time.time()
interval_seconds = FETCH_INTERVAL_MINUTES * 60
should_fetch = (now - st.session_state.last_fetch_ts) >= interval_seconds

if should_fetch:
    with st.spinner("Fetching new signals..."):
        fetch_news()
        cleanup_old()
        st.session_state.last_fetch_ts = now
        st.success("Signals updated")

st.subheader("Top Opportunities")
opps = generate_opportunities()

if not opps:
    st.info("No strong opportunities yet.")

for opp in opps[:5]:
    st.markdown(f"### ✈️ {opp['airport']}")
    st.write(f"Stage: {opp['stage']}")
    st.write(opp["insight"])
    st.write("👉 Action:")
    st.write(opp["action"])

    with st.expander("Signals"):
        for s in opp["signals"]:
            st.write(f"- {s['signal']}")
            st.write(s["source"])

st.caption(
    f"Last fetch: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(st.session_state.last_fetch_ts)) if st.session_state.last_fetch_ts else 'not yet'}"
)
