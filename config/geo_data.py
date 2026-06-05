"""
Dati geografici consolidati.

LOGICA GEOGRAFICA:
- Trapani e provincia → SEMPRE OK (in presenza)
- Palermo città → OK (se ne vale la pena)
- Smart working/remoto → SEMPRE OK (qualsiasi città)
- Altre città siciliane (Catania, Messina...) → SOLO se offre vitto+alloggio
- Altre regioni italiane → ESCLUSE (a meno che non sia remoto)
"""

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
# COMUNI AREA PALERMO (accettati in presenza)
# ============================================================
PALERMO_TOWNS: list[str] = [
    "palermo", "bagheria", "monreale", "carini",
    "partinico", "termini imerese",
]

# ============================================================
# CITTÀ SICILIANE ACCETTATE (Trapani + Palermo)
# ============================================================
SICILIA_ACCETTATE: list[str] = TRAPANI_TOWNS + PALERMO_TOWNS

# ============================================================
# CITTÀ SICILIANE NON ACCETTATE (troppo lontane, solo con vitto/alloggio)
# ============================================================
SICILIA_ALTRE_CITTA: list[str] = [
    "catania", "messina", "siracusa", "ragusa",
    "enna", "caltanissetta", "agrigento",
    "modica", "noto", "taormina", "milazzo", "acireale",
    "gela", "vittoria", "comiso", "caltagirone",
    "piazza armerina", "augusta", "lentini",
]

# Mantenuta per compatibilità — ora include TUTTE le città siciliane
SICILIA_CITIES: list[str] = [
    "palermo", "catania", "messina", "siracusa", "ragusa",
    "enna", "caltanissetta", "agrigento", "trapani",
    "sicilia", "sicily",
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
# KEYWORD VITTO E ALLOGGIO (per accettare città lontane)
# ============================================================
VITTO_ALLOGGIO_KEYWORDS: list[str] = [
    "vitto e alloggio", "vitto alloggio", "alloggio incluso",
    "alloggio fornito", "alloggio gratuito", "con alloggio",
    "con vitto", "residenza inclusa", "posto letto",
    "accommodation", "housing provided", "dormitorio",
]

# ============================================================
# KEYWORD LAVORO DA REMOTO / SMART WORKING
# ============================================================
SMART_WORKING_KEYWORDS: list[str] = [
    "smart working", "remoto", "remote", "da remoto",
    "lavoro da casa", "telelavoro", "full remote",
    "100% remote", "lavoro agile",
]

# Mantenuta per compatibilità
LOCALITY_KEYWORDS: dict[str, list[str]] = {
    "trapani": TRAPANI_TOWNS,
    "sicilia": SICILIA_CITIES,
    "palermo": PALERMO_TOWNS,
}
