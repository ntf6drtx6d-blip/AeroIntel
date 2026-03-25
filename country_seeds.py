from operator_sources import OPERATOR_SOURCES

BASE_COUNTRY_SEEDS = {
    "Brazil": [
        {"name": "ANAC Brazil EN", "type": "caa", "url": "https://www.gov.br/anac/en"},
        {"name": "ANAC Brazil PT", "type": "caa", "url": "https://www.gov.br/anac/pt-br"},
        {"name": "Infraero", "type": "airport_operator", "url": "https://www4.infraero.gov.br/"},
        {"name": "Ministry of Ports and Airports", "type": "ministry", "url": "https://www.gov.br/portos-e-aeroportos/pt-br"},
    ],
    "Thailand": [
        {"name": "CAAT", "type": "caa", "url": "https://www.caat.or.th/en/front-page/"},
        {"name": "Airports of Thailand", "type": "airport_operator", "url": "https://www.airportthai.co.th/en/"},
        {"name": "Ministry of Transport Thailand", "type": "ministry", "url": "https://www.mot.go.th/"},
    ],
    "Colombia": [
        {"name": "Aerocivil", "type": "caa", "url": "https://www.aerocivil.gov.co/"},
        {"name": "Ministry of Transport Colombia", "type": "ministry", "url": "https://www.mintransporte.gov.co/"},
        {"name": "ANI Colombia", "type": "infrastructure_agency", "url": "https://www.ani.gov.co/"},
    ],
    "Mexico": [
        {"name": "AFAC", "type": "caa", "url": "https://www.gob.mx/afac"},
        {"name": "SICT Mexico", "type": "ministry", "url": "https://www.gob.mx/sct"},
        {"name": "ASA Mexico", "type": "airport_operator", "url": "https://www.asa.gob.mx/"},
    ],
    "Australia": [
        {"name": "CASA", "type": "caa", "url": "https://www.casa.gov.au/"},
        {"name": "Department of Infrastructure Australia", "type": "ministry", "url": "https://www.infrastructure.gov.au/"},
        {"name": "Airservices Australia", "type": "aviation_service_provider", "url": "https://www.airservicesaustralia.com/"},
    ],
    "Jordan": [
        {"name": "CARC Jordan", "type": "caa", "url": "https://carc.gov.jo/en"},
        {"name": "Jordan Airports Company", "type": "airport_operator", "url": "https://www.jac.com.jo/"},
        {"name": "Ministry of Transport Jordan", "type": "ministry", "url": "https://mot.gov.jo/En"},
    ],
}


def _merge_seeds():
    merged = {}
    for country, seeds in BASE_COUNTRY_SEEDS.items():
        merged[country] = list(seeds) + list(OPERATOR_SOURCES.get(country, []))
    return merged


COUNTRY_SEEDS = _merge_seeds()
