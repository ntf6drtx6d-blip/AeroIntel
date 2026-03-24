import os
import streamlit as st


def get_openai_api_key():
    # 1) Streamlit Cloud secrets
    if "OPENAI_API_KEY" in st.secrets:
        return st.secrets["OPENAI_API_KEY"]

    # 2) Local environment variable fallback
    value = os.getenv("OPENAI_API_KEY")
    if value:
        return value

    raise RuntimeError(
        "OPENAI_API_KEY not found. Add it to Streamlit secrets or environment variables."
    )


OPENAI_API_KEY = get_openai_api_key()

FETCH_INTERVAL_MINUTES = 30

RSS_FEEDS = [
    "https://news.google.com/rss/search?q=airport+master+plan",
    "https://news.google.com/rss/search?q=runway+rehabilitation",
    "https://news.google.com/rss/search?q=airport+infrastructure",
    "https://news.google.com/rss/search?q=aeropuerto+expansion",
    "https://news.google.com/rss/search?q=aeroport+modernisation",
    "https://news.google.com/rss/search?q=site:linkedin.com+airport+project",
]
