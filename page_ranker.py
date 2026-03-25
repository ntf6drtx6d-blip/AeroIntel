from config import RELEVANT_KEYWORDS, NEGATIVE_KEYWORDS


POSITIVE_URL_HINTS = [
    "airport", "airports", "aerodrome", "aerodromo", "aeródromo",
    "airfield", "airstrip", "base", "military", "infrastructure",
    "project", "projects", "obra", "obras", "pista", "modern",
    "rehabilit", "procurement", "tender", "licit", "concession",
    "operator", "operators", "regional", "municipal", "safety",
    "night", "mine", "mining", "portfolio", "our-airports", "investments"
]

NEGATIVE_URL_HINTS = [
    "contact", "about", "search", "transparency", "departments", "offices",
    "service_channels", "login", "employee", "faq", "privacy", "cookies",
    "join-us", "careers", "jobs", "working-at", "leadership", "sustainable",
    "sustainability", "noise", "community", "equality", "training"
]


def classify_page_category(title: str, url: str, body_text: str) -> str:
    haystack = " ".join([title or "", url or "", body_text or ""]).lower()
    lowered_url = (url or "").lower()

    if "aeroporto-" in lowered_url or "aerodromo-" in lowered_url or "airport-" in lowered_url:
        return "airport_page"
    if "airstrip" in haystack:
        return "airstrip_page"
    if any(x in haystack for x in ["air base", "naval air station", "army aviation", "defence", "defense", "military base"]):
        return "military_base_page"
    if any(x in haystack for x in ["mining", "mine", "fifo", "site aviation"]):
        return "mining_airstrip_page"
    if any(x in haystack for x in ["licit", "tender", "procurement", "bid"]):
        return "procurement_page"
    if any(x in haystack for x in ["project", "projects", "obra", "obras", "modern", "rehabilit", "expansion"]):
        return "projects_page"
    if any(x in haystack for x in ["airport list", "airports", "aerodromes", "aerodromos", "aeródromos", "registry", "portfolio", "our airports"]):
        return "airport_registry"
    if any(x in haystack for x in ["operator", "operators", "concession", "concessionaire"]):
        return "operator_page"
    if any(x in haystack for x in ["municipality", "municipal", "prefeitura", "alcaldía", "council"]):
        return "municipality_airport_page"
    if any(x in haystack for x in ["news", "noticias", "notícias", "media", "press"]):
        return "news_page"
    if any(x in haystack for x in ["contact", "about", "transparency", "search", "departments", "offices", "careers", "join us", "working at", "leadership", "sustainable"]):
        return "junk"

    return "other"


def score_page(title: str, url: str, body_text: str):
    haystack = " ".join([title or "", url or "", body_text or ""]).lower()
    score = 0
    positives = []
    negatives = []

    for kw in RELEVANT_KEYWORDS:
        if kw.lower() in haystack:
            score += 5
            positives.append(kw)

    for kw in NEGATIVE_KEYWORDS:
        if kw.lower() in haystack:
            score -= 12
            negatives.append(kw)

    lowered_url = (url or "").lower()

    for hint in POSITIVE_URL_HINTS:
        if hint in lowered_url:
            score += 10
            positives.append(f"url:{hint}")

    for hint in NEGATIVE_URL_HINTS:
        if hint in lowered_url:
            score -= 30
            negatives.append(f"url:{hint}")

    category = classify_page_category(title, url, body_text)

    category_boosts = {
        "airport_page": 35,
        "airstrip_page": 30,
        "military_base_page": 34,
        "mining_airstrip_page": 34,
        "procurement_page": 25,
        "projects_page": 28,
        "airport_registry": 24,
        "operator_page": 18,
        "municipality_airport_page": 24,
        "news_page": 8,
        "other": 0,
        "junk": -60,
    }

    score += category_boosts.get(category, 0)
    score = max(0, min(100, score))

    if positives:
        reason = f"Positive matches: {', '.join(positives[:8])}"
    elif negatives:
        reason = f"Negative matches: {', '.join(negatives[:8])}"
    else:
        reason = "No strong signals"

    return score, reason, category
