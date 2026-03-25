from urllib.parse import urljoin, urlparse, urlunparse
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


def normalize_url(url: str) -> str:
    try:
        parsed = urlparse(url)
        cleaned = parsed._replace(fragment="")
        return urlunparse(cleaned)
    except Exception:
        return url


def looks_like_junk_url(url: str) -> bool:
    if not url:
        return True

    lowered = url.lower()
    junk_parts = [
        "#",
        "search?",
        "/search",
        "/contact",
        "/about",
        "/offices",
        "/departments",
        "/transparency",
        "/service_channels",
        "/login",
        "/signin",
        "/signup",
        "empregados",
        "portal-footer",
        "main-navigation",
        "wrapper",
        "govbr-busca-input",
        "privacy",
        "cookies",
        "faq",
    ]
    return any(part in lowered for part in junk_parts)


def split_sentences(text: str):
    if not text:
        return []
    parts = re.split(r"(?<=[\.\!\?])\s+", text)
    return [normalize_whitespace(p) for p in parts if normalize_whitespace(p)]
