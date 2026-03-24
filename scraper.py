import feedparser
import json
from config import RSS_FEEDS
from ai_engine import extract_signals
from db import save_signal, signal_exists


def fetch_news():

    for url in RSS_FEEDS:
        feed = feedparser.parse(url)

        for entry in feed.entries[:2]:

            text = entry.title + " " + entry.summary

            result = extract_signals(text)

            try:
                data_list = json.loads(result)

                for d in data_list:

                    if not d.get("relevant"):
                        continue

                    if d.get("confidence", 0) < 50:
                        continue

                    if not signal_exists(d.get("signal")):
                        save_signal(d, entry.link)

            except:
                continue
