import requests
from bs4 import BeautifulSoup

from config import REQUEST_TIMEOUT_SECONDS, MAX_LINKS_PER_SEED_PAGE, MAX_PAGES_PER_DOMAIN, RELEVANT_KEYWORDS, NEGATIVE_KEYWORDS
from utils import (
    extract_domain,
    is_same_domain,
    make_absolute_url,
    is_probably_html_url,
    normalize_whitespace,
    score_page,
)
from db import save_page, page_exists
from country_seeds import COUNTRY_SEEDS


HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AeroIntel/1.0; +https://example.com)"
}


def fetch_html(url: str):
    response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    content_type = response.headers.get("Content-Type", "").lower()

    if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
        return None

    return response.text


def parse_links(base_url: str, html: str):
    soup = BeautifulSoup(html, "html.parser")
    links = []

    for a in soup.find_all("a", href=True):
        href = a.get("href", "").strip()
        text = normalize_whitespace(a.get_text(" ", strip=True))

        if not href:
            continue

        absolute = make_absolute_url(base_url, href)
        if not absolute.startswith("http"):
            continue
        if not is_probably_html_url(absolute):
            continue
        if not is_same_domain(base_url, absolute):
            continue

        links.append({
            "text": text,
            "url": absolute,
        })

    dedup = {}
    for item in links:
        dedup[item["url"]] = item

    return list(dedup.values())[:MAX_LINKS_PER_SEED_PAGE]


def extract_page_title_and_text(html: str):
    soup = BeautifulSoup(html, "html.parser")

    title = ""
    if soup.title and soup.title.string:
        title = normalize_whitespace(soup.title.string)

    body_text = normalize_whitespace(soup.get_text(" ", strip=True))
    if len(body_text) > 4000:
        body_text = body_text[:4000]

    return title, body_text


def discover_pages_for_country(country: str):
    seeds = COUNTRY_SEEDS.get(country, [])

    discovered = []
    logs = []

    for seed in seeds:
        seed_name = seed["name"]
        seed_type = seed["type"]
        seed_url = seed["url"]

        try:
            html = fetch_html(seed_url)
            if not html:
                logs.append({
                    "country": country,
                    "seed": seed_name,
                    "stage": "fetch_seed",
                    "error": "Seed is not HTML or returned empty content",
                    "url": seed_url,
                })
                continue
        except Exception as e:
            logs.append({
                "country": country,
                "seed": seed_name,
                "stage": "fetch_seed",
                "error": str(e),
                "url": seed_url,
            })
            continue

        try:
            links = parse_links(seed_url, html)
        except Exception as e:
            logs.append({
                "country": country,
                "seed": seed_name,
                "stage": "parse_links",
                "error": str(e),
                "url": seed_url,
            })
            continue

        checked = 0

        for link in links:
            if checked >= MAX_PAGES_PER_DOMAIN:
                break

            page_url = link["url"]
            if page_exists(page_url):
                continue

            try:
                page_html = fetch_html(page_url)
                if not page_html:
                    continue
            except Exception:
                continue

            try:
                page_title, body_text = extract_page_title_and_text(page_html)
                score, reason = score_page(
                    title=page_title or link["text"],
                    url=page_url,
                    body_text=body_text,
                    relevant_keywords=RELEVANT_KEYWORDS,
                    negative_keywords=NEGATIVE_KEYWORDS,
                )
            except Exception as e:
                logs.append({
                    "country": country,
                    "seed": seed_name,
                    "stage": "score_page",
                    "error": str(e),
                    "url": page_url,
                })
                continue

            record = {
                "country": country,
                "seed_name": seed_name,
                "seed_type": seed_type,
                "page_title": page_title or link["text"] or page_url,
                "page_url": page_url,
                "page_domain": extract_domain(page_url),
                "relevance_score": score,
                "reason": reason,
                "status": "new",
            }

            save_page(record)
            discovered.append(record)
            checked += 1

    return discovered, logs
