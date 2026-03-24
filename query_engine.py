from config import MAX_QUERIES_PER_COUNTRY


COUNTRY_LANGUAGE_HINTS = {
    "Brazil": ["Portuguese", "English"],
    "Colombia": ["Spanish", "English"],
    "Mexico": ["Spanish", "English"],
    "Australia": ["English"],
    "Jordan": ["English", "Arabic"],
    "Thailand": ["English", "Thai"],
}


BASE_INTENTS = [
    "civil aviation authority airport planning",
    "airport operator regional airport",
    "ministry transport airport infrastructure",
    "municipality airport master plan",
    "airport modernization runway rehabilitation",
    "airport night operations safety upgrade",
    "airport consultant aviation infrastructure",
    "airport procurement infrastructure planning",
]


def generate_queries_for_country(country: str):
    langs = COUNTRY_LANGUAGE_HINTS.get(country, ["English"])
    queries = []

    for lang in langs:
        for intent in BASE_INTENTS:
            queries.append(f"{country} {intent} {lang}")

    return queries[:MAX_QUERIES_PER_COUNTRY]
