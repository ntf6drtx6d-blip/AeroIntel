import requests
from bs4 import BeautifulSoup

from config import REQUEST_TIMEOUT_SECONDS, MAX_LINKS_PER_SEED_PAGE, MAX_PAGES_PER_DOMAIN, MIN_RELEVANCE_SCORE
from utils import (
    extract_domain,
    is_same_domain,
    make_absolute_url,
    is_probably_html_url,
    normalize_whitespace,
    normalize_url,
    looks_like_junk_url,
)
from db import save_page, save_entity, page_exists
from country_seeds import COUNTRY_SEEDS
from page_ranker import score_page
from entity_expander import extract_entities


HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AeroIntel/1.0)"
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

        absolute = normalize_url(make_absolute_url(base_url, href))
        if not absolute.startswith("http"):
            continue
        if not is_probably_html_url(absolute):
            continue

        # keep same-domain crawling for stability
        if not is_same_domain(base_url, absolute):
            continue

        if looks_like_junk_url(absolute):
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
    if len(body_text) > 10000:
        body_text = body_text[:10000]

    return title, body_text


def discover_pages_for_country(country: str, log_callback=None):
    seeds = COUNTRY_SEEDS.get(country, [])
    discovered = []
    logs = []
    discovered_entities = []

    def log(msg):
        logs.append(msg)
        if log_callback:
            log_callback(msg)

    for seed in seeds:
        seed_name = seed["name"]
        seed_type = seed["type"]
        seed_url = seed["url"]

        log(f"Fetching seed: {seed_name}")

        try:
            html = fetch_html(seed_url)
            if not html:
                log(f"Seed not HTML: {seed_url}")
                continue
        except Exception as e:
            log(f"Seed fetch failed: {seed_name} | {str(e)}")
            continue

        try:
            _, seed_body = extract_page_title_and_text(html)
            entities = extract_entities(seed_body)
            for ent in entities:
                ent_record = {
                    "country": country,
                    "source_url": seed_url,
                    "entity_name": ent["entity_name"],
                    "entity_type": ent["entity_type"],
                    "rationale": ent["rationale"],
                }
                save_entity(ent_record)
                discovered_entities.append(ent_record)
        except Exception:
            pass

        try:
            links = parse_links(seed_url, html)
        except Exception as e:
            log(f"Parse links failed: {seed_name} | {str(e)}")
            continue

        checked = 0

        for link in links:
            if checked >= MAX_PAGES_PER_DOMAIN:
                break

            page_url = link["url"]
            if page_exists(page_url):
                checked += 1
                continue

            try:
                page_html = fetch_html(page_url)
                if not page_html:
                    checked += 1
                    continue
            except Exception:
                checked += 1
                continue

            try:
                page_title, body_text = extract_page_title_and_text(page_html)
                score, reason, category = score_page(
                    title=page_title or link["text"],
                    url=page_url,
                    body_text=body_text,
                )
            except Exception as e:
                log(f"Score page failed: {page_url} | {str(e)}")
                checked += 1
                continue

            if score < MIN_RELEVANCE_SCORE:
                checked += 1
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
                "page_category": category,
                "status": "new",
                "body_text": body_text,
            }

            save_page(record)
            discovered.append(record)

            try:
                entities = extract_entities(body_text)
                for ent in entities:
                    ent_record = {
                        "country": country,
                        "source_url": page_url,
                        "entity_name": ent["entity_name"],
                        "entity_type": ent["entity_type"],
                        "rationale": ent["rationale"],
                    }
                    save_entity(ent_record)
                    discovered_entities.append(ent_record)
            except Exception:
                pass

            checked += 1

    return discovered, discovered_entities, logs
