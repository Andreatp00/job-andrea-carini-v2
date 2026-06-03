"""
Utilità per la manipolazione del testo.

Funzioni di normalizzazione e ricerca testuale usate in tutto il progetto
Job Hunter 2.0 per pulire e confrontare stringhe.
"""

import re


def normalize_text(value: object) -> str:
    """Normalizza un valore arbitrario in una stringa pulita.

    - ``None`` e ``"nan"`` diventano stringa vuota.
    - Sequenze di spazi bianchi vengono ridotte a un singolo spazio.
    - Spazi iniziali e finali vengono rimossi.

    Args:
        value: Qualsiasi valore convertibile in stringa.

    Returns:
        Stringa normalizzata (può essere vuota).
    """
    text = "" if value is None else str(value)
    if text.lower() == "nan":
        return ""
    return re.sub(r"\s+", " ", text).strip()


def contains_any(text: str, keywords: list[str]) -> bool:
    """Verifica se *text* contiene almeno una delle *keywords*.

    Il confronto è case-insensitive; il testo viene prima normalizzato
    tramite :func:`normalize_text`.

    Args:
        text: Testo in cui cercare.
        keywords: Lista di parole chiave da cercare.

    Returns:
        ``True`` se almeno una keyword è presente nel testo.
    """
    text = normalize_text(text).lower()
    return any(keyword.lower() in text for keyword in keywords)
