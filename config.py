import os
import streamlit as st


def get_openai_api_key():
    if "OPENAI_API_KEY" in st.secrets:
        return st.secrets["OPENAI_API_KEY"]

    value = os.getenv("OPENAI_API_KEY")
    if value:
        return value

    raise RuntimeError(
        "OPENAI_API_KEY not found in Streamlit secrets or environment variables."
    )


OPENAI_API_KEY = get_openai_api_key()

RSS_FEEDS = [
    "https://news.google.com/rss/search?q=airport+master+plan",
    "https://news.google.com/rss/search?q=runway+rehabilitation",
    "https://news.google.com/rss/search?q=airport+night+operations",
]

# Keep this very low for stability while testing
MAX_ITEMS_PER_FEED = 1

# Minimum confidence accepted from AI extraction
MIN_CONFIDENCE = 30
