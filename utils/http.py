"""
Gestione delle sessioni HTTP e degli header.

Fornisce una sessione TLS stealth (per bypassare Cloudflare),
header browser-like e una funzione di richiesta con retry automatico.
"""

import logging
import time

import requests
import tls_client

logger = logging.getLogger("JobHunter")

# Header che simulano un browser Chrome reale
HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
}


def get_tls_session() -> tls_client.Session:
    """Crea e restituisce una sessione TLS stealth con identificativo Chrome 120.

    Utilizzata per bypassare protezioni Cloudflare su siti come
    Subito.it, DuckDuckGo e siti aziendali.

    Returns:
        Sessione ``tls_client.Session`` configurata.
    """
    return tls_client.Session(client_identifier="chrome_120")


def get_headers() -> dict[str, str]:
    """Restituisce una copia degli header HTTP standard.

    Returns:
        Dizionario con ``User-Agent`` e ``Accept-Language``.
    """
    return HEADERS.copy()


def retry_request(
    url: str,
    *,
    max_retries: int = 3,
    delay: float = 2.0,
    timeout: int = 30,
    headers: dict[str, str] | None = None,
) -> requests.Response | None:
    """Esegue una richiesta GET con retry automatico in caso di errore.

    Args:
        url: URL da richiedere.
        max_retries: Numero massimo di tentativi (default 3).
        delay: Secondi di attesa tra un tentativo e l'altro (default 2).
        timeout: Timeout della richiesta in secondi (default 30).
        headers: Header personalizzati; se ``None`` usa quelli standard.

    Returns:
        Oggetto ``requests.Response`` in caso di successo, ``None`` se
        tutti i tentativi falliscono.
    """
    if headers is None:
        headers = HEADERS

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            logger.warning(
                f"Tentativo {attempt}/{max_retries} fallito per {url}: {exc}"
            )
            if attempt < max_retries:
                time.sleep(delay)

    logger.error(f"Tutti i {max_retries} tentativi falliti per {url}")
    return None
