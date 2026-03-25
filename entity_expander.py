import re
from utils import normalize_whitespace


ENTITY_PATTERNS = {
    "municipality": [
        r"\bPrefeitura de [A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ][A-Za-zÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇáàâãéèêíìîóòôõúùûç\- ]+",
        r"\bMunicipality of [A-Z][A-Za-z\- ]+",
        r"\bMunicípio de [A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ][A-Za-zÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇáàâãéèêíìîóòôõúùûç\- ]+",
        r"\bAlcaldía de [A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ\- ]+",
        r"\bCity of [A-Z][A-Za-z\- ]+",
        r"\bShire of [A-Z][A-Za-z\- ]+",
        r"\bCouncil of [A-Z][A-Za-z\- ]+",
    ],
    "airport_operator": [
        r"\bAirports of [A-Z][A-Za-z\- ]+",
        r"\b[A-Z][A-Za-z\- ]+ Airports\b",
        r"\b[A-Z][A-Za-z\- ]+ Airport Authority\b",
        r"\b[A-Z][A-Za-z\- ]+ Concession\b",
        r"\bConcession[a-z]* [A-Z][A-Za-z\- ]+",
    ],
    "mining_company": [
        r"\bVale\b",
        r"\bBHP\b",
        r"\bRio Tinto\b",
        r"\bAnglo American\b",
        r"\bGlencore\b",
        r"\bNewmont\b",
        r"\bBarrick\b",
        r"\b[A-Z][A-Za-z&\- ]+ Mining\b",
        r"\b[A-Z][A-Za-z&\- ]+ Minerals\b",
    ],
    "regional_actor": [
        r"\bState of [A-Z][A-Za-z\- ]+",
        r"\bProvince of [A-Z][A-Za-z\- ]+",
        r"\bDepartment of [A-Z][A-Za-z\- ]+",
        r"\bSecretaria de [A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ][A-Za-zÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇáàâãéèêíìîóòôõúùûç\- ]+",
    ],
    "military_branch": [
        r"\bAir Force\b",
        r"\bNavy\b",
        r"\bArmy\b",
        r"\bDefence\b",
        r"\bDefense\b",
        r"\bSpecial Operations\b",
        r"\bNaval Air Station\b",
    ],
}

BAD_ENTITY_WORDS = [
    "telefone", "phone", "gestor", "email", "menu", "careers",
    "newsroom", "cookie"
]


def extract_entities(body_text: str):
    text = normalize_whitespace(body_text)
    if not text:
        return []

    found = []

    for entity_type, patterns in ENTITY_PATTERNS.items():
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for m in matches:
                name = normalize_whitespace(m)
                lowered = name.lower()

                if len(name) < 4:
                    continue
                if len(name.split()) > 10:
                    continue
                if any(bad in lowered for bad in BAD_ENTITY_WORDS):
                    continue

                found.append({
                    "entity_name": name,
                    "entity_type": entity_type,
                    "rationale": f"Matched pattern for {entity_type}",
                })

    dedup = {}
    for item in found:
        dedup[(item["entity_name"], item["entity_type"])] = item

    return list(dedup.values())
