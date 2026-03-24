from config import RELEVANT_KEYWORDS, NEGATIVE_KEYWORDS


POSITIVE_URL_HINTS = [
    "airport",
    "airports",
    "aerodrome",
    "aerodromo",
    "aerodromo",
    "airfield",
    "infrastructure",
    "project",
    "projects",
    "obra",
    "obras",
    "pista",
    "modern",
    "rehabilit",
    "procurement",
    "tender",
    "licit",
    "concession",
    "operator",
    "operators",
    "regional",
    "municipal",
    "safety",
    "night",
]

NEGATIVE_URL_HINTS = [
    "contact",
    "about",
    "search",
    "transparency",
    "departments",
    "offices",
    "service_channels",
    "login",
    "employee",
    "faq",
    "privacy",
    "cookies",
]


def classify_page_category(title: str, url: str, body_text: str) -> str:
    haystack = " ".join([title or "", url or "", body_text or ""]).lower()

    if any(x in haystack for x in ["licit", "tender", "procurement", "bid"]):
        return "procurement_page"
    if any(x in haystack for x in ["project", "projects", "obra", "obras", "modern", "rehabilit", "expansion"]):
        return "projects_page"
    if any(x in haystack for x in ["airport list", "airports", "aerodromes", "aerodromos", "aeródromos", "registry"]):
        return "airport_registry"
    if any(x in haystack for x in ["operator", "operators", "concession", "concessionaire"]):
        return "operator_page"
    if any(x in haystack for x in ["municipality", "municipal", "prefeitura", "alcaldía", "council"]):
        return "municipality_airport_page"
    if any(x in haystack for x in ["mining", "mine", "mineracao", "mineração", "logistics"]):
        return "mining_airstrip_related"
    if any(x in haystack for x in ["news", "noticias", "notícias", "media", "press"]):
        return "news_page"
    if any(x in haystack for x in ["contact", "about", "transparency", "search", "departments", "offices"]):
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
            score -= 25
            negatives.append(f"url:{hint}")

    category = classify_page_category(title, url, body_text)

    category_boosts = {
        "procurement_page": 35,
        "projects_page": 30,
        "airport_registry": 28,
        "operator_page": 22,
        "municipality_airport_page": 24,
        "mining_airstrip_related": 22,
        "news_page": 12,
        "other": 0,
        "junk": -50,
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
