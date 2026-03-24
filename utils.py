from urllib.parse import urljoin, urlparse
import re


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def extract_domain(url: str) -> str:
    try:
        netloc = urlparse(url).netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return ""


def is_same_domain(url_a: str, url_b: str) -> bool:
    return extract_domain(url_a) == extract_domain(url_b)


def make_absolute_url(base_url: str, href: str) -> str:
    try:
        return urljoin(base_url, href)
    except Exception:
        return ""


def is_probably_html_url(url: str) -> bool:
    lowered = url.lower()
    blocked_suffixes = [
        ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg",
        ".zip", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
        ".mp4", ".mp3"
    ]
    return not any(lowered.endswith(s) for s in blocked_suffixes)


def score_page(title: str, url: str, body_text: str, relevant_keywords: list[str], negative_keywords: list[str]):
    haystack = " ".join([title or "", url or "", body_text or ""]).lower()

    score = 0
    matched_positive = []
    matched_negative = []

    for kw in relevant_keywords:
        if kw.lower() in haystack:
            score += 12
            matched_positive.append(kw)

    for kw in negative_keywords:
        if kw.lower() in haystack:
            score -= 20
            matched_negative.append(kw)

    if "/airport" in (url or "").lower() or "/airports" in (url or "").lower():
        score += 10
    if "/aerodrome" in (url or "").lower():
        score += 10
    if "/procurement" in (url or "").lower() or "/tender" in (url or "").lower():
        score += 10
    if "/projects" in (url or "").lower():
        score += 8

    score = max(0, min(100, score))

    if matched_positive:
        reason = f"Positive matches: {', '.join(matched_positive[:6])}"
    elif matched_negative:
        reason = f"Negative matches: {', '.join(matched_negative[:6])}"
    else:
        reason = "No clear airport-project keywords found"

    return score, reason
