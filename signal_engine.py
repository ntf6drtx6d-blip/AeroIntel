import re
from collections import defaultdict

from utils import split_sentences, normalize_whitespace
from operator_map import OPERATOR_KEYWORDS

SIGNAL_PATTERNS = {
    "runway": ["runway", "pista", "recapeamento", "resurfacing", "taxiway", "taxiamento"],
    "lighting": ["lighting", "balizamento", "papi", "visual aids", "illumination", "auxílios visuais"],
    "construction": ["construction", "obra", "obras", "expansion", "modernization", "reform", "ampliação", "reforma"],
    "budget": ["investment", "investimento", "budget", "funding", "grant", "program", "programa", "fnac"],
    "energy": ["transformador", "substation", "energia", "power", "subestação"],
}

AIRPORT_PATTERNS = [
    r"Aeroporto [A-ZÁÉÍÓÚÂÊÔÃÕÇa-záéíóúâêôãõç0-9\-/ ]+",
    r"Aeródromo [A-ZÁÉÍÓÚÂÊÔÃÕÇa-záéíóúâêôãõç0-9\-/ ]+",
    r"Airport [A-Z][A-Za-z0-9\-/ ]+",
    r"Airstrip [A-Z][A-Za-z0-9\-/ ]+",
]

BAD_ASSET_PATTERNS = [
    "assuntos",
    "notícias",
    "noticias",
    "formação",
    "capacitação",
    "programa",
    "gov.br",
    "ministry",
    "secretaria",
    "conselho",
    "fundo",
]

NOISE_PATTERNS = [
    "acesso rápido",
    "links externos",
    "fale conosco",
    "portal financeiro",
    "video aulas",
    "cookies",
    "privacy",
    "copyright",
    "service channels",
    "contact us",
    "todos os direitos reservados",
]


def looks_like_bad_asset(name: str) -> bool:
    if not name:
        return True
    lowered = name.lower()
    return any(p in lowered for p in BAD_ASSET_PATTERNS)


def slug_to_asset_name(page_url: str) -> str:
    slug = page_url.lower()

    if "aeroporto-" in slug or "/aeroporto-" in slug:
        m = re.search(r"/(aeroporto-[a-z0-9\-]+)/?", slug)
        if m:
            text = m.group(1).replace("-", " ").title()
            return normalize_whitespace(text)

    if "aerodromo-" in slug or "/aerodromo-" in slug:
        m = re.search(r"/(aerodromo-[a-z0-9\-]+)/?", slug)
        if m:
            text = m.group(1).replace("-", " ").title()
            text = text.replace("Aerodromo", "Aeródromo")
            return normalize_whitespace(text)

    return ""


def clean_asset_name(page_title: str, body_text: str, page_url: str, page_category: str) -> str:
    # Priority 1: URL slug
    slug_name = slug_to_asset_name(page_url)
    if slug_name and not looks_like_bad_asset(slug_name):
        return slug_name

    # Priority 2: title
    for pattern in AIRPORT_PATTERNS:
        m = re.search(pattern, page_title or "")
        if m:
            candidate = normalize_whitespace(m.group())
            if not looks_like_bad_asset(candidate):
                return candidate

    # Priority 3: body
    for pattern in AIRPORT_PATTERNS:
        m = re.search(pattern, body_text or "")
        if m:
            candidate = normalize_whitespace(m.group())
            if not looks_like_bad_asset(candidate):
                return candidate

    # Priority 4: only for airport/airstrip-like pages
    if page_category in ["airport_page", "airstrip_page", "military_base_page", "mining_airstrip_page"]:
        candidate = normalize_whitespace(page_title or "")
        if candidate and not looks_like_bad_asset(candidate):
            return candidate

    return ""


def is_noise_sentence(sentence: str) -> bool:
    s = normalize_whitespace(sentence)
    if not s:
        return True

    lowered = s.lower()

    if len(s) < 35:
        return True
    if len(s) > 350:
        return True
    if any(p in lowered for p in NOISE_PATTERNS):
        return True
    if s.count("|") > 1:
        return True
    if len(s.split()) > 55:
        return True

    # only years / only numbers
    if re.fullmatch(r"[\d\s\-\(\)\/]+", s):
        return True
    if re.fullmatch(r"(\d{4}\s*){2,}", s):
        return True

    return False


def classify_sentence_types(sentence: str):
    lowered = sentence.lower()
    matched = []

    for signal_type, words in SIGNAL_PATTERNS.items():
        if any(w in lowered for w in words):
            matched.append(signal_type)

    return matched


def to_english(sentence: str):
    txt = sentence

    replacements = {
        "recapeamento": "resurfacing",
        "pista": "runway",
        "pistas": "runways",
        "balizamento": "airfield lighting",
        "obra": "construction",
        "obras": "construction works",
        "aeródromo": "aerodrome",
        "aeroporto": "airport",
        "energia": "power supply",
        "prefeitura": "municipality",
        "município": "municipality",
        "secretaria": "department",
        "investimento": "investment",
        "programa": "program",
        "ampliação": "expansion",
        "reforma": "renovation",
        "taxiamento": "taxiway operations",
        "auxílios visuais": "visual aids",
        "subestação": "substation",
    }

    for k, v in replacements.items():
        txt = re.sub(rf"\b{k}\b", v, txt, flags=re.IGNORECASE)

    return normalize_whitespace(txt)


def extract_signal_quotes(body_text: str):
    sentences = split_sentences(body_text)
    found = []

    for sentence in sentences:
        if is_noise_sentence(sentence):
            continue

        matched_types = classify_sentence_types(sentence)
        if not matched_types:
            continue

        found.append({
            "types": matched_types,
            "quote_original": normalize_whitespace(sentence),
            "quote_english": to_english(sentence),
        })

    dedup = {}
    for item in found:
        key = item["quote_original"]
        dedup[key] = item

    return list(dedup.values())


def detect_operator(*texts) -> str:
    haystack = " ".join([t for t in texts if t]).lower()

    for key, val in OPERATOR_KEYWORDS.items():
        if key in haystack:
            return val

    return ""


def infer_need(signal_types):
    needs = set()
    if "lighting" in signal_types:
        needs.add("Airfield lighting / visual aids")
    if "runway" in signal_types:
        needs.add("Runway / taxiway works")
    if "energy" in signal_types:
        needs.add("Power infrastructure")
    if "construction" in signal_types:
        needs.add("General airport upgrade")
    if "budget" in signal_types:
        needs.add("Funding / program-backed works")
    return sorted(list(needs))


def build_signal_records_from_pages(pages, entities, country):
    grouped = defaultdict(lambda: {
        "asset": "",
        "operator": "",
        "signals": [],
        "sources": set(),
        "needs": set(),
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
        asset = clean_asset_name(
            p.get("page_title", ""),
            p.get("body_text", ""),
            p.get("page_url", ""),
            p.get("page_category", ""),
        )

        if not asset:
            continue

        group = grouped[asset]
        group["asset"] = asset
        group["sources"].add(p["page_url"])

        page_operator = detect_operator(
            p.get("seed_name", ""),
            p.get("page_title", ""),
            p.get("body_text", ""),
            p.get("page_url", ""),
        )
        if page_operator and not group["operator"]:
            group["operator"] = page_operator

        signals = extract_signal_quotes(p.get("body_text", ""))

        for s in signals:
            signal_types = s["types"]
            group["signals"].append({
                "types": signal_types,
                "text": s["quote_english"],
                "quote_original": s["quote_original"],
                "source": p["page_url"],
            })
            for n in infer_need(signal_types):
                group["needs"].add(n)

        for e in entities:
            if e["source_url"] != p["page_url"]:
                continue

            et = e["entity_type"]
            ename = e["entity_name"]

            # actor buckets
            if et in group["actors"]:
                group["actors"][et].add(ename)

            # budget owners
            if et in ["municipality", "regional_actor", "airport_operator", "mining_company", "military_branch"]:
                group["budget_owners"].add(ename)

            # operator enrichment from entities too
            enriched_operator = detect_operator(ename)
            if enriched_operator and not group["operator"]:
                group["operator"] = enriched_operator

    result = []

    for g in grouped.values():
        seen = set()
        unique_signals = []
        for s in g["signals"]:
            key = (s["quote_original"], s["source"])
            if key in seen:
                continue
            seen.add(key)
            unique_signals.append(s)

        g["signals"] = unique_signals[:12]
        g["signal_count"] = len(unique_signals)
        g["sources"] = sorted(list(g["sources"]))
        g["needs"] = sorted(list(g["needs"]))

        for k in g["actors"]:
            g["actors"][k] = sorted(list(g["actors"][k]))

        g["budget_owners"] = sorted(list(g["budget_owners"]))

        if g["signal_count"] > 0:
            result.append(g)

    result.sort(key=lambda x: x["signal_count"], reverse=True)
    return result
