import json
import time
import feedparser

from config import RSS_FEEDS, MAX_ITEMS_PER_FEED, MIN_CONFIDENCE
from ai_engine import extract_signals
from db import save_signal, signal_exists


def fetch_news():
    added = 0
    skipped = 0
    errors = 0
    raw_results = []

    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
        except Exception:
            errors += 1
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
                continue

            try:
                data_list = json.loads(result)
            except Exception:
                errors += 1
                continue

            if not isinstance(data_list, list):
                skipped += 1
                continue

            raw_results.append(
                {
                    "title": title,
                    "source": link,
                    "ai_output": data_list,
                }
            )

            for d in data_list:
                if not isinstance(d, dict):
                    skipped += 1
                    continue

                signal_text = d.get("signal")
                if not signal_text:
                    skipped += 1
                    continue

                confidence = d.get("confidence", 0)
                if not isinstance(confidence, int):
                    try:
                        confidence = int(confidence)
                    except Exception:
                        confidence = 0

                if confidence < MIN_CONFIDENCE:
                    skipped += 1
                    continue

                if signal_exists(signal_text):
                    skipped += 1
                    continue

                save_signal(d, link)
                added += 1

            time.sleep(2)

    return added, skipped, errors, raw_results
