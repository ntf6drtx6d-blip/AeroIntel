import json
import time
from openai import OpenAI, RateLimitError
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


def _call_with_backoff(messages, model="gpt-4o-mini", max_retries=3):
    delay = 3

    for _ in range(max_retries):
        try:
            return client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0,
            )
        except RateLimitError:
            time.sleep(delay)
            delay *= 2
        except Exception:
            return None

    return None


def clean_json_text(raw_text):
    if raw_text is None:
        return None

    text = raw_text.strip()

    if text.startswith("```json"):
        text = text[len("```json"):].strip()

    if text.startswith("```"):
        text = text[len("```"):].strip()

    if text.endswith("```"):
        text = text[:-3].strip()

    return text


def classify_source(country: str, query: str, title: str, url: str, snippet: str = ""):
    prompt = f"""
You are evaluating whether a discovered website/page is a valuable source for early airport project intelligence.

Country: {country}
Search query: {query}
Title: {title}
URL: {url}
Snippet: {snippet}

Classify this result for airport opportunity intelligence.

Prefer sources such as:
- civil aviation authorities
- ministries of transport/infrastructure
- airport operator companies
- municipal/state/provincial government pages about airports
- procurement portals
- engineering consultants active in aviation
- serious aviation news sources

Do NOT prefer:
- airline booking pages
- passenger tips
- generic travel blogs
- commercial retail pages
- random airport info directories

Return JSON only:
{{
  "source_type": "caa/ministry/airport_operator/municipality/procurement/consultant/news/other",
  "relevance_score": 0,
  "rationale": "short reason"
}}

Rules:
- relevance_score must be integer 0-100
- if doubtful, score lower
"""

    response = _call_with_backoff(
        messages=[{"role": "user", "content": prompt}]
    )

    if response is None:
        return {
            "source_type": "other",
            "relevance_score": 0,
            "rationale": "AI classification failed",
        }

    text = clean_json_text(response.choices[0].message.content)

    try:
        return json.loads(text)
    except Exception:
        return {
            "source_type": "other",
            "relevance_score": 0,
            "rationale": "Invalid AI JSON",
        }
