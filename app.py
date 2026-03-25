import pandas as pd
import streamlit as st

import db
from country_seeds import COUNTRY_SEEDS
from site_explorer import discover_pages_for_country
from signal_engine import build_signal_records_from_pages
from config import AUTO_APPROVE_SCORE

db.init_db()

st.set_page_config(layout="wide", page_title="AeroIntel")
st.title("AeroIntel")
st.caption("One-screen airport opportunity radar")

countries = list(COUNTRY_SEEDS.keys())
selected_country = st.selectbox("Country", countries)

status_box = st.empty()
progress_box = st.empty()
log_box = st.empty()

if "live_logs" not in st.session_state:
    st.session_state.live_logs = []

if "signal_records" not in st.session_state:
    st.session_state.signal_records = []


def add_log(message: str):
    st.session_state.live_logs.append(message)
    log_box.code("\n".join(st.session_state.live_logs[-30:]))


if st.button("Run Radar"):
    st.session_state.live_logs = []
    st.session_state.signal_records = []

    progress = progress_box.progress(0, text="Starting radar...")
    add_log(f"Country selected: {selected_country}")

    add_log("1/4 Discovering pages and entities")
    discovered, entities, logs = discover_pages_for_country(selected_country, log_callback=add_log)
    progress.progress(25, text="Discovery completed")

    add_log("2/4 Auto-filtering strong pages")
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
    progress.progress(50, text="Auto-filtering completed")

    add_log("3/4 Loading approved pages and entities")
    rows = db.get_pages(selected_country)
    entity_rows = db.get_entities(selected_country)

    pages = [
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

    entities = [
        {
            "country": e[0],
            "source_url": e[1],
            "entity_name": e[2],
            "entity_type": e[3],
            "rationale": e[4],
        }
        for e in entity_rows
    ]

    add_log("4/4 Building signal records")
    progress.progress(75, text="Building signal records")

    records = build_signal_records_from_pages(pages, entities, selected_country)
    st.session_state.signal_records = records

    progress.progress(100, text="Radar finished")
    status_box.success(
        f"Radar finished | Pages: {len(discovered)} | Entities: {len(entities)} | Assets with signals: {len(records)}"
    )

st.subheader("Run log")
log_box.code("\n".join(st.session_state.live_logs[-30:]) if st.session_state.live_logs else "No run yet")

records = st.session_state.get("signal_records", [])

st.subheader("Radar overview")

if not records:
    st.info("No radar results yet. Click 'Run Radar'.")
else:
    rows = []
    for r in records:
        rows.append({
            "Asset": r["asset"],
            "Operator": r["operator"],
            "Signal count": r["signal_count"],
            "What is happening": r["signals"][0]["text"] if r["signals"] else "",
            "Likely need": ", ".join(r["needs"]),
            "Budget / decision body": ", ".join(r["budget_owners"][:3]),
            "Source count": len(r["sources"]),
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)

    asset_names = [r["asset"] for r in records]
    selected_asset = st.selectbox("Select asset", asset_names)

    rec = next(r for r in records if r["asset"] == selected_asset)

    st.markdown(f"## {rec['asset']}")
    st.write(f"Operator: {rec['operator'] or 'Unknown'}")

    if rec["budget_owners"]:
        st.write(f"Budget / decision body: {', '.join(rec['budget_owners'])}")

    if rec["actors"]["municipality"]:
        st.write(f"Municipality: {', '.join(rec['actors']['municipality'])}")
    if rec["actors"]["regional_actor"]:
        st.write(f"Regional actor: {', '.join(rec['actors']['regional_actor'])}")
    if rec["actors"]["mining_company"]:
        st.write(f"Mining company: {', '.join(rec['actors']['mining_company'])}")
    if rec["actors"]["military_branch"]:
        st.write(f"Military branch: {', '.join(rec['actors']['military_branch'])}")

    st.subheader("What is happening")
    for s in rec["signals"][:6]:
        st.write(f"- {s['text']}")
        st.caption(s["source"])

    st.subheader("Likely need")
    if rec["needs"]:
        for n in rec["needs"]:
            st.write(f"- {n}")
    else:
        st.write("No clear need extracted.")

    with st.expander("Evidence (original quotes + sources)", expanded=False):
        for idx, s in enumerate(rec["signals"], start=1):
            st.markdown(f"**{idx}. {', '.join(s['types'])}**")
            st.write(s["quote_original"])
            st.caption(s["source"])

    with st.expander("All source pages", expanded=False):
        for url in rec["sources"]:
            st.write(url)

with st.expander("Discovered pages", expanded=False):
    raw_pages = db.get_pages(selected_country)
    if raw_pages:
        raw_df = pd.DataFrame(
            raw_pages,
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
        st.dataframe(raw_df.drop(columns=["body_text"]), use_container_width=True)

with st.expander("Discovered entities", expanded=False):
    raw_entities = db.get_entities(selected_country)
    if raw_entities:
        ent_df = pd.DataFrame(
            raw_entities,
            columns=[
                "country",
                "source_url",
                "entity_name",
                "entity_type",
                "rationale",
                "discovered_at",
            ],
        )
        st.dataframe(ent_df, use_container_width=True)
