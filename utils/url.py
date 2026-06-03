"""
Utilità per la manipolazione degli URL.

Canonicalizzazione, estrazione dominio e risoluzione di URL di
reindirizzamento (Yahoo, Bing, Ecosia, DuckDuckGo).
"""

import logging
import re
from urllib.parse import parse_qsl, unquote, urlencode, urlparse, urlunparse

from utils.text import normalize_text

logger = logging.getLogger("JobHunter")


def canonicalize_url(url: str) -> str:
    """Canonicalizza un URL rimuovendo parametri UTM e frammenti.

    Valori speciali (``None``, ``"#"``, ``"N/A"``, stringa vuota) restituiscono
    stringa vuota.

    Args:
        url: URL da canonicalizzare.

    Returns:
        URL pulito oppure stringa vuota.
    """
    url = normalize_text(url)
    if not url or url in {"#", "N/A"}:
        return ""
    try:
        parsed = urlparse(url)
        query = [
            (k, v)
            for k, v in parse_qsl(parsed.query, keep_blank_values=True)
            if not k.lower().startswith("utm_")
        ]
        clean = parsed._replace(query=urlencode(query), fragment="")
        return urlunparse(clean)
    except Exception:
        return url


def extract_domain(url: str) -> str:
    """Estrae il dominio (senza ``www.``) da un URL.

    Args:
        url: URL da cui estrarre il dominio.

    Returns:
        Dominio estratto oppure il testo normalizzato dell'URL originale.
    """
    match = re.search(r"https?://(?:www\.)?([^/]+)", normalize_text(url))
    return match.group(1) if match else normalize_text(url)


def extract_real_url_from_redirect(url: str) -> str:
    """Estrae l'URL reale da URL di reindirizzamento (Yahoo, Bing, Ecosia, ecc.).

    Gestisce tutti i formati noti di redirect:
    - Yahoo: ``r.search.yahoo.com/.../RU=URL/RK=...`` o ``/RS=...``
    - Yahoo: ``it.search.yahoo.com/.../RU=URL&...``
    - Yahoo: ``search.yahoo.com/...?ru=URL&...``
    - Bing: ``bing.com/redir?url=URL&...``
    - Ecosia: ``ecosia.org/search?...&url=URL``
    - DuckDuckGo: ``duckduckgo.com/...?uddg=URL``

    Args:
        url: URL potenzialmente di redirect.

    Returns:
        URL reale decodificato, oppure l'URL originale se non è un redirect.
    """
    if not url:
        return url

    url_lower = url.lower()

    # === YAHOO REDIRECT ===
    if any(x in url_lower for x in ["r.search.yahoo.com", "it.search.yahoo.com", "search.yahoo.com"]):
        try:
            # Caso 1: /RU= nel path (formato più comune)
            # Esempio: https://r.search.yahoo.com/.../RU=https%3A%2F%2Fsite.com%2F.../RK=2/RS=...
            if "/RU=" in url:
                start = url.find("/RU=") + 4
                # Marker di fine: /RK=, /RS=, &, ?, #
                end_markers = [
                    url.find("/RK=", start),
                    url.find("/RS=", start),
                    url.find("&", start),
                    url.find("?", start),
                    url.find("#", start),
                ]
                end_markers = [x for x in end_markers if x > 0]
                end = min(end_markers) if end_markers else len(url)
                encoded_url = url[start:end]
                real_url = unquote(encoded_url)
                if real_url.startswith("http"):
                    logger.debug(f"  Yahoo redirect estratto: {real_url[:100]}")
                    return real_url

            # Caso 2: ?ru= nella query string
            if "?ru=" in url_lower:
                start = url_lower.find("?ru=") + 4
                end_markers = [url.find("&", start), url.find("#", start)]
                end_markers = [x for x in end_markers if x > 0]
                end = min(end_markers) if end_markers else len(url)
                encoded_url = url[start:end]
                real_url = unquote(encoded_url)
                if real_url.startswith("http"):
                    logger.debug(f"  Yahoo redirect (query) estratto: {real_url[:100]}")
                    return real_url

            # Caso 3: URL diretto (nessun redirect)
            if url.startswith("http"):
                return url

        except Exception as exc:
            logger.debug(f"Errore estrazione URL Yahoo: {exc}")

    # === BING REDIRECT ===
    if "bing.com" in url_lower and "url=" in url_lower:
        try:
            # Bing metter url= nel path o query string
            # Esempio: https://www.bing.com/redir?k=...&url=https%3A%2F%2Fsite.com%2F...
            # parse_qs NON funziona, estraiamo manualmente
            start = url_lower.find("url=") + 4
            if start > 3:  # Found
                # Trova il prossimo delimiter: &, #, ?
                end_markers = [url.find("&", start), url.find("#", start), url.find("?", start)]
                end_markers = [x for x in end_markers if x > start]
                end = min(end_markers) if end_markers else len(url)
                encoded_url = url[start:end]
                real_url = unquote(encoded_url)
                if real_url.startswith("http"):
                    logger.debug(f"  Bing redirect estratto: {real_url[:100]}")
                    return real_url
        except Exception as exc:
            logger.debug(f"Errore estrazione URL Bing: {exc}")

    # === ECOSIA REDIRECT ===
    if "ecosia.org" in url_lower and "url=" in url_lower:
        try:
            start = url_lower.find("url=") + 4
            if start > 3:
                end_markers = [url.find("&", start), url.find("#", start)]
                end_markers = [x for x in end_markers if x > start]
                end = min(end_markers) if end_markers else len(url)
                encoded_url = url[start:end]
                real_url = unquote(encoded_url)
                if real_url.startswith("http"):
                    logger.debug(f"  Ecosia redirect estratto: {real_url[:100]}")
                    return real_url
        except Exception as exc:
            logger.debug(f"Errore estrazione URL Ecosia: {exc}")

    # === DDUCKGO REDIRECT ===
    if "duckduckgo.com" in url_lower and "uddg=" in url_lower:
        try:
            start = url_lower.find("uddg=") + 5
            if start > 4:
                end_markers = [url.find("&", start), url.find("#", start)]
                end_markers = [x for x in end_markers if x > start]
                end = min(end_markers) if end_markers else len(url)
                encoded_url = url[start:end]
                real_url = unquote(encoded_url)
                if real_url.startswith("http"):
                    logger.debug(f"  DuckDuckGo redirect estratto: {real_url[:100]}")
                    return real_url
        except Exception as exc:
            logger.debug(f"Errore estrazione URL DuckDuckGo: {exc}")

    # Se non è un redirect noto, restituisci l'URL originale
    return url
