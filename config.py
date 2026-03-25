REQUEST_TIMEOUT_SECONDS = 20
MAX_LINKS_PER_SEED_PAGE = 150
MAX_PAGES_PER_DOMAIN = 40
MIN_RELEVANCE_SCORE = 25
AUTO_APPROVE_SCORE = 40

RELEVANT_KEYWORDS = [
    "airport",
    "airports",
    "aerodrome",
    "aerodromes",
    "aviation",
    "civil aviation",
    "runway",
    "runways",
    "airfield",
    "infrastructure",
    "modernization",
    "rehabilitation",
    "operations",
    "night operations",
    "safety",
    "master plan",
    "procurement",
    "tender",
    "projects",
    "project",
    "expansion",
    "operator",
    "operators",
    "regional airport",
    "municipal airport",
    "airport development",
    "airport upgrade",
    "concession",
    "concessions",
    "works",
    "obra",
    "obras",
    "pista",
    "licitacao",
    "licitación",
    "licitacoes",
    "airstrip",
    "aerodromo",
    "aeródromo",
    "air base",
    "naval air station",
    "army aviation",
    "defence",
    "defense",
    "military",
    "mine",
    "mining",
    "fifo",
    "logistics base",
]

NEGATIVE_KEYWORDS = [
    "tourism",
    "travel guide",
    "trip",
    "vacation",
    "hotel",
    "restaurant",
    "shopping",
    "retail",
    "visa",
    "tripadvisor",
    "booking",
    "wikipedia",
    "culture",
    "must visit",
    "contact",
    "about",
    "transparency",
    "search",
    "login",
    "employee",
    "press office",
    "service channels",
    "departments",
    "offices",
]

SIGNAL_PATTERNS = {
    "construction_works": [
        "obra", "obras", "construction", "works", "rehabilitation", "modernization", "ampliação", "expansion"
    ],
    "runway_signal": [
        "pista", "runway", "airfield lighting", "aerodrome lighting", "lighting", "balizamento"
    ],
    "concession_signal": [
        "concession", "concessão", "concessionaire", "privatization", "privatização"
    ],
    "budget_signal": [
        "investment", "investimento", "budget", "funding", "grant", "program", "programa"
    ],
    "municipality_signal": [
        "prefeitura", "município", "municipality", "council", "city of"
    ],
    "regional_authority_signal": [
        "secretaria", "department of", "state of", "province of", "infraestrutura"
    ],
    "mining_signal": [
        "vale", "mining", "mine", "mineracao", "mineração", "fifo"
    ],
    "military_signal": [
        "air force", "navy", "army", "defence", "defense", "special operations", "air base"
    ],
}
