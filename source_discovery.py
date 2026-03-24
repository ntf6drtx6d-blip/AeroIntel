from duckduckgo_search import DDGS

from config import MAX_SEARCH_RESULTS_PER_QUERY
from query_engine import generate_queries_for_country
from ai_engine import classify_source
from db import save_source, source_exists
from utils import extract_domain, dedupe_by_url


def discover_sources_for_country(country: str):
    queries = generate_queries_for_country(country)

    discovered = []
    logs = []

    for query in queries:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=MAX_SEARCH_RESULTS_PER_QUERY))
        except Exception as e:
            logs.append({
                "country": country,
                "query": query,
                "stage": "search",
                "error": str(e),
            })
            continue

        for r in results:
            title = r.get("title", "")
            url = r.get("href", "")
            snippet = r.get("body", "")

            if not url:
                continue

            if source_exists(url):
                continue

            domain = extract_domain(url)

            meta = classify_source(
                country=country,
                query=query,
                title=title,
                url=url,
                snippet=snippet,
            )

            record = {
                "country": country,
                "query": query,
                "title": title,
                "url": url,
                "domain": domain,
                "source_type": meta.get("source_type", "other"),
                "relevance_score": int(meta.get("relevance_score", 0) or 0),
                "rationale": meta.get("rationale", ""),
            }

            discovered.append(record)

    discovered = dedupe_by_url(discovered)

    for item in discovered:
        save_source(item)

    return discovered, logs
