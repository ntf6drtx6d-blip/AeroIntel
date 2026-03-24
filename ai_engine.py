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

Analyze this text and extract ONLY airport project signals that could matter for airfield lighting.

Relevant examples:
- runway rehabilitation
- runway extension
- taxiway construction
- airport master plan
- night operations
- safety upgrade
- airport infrastructure funding
- consultant appointment
- airside modernization

Not relevant:
- terminal expansion only
- parking
- restaurants
- retail
- immigration raids
- security incidents
- airline passenger issues
- commercial real estate
- passenger comfort upgrades

Text:
{text}

Rules:
- Return ONLY valid JSON
- Do NOT use markdown
- Do NOT use ```json fences
- If nothing relevant is found, return []

Return format:
[
  {{
    "airport": "string",
    "signal": "string",
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
- Return ONLY valid JSON
- Do NOT use markdown
- Do NOT use ```json fences

Return format:
{{
  "opportunity": true,
  "stage": "idea/planning/funding/consultant/tender/unknown",
  "insight": "string",
  "action": "string"
}}
"""

    response = _call_with_backoff(
        messages=[{"role": "user", "content": prompt}]
    )

    if response is None:
        return None

    return response.choices[0].message.content
