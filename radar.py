import json
from db import get_all_signals
from utils import normalize_airport
from ai_engine import synthesize


def generate_opportunities():
    rows = get_all_signals()
    grouped = {}

    for airport, signal, source, typ, stage in rows:
        airport_name = normalize_airport(airport)

        if airport_name not in grouped:
            grouped[airport_name] = []

        grouped[airport_name].append(
            {
                "signal": signal,
                "source": source,
                "type": typ,
                "stage": stage,
            }
        )

    opportunities = []

    for airport, signals in grouped.items():
        if len(signals) < 2:
            continue

        combined = "\n".join(
            [f"- {s['signal']} ({s['type']}, {s['stage']})" for s in signals]
        )

        result = synthesize(combined)
        if result is None:
            continue

        try:
            data = json.loads(result)
        except Exception:
            continue

        if data.get("opportunity"):
            opportunities.append(
                {
                    "airport": airport,
                    "insight": data.get("insight", ""),
                    "stage": data.get("stage", "unknown"),
                    "action": data.get("action", ""),
                    "signals": signals,
                }
            )

    return sorted(opportunities, key=lambda x: len(x["signals"]), reverse=True)
