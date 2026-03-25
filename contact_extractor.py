import re
from utils import normalize_whitespace


EMAIL_PATTERN = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
PHONE_PATTERN = r"(\+?\d[\d\-\s\(\)]{7,}\d)"

ROLE_KEYWORDS = [
    "manager",
    "operations",
    "infrastructure",
    "engineering",
    "procurement",
    "commander",
    "logistics",
    "secretary",
    "director",
    "administrator",
    "gestor",
    "compras",
    "obras",
]


def extract_contacts(body_text: str):
    text = normalize_whitespace(body_text)
    if not text:
        return {
            "emails": [],
            "phones": [],
            "roles": [],
        }

    emails = sorted(list(set(re.findall(EMAIL_PATTERN, text, flags=re.IGNORECASE))))

    phones = []
    for match in re.findall(PHONE_PATTERN, text):
        cleaned = normalize_whitespace(match)
        if len(cleaned) >= 8:
            phones.append(cleaned)
    phones = sorted(list(set(phones)))

    roles = []
    lowered = text.lower()
    for role in ROLE_KEYWORDS:
        if role in lowered:
            roles.append(role)

    return {
        "emails": emails[:10],
        "phones": phones[:10],
        "roles": sorted(list(set(roles)))[:10],
    }
