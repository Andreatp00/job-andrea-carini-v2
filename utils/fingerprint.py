"""
Funzioni di fingerprinting e classificazione delle offerte di lavoro.

Genera identificatori univoci per le offerte (fingerprint), assegna
gradi in base al punteggio e determina la priorità delle sorgenti dati.
"""

from hashlib import sha1

from utils.text import normalize_text
from utils.url import canonicalize_url


def fingerprint_job(row: dict) -> str:
    """Calcola un fingerprint SHA-1 per un'offerta di lavoro.

    Se l'offerta ha un URL valido, il fingerprint è basato sull'URL
    canonicalizzato. Altrimenti usa una firma composta da titolo,
    azienda, location e paese di ricerca.

    Args:
        row: Dizionario con i dati dell'offerta.

    Returns:
        Hash SHA-1 come stringa esadecimale.
    """
    canonical_url = canonicalize_url(row.get("job_url") or row.get("official_url") or "")
    if canonical_url:
        return sha1(canonical_url.lower().encode("utf-8")).hexdigest()
    signature = " | ".join(
        [
            normalize_text(row.get("title")).lower(),
            normalize_text(row.get("company")).lower(),
            normalize_text(row.get("location")).lower(),
            normalize_text(row.get("search_country")).lower(),
        ]
    )
    return sha1(signature.encode("utf-8")).hexdigest()


def _smart_fingerprint(row: dict, full_df: "pd.DataFrame") -> str:
    """Fingerprint intelligente che rileva URL generici/duplicati di LinkedIn.

    Problema: JobSpy/LinkedIn spesso ritorna lo STESSO URL (es. /jobs/view/4415255278)
    per molte offerte diverse nella stessa ricerca. Se usiamo quell'URL come fingerprint,
    la deduplicazione eliminerebbe offerte reali diverse.

    Soluzione: Se un URL appare 3+ volte nel dataset → è un URL generico/fallback →
    usa titolo+azienda come fingerprint invece dell'URL.

    Args:
        row: Dizionario con i dati dell'offerta.
        full_df: DataFrame completo per contare le occorrenze dell'URL.

    Returns:
        Hash SHA-1 come stringa esadecimale.
    """
    canonical_url = canonicalize_url(row.get("job_url") or row.get("official_url") or "")

    if canonical_url:
        # Conta quante volte questo URL appare nel dataset
        url_col = full_df.get("job_url")
        if url_col is not None:
            url_count = (url_col == canonical_url).sum()
        else:
            url_count = 1

        # Se l'URL è unico (o quasi), usalo come fingerprint → deduplicazione normale
        if url_count < 3:
            return sha1(canonical_url.lower().encode("utf-8")).hexdigest()

        # Se l'URL appare 3+ volte → è un URL generico LinkedIn
        # Usa titolo+azienda come fingerprint per non perdere offerte diverse

    # Fingerprint basato su titolo+azienda+location (fallback per URL duplicati/mancanti)
    signature = " | ".join(
        [
            normalize_text(row.get("title")).lower()[:100],
            normalize_text(row.get("company")).lower()[:50],
            normalize_text(row.get("location")).lower()[:50],
        ]
    )
    return sha1(signature.encode("utf-8")).hexdigest()


def grade_from_score(score: float) -> str:
    """Converte un punteggio numerico in un grado letterale.

    Scala:
        - ≥ 90 → ``A+``
        - ≥ 80 → ``A``
        - ≥ 70 → ``B``
        - ≥ 60 → ``C``
        - ≥ 50 → ``D``
        - < 50 → ``X``

    Args:
        score: Punteggio numerico dell'offerta.

    Returns:
        Grado come stringa (``A+``, ``A``, ``B``, ``C``, ``D`` o ``X``).
    """
    if score >= 90:
        return "A+"
    if score >= 80:
        return "A"
    if score >= 70:
        return "B"
    if score >= 60:
        return "C"
    if score >= 50:
        return "D"
    return "X"


def source_priority(source_type: str, site: str) -> int:
    """Restituisce la priorità numerica di una sorgente dati.

    Sorgenti più rilevanti per il contesto (es. Subito molto usato
    a Trapani) hanno priorità maggiore.

    Args:
        source_type: Tipo di sorgente (es. ``"company_site"``).
        site: Nome del sito (es. ``"subito.it"``).

    Returns:
        Valore di priorità (più alto = più importante).
    """
    source = normalize_text(source_type or site).lower()
    if source in ("subito", "subito.it"):
        return 200  # Priorità massima per Subito (molto usato a Trapani)
    if source in ("concorso_pubblico", "concorsi"):
        return 180  # Priorità alta per concorsi pubblici
    if source == "company_site":
        return 150
    if source == "agenzia_lavoro":
        return 130
    if source == "google":
        return 100
    if source == "linkedin":
        return 90
    if source == "indeed":
        return 80
    return 50
