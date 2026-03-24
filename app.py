import pandas as pd
import streamlit as st

from country_seeds import COUNTRY_SEEDS
from db import (
    init_db,
    get_pages,
    get_entities,
    get_airport_profiles,
    clear_pages,
    update_page_status,
)
from site_explorer import discover_pages_for_country
from airport_profile_builder import build_profiles_from_pages

init_db()

st.set_page_config(layout="wide", page_title="AeroIntel")
st.title("🧠 AeroIntel")
st.caption("Regional Source Hunter — official seeds + page ranking + entity expansion")

countries = list(COUNTRY_SEEDS.keys())
selected_country = st.selectbox("Country", countries)

with st.expander("Seed institutions for selected country", expanded=False):
    for seed in COUNTRY_SEEDS[selected_country]:
        st.write(f"- {seed['name']} | {seed['type']} | {seed['url']}")

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    if st.button("Discover pages and entities"):
        with st.spinner(f"Exploring {selected_country}..."):
            discovered, entities, logs = discover_pages_for_country(selected_country)

        st.success(
            f"Discovered {len(discovered)} pages and {len(entities)} entities for {selected_country}"
        )

        with st.expander("Discovery logs"):
            if not logs:
                st.write("No logs")
            else:
                for item in logs:
                    st.json(item)

with col2:
    if st.button("Refresh tables"):
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
    df = pd.DataFrame()
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
            "page_category",
            "status",
            "discovered_at",
        ],
    )

    action_col1, action_col2, action_col3 = st.columns([1, 1, 1])

    with action_col1:
        if st.button("Auto-approve strong pages"):
            for _, row in df.iterrows():
                if row["relevance_score"] >= 45 and row["page_category"] in [
                    "projects_page",
                    "airport_registry",
                    "municipality_airport_page",
                    "operator_page"
                ]:
                    update_page_status(row["page_url"], "approved")

            st.success("Auto-approved strong pages")
            st.rerun()

    with action_col2:
        if st.button("Reject junk pages"):
            for _, row in df.iterrows():
                if row["page_category"] == "junk" or row["relevance_score"] < 20:
                    update_page_status(row["page_url"], "rejected")

            st.success("Rejected junk pages")
            st.rerun()

    with action_col3:
        if st.button("Build airport profiles"):
            pages_list = df.to_dict("records")

            entity_rows = get_entities(selected_country)
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

            profiles = build_profiles_from_pages(
                pages_list,
                entities_list,
                selected_country
            )

            st.success(f"Built {len(profiles)} airport profiles")
            st.rerun()

    st.dataframe(df, use_container_width=True)

    st.subheader("Top candidate pages")

    top_df = df.sort_values(
        by=["relevance_score", "discovered_at"],
        ascending=[False, False]
    ).head(25)

    for idx, row in top_df.iterrows():
        st.markdown(f"### {row['page_title']}")
        st.write(f"**Seed:** {row['seed_name']} | **Type:** {row['seed_type']}")
        st.write(f"**Category:** {row['page_category']} | **Score:** {row['relevance_score']}")
        st.write(f"**Domain:** {row['page_domain']}")
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

st.subheader("Discovered entities")

entity_rows = get_entities(selected_country)

if not entity_rows:
    st.info("No entities discovered yet.")
else:
    entity_df = pd.DataFrame(
        entity_rows,
        columns=[
            "country",
            "source_url",
            "entity_name",
            "entity_type",
            "rationale",
            "discovered_at",
        ],
    )
    st.dataframe(entity_df, use_container_width=True)

    st.subheader("Latest entities")
    for _, row in entity_df.head(30).iterrows():
        st.markdown(f"**{row['entity_name']}**")
        st.write(f"Type: {row['entity_type']}")
        st.write(f"Why: {row['rationale']}")
        st.write(row["source_url"])

st.subheader("Airport Profiles")

profiles = get_airport_profiles(selected_country)

if not profiles:
    st.info("No airport profiles yet.")
else:
    for p in profiles:
        st.markdown(f"### ✈️ {p[0]}")
        st.write(f"Municipality: {p[2]}")
        st.write(f"Regional: {p[3]}")
        st.write(f"Mining: {p[4]}")
        st.write(p[5])
