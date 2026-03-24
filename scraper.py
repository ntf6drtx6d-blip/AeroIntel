import json
import time
import feedparser

from config import RSS_FEEDS, MAX_ITEMS_PER_FEED, MIN_CONFIDENCE
from ai_engine import extract_signals
from db import save_signal, signal_exists


IRRELEVANT_SIGNAL_KEYWORDS = [
    "immigration",
    "raid",
    "passenger",
    "restaurant",
    "retail",
    "parking",
    "terminal only",
    "security incident",
]


def normalize_confidence(value):
    if value is None:
        return 0

    try:
        value = float(value)
    except Exception:
        return 0

    if 0 <= value <= 1:
        return int(value * 100)

    return int(value)


def clean_ai_json_text(raw_text):
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


def is_irrelevant_signal(signal_text):
    if not signal_text:
        return True

    s = signal_text.lower()
    return any(keyword in s for keyword in IRRELEVANT_SIGNAL_KEYWORDS)


def fetch_news():
    added = 0
    skipped = 0
    errors = 0

    raw_results = []
    error_logs = []
    skip_logs = []

    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
        except Exception as e:
            errors += 1
            error_logs.append({
                "stage": "feed_parse",
                "error": str(e),
                "url": url
            })
            continue

        for entry in feed.entries[:MAX_ITEMS_PER_FEED]:
            title = getattr(entry, "title", "")
            summary = getattr(entry, "summary", "")
            link = getattr(entry, "link", "")
            text = f"{title} {summary}".strip()

            if not text:
                skipped += 1
                skip_logs.append({
                    "stage": "empty_text",
                    "title": title,
                    "reason": "Entry text is empty"
                })
                continue

            result = extract_signals(text)

            if result is None:
                errors += 1
                error_logs.append({
                    "stage": "ai_call",
                    "title": title,
                    "error": "AI returned None (likely rate limit, quota, or API issue)"
                })
                continue

            cleaned_result = clean_ai_json_text(result)

            try:
                data_list = json.loads(cleaned_result)
            except Exception as e:
                errors += 1
                error_logs.append({
                    "stage": "json_parse",
                    "title": title,
                    "error": str(e),
                    "raw": result,
                    "cleaned_raw": cleaned_result
                })
                continue

            if not isinstance(data_list, list):
                skipped += 1
                skip_logs.append({
                    "stage": "json_format",
                    "title": title,
                    "reason": "AI returned non-list JSON",
                    "raw": data_list
                })
                continue

            raw_results.append({
                "title": title,
                "source": link,
                "ai_output": data_list
            })

            if len(data_list) == 0:
                skipped += 1
                skip_logs.append({
                    "stage": "empty_ai_output",
                    "title": title,
                    "reason": "AI returned empty list []"
                })
                continue

            for d in data_list:
                try:
                    if not isinstance(d, dict):
                        skipped += 1
                        skip_logs.append({
                            "stage": "invalid_signal_item",
                            "title": title,
                            "reason": "Signal item is not a dict",
                            "data": d
                        })
                        continue

                    signal_text = d.get("signal")
                    if not signal_text:
                        skipped += 1
                        skip_logs.append({
                            "stage": "missing_signal_text",
                            "title": title,
                            "reason": "Missing signal text",
                            "data": d
                        })
                        continue

                    if is_irrelevant_signal(signal_text):
                        skipped += 1
                        skip_logs.append({
                            "stage": "irrelevant_signal",
                            "title": title,
                            "reason": "Signal matched irrelevant keywords",
                            "signal": signal_text
                        })
                        continue

                    confidence = normalize_confidence(d.get("confidence"))
                    d["confidence"] = confidence

                    if confidence < MIN_CONFIDENCE:
                        skipped += 1
                        skip_logs.append({
                            "stage": "low_confidence",
                            "title": title,
                            "reason": f"Confidence {confidence} below MIN_CONFIDENCE {MIN_CONFIDENCE}",
                            "signal": signal_text
                        })
                        continue

                    if signal_exists(signal_text):
                        skipped += 1
                        skip_logs.append({
                            "stage": "duplicate_signal",
                            "title": title,
                            "reason": "Signal already exists in database",
                            "signal": signal_text
                        })
                        continue

                    save_signal(d, link)
                    added += 1

                except Exception as e:
                    errors += 1
                    error_logs.append({
                        "stage": "processing_signal",
                        "title": title,
                        "error": str(e),
                        "data": d
                    })

            time.sleep(2)

    return added, skipped, errors, raw_results, error_logs, skip_logs
