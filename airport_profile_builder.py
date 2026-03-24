import re
from db import save_airport_profile
from utils import normalize_whitespace


def extract_airport_name(title: str, text: str):
    patterns = [
        r"Aeroporto [A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-zÁÉÍÓÚÂÊÔÃÕÇáéíóúâêôãõç\- ]+",
        r"Aeródromo [A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-zÁÉÍÓÚÂÊÔÃÕÇáéíóúâêôãõç\- ]+",
        r"Airport [A-Z][A-Za-z\- ]+",
    ]

    hay = f"{title} {text}"

    for p in patterns:
        match = re.search(p, hay)
        if match:
            return normalize_whitespace(match.group())

    return None


def build_profiles_from_pages(pages, entities, country):
    profiles = []

    for p in pages:
        if p["status"] != "approved":
            continue

        if p["page_category"] not in [
            "airport_registry",
            "projects_page",
            "municipality_airport_page",
            "operator_page",
        ]:
            continue

        airport_name = extract_airport_name(
            p["page_title"],
            p.get("reason", "")
        )

        if not airport_name:
            continue

        municipality = None
        regional = None
        mining = None

        for e in entities:
            if e["source_url"] != p["page_url"]:
                continue

            if e["entity_type"] == "municipality":
                municipality = e["entity_name"]

            if e["entity_type"] == "regional_actor":
                regional = e["entity_name"]

            if e["entity_type"] == "mining_company":
                mining = e["entity_name"]

        profile = {
            "airport_name": airport_name,
            "country": country,
            "source_url": p["page_url"],
            "municipality": municipality,
            "regional_actor": regional,
            "mining_company": mining,
            "confidence": 60,
        }

        save_airport_profile(profile)
        profiles.append(profile)

    return profiles
