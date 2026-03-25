import re
from collections import defaultdict

from utils import split_sentences, normalize_whitespace
from operators import KNOWN_OPERATORS

SIGNAL_PATTERNS = {
    "runway": ["runway", "pista", "recapeamento", "resurfacing"],
    "lighting": ["lighting", "balizamento", "papi", "visual aids"],
    "construction": ["construction", "obra", "expansion", "modernization"],
    "budget": ["investment", "budget", "funding", "program"],
    "energy": ["transformador", "substation", "energia"],
}

def clean_asset_name(text):
    if not text:
        return ""

    patterns = [
        r"Aeroporto [A-Za-zÁÉÍÓÚÂÊÔÃÕÇáéíóúâêôãõç\- ]+",
        r"Aeródromo [A-Za-zÁÉÍÓÚÂÊÔÃÕÇáéíóúâêôãõç\- ]+",
        r"Airport [A-Za-z\- ]+",
    ]

    for p in patterns:
        m = re.search(p, text)
        if m:
            return normalize_whitespace(m.group())

    return normalize_whitespace(text[:80])


def detect_operator(text):
    lowered = text.lower()
    for key, val in KNOWN_OPERATORS.items():
        if key in lowered:
            return val
    return ""


def extract_signals(body_text):
    sentences = split_sentences(body_text)
    results = []

    for s in sentences:
        s_clean = normalize_whitespace(s)
        if len(s_clean) < 40 or len(s_clean) > 300:
            continue

        matched = []
        for k, words in SIGNAL_PATTERNS.items():
            if any(w in s_clean.lower() for w in words):
                matched.append(k)

        if matched:
            results.append({
                "types": matched,
                "quote": s_clean
            })

    return results


def to_english(signal):
    txt = signal["quote"]

    # simple normalization layer (not AI hallucination)
    replacements = {
        "recapeamento": "resurfacing",
        "pista": "runway",
        "balizamento": "airfield lighting",
        "obra": "construction",
        "aeródromo": "aerodrome",
        "aeroporto": "airport",
        "energia": "power supply",
    }

    for k, v in replacements.items():
        txt = txt.replace(k, v)

    return txt


def detect_need(signal_types):
    if "lighting" in signal_types:
        return "Airfield lighting / visual aids"
    if "runway" in signal_types:
        return "Runway / taxiway works"
    if "energy" in signal_types:
        return "Power infrastructure"
    if "construction" in signal_types:
        return "General airport upgrade"
    return ""


def build_signal_records_from_pages(pages, entities, country):
    grouped = defaultdict(lambda: {
        "asset": "",
        "operator": "",
        "signals": [],
        "sources": set(),
        "needs": set(),
    })

    for p in pages:
        if p["status"] != "approved":
            continue

        asset = clean_asset_name(
            p.get("page_title", "") + " " + p.get("body_text", "")
        )

        group = grouped[asset]
        group["asset"] = asset

        operator = detect_operator(p.get("body_text", ""))
        if operator:
            group["operator"] = operator

        signals = extract_signals(p.get("body_text", ""))

        for s in signals:
            en = to_english(s)
            need = detect_need(s["types"])

            group["signals"].append({
                "text": en,
                "source": p["page_url"],
                "types": s["types"]
            })

            if need:
                group["needs"].add(need)

        group["sources"].add(p["page_url"])

    result = []

    for g in grouped.values():
        if not g["signals"]:
            continue

        result.append({
            "asset": g["asset"],
            "operator": g["operator"],
            "signals": g["signals"],
            "signal_count": len(g["signals"]),
            "sources": list(g["sources"]),
            "needs": list(g["needs"])
        })

    result.sort(key=lambda x: x["signal_count"], reverse=True)
    return result
