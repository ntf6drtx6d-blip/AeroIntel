import json
import time
import feedparser

from config import RSS_FEEDS, MAX_ITEMS_PER_FEED, MIN_CONFIDENCE
from ai_engine import extract_signals
from db import save_signal, signal_exists


def normalize_confidence(value):
    """
    Accept both:
    - 0.0 to 1.0
    - 0 to 100
    Return normalized 0-100 integer
    """
    if value is None:
        return 0

    try:
        value = float(value)
    except Exception:
        return 0

    if 0 <= value <= 1:
        return int(value * 100)

    return int(value)


def fetch_news():
    added = 0
    skipped = 0
    errors = 0

    raw_results = []
    error_logs = []

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

            try:
                data_list = json.loads(result)
            except Exception as e:
                errors += 1
                error_logs.append({
                    "stage": "json_parse",
                    "title": title,
                    "error": str(e),
                    "raw": result
                })
                continue

            if not isinstance(data_list, list):
                skipped += 1
                error_logs.append({
                    "stage": "json_format",
                    "title": title,
                    "error": "AI returned non-list JSON",
                    "raw": data_list
                })
                continue

            raw_results.append({
                "title": title,
                "source": link,
                "ai_output": data_list
            })

            for d in data_list:
                try:
                    if not isinstance(d, dict):
                        skipped += 1
                        continue

                    signal_text = d.get("signal")
                    if not signal_text:
                        skipped += 1
                        continue

                    confidence = normalize_confidence(d.get("confidence"))

                    if confidence < MIN_CONFIDENCE:
                        skipped += 1
                        continue

                    d["confidence"] = confidence

                    if signal_exists(signal_text):
                        skipped += 1
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

    return added, skipped, errors, raw_results, error_logs
