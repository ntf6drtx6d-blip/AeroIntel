import streamlit as st
import time
from db import init_db, cleanup_old
from scraper import fetch_news
from radar import generate_opportunities
from config import FETCH_INTERVAL_MINUTES

init_db()

st.set_page_config(layout="wide")

st.title("🧠 Airport Opportunity Radar (LIVE)")

# -------------------------
# AUTO ENGINE
# -------------------------
if "last_run" not in st.session_state:
    st.session_state.last_run = 0

current_time = time.time()
interval = FETCH_INTERVAL_MINUTES * 60

if current_time - st.session_state.last_run > interval:
    with st.spinner("Updating signals..."):
        fetch_news()
        cleanup_old()
        st.session_state.last_run = current_time

# -------------------------
# UI
# -------------------------
st.subheader("🔥 Top Opportunities")

opps = generate_opportunities()

if not opps:
    st.info("No strong opportunities yet. Let it run...")

top = opps[:5]

for opp in top:
    st.markdown(f"### ✈️ {opp['airport']}")
    st.write(f"Stage: {opp['stage']}")

    st.write(opp["insight"])

    st.write("👉 Action:")
    st.write(opp["action"])

    with st.expander("Signals"):
        for s in opp["signals"]:
            st.write(f"- {s['signal']}")
            st.write(s["source"])

# -------------------------
# AUTO REFRESH
# -------------------------
time.sleep(60)
st.rerun()
