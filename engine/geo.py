import re
from utils.text import normalize_text
from utils.url import extract_domain
from config.geo_data import (
    TRAPANI_TOWNS, SICILIA_CITIES, PALERMO_TOWNS,
    SICILIA_ALTRE_CITTA, VITTO_ALLOGGIO_KEYWORDS,
    WRONG_REGIONS, SMART_WORKING_KEYWORDS
)

def infer_country_label(location: str, existing_label: str = "") -> str:
    label = normalize_text(existing_label)
    location_text = normalize_text(location).lower()
    if label:
        return label
    
    for loc_keyword in TRAPANI_TOWNS:
        if loc_keyword in location_text:
            return "Trapani"
    
    for loc_keyword in PALERMO_TOWNS:
        if loc_keyword in location_text:
            return "Palermo"
    
    # Altre città siciliane → etichettate come "Sicilia (altra)"
    for loc_keyword in SICILIA_ALTRE_CITTA:
        if loc_keyword in location_text:
            return "Sicilia (altra)"
    
    if any(kw in location_text for kw in ["sicilia", "sicily"]):
        return "Sicilia"
            
    if any(reg in location_text for reg in ["italia", "italy", "italiano", "nazionale"]):
        return "Italia"
    
    return "Italia"

def is_trapani_area(location: str) -> bool:
    """Verifica se la località è in provincia di Trapani."""
    loc = normalize_text(location).lower()
    return any(area in loc for area in TRAPANI_TOWNS)

def is_palermo_area(location: str) -> bool:
    """Verifica se la località è Palermo o provincia."""
    loc = normalize_text(location).lower()
    return any(area in loc for area in PALERMO_TOWNS)

def is_sicily_other(location: str) -> bool:
    """Verifica se la località è in un'altra città siciliana (non Trapani/Palermo)."""
    loc = normalize_text(location).lower()
    return any(area in loc for area in SICILIA_ALTRE_CITTA)

def is_sicily_area(location: str) -> bool:
    """Verifica se la località è in Sicilia (qualsiasi città)."""
    loc = normalize_text(location).lower()
    return any(area in loc for area in SICILIA_CITIES)

def has_vitto_alloggio(description: str, title: str) -> bool:
    """Verifica se l'annuncio offre vitto e alloggio."""
    text = f"{title} {description}".lower()
    return any(kw in text for kw in VITTO_ALLOGGIO_KEYWORDS)

def has_valid_training(description: str, title: str) -> bool:
    """Verifica se l'annuncio offre formazione valida o non richiede esperienza."""
    text = f"{title} {description}".lower()
    training_keywords = [
        "formazione gratuita", "corso gratuito", "academy",
        "tirocinio", "stage", "formazione retribuita",
        "si offre formazione", "formazione iniziale", "percorso formativo",
        "senza esperienza", "prima esperienza", "nessuna esperienza",
        "neo diplomati", "neodiplomati", "apprendistato"
    ]
    return any(kw in text for kw in training_keywords)

def is_wrong_region(location: str) -> bool:
    """Rileva se la località è palesemente in un'altra regione."""
    loc = normalize_text(location).lower()
    if any(reg in loc for reg in WRONG_REGIONS):
        if not is_trapani_area(location) and not is_sicily_area(location):
            return True
    return False

def is_smart_working(location: str, description: str, title: str) -> bool:
    """Verifica se l'annuncio è per smart working / remoto."""
    text = f"{location} {description} {title}".lower()
    return any(kw in text for kw in SMART_WORKING_KEYWORDS)

def has_strict_wrong_region_in_text(title: str, description: str) -> bool:
    """Controlla se il testo indica esplicitamente una regione sbagliata come sede prevalente."""
    text = f"{title} {description}".lower()
    
    if is_smart_working("", description, title):
        return False
        
    title_lower = title.lower()
    strict_wrong = ["milano", "roma", "torino", "bologna", "firenze", "venezia", "lombardia", "veneto", "emilia"]
    for w in strict_wrong:
        if re.search(rf"\b{w}\b", title_lower):
            return True
            
    if re.search(r"(sede di lavoro|sede|lavoro|location)[:\-\s]*(milano|roma|torino|bologna|firenze|venezia|lombardia|veneto|emilia|padova|verona|brescia|bergamo)", text):
        return True
        
    if re.search(r"(disponibilità al trasferimento|trasferimento richiesto a)\s*(milano|roma|torino|bologna|firenze|venezia|lombardia|veneto|emilia|nord italia)", text):
        return True
        
    return False

def is_italy_only_location(location: str) -> bool:
    """Verifica se la location è generica Italia senza specifiche regionali."""
    loc = normalize_text(location).lower()
    italy_keywords = ["italia", "italy", "nazionale", "tutta italia"]
    return any(kw in loc for kw in italy_keywords)

def is_allowed_location(location: str, search_country: str = "", description: str = "", title: str = "") -> bool:
    """
    Determina se una località è permessa per questo profilo.
    
    REGOLE:
    - Trapani e provincia → SEMPRE OK
    - Palermo città → OK
    - Smart Working/Remoto → SEMPRE OK
    - Altre città siciliane (Catania, Messina...) → SOLO con vitto e alloggio
    - Italia generica → OK solo se smart working
    - Altre regioni → ESCLUSE
    """
    # Trapani e provincia → sempre OK
    if is_trapani_area(location):
        return True
    
    # Palermo → OK
    if is_palermo_area(location):
        return True
    
    # Smart working → sempre OK indipendentemente dalla località
    if is_smart_working(location, description, title):
        return True
        
    # Formazione valida → OK ovunque in Italia
    if has_valid_training(description, title):
        return True
    
    # Altre città siciliane → SOLO con vitto e alloggio o formazione
    if is_sicily_other(location):
        if has_vitto_alloggio(description, title) or has_valid_training(description, title):
            return True
        return False
    
    # Italia generica → accettata (verrà filtrata dopo se non è smart working o formazione)
    if is_italy_only_location(location):
        return True
    
    # Regione sbagliata → esclusa
    if is_wrong_region(location):
        return False
    
    # Default: accetta (potrebbe essere smart working non rilevato)
    return True

def has_wrong_location_in_text(title: str, description: str, location: str) -> bool:
    """
    Verifica se il testo dell'annuncio indica una località diversa da quella dichiarata.
    """
    full_text = f"{title} {description}".lower()
    declared_location = location.lower()
    
    if any(keyword in declared_location for keyword in ["trapani", "sicilia", "smart", "remoto"]):
        for city in WRONG_REGIONS:
            if city in full_text and city not in declared_location:
                return True
    
    return False

def get_location_from_url(url: str) -> str:
    if not url:
        return ""
    
    url_lower = url.lower()
    
    city_patterns = [
        ("milano", "Milano"), ("roma", "Roma"), ("torino", "Torino"),
        ("bologna", "Bologna"), ("firenze", "Firenze"), ("napoli", "Napoli"),
        ("bari", "Bari"), ("venezia", "Venezia"), ("verona", "Verona"),
        ("genova", "Genova"), ("palermo", "Palermo"), ("catania", "Catania"),
        ("trapani", "Trapani"), ("marsala", "Marsala"), ("alcamo", "Alcamo"),
        ("mazara", "Mazara"), ("erice", "Erice"),
    ]
    
    for pattern, city in city_patterns:
        if pattern in url_lower:
            return city
    
    for region in WRONG_REGIONS:
        if region in url_lower:
            return region.title()
    
    return ""

def extract_location_from_linkedin_url(url: str) -> str:
    if not url or "linkedin.com/jobs/view/" not in url.lower():
        return ""
    
    url_lower = url.lower()
    
    if "location=" in url_lower:
        match = re.search(r'location=([^&]+)', url_lower)
        if match:
            loc = match.group(1).replace("+", " ").replace("%20", " ").replace("%2c", ",")
            return normalize_text(loc)
    
    domain = extract_domain(url)
    if any(city in domain for city in TRAPANI_TOWNS + SICILIA_CITIES):
        return "Trapani"
    elif any(city in domain for city in WRONG_REGIONS):
        return domain.split(".")[0].title()
    
    return ""
