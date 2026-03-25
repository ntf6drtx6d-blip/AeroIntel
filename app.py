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
    add_log(f"New pages found this run: {len(discovered)}")

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

    total_pages_in_db = len(db.get_pages(selected_country))
    total_entities_in_db = len(db.get_entities(selected_country))

    progress.progress(100, text="Radar finished")
    status_box.success(
        f"Radar finished | New pages this run: {len(discovered)} | Total pages in DB: {total_pages_in_db} | "
        f"Entities in DB: {total_entities_in_db} | Assets with signals: {len(records)}"
    )

st.subheader("Run log")
log_box.code("\n".join(st.session_state.live_logs[-30:]) if st.session_state.live_logs else "No run yet")

records = st.session_state.get("signal_records", [])

# Management Summary
st.subheader("Management Summary")

if records:
    total_assets = len(records)
    total_signals = sum(len(r.get("signals", [])) for r in records)

    operators = {}
    budget_bodies = {}
    signal_types = {}

    for r in records:
        op = r.get("operator") or "Unknown"
        operators[op] = operators.get(op, 0) + 1

        for b in r.get("budget_owners", []):
            budget_bodies[b] = budget_bodies.get(b, 0) + 1

        for s in r.get("signals", []):
            for t in s.get("types", []):
                signal_types[t] = signal_types.get(t, 0) + 1

    top_ops = sorted(operators.items(), key=lambda x: x[1], reverse=True)[:8]
    top_budget = sorted(budget_bodies.items(), key=lambda x: x[1], reverse=True)[:8]
    top_signal_types = sorted(signal_types.items(), key=lambda x: x[1], reverse=True)[:8]

    c1, c2, c3 = st.columns(3)
    with c1:
        st.write(f"Assets detected: {total_assets}")
        st.write(f"Total signals: {total_signals}")
    with c2:
        st.write("Top operators:")
        for op, cnt in top_ops:
            st.write(f"- {op}: {cnt}")
    with c3:
        st.write("Top budget bodies:")
        for b, cnt in top_budget:
            st.write(f"- {b}: {cnt}")

    with st.expander("Top signal types", expanded=False):
        for s, cnt in top_signal_types:
            st.write(f"- {s}: {cnt}")
else:
    st.info("No radar results yet. Click 'Run Radar'.")

st.subheader("Radar overview")

if records:
    table_rows = []
    for r in records:
        table_rows.append({
            "Asset": r.get("asset", ""),
            "Operator": r.get("operator", "") or "Unknown",
            "Signal count": r.get("signal_count", 0),
            "What is happening": r.get("signals", [{}])[0].get("text", "") if r.get("signals") else "",
            "Likely need": ", ".join(r.get("needs", [])),
            "Budget / decision body": ", ".join(r.get("budget_owners", [])[:3]),
            "Source count": len(r.get("sources", [])),
        })

    df = pd.DataFrame(table_rows)
    st.dataframe(df, use_container_width=True)

    asset_names = [r.get("asset", "") for r in records if r.get("asset")]
    selected_asset = st.selectbox("Select asset", asset_names)

    rec = next(r for r in records if r.get("asset") == selected_asset)

    signal_count = len(rec.get("signals", []))
    st.markdown(f"## {rec.get('asset', '')} ({signal_count} signals)")
    st.write(f"Operator: {rec.get('operator') or 'Unknown'}")

    if rec.get("budget_owners"):
        st.write(f"Budget / decision body: {', '.join(rec.get('budget_owners', []))}")

    actors = rec.get("actors", {})

    if actors.get("municipality"):
        st.write(f"Municipality: {', '.join(actors.get('municipality', []))}")
    if actors.get("regional_actor"):
        st.write(f"Regional actor: {', '.join(actors.get('regional_actor', []))}")
    if actors.get("mining_company"):
        st.write(f"Mining: {', '.join(actors.get('mining_company', []))}")
    if actors.get("military_branch"):
        st.write(f"Military: {', '.join(actors.get('military_branch', []))}")

    st.subheader("What is happening")
    for s in rec.get("signals", [])[:6]:
        st.write(f"- {s.get('text', '')}")
        st.caption(f"Source page: {s.get('source', '')}")
        st.caption(f"Original quote: {s.get('quote_original', '')}")

    st.subheader("Likely need")
    if rec.get("needs"):
        for n in rec.get("needs", []):
            st.write(f"- {n}")
    else:
        st.write("No clear need extracted.")

    with st.expander("Evidence (original quotes + sources)", expanded=False):
        for idx, s in enumerate(rec.get("signals", []), start=1):
            st.markdown(f"**{idx}. {', '.join(s.get('types', []))}**")
            st.write(f"English: {s.get('text', '')}")
            st.write(f"Original: {s.get('quote_original', '')}")
            st.caption(s.get("source", ""))

    with st.expander("All source pages", expanded=False):
        for url in rec.get("sources", []):
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
