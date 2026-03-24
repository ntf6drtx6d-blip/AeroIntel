import streamlit as st

from db import init_db, cleanup_old
from scraper import fetch_news
from radar import generate_opportunities

init_db()

st.set_page_config(layout="wide", page_title="AeroIntel")

st.title("🧠 AeroIntel")
st.caption("Manual mode. Fetch runs only when you press the button.")

col1, col2 = st.columns([1, 1])

with col1:
    if st.button("Fetch new signals"):
        with st.spinner("Fetching signals..."):
            added, skipped, errors, raw_results, error_logs = fetch_news()
            cleanup_old()

        st.success(f"Done. Added: {added}, skipped: {skipped}, errors: {errors}")

        with st.expander("Raw AI extraction output"):
            if not raw_results:
                st.write("No raw results returned.")
            else:
                for item in raw_results:
                    st.markdown(f"**Title:** {item['title']}")
                    st.write(item["source"])
                    st.json(item["ai_output"])

        with st.expander("Error logs"):
            if not error_logs:
                st.write("No errors")
            else:
                for err in error_logs:
                    st.json(err)

with col2:
    if st.button("Refresh opportunities"):
        st.rerun()

st.subheader("Top Opportunities")

opps = generate_opportunities()

if not opps:
    st.info("No strong opportunities yet.")

for opp in opps[:5]:
    st.markdown(f"### ✈️ {opp['airport']}")
    st.write(f"**Stage:** {opp['stage']}")
    st.write(opp["insight"])

    st.write("👉 Action:")
    st.write(opp["action"])

    with st.expander("Signals"):
        for s in opp["signals"]:
            st.write(f"- {s['signal']}")
            st.write(f"Type: {s['type']} | Stage: {s['stage']}")
            st.write(s["source"])
