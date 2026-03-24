def normalize_airport(name):
    if not name:
        return "Unknown"

    name = name.lower()

    remove_words = [
        "airport",
        "international",
        "aeropuerto",
        "aeroport",
        "airfield",
    ]

    for word in remove_words:
        name = name.replace(word, "")

    cleaned = " ".join(name.split()).strip()
    if not cleaned:
        return "Unknown"

    return cleaned.title()
