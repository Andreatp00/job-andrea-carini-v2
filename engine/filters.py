import re
from utils.text import contains_any
from config import EXCLUDE_KEYWORDS_TITLE, EXCLUDE_KEYWORDS_TEXT, IT_KEYWORDS_TITLE
from engine.geo import has_valid_training

def is_actual_job_posting(url: str, title: str) -> bool:
    """
    Verifica se un URL è un annuncio di lavoro reale e non una pagina generica.
    Esclude risultati di ricerca, home page, pagine di login, ecc.
    """
    url_lower = url.lower()
    title_lower = title.lower()
    
    if any(x in url_lower for x in [
        "/search", "/cerca", "/ricerca", "?q=", "?s=", "&search=",
        "/offerte-lavoro/", "/cerca-lavoro/", "/trova-lavoro/"
    ]):
        return False
    
    if any(x in url_lower for x in [
        "/login", "/registrazione", "/accedi", "/signin", "/signup",
        "/area-riservata", "/my-account"
    ]):
        return False
    
    if url_lower.endswith("/") or url_lower.endswith(".it") or url_lower.endswith(".com"):
        return False
    
    job_keywords = ["annuncio", "offerta", "job", "lavoro", "posizione", "dettaglio", "bando", "concorso"]
    if any(kw in url_lower for kw in job_keywords):
        return True
    
    if any(kw in title_lower for kw in [
        "impiegato", "addetto", "back office", "amministrativo", "contabilità",
        "segreteria", "ragioneria", "stage", "tirocinio", "praticante",
        "call center", "data entry", "customer service", "operatore",
        "assistente", "smart working", "remoto", "social media",
    ]):
        return True
    
    return True

def is_english_text(text: str, threshold: float = 0.7) -> bool:
    """Verifica se un testo è prevalentemente in inglese."""
    if not text or len(text.strip()) < 50:
        return False
    
    text_lower = text.lower()
    words = re.findall(r'\b\w+\b', text_lower)
    
    if not words or len(words) < 10:
        return False
    
    english_words = {
        "the", "and", "to", "of", "a", "in", "is", "it", "that", "for",
        "you", "was", "on", "are", "with", "as", "at", "be", "this",
        "have", "from", "or", "an", "by", "not", "but", "they", "which",
        "their", "we", "if", "will", "what", "so", "can", "when", "there",
        "job", "position", "company", "requirements", "skills", "experience",
        "application", "send", "your", "resume", "cv", "apply", "now",
        "remote", "working", "office", "administrative", "accounting",
        "customer", "service", "support", "assistant", "clerk", "role",
        "responsibilities", "duties", "qualifications", "benefits", "salary"
    }
    
    italian_words = {
        "il", "di", "e", "a", "in", "la", "che", "è", "non", "un", "con",
        "per", "una", "son", "ma", "io", "si", "più", "del", "lo", "come",
        "lavoro", "ufficio", "amministrativo", "contabilità", "segreteria",
        "impiegato", "addetto", "azienda", "cercasi", "offerta", "annuncio",
        "sede", "reparto", "part", "time", "full", "contratto", "esperienza",
        "diploma", "ragioneria", "back", "office", "stagista", "tirocinio",
        "remoto", "smart", "working", "call", "center", "operatore",
    }
    
    english_count = sum(1 for word in words if word in english_words)
    italian_count = sum(1 for word in words if word in italian_words)
    total = len(words)
    
    # Se c'è abbastanza italiano, NON è testo inglese
    if total > 10 and (italian_count / total) > 0.15:
        return False
    
    if total > 10 and (italian_count / total) < 0.05 and (english_count / total) > 0.4:
        return True
    
    if total > 10 and (english_count / total) > threshold:
        return True
    
    return False

def detect_language_fit(full_text: str) -> tuple[bool, bool, bool]:
    english_ok = contains_any(full_text, ["english", "inglese", "english speaking"])
    other_lang_required = contains_any(full_text, [
        "french required", "german required", "spagnolo richiesto",
        "francese richiesto", "tedesco richiesto",
    ])
    local_language_plus = False
    return english_ok, other_lang_required, local_language_plus

def check_degree_requirement(full_text: str) -> str:
    """Restituisce il motivo dell'esclusione o una stringa vuota.
    
    NOTA: Reso meno aggressivo. Esclude SOLO se la laurea è
    esplicitamente OBBLIGATORIA. Non esclude se dice solo 'laurea'
    senza 'richiesta/obbligatoria', perché molti annunci la menzionano
    come 'preferibile' ma accettano anche il diploma.
    """
    # Esclude solo se dice esplicitamente "laurea richiesta/obbligatoria"
    if re.search(r"\blaurea\b.{0,30}\b(richiesta|richiesto|necessaria|obbligatoria|indispensabile)\b", full_text):
        # Ma NON escludere se dice anche "diploma" come alternativa
        if contains_any(full_text, ["diploma", "diplomato", "o diploma", "oppure diploma"]):
            return ""
        return "richiede_laurea"
    
    # NON escludere più su "probabilmente richiede laurea" — troppi falsi positivi
    return ""

def check_seniority_requirement(full_text: str) -> str:
    # Esclude solo se richiede 7+ anni di esperienza (prima era 5+)
    if re.search(r"\b([7-9]|[1-9][0-9])\+?\s*(?:anni?|years?)\b|>\s*[7-9]\s*(?:anni?|years?)", full_text):
        return "troppo_senior"
    return ""

def check_excluded_keywords(title: str, description: str) -> str:
    full_text = f"{title} {description}".lower()
    title_lower = title.lower()
    
    if contains_any(title_lower, EXCLUDE_KEYWORDS_TITLE):
        return "titolo_non_compatibile"

    if contains_any(title_lower, IT_KEYWORDS_TITLE):
        if not has_valid_training(description, title):
            return "ruolo_it_richiede_esperienza"

    if contains_any(full_text, EXCLUDE_KEYWORDS_TEXT):
        return "testo_non_compatibile"
        
    return ""

def check_manual_role_blacklist(title: str) -> str:
    if contains_any(title.lower(), ["operaio", "cameriere", "barista", "cuoco", "pizzaiolo", 
                                    "elettricista", "idraulico", "muratore", "oss", "badante"]):
        return "ruolo_non_compatibile"
    return ""
