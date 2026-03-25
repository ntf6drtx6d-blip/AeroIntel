import re
from collections import defaultdict

from utils import split_sentences, normalize_whitespace

try:
    from config import SIGNAL_PATTERNS
except ImportError:
    SIGNAL_PATTERNS = {
        "construction_works": [
            "obra", "obras", "construction", "works", "rehabilitation", "modernization", "ampliação", "expansion"
        ],
        "runway_signal": [
            "pista", "runway", "airfield lighting", "aerodrome lighting", "lighting", "balizamento"
        ],
        "concession_signal": [
            "concession", "concessão", "concessionaire", "privatization", "privatização"
        ],
        "budget_signal": [
            "investment", "investimento", "budget", "funding", "grant", "program", "programa"
        ],
        "municipality_signal": [
            "prefeitura", "município", "municipality", "council", "city of"
        ],
        "regional_authority_signal": [
            "secretaria", "department of", "state of", "province of", "infraestrutura"
        ],
        "mining_signal": [
            "vale", "mining", "mine", "mineracao", "mineração", "fifo"
        ],
        "military_signal": [
            "air force", "navy", "army", "defence", "defense", "special operations", "air base"
        ],
    }


AIRPORT_PATTERNS = [
    r"Aeroporto [A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-zÁÉÍÓÚÂÊÔÃÕÇáéíóúâêôãõç\- ]+",
    r"Aeródromo [A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-zÁÉÍÓÚÂÊÔÃÕÇáéíóúâêôãõç\- ]+",
    r"Airport [A-Z][A-Za-z\- ]+",
    r"Airstrip [A-Z][A-Za-z\- ]+",
    r"Base [A-Z][A-Za-z\- ]+",
    r"Naval Air Station [A-Z][A-Za-z\- ]+",
]


def extract_asset_name(page_title: str, body_text: str, page_url: str):
    hay = " ".join([page_title or "", body_text or "", page_url or ""])

    for pattern in AIRPORT_PATTERNS:
        m = re.search(pattern, hay)
        if m:
            return normalize_whitespace(m.group())

    if page_title:
        return normalize_whitespace(page_title)

    return page_url


def extract_signal_quotes(body_text: str):
    sentences = split_sentences(body_text)
    found = []

    for signal_type, keywords in SIGNAL_PATTERNS.items():
        for sentence in sentences:
            lowered = sentence.lower()
            if any(keyword.lower() in lowered for keyword in keywords):
                found.append({
                    "type": signal_type,
                    "quote": sentence,
                })

    dedup = {}
    for item in found:
        key = (item["type"], item["quote"])
        dedup[key] = item

    return list(dedup.values())


def build_signal_records_from_pages(pages, entities, country):
    grouped = defaultdict(lambda: {
        "asset_name": None,
        "country": country,
        "page_urls": set(),
        "signals": [],
        "actors": {
            "municipality": set(),
            "regional_actor": set(),
            "airport_operator": set(),
            "mining_company": set(),
            "military_branch": set(),
        },
        "budget_owners": set(),
    })

    approved_pages = [
        p for p in pages
        if p["status"] == "approved" and p["page_category"] in [
            "airport_page",
            "airstrip_page",
            "military_base_page",
            "mining_airstrip_page",
            "projects_page",
            "airport_registry",
            "municipality_airport_page",
            "operator_page",
            "procurement_page",
        ]
    ]

    for p in approved_pages:
        asset_name = extract_asset_name(
            p.get("page_title", ""),
            p.get("body_text", ""),
            p.get("page_url", ""),
        )

        group = grouped[asset_name]
        group["asset_name"] = asset_name
        group["page_urls"].add(p["page_url"])

        quotes = extract_signal_quotes(p.get("body_text", ""))
        for q in quotes:
            group["signals"].append({
                "type": q["type"],
                "quote": q["quote"],
                "source": p["page_url"],
            })

        for e in entities:
            if e["source_url"] != p["page_url"]:
                continue

            et = e["entity_type"]
            if et in group["actors"]:
                group["actors"][et].add(e["entity_name"])

                if et in ["municipality", "regional_actor", "airport_operator", "mining_company", "military_branch"]:
                    group["budget_owners"].add(e["entity_name"])

    result = []

    for _, item in grouped.items():
        item["page_urls"] = sorted(list(item["page_urls"]))

        for k in item["actors"]:
            item["actors"][k] = sorted(list(item["actors"][k]))

        item["budget_owners"] = sorted(list(item["budget_owners"]))

        if item["signals"] or any(item["actors"].values()):
            result.append(item)

    result.sort(key=lambda x: len(x["signals"]), reverse=True)
    return result
