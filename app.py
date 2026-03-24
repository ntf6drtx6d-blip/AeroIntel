import pandas as pd
import streamlit as st

from country_seeds import COUNTRY_SEEDS
from db import init_db, get_pages, clear_pages, update_page_status
from site_explorer import discover_pages_for_country

init_db()

st.set_page_config(layout="wide", page_title="AeroIntel")
st.title("🧠 AeroIntel")
st.caption("Seeded Source Discovery Mode — crawl official aviation institutions first.")

countries = list(COUNTRY_SEEDS.keys())
selected_country = st.selectbox("Country", countries)

with st.expander("Seed institutions for selected country", expanded=False):
    for seed in COUNTRY_SEEDS[selected_country]:
        st.write(f"- {seed['name']} | {seed['type']} | {seed['url']}")

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    if st.button("Discover pages from seed institutions"):
        with st.spinner(f"Exploring seed domains for {selected_country}..."):
            discovered, logs = discover_pages_for_country(selected_country)

        st.success(f"Discovered {len(discovered)} pages for {selected_country}")

        with st.expander("Discovery logs"):
            if not logs:
                st.write("No logs")
            else:
                for item in logs:
                    st.json(item)

with col2:
    if st.button("Refresh table"):
        st.rerun()

with col3:
    if st.button("Clear database"):
        clear_pages()
        st.success("Database cleared")
        st.rerun()

st.subheader("Discovered pages")

rows = get_pages(selected_country)

if not rows:
    st.info("No pages discovered yet.")
else:
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
            "status",
            "discovered_at",
        ],
    )

    st.dataframe(df, use_container_width=True)

    st.subheader("Top candidate pages")

    top_df = df.sort_values(
        by=["relevance_score", "discovered_at"],
        ascending=[False, False]
    ).head(25)

    for idx, row in top_df.iterrows():
        st.markdown(f"### {row['page_title']}")
        st.write(f"**Seed:** {row['seed_name']} | **Type:** {row['seed_type']}")
        st.write(f"**Domain:** {row['page_domain']}")
        st.write(f"**Score:** {row['relevance_score']}")
        st.write(f"**Why:** {row['reason']}")
        st.write(row["page_url"])
        st.write(f"**Status:** {row['status']}")

        c1, c2, c3 = st.columns([1, 1, 1])

        with c1:
            if st.button("Approve", key=f"approve_{selected_country}_{idx}"):
                update_page_status(row["page_url"], "approved")
                st.rerun()

        with c2:
            if st.button("Reject", key=f"reject_{selected_country}_{idx}"):
                update_page_status(row["page_url"], "rejected")
                st.rerun()

        with c3:
            if st.button("Keep new", key=f"new_{selected_country}_{idx}"):
                update_page_status(row["page_url"], "new")
                st.rerun()
