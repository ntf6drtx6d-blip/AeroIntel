import os
import streamlit as st


def get_openai_api_key():
    if "OPENAI_API_KEY" in st.secrets:
        return st.secrets["OPENAI_API_KEY"]

    value = os.getenv("OPENAI_API_KEY")
    if value:
        return value

    raise RuntimeError("OPENAI_API_KEY not found in Streamlit secrets or environment variables.")


OPENAI_API_KEY = get_openai_api_key()

TARGET_COUNTRIES = [
    "Brazil",
    "Thailand",
    "Colombia",
    "Mexico",
    "Australia",
    "Jordan",
]

MAX_SEARCH_RESULTS_PER_QUERY = 8
MAX_QUERIES_PER_COUNTRY = 8
