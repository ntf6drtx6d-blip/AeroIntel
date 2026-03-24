import json
from db import get_all_signals
from utils import normalize_airport
from ai_engine import synthesize


def generate_opportunities():

    rows = get_all_signals()

    grouped = {}

    for airport, signal, source, typ, stage in rows:

        airport = normalize_airport(airport)

        if airport not in grouped:
            grouped[airport] = []

        grouped[airport].append({
            "signal": signal,
            "source": source
        })

    opportunities = []

    for airport, signals in grouped.items():

        if len(signals) < 2:
            continue

        combined = "\n".join([s["signal"] for s in signals])

        result = synthesize(combined)

        try:
            data = json.loads(result)

            if data["opportunity"]:
                opportunities.append({
                    "airport": airport,
                    "insight": data["insight"],
                    "stage": data["stage"],
                    "action": data["action"],
                    "signals": signals
                })

        except:
            continue

    return sorted(opportunities, key=lambda x: len(x["signals"]), reverse=True)
