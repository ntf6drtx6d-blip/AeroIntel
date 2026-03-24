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


def extract_signals(text: str):
    prompt = f"""
You are an aviation intelligence analyst.

Analyze text from news and extract airport-related signals.

Focus on:
- runway works
- infrastructure
- funding
- consultants
- night operations
- safety upgrades

Ignore:
- terminals
- restaurants
- parking
- retail
- passenger comfort upgrades

Text:
{text}

Return JSON list only, no explanation:

[
  {{
    "airport": "...",
    "signal": "...",
    "type": "infrastructure/funding/operations/consultant/regulatory/other",
    "stage": "idea/planning/funding/consultant/tender/unknown",
    "confidence": 0,
    "relevant": true
  }}
]
"""

    response = _call_with_backoff(
        messages=[{"role": "user", "content": prompt}]
    )

    if response is None:
        return None

    return response.choices[0].message.content


def synthesize(signals_text: str):
    prompt = f"""
You are detecting early-stage airport investment opportunities.

Signals:
{signals_text}

Rules:
- Look for combined signals
- Ignore isolated weak information
- Focus before tender stage
- Explain why this matters for airfield lighting

Return JSON only, no explanation:

{{
  "opportunity": true,
  "stage": "idea/planning/funding/consultant/tender/unknown",
  "insight": "...",
  "action": "..."
}}
"""

    response = _call_with_backoff(
        messages=[{"role": "user", "content": prompt}]
    )

    if response is None:
        return None

    return response.choices[0].message.content
