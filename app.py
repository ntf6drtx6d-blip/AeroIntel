import pandas as pd
import streamlit as st

from country_seeds import COUNTRY_SEEDS
from db import (
    init_db,
    get_pages,
    get_entities,
    get_target_profiles,
    clear_pages,
    update_page_status,
)
from site_explorer import discover_pages_for_country
from target_profile_builder import build_target_profiles_from_pages

init_db()

st.set_page_config(layout="wide", page_title="AeroIntel")
st.title("🧠 AeroIntel")
st.caption("Regional Source Hunter + Target Profiles + Contact Extraction")

countries = list(COUNTRY_SEEDS.keys())
selected_country = st.selectbox("Country", countries)

with st.expander("Seed institutions for selected country", expanded=False):
    for seed in COUNTRY_SEEDS[selected_country]:
        st.write(f"- {seed['name']} | {seed['type']} | {seed['url']}")

progress_box = st.empty()
log_box = st.expander("Live action log", expanded=False)

col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

with col1:
    if st.button("Discover pages and entities"):
        progress = st.progress(0, text=f"Exploring {selected_country}...")
        progress_box.info(f"Starting discovery for {selected_country}")

        with log_box:
            st.write("Fetching seed domains...")
        discovered, entities, logs = discover_pages_for_country(selected_country)

        progress.progress(100, text="Discovery finished")
        progress_box.success(
            f"Discovered {len(discovered)} pages and {len(entities)} entities for {selected_country}"
        )

        with log_box:
            if logs:
                for item in logs:
                    st.json(item)
            else:
                st.write("No logs")

        st.rerun()

with col2:
    if st.button("Auto-approve strong pages"):
        rows = get_pages(selected_country)
        approved_count = 0

        for row in rows:
            page_url = row[4]
            relevance_score = row[6]
            page_category = row[8]

            if relevance_score >= 45 and page_category in [
                "airport_page",
                "airstrip_page",
                "military_base_page",
                "mining_airstrip_page",
                "projects_page",
                "airport_registry",
                "municipality_airport_page",
                "operator_page",
            ]:
                update_page_status(page_url, "approved")
                approved_count += 1

        progress_box.success(f"Auto-approved {approved_count} pages")
        st.rerun()

with col3:
    if st.button("Reject junk pages"):
        rows = get_pages(selected_country)
        rejected_count = 0

        for row in rows:
            page_url = row[4]
            relevance_score = row[6]
            page_category = row[8]

            if page_category == "junk" or relevance_score < 20:
                update_page_status(page_url, "rejected")
                rejected_count += 1

        progress_box.success(f"Rejected {rejected_count} pages")
        st.rerun()

with col4:
    if st.button("Build target profiles"):
        rows = get_pages(selected_country)
        entity_rows = get_entities(selected_country)

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

        progress = st.progress(0, text="Building target profiles...")
        progress_box.info("Building target profiles from approved pages...")

        profiles = build_target_profiles_from_pages(
            pages_list,
            entities_list,
            selected_country
        )

        progress.progress(100, text="Target profile build finished")
        progress_box.success(f"Built {len(profiles)} target profiles")
        st.rerun()

extra_col1, extra_col2 = st.columns([1, 1])

with extra_col1:
    if st.button("Refresh tables"):
        st.rerun()

with extra_col2:
    if st.button("Clear database"):
        clear_pages()
        progress_box.success("Database cleared")
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
            "body_text",
        ],
    )

    st.dataframe(
        df.drop(columns=["body_text"]),
        use_container_width=True
    )

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

st.subheader("Target Profiles")

profiles = get_target_profiles(selected_country)

if not profiles:
    st.info("No target profiles yet.")
else:
    for p in profiles:
        st.markdown(f"### ✈️ {p[0]}")
        st.write(f"Asset type: {p[2]}")
        st.write(f"Owner: {p[3]}")
        st.write(f"Operator: {p[4]}")
        st.write(f"Regional actor: {p[5]}")
        st.write(f"Mining company: {p[6]}")
        st.write(f"Military branch: {p[7]}")
        st.write(f"Email: {p[8]}")
        st.write(f"Phone: {p[9]}")
        st.write(f"Roles: {p[10]}")
        st.write(p[11])
