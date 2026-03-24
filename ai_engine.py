import time
from openai import OpenAI, RateLimitError
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


def _call_with_backoff(messages, model="gpt-4.1-mini", max_retries=5):
    delay = 2
    last_error = None

    for _ in range(max_retries):
        try:
            return client.chat.completions.create(
                model=model,
                messages=messages,
            )
        except RateLimitError as e:
            last_error = e
            time.sleep(delay)
            delay *= 2

    raise last_error


def extract_signals(text: str) -> str:
    prompt = f"""
You are an aviation intelligence analyst.

Analyze text from news or LinkedIn and extract airport-related signals.

Focus on:
- runway works
- infrastructure
- funding
- consultants
- night operations
- safety upgrades

IGNORE:
- terminals
- restaurants
- parking

Text:
{text}

Return JSON list:

[
  {{
    "airport": "...",
    "signal": "...",
    "type": "infrastructure/funding/operations/consultant/regulatory",
    "stage": "idea/planning/funding/consultant/tender",
    "confidence": 0-100,
    "relevant": true
  }}
]
"""

    response = _call_with_backoff(
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content


def synthesize(signals_text: str) -> str:
    prompt = f"""
You are detecting early-stage airport investment opportunities.

Signals:
{signals_text}

Rules:
- Look for COMBINED signals
- Ignore weak or isolated info
- Focus BEFORE tender stage

Explain WHY this matters for airfield lighting.

Return JSON:
{{
  "opportunity": true/false,
  "stage": "idea/planning/funding/consultant/tender",
  "insight": "...",
  "action": "..."
}}
"""

    response = _call_with_backoff(
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
