import feedparser
import json
import time

from config import RSS_FEEDS, MAX_ITEMS_PER_FEED
from ai_engine import extract_signals
from db import save_signal, signal_exists


def fetch_news():
    added = 0
    skipped = 0
    errors = 0

    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
        except Exception:
            errors += 1
            continue

        for entry in feed.entries[:MAX_ITEMS_PER_FEED]:
            text = f"{getattr(entry, 'title', '')} {getattr(entry, 'summary', '')}".strip()

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

            for d in data_list:
                if not d.get("relevant"):
                    skipped += 1
                    continue

                if d.get("confidence", 0) < 60:
                    skipped += 1
                    continue

                signal_text = d.get("signal")
                if not signal_text:
                    skipped += 1
                    continue

                if signal_exists(signal_text):
                    skipped += 1
                    continue

                save_signal(d, entry.link)
                added += 1

            time.sleep(2)

    return added, skipped, errors
