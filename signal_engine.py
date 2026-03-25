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
            "pista", "runway", "airfield lighting", "aerodrome lighting", "lighting", "balizamento", "papi"
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

NOISE_PATTERNS = [
    "acesso rápido",
    "links externos",
    "fale conosco",
    "portal financeiro",
    "video aulas",
    "notícias",
    "governo federal",
    "cookies",
    "privacy",
    "copyright",
    "todos os direitos reservados",
    "main navigation",
    "wrapper",
    "service channels",
    "contact us",
]

NOISE_REGEXES = [
    r"^\d{4}(\s+\d{4})+$",              # years only
    r"^[\d\-\(\)\s]{7,}$",              # numbers/phone-like only
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


def is_noise_sentence(sentence: str) -> bool:
    s = normalize_whitespace(sentence)
    if not s:
        return True

    lowered = s.lower()

    if len(s) < 25:
        return True

    if len(s) > 450:
        return True

    if any(p in lowered for p in NOISE_PATTERNS):
        return True

    if sum(lowered.count(x) for x in ["aeroporto", "airport", "aeródromo"]) > 5:
        return True

    if s.count("|") > 2:
        return True

    if len(s.split()) > 70:
        return True

    for rgx in NOISE_REGEXES:
        if re.match(rgx, s):
            return True

    return False


def classify_sentence_type(sentence: str):
    lowered = sentence.lower()
    matched_types = []

    for signal_type, keywords in SIGNAL_PATTERNS.items():
        if any(keyword.lower() in lowered for keyword in keywords):
            matched_types.append(signal_type)

    return matched_types


def extract_signal_quotes(body_text: str):
    sentences = split_sentences(body_text)
    found = []

    for sentence in sentences:
        if is_noise_sentence(sentence):
            continue

        matched_types = classify_sentence_type(sentence)
        if not matched_types:
            continue

        for signal_type in matched_types:
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
        "signal_type_counts": defaultdict(int),
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
            group["signal_type_counts"][q["type"]] += 1

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
        item["signal_type_counts"] = dict(item["signal_type_counts"])

        # short signals for "captain" level
        short_signals = []
        seen_short = set()
        for sig in item["signals"]:
            short_quote = sig["quote"]
            if len(short_quote) > 180:
                short_quote = short_quote[:177] + "..."
            key = (sig["type"], short_quote)
            if key in seen_short:
                continue
            seen_short.add(key)
            short_signals.append({
                "type": sig["type"],
                "quote": short_quote,
                "source": sig["source"],
            })

        item["short_signals"] = short_signals[:8]

        if item["signals"] or any(item["actors"].values()):
            result.append(item)

    result.sort(
        key=lambda x: (
            len(x["signals"]),
            len(x["budget_owners"]),
            len(x["page_urls"]),
        ),
        reverse=True
    )
    return result
