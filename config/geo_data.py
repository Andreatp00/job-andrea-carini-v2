"""
Dati geografici consolidati.

Contiene tutte le liste di località, comuni, province e regioni
usate per il filtraggio geografico degli annunci, più le keyword
per il lavoro da remoto.
"""

# ============================================================
# KEYWORD LOCALITÀ — dal config.py originale (righe 362-366)
# ============================================================
LOCALITY_KEYWORDS: dict[str, list[str]] = {
    "trapani": [
        "trapani", "valderice", "paceco", "erice", "custonaci",
        "san vito", "alcamo", "marsala", "mazara", "castelvetrano",
    ],
    "sicilia": [
        "sicilia", "sicily", "catania", "messina", "siracusa",
        "ragusa", "enna", "caltanissetta", "agrigento",
    ],
    "palermo": [
        "palermo", "bagheria", "monreale", "carini",
        "partinico", "termini imerese",
    ],
}

# ============================================================
# COMUNI PROVINCIA DI TRAPANI — lista completa
# ============================================================
TRAPANI_TOWNS: list[str] = [
    "trapani", "valderice", "paceco", "erice", "custonaci",
    "san vito lo capo", "alcamo", "marsala", "mazara del vallo",
    "mazara", "castelvetrano", "castellammare del golfo", "favignana",
    "pantelleria", "calatafimi", "gibellina", "salemi", "vita",
    "buseto palizzolo", "campobello di mazara",
]

# ============================================================
# PRINCIPALI CITTÀ SICILIANE (capoluoghi + isola)
# ============================================================
SICILIA_CITIES: list[str] = [
    "palermo", "catania", "messina", "siracusa", "ragusa",
    "enna", "caltanissetta", "agrigento", "trapani",
    "sicilia", "sicily",
]

# ============================================================
# COMUNI AREA PALERMO
# ============================================================
PALERMO_TOWNS: list[str] = [
    "palermo", "bagheria", "monreale", "carini",
    "partinico", "termini imerese",
]

# ============================================================
# REGIONI ITALIANE NON SICILIANE (per filtro is_wrong_region)
# ============================================================
WRONG_REGIONS: list[str] = [
    "lombardia", "veneto", "piemonte", "emilia", "toscana",
    "lazio", "campania", "puglia", "calabria", "sardegna",
    "liguria", "friuli", "trentino", "marche", "umbria",
    "abruzzo", "molise", "basilicata", "valle d'aosta",
]

# ============================================================
# KEYWORD LAVORO DA REMOTO / SMART WORKING
# ============================================================
SMART_WORKING_KEYWORDS: list[str] = [
    "smart working", "remoto", "remote", "da remoto",
    "lavoro da casa", "telelavoro", "full remote",
    "100% remote", "lavoro agile",
]
