from urllib.parse import quote
from bs4 import BeautifulSoup
import logging

from utils.text import normalize_text
from utils.url import extract_real_url_from_redirect
from utils.http import get_tls_session, get_headers

logger = logging.getLogger('JobHunter.web_search')

def search_web_engines(query: str, num_results: int = 10) -> list[tuple[str, str]]:
    """
    Motore di ricerca multi-engine sicurissimo. Prova in cascata motori diversi.
    Elimina la dipendenza da DuckDuckGo (che blocca con 202).
    Restituisce una lista di tuple (titolo, url reale).
    """
    results = []
    seen_titles = set()
    tls_session = get_tls_session()
    headers_base = get_headers()

    # --- 1. BING SEARCH ---
    try:
        url = f"https://www.bing.com/search?q={quote(query)}"
        # SRCHHPGUSR=ADLT=DEMOTE disattiva i filtri severi che potrebbero bloccare
        headers = {**headers_base, "Cookie": "SRCHHPGUSR=ADLT=DEMOTE&NRSLT=20;"}
        response = tls_session.get(url, headers=headers, timeout_seconds=30)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            for li in soup.select("li.b_algo"):
                a_tag = li.select_one("h2 a")
                if a_tag:
                    href = a_tag.get("href", "")
                    title = normalize_text(a_tag.get_text(" ", strip=True))
                    if href and title and href.startswith("http"):
                        # Estrai URL reale da redirect (Yahoo/Bing)
                        real_url = extract_real_url_from_redirect(href)
                        if real_url and title not in seen_titles:
                            results.append((title, real_url))
                            seen_titles.add(title)
            if results:
                logger.debug(f"    [Bing] {len(results)} risultati trovati")
                return results[:num_results]
    except Exception as exc:
        logger.debug(f"Bing search error: {exc}")
        pass

    # --- 2. YAHOO SEARCH ---
    try:
        url = f"https://it.search.yahoo.com/search?p={quote(query)}"
        response = tls_session.get(url, headers=headers_base, timeout_seconds=30)
        if response.status_code == 200 and "guce.yahoo" not in response.url:
            soup = BeautifulSoup(response.text, "html.parser")
            for div in soup.select("div.compTitle"):
                a_tag = div.select_one("h3.title a")
                if a_tag:
                    href = a_tag.get("href", "")
                    title = normalize_text(a_tag.get_text(" ", strip=True))
                    if href and title and href.startswith("http"):
                        # Estrai URL reale da redirect (Yahoo/Bing)
                        real_url = extract_real_url_from_redirect(href)
                        if real_url and title not in seen_titles:
                            results.append((title, real_url))
                            seen_titles.add(title)
            if results:
                logger.debug(f"    [Yahoo] {len(results)} risultati trovati")
                return results[:num_results]
    except Exception as exc:
        logger.debug(f"Yahoo search error: {exc}")
        pass

    # --- 3. ECOSIA SEARCH ---
    try:
        url = f"https://www.ecosia.org/search?q={quote(query)}"
        response = tls_session.get(url, headers=headers_base, timeout_seconds=30)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            for a_tag in soup.select("a.result-title"):
                href = a_tag.get("href", "")
                title = normalize_text(a_tag.get_text(" ", strip=True))
                if href and title and href.startswith("http"):
                    # Estrai URL reale da redirect (Yahoo/Bing)
                    real_url = extract_real_url_from_redirect(href)
                    if real_url and title not in seen_titles:
                        results.append((title, real_url))
                        seen_titles.add(title)
            if results:
                logger.debug(f"    [Ecosia] {len(results)} risultati trovati")
                return results[:num_results]
    except Exception as exc:
        logger.debug(f"Ecosia search error: {exc}")
        pass

    return []
