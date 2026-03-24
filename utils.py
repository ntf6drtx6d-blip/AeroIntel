def normalize_airport(name):
    if not name:
        return "Unknown"

    name = name.lower()

    remove_words = [
        "airport",
        "international",
        "aeropuerto",
        "aeroport"
    ]

    for word in remove_words:
        name = name.replace(word, "")

    return name.strip().title()
