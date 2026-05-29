"""
Scraper per Agenzie per il Lavoro — Ricerca annunci amministrativi part-time
Cerca su Adecco, Manpower, Randstad, Gi Group, Openjobmetis, Synergie, Humangest
con focus su Trapani, Sicilia e Smart Working.

URL verificati e aggiornati al 2025. Per le agenzie che cambiano spesso URL,
è presente un fallback automatico via DuckDuckGo site: search.
"""

import logging
import re
import time
from datetime import datetime
from urllib.parse import quote

import pandas as pd
import requests
import tls_client
from bs4 import BeautifulSoup

logger = logging.getLogger("JobHunter.Agenzie")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Sessione stealth per siti con anti-bot
tls_session = tls_client.Session(client_identifier="chrome_120")

# ─── Configurazione agenzie ───────────────────────────────────────────────────
# URL aggiornati al 2025. Se un URL restituisce 404, il fallback DuckDuckGo
# cercherà automaticamente offerte sul dominio dell'agenzia.
AGENCY_CONFIGS = [
    {
        "name": "Adecco",
        "search_url_trapani": "https://www.adecco.it/ricerca-lavoro/trapani/",
        "search_url_smart": "https://www.adecco.it/ricerca-lavoro/smart-working/",
        "keywords": ["amministrativo", "contabilità", "back office", "impiegato", "segreteria", "part-time"],
        "site_domain": "adecco.it",
    },
    {
        "name": "Manpower",
        "search_url_trapani": "https://www.manpower.it/cerca-lavoro/trapani/",
        "search_url_smart": "https://www.manpower.it/cerca-lavoro/smart-working/",
        "keywords": ["amministrativo", "contabilità", "back office", "impiegato", "part-time"],
        "site_domain": "manpower.it",
    },
    {
        # URL corretto 2025: randstad usa /offerte-di-lavoro/ non /trovare-lavoro/
        "name": "Randstad",
        "search_url_trapani": "https://www.randstad.it/offerte-di-lavoro/trapani/",
        "search_url_smart": "https://www.randstad.it/offerte-di-lavoro/smart-working/",
        # Fallback URL se il precedente dà 404
        "alt_url_trapani": "https://www.randstad.it/offerte-lavoro/trapani/",
        "alt_url_smart": "https://www.randstad.it/offerte-lavoro/smart-working/",
        "keywords": ["amministrativo", "contabilità", "back office", "impiegato", "segreteria", "part-time"],
        "site_domain": "randstad.it",
    },
    {
        "name": "Gi Group",
        "search_url_trapani": "https://www.gigroup.it/offerte-lavoro/trapani/",
        "search_url_smart": "https://www.gigroup.it/offerte-lavoro/remote/",
        "keywords": ["amministrativo", "contabilità", "back office", "impiegato", "part-time"],
        "site_domain": "gigroup.it",
    },
    {
        # Openjobmetis — URL corretto 2025
        "name": "Openjobmetis",
        "search_url_trapani": "https://www.openjobmetis.it/offerte-lavoro/trapani/",
        "search_url_smart": "https://www.openjobmetis.it/offerte-lavoro/smart-working/",
        "alt_url_trapani": "https://www.openjobmetis.it/cerca-lavoro/trapani/",
        "alt_url_smart": "https://www.openjobmetis.it/cerca-lavoro/smart-working/",
        "keywords": ["amministrativo", "contabilità", "back office", "impiegato", "part-time"],
        "site_domain": "openjobmetis.it",
    },
    {
        # Synergie Italia — URL corretto 2025
        "name": "Synergie Italia",
        "search_url_trapani": "https://www.synergie-italia.it/offerte-lavoro/trapani/",
        "search_url_smart": "https://www.synergie-italia.it/offerte-lavoro/smart-working/",
        "alt_url_trapani": "https://www.synergie-italia.it/offerte-di-lavoro/trapani/",
        "alt_url_smart": "https://www.synergie-italia.it/offerte-di-lavoro/remote/",
        "keywords": ["amministrativo", "contabilità", "back office", "impiegato"],
        "site_domain": "synergie-italia.it",
    },
    {
        # Humangest — URL corretto 2025
        "name": "Humangest",
        "search_url_trapani": "https://www.humangest.it/offerte-di-lavoro/trapani/",
        "search_url_smart": "https://www.humangest.it/offerte-di-lavoro/smart-working/",
        "alt_url_trapani": "https://www.humangest.it/cerca-lavoro/trapani/",
        "alt_url_smart": "https://www.humangest.it/cerca-lavoro/remote/",
        "keywords": ["amministrativo", "contabilità", "back office", "impiegato", "segreteria"],
        "site_domain": "humangest.it",
    },
    {
        "name": "Etjca",
        "search_url_trapani": "https://www.etjca.it/offerte-lavoro/trapani/",
        "search_url_smart": "https://www.etjca.it/offerte-lavoro/smart-working/",
        "keywords": ["amministrativo", "contabilità", "back office", "impiegato"],
        "site_domain": "etjca.it",
    },
]

TARGET_ROLE_KEYWORDS = [
    "amministrativo", "contabilità", "fatturazione", "back office", "segreteria",
    "impiegato", "ufficio", "commercialista", "contabile", "segreterio",
    "addetto", "assistente amministrativo", "praticante", "stage",
    "part-time", "tempo parziale", "mezza giornata",
    "customer service", "servizio clienti", "amministrazione",
    "ragioneria", "bilancio", "iva", "fatture", "ordini",
    "trapani", "marsala", "mazara", "alcamo", "castelvetrano",
    "smart working", "remoto", "da remoto", "lavoro da casa",
]

EXCLUDE_ROLE_KEYWORDS = [
    "operaio", "magazziniere", "cameriere", "barista", "cuoco",
    "pizzaiolo", "commesso", "venditore", "promoter", "agente di commercio",
    "autista", "elettricista", "idraulico", "manutenzione", "programmatore",
    "sviluppatore", "informatico", "tecnico informatico",
    "infermiere", "medico", "farmacista", "ingegnere", "architetto",
]


def _fetch_url(url: str, use_tls: bool = False) -> tuple[int, str]:
    """
    Scarica una URL. Prova prima con requests standard.
    Se fallisce o ritorna errore, prova con tls_client (anti-bot).
    Ritorna (status_code, html).
    """
    try:
        if use_tls:
            resp = tls_session.get(url, headers=HEADERS, timeout_seconds=20)
            return resp.status_code, resp.text
        else:
            resp = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
            return resp.status_code, resp.text
    except Exception as exc:
        logger.debug(f"    Fetch error ({url}): {exc}")
        return 0, ""


def _scrape_agency_via_duckduckgo(agency_name: str, site_domain: str, location: str) -> list[dict]:
    """
    Fallback: cerca offerte dell'agenzia via DuckDuckGo site: search.
    Usato quando l'URL diretto dell'agenzia ritorna 404 o è bloccato.
    """
    results = []
    kw_query = "amministrativo OR contabilità OR back office OR segreteria OR impiegato"
    loc_query = "Trapani OR Sicilia" if location == "Trapani" else "smart working OR remoto"
    query = f'site:{site_domain} ({kw_query}) ({loc_query})'

    try:
        ddg_url = f"https://html.duckduckgo.com/html/?q={quote(query)}&kl=it-it"
        resp_code, html = _fetch_url(ddg_url, use_tls=True)

        if resp_code != 200:
            logger.debug(f"    DuckDuckGo fallback HTTP {resp_code} per {agency_name}")
            return []

        soup = BeautifulSoup(html, "html.parser")
        links = soup.select("a.result__a")[:8]

        for link in links:
            title = link.get_text(" ", strip=True)
            href = link.get("href", "")
            if not title or not href or len(title) < 8:
                continue
            title_lower = title.lower()
            if not any(kw in title_lower for kw in TARGET_ROLE_KEYWORDS):
                continue
            if any(kw in title_lower for kw in EXCLUDE_ROLE_KEYWORDS):
                continue
            results.append({
                "title": title[:200],
                "company": agency_name,
                "location": location,
                "search_country": location,
                "job_url": href,
                "official_url": href,
                "description": f"{agency_name} (DDG) | {title[:200]}",
                "site": site_domain,
                "source_type": "agenzia_lavoro",
                "date_posted": datetime.now().strftime("%Y-%m-%d"),
            })

        if results:
            logger.info(f"    DuckDuckGo fallback: {len(results)} risultati per {agency_name}")
    except Exception as exc:
        logger.debug(f"    DuckDuckGo fallback errore {agency_name}: {exc}")

    return results


def _parse_agency_page(html: str, agency_name: str, site_domain: str, location: str) -> list[dict]:
    """
    Parsa una pagina di agenzia di lavoro e cerca annunci pertinenti.
    """
    results = []
    soup = BeautifulSoup(html, "html.parser")

    # Strategia 1: Cerca in articoli o card
    items = soup.select(
        "article, div[class*='job'], div[class*='card'], li[class*='job'], "
        "tr[class*='job'], div[class*='offerta'], div[class*='vacancy'], "
        "div[class*='annuncio'], div[class*='listing']"
    )

    for item in items:
        link_el = item.find("a", href=True)
        if not link_el:
            continue

        href = link_el.get("href", "")
        title = item.get_text(" ", strip=True)

        # Prova a trovare il link diretto all'annuncio
        if any(x in href.lower() for x in ["/offerte-lavoro/", "/cerca-lavoro/", "?", "filter", "ricerca"]):
            for lnk in item.find_all("a", href=True):
                h = lnk.get("href", "")
                if any(x in h.lower() for x in ["/job/", "/dettaglio/", "-annuncio-", "/lavoro/", "/offerta/"]):
                    href = h
                    title = lnk.get_text(" ", strip=True) or title
                    break

        if not title or len(title) < 8:
            continue

        title_lower = title.lower()
        if not any(kw in title_lower for kw in TARGET_ROLE_KEYWORDS):
            continue
        if any(kw in title_lower for kw in EXCLUDE_ROLE_KEYWORDS):
            continue

        if href.startswith("/"):
            href = f"https://www.{site_domain}{href}"
        elif not href.startswith("http"):
            continue

        results.append({
            "title": title[:200],
            "company": agency_name,
            "location": location,
            "search_country": location,
            "job_url": href,
            "official_url": href,
            "description": f"{agency_name} | {title[:250]}",
            "site": site_domain,
            "source_type": "agenzia_lavoro",
            "date_posted": datetime.now().strftime("%Y-%m-%d"),
        })

    if results:
        return results

    # Strategia 2: Fallback — cerca tutti i link rilevanti
    for link in soup.find_all("a", href=True):
        href = link.get("href", "")
        text = link.get_text(" ", strip=True)

        if not text or len(text) < 10:
            continue

        text_lower = text.lower()
        if not any(kw in text_lower for kw in TARGET_ROLE_KEYWORDS):
            continue
        if any(kw in text_lower for kw in EXCLUDE_ROLE_KEYWORDS):
            continue

        if href.startswith("/"):
            href = f"https://www.{site_domain}{href}"
        elif not href.startswith("http"):
            continue

        results.append({
            "title": text[:200],
            "company": agency_name,
            "location": location,
            "search_country": location,
            "job_url": href,
            "official_url": href,
            "description": f"{agency_name} | {text[:200]}",
            "site": site_domain,
            "source_type": "agenzia_lavoro",
            "date_posted": datetime.now().strftime("%Y-%m-%d"),
        })

    return results


def _get_agency_results(agency: dict, url: str, alt_url: str | None, location: str) -> list[dict]:
    """
    Prova l'URL principale, poi l'alternativo, poi DuckDuckGo fallback.
    """
    name = agency["name"]
    domain = agency["site_domain"]

    # Tentativo 1: URL principale
    status, html = _fetch_url(url)
    if status == 200 and html:
        results = _parse_agency_page(html, name, domain, location)
        if results:
            return results
        # Pagina ok ma nessun annuncio trovato (es. lista vuota)
        logger.info(f"  -> {name} [{location}]: 0 annunci (pagina vuota)")
        return []

    logger.warning(f"  -> {name} [{location}]: HTTP {status} per {url}")

    # Tentativo 2: URL alternativo (se disponibile)
    if alt_url and alt_url != url:
        status2, html2 = _fetch_url(alt_url)
        if status2 == 200 and html2:
            results = _parse_agency_page(html2, name, domain, location)
            logger.info(f"  -> {name} [{location}] (alt URL): {len(results)} annunci")
            return results
        logger.warning(f"  -> {name} [{location}] (alt): HTTP {status2}")

    # Tentativo 3: DuckDuckGo fallback
    logger.info(f"  -> {name} [{location}]: uso DuckDuckGo fallback...")
    return _scrape_agency_via_duckduckgo(name, domain, location)


def scrape_agenzie_lavoro() -> pd.DataFrame:
    """
    Scraping di tutte le agenzie per il lavoro.
    Cerca annunci a Trapani e Smart Working con fallback automatico.
    """
    logger.info("=== SCRAPING AGENZIE PER IL LAVORO ===")
    all_results = []

    for agency in AGENCY_CONFIGS:
        name = agency["name"]

        # ── Trapani ──────────────────────────────────────────────────────────
        logger.info(f"Agenzia: {name} - Trapani")
        items = _get_agency_results(
            agency,
            url=agency["search_url_trapani"],
            alt_url=agency.get("alt_url_trapani"),
            location="Trapani",
        )
        all_results.extend(items)
        logger.info(f"  -> Trapani: {len(items)} annunci")

        time.sleep(1.5)

        # ── Smart Working ─────────────────────────────────────────────────────
        logger.info(f"Agenzia: {name} - Smart Working")
        items = _get_agency_results(
            agency,
            url=agency["search_url_smart"],
            alt_url=agency.get("alt_url_smart"),
            location="Italia (Smart Working)",
        )
        all_results.extend(items)
        logger.info(f"  -> Smart Working: {len(items)} annunci")

        time.sleep(1.5)

    if not all_results:
        logger.info("Nessun annuncio trovato dalle agenzie per il lavoro")
        return pd.DataFrame()

    df = pd.DataFrame(all_results)
    df = df.drop_duplicates(subset=["title", "company", "job_url"])
    logger.info(f"Agenzie lavoro: totale {len(df)} annunci unici")
    return df