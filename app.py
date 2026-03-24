import pandas as pd
import streamlit as st

from config import TARGET_COUNTRIES
from db import init_db, get_sources, clear_sources
from source_discovery import discover_sources_for_country

init_db()

st.set_page_config(layout="wide", page_title="AeroIntel")
st.title("🧠 AeroIntel")
st.caption("Source Discovery Mode — build country-specific intelligence sources first.")

selected_country = st.selectbox("Country", TARGET_COUNTRIES)

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    if st.button("Discover sources for selected country"):
        with st.spinner(f"Discovering sources for {selected_country}..."):
            discovered, logs = discover_sources_for_country(selected_country)

        st.success(f"Discovered {len(discovered)} new sources for {selected_country}")

        with st.expander("Discovery logs"):
            if logs:
                for item in logs:
                    st.json(item)
            else:
                st.write("No logs")

with col2:
    if st.button("Show saved sources"):
        st.rerun()

with col3:
    if st.button("Clear database"):
        clear_sources()
        st.success("Source database cleared")
        st.rerun()

st.subheader("Saved Sources")

rows = get_sources(selected_country)

if not rows:
    st.info("No sources saved yet.")
else:
    df = pd.DataFrame(
        rows,
        columns=[
            "country",
            "query",
            "title",
            "url",
            "domain",
            "source_type",
            "relevance_score",
            "rationale",
            "discovered_at",
        ],
    )

    st.dataframe(df, use_container_width=True)

    st.subheader("Top Sources")
    top_df = df.sort_values(by=["relevance_score", "discovered_at"], ascending=[False, False]).head(20)

    for _, row in top_df.iterrows():
        st.markdown(f"### {row['title']}")
        st.write(f"**Type:** {row['source_type']} | **Score:** {row['relevance_score']}")
        st.write(f"**Domain:** {row['domain']}")
        st.write(f"**Why it matters:** {row['rationale']}")
        st.write(row["url"])
        st.caption(f"Query: {row['query']}")
