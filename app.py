import pandas as pd
import streamlit as st

import db
from country_seeds import COUNTRY_SEEDS
from site_explorer import discover_pages_for_country
from signal_engine import build_signal_records_from_pages
from config import AUTO_APPROVE_SCORE

db.init_db()

st.set_page_config(layout="wide", page_title="AeroIntel")
st.title("🧠 AeroIntel")
st.caption("Signals + quotes + sources only")

countries = list(COUNTRY_SEEDS.keys())
selected_country = st.selectbox("Country", countries)

with st.expander("Seed institutions for selected country", expanded=False):
    for seed in COUNTRY_SEEDS[selected_country]:
        st.write(f"- {seed['name']} | {seed['type']} | {seed['url']}")

status_box = st.empty()
progress_box = st.empty()
log_placeholder = st.empty()

if "live_logs" not in st.session_state:
    st.session_state.live_logs = []

def add_log(message: str):
    st.session_state.live_logs.append(message)
    log_placeholder.code("\n".join(st.session_state.live_logs[-50:]))

if st.button("Run radar"):
    st.session_state.live_logs = []
    add_log(f"Start radar for {selected_country}")
    progress = progress_box.progress(0, text="Starting radar...")

    add_log("Step 1/4: Discovering pages and entities")
    discovered, entities, logs = discover_pages_for_country(selected_country, log_callback=add_log)
    progress.progress(25, text="Discovery done")

    add_log("Step 2/4: Auto-approving strong pages")
    rows = db.get_pages(selected_country)
    approved_count = 0
    rejected_count = 0

    for row in rows:
        page_url = row[4]
        relevance_score = row[6]
        page_category = row[8]

        if relevance_score >= AUTO_APPROVE_SCORE and page_category in [
            "airport_page",
            "airstrip_page",
            "military_base_page",
            "mining_airstrip_page",
            "projects_page",
            "airport_registry",
            "municipality_airport_page",
            "operator_page",
            "procurement_page",
        ]:
            db.update_page_status(page_url, "approved")
            approved_count += 1
        elif page_category == "junk" or relevance_score < 20:
            db.update_page_status(page_url, "rejected")
            rejected_count += 1

    add_log(f"Approved: {approved_count} | Rejected: {rejected_count}")
    progress.progress(50, text="Auto-filtering done")

    add_log("Step 3/4: Loading approved pages and entities")
    rows = db.get_pages(selected_country)
    entity_rows = db.get_entities(selected_country)

    pages_list = [
        {
            "country": r[0],
            "seed_name": r[1],
            "seed_type": r[2],
            "page_title": r[3],
            "page_url": r[4],
            "page_domain": r[5],
            "relevance_score": r[6],
            "reason": r[7],
            "page_category": r[8],
            "status": r[9],
            "body_text": r[11],
        }
        for r in rows
    ]

    entities_list = [
        {
            "country": e[0],
            "source_url": e[1],
            "entity_name": e[2],
            "entity_type": e[3],
            "rationale": e[4],
        }
        for e in entity_rows
    ]

    progress.progress(75, text="Building signal records")
    add_log("Step 4/4: Building signals with quotes and sources")

    signal_records = build_signal_records_from_pages(
        pages_list,
        entities_list,
        selected_country
    )

    st.session_state["signal_records"] = signal_records
    progress.progress(100, text="Radar finished")
    status_box.success(
        f"Radar finished. Pages discovered: {len(discovered)} | Entities: {len(entities)} | Signal groups: {len(signal_records)}"
    )

st.subheader("Live action log")
log_placeholder.code("\n".join(st.session_state.live_logs[-50:]) if st.session_state.live_logs else "No logs yet")

st.subheader("Discovered pages")

rows = db.get_pages(selected_country)
if rows:
    df = pd.DataFrame(
        rows,
        columns=[
            "country",
            "seed_name",
            "seed_type",
            "page_title",
            "page_url",
            "page_domain",
            "relevance_score",
            "reason",
            "page_category",
            "status",
            "discovered_at",
            "body_text",
        ],
    )
    st.dataframe(df.drop(columns=["body_text"]), use_container_width=True)
else:
    st.info("No pages discovered yet.")

st.subheader("Signals")

signal_records = st.session_state.get("signal_records", [])

if not signal_records:
    st.info("No signals yet. Click 'Run radar'.")
else:
    for rec in signal_records:
        st.markdown(f"### ✈️ {rec['asset_name']}")
        st.write(f"Country: {rec['country']}")

        if rec["actors"]["airport_operator"]:
            st.write(f"Airport operator: {', '.join(rec['actors']['airport_operator'])}")
        if rec["actors"]["municipality"]:
            st.write(f"Municipality: {', '.join(rec['actors']['municipality'])}")
        if rec["actors"]["regional_actor"]:
            st.write(f"Regional actor: {', '.join(rec['actors']['regional_actor'])}")
        if rec["actors"]["mining_company"]:
            st.write(f"Mining company: {', '.join(rec['actors']['mining_company'])}")
        if rec["actors"]["military_branch"]:
            st.write(f"Military branch: {', '.join(rec['actors']['military_branch'])}")
        if rec["budget_owners"]:
            st.write(f"Who may control / allocate budget: {', '.join(rec['budget_owners'])}")

        st.write("**Signals:**")
        if rec["signals"]:
            for sig in rec["signals"]:
                st.write(f"- [{sig['type']}] {sig['quote']}")
                st.write(f"  Source: {sig['source']}")
        else:
            st.write("No explicit signal quotes found.")

        with st.expander("All source pages"):
            for url in rec["page_urls"]:
                st.write(url)
