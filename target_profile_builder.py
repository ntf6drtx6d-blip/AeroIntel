import re
from db import save_target_profile
from utils import normalize_whitespace
from contact_extractor import extract_contacts


def extract_asset_name(title: str, text: str):
    patterns = [
        r"Aeroporto [A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-zÁÉÍÓÚÂÊÔÃÕÇáéíóúâêôãõç\- ]+",
        r"Aeródromo [A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-zÁÉÍÓÚÂÊÔÃÕÇáéíóúâêôãõç\- ]+",
        r"Airport [A-Z][A-Za-z\- ]+",
        r"Airstrip [A-Z][A-Za-z\- ]+",
        r"Base [A-Z][A-Za-z\- ]+",
        r"Naval Air Station [A-Z][A-Za-z\- ]+",
    ]

    hay = f"{title} {text}"

    for p in patterns:
        match = re.search(p, hay)
        if match:
            return normalize_whitespace(match.group())

    return None


def infer_asset_type(page_category: str, body_text: str):
    lowered = (body_text or "").lower()

    if page_category == "military_base_page":
        return "military air base"
    if page_category == "mining_airstrip_page":
        return "mining airstrip"
    if page_category == "airstrip_page":
        return "airstrip"
    if "naval air station" in lowered:
        return "naval air station"
    if "air force" in lowered:
        return "air force base"
    if "army aviation" in lowered:
        return "army aviation base"
    if page_category == "airport_page":
        return "airport"

    return "unknown"


def build_target_profiles_from_pages(pages, entities, country):
    profiles = []

    for p in pages:
        if p["status"] != "approved":
            continue

        if p["page_category"] not in [
            "airport_page",
            "airstrip_page",
            "military_base_page",
            "mining_airstrip_page",
            "projects_page",
            "municipality_airport_page",
            "operator_page",
            "airport_registry",
        ]:
            continue

        title = p["page_title"]
        reason = p.get("reason", "")
        body_text = p.get("body_text", "")

        asset_name = extract_asset_name(title, body_text or reason or title)
        if not asset_name:
            asset_name = title

        asset_type = infer_asset_type(p["page_category"], body_text or reason or title)

        municipality = None
        regional = None
        mining = None
        operator = None
        military_branch = None

        for e in entities:
            if e["source_url"] != p["page_url"]:
                continue

            if e["entity_type"] == "municipality":
                municipality = e["entity_name"]

            if e["entity_type"] == "regional_actor":
                regional = e["entity_name"]

            if e["entity_type"] == "mining_company":
                mining = e["entity_name"]

            if e["entity_type"] == "airport_operator":
                operator = e["entity_name"]

            if e["entity_type"] == "military_branch":
                military_branch = e["entity_name"]

        contacts = extract_contacts(body_text or "")

        profile = {
            "asset_name": asset_name,
            "country": country,
            "asset_type": asset_type,
            "owner": municipality or regional,
            "operator": operator,
            "regional_actor": regional,
            "mining_company": mining,
            "military_branch": military_branch,
            "official_contact_email": ", ".join(contacts["emails"]) if contacts["emails"] else None,
            "official_contact_phone": ", ".join(contacts["phones"]) if contacts["phones"] else None,
            "contact_roles": ", ".join(contacts["roles"]) if contacts["roles"] else None,
            "source_url": p["page_url"],
            "confidence": 60,
        }

        save_target_profile(profile)
        profiles.append(profile)

    return profiles
