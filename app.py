import streamlit as st
import pandas as pd

import db
from country_seeds import COUNTRY_SEEDS
from site_explorer import discover_pages_for_country
from signal_engine import build_signal_records_from_pages

db.init_db()

st.set_page_config(layout="wide")
st.title("🧠 AeroIntel")

country = st.selectbox("Country", list(COUNTRY_SEEDS.keys()))

if st.button("Run Radar"):
    with st.spinner("Running full scan..."):
        discover_pages_for_country(country)

        rows = db.get_pages(country)
        entities = db.get_entities(country)

        pages = [{
            "page_title": r[3],
            "page_url": r[4],
            "body_text": r[11],
            "status": r[9],
        } for r in rows]

        ents = [{
            "entity_name": e[2],
            "entity_type": e[3],
            "source_url": e[1],
        } for e in entities]

        results = build_signal_records_from_pages(pages, ents, country)

        st.session_state["results"] = results

if "results" not in st.session_state:
    st.info("Run radar first")
    st.stop()

results = st.session_state["results"]

# ======================
# MAIN TABLE
# ======================

table_data = []

for r in results:
    table_data.append({
        "Asset": r["asset"],
        "Operator": r["operator"],
        "Signals": r["signal_count"],
        "What is happening": r["signals"][0]["text"][:120],
        "Likely need": ", ".join(r["needs"]),
        "Sources": len(r["sources"]),
    })

df = pd.DataFrame(table_data)

st.subheader("Radar overview")
selected = st.dataframe(df, use_container_width=True)

# ======================
# DETAIL VIEW
# ======================

asset_names = [r["asset"] for r in results]
selected_asset = st.selectbox("Select asset", asset_names)

rec = next(r for r in results if r["asset"] == selected_asset)

st.markdown(f"## {rec['asset']}")
st.write(f"Operator: {rec['operator']}")

st.subheader("What is happening")
for s in rec["signals"][:5]:
    st.write(f"- {s['text']}")
    st.caption(s["source"])

st.subheader("Likely need")
for n in rec["needs"]:
    st.write(f"- {n}")

st.subheader("Sources")
for url in rec["sources"]:
    st.write(url)
