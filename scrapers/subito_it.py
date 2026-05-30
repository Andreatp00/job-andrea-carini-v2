"""
Scraper per Subito.it — Annunci di lavoro Trapani e provincia
USA L'API JSON UFFICIALE di Subito.it (endpoint hades.subito.it)
usata dalla loro app mobile e web React → NESSUN anti-bot, nessun 403.
"""

import logging
import time
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import EXCLUDE_KEYWORDS_TITLE as EXCLUDE_ROLE_KEYWORDS

import pandas as pd
import requests
import tls_client

logger = logging.getLogger("JobHunter.Subito")

# ─── API JSON ufficiale Subito.it ─────────────────────────────────────────────
SUBITO_API = "https://hades.subito.it/v1/search/classifieds"

# Sessione stealth per bypassare Cloudflare
SUBITO_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
    "Referer": "https://www.subito.it/",
    "Origin": "https://www.subito.it",
    "X-Subito-Env": "production",
    "X-Requested-With": "XMLHttpRequest",
}

# Sessione TLS per evitare blocchi Cloudflare
tls_session = tls_client.Session(client_identifier="chrome_120")

# Categoria 29 = Lavoro > Offerte di lavoro su Subito.it
SUBITO_CATEGORY = 29
# Region ID 11 = Sicilia (regione interna Subito)
SUBITO_REGION_SICILIA = 11

# ─── Ricerche configurate ────────────────────────────────────────────────────
SUBITO_SEARCHES = [
    # Trapani e provincia (region=11 = Sicilia, filtriamo per città nella risposta)
    {"q": "back office",               "region": SUBITO_REGION_SICILIA, "label": "Trapani"},
    {"q": "impiegato amministrativo",  "region": SUBITO_REGION_SICILIA, "label": "Trapani"},
    {"q": "contabilità",               "region": SUBITO_REGION_SICILIA, "label": "Trapani"},
    {"q": "fatturazione ufficio",      "region": SUBITO_REGION_SICILIA, "label": "Trapani"},
    {"q": "segreteria",                "region": SUBITO_REGION_SICILIA, "label": "Trapani"},
    {"q": "ragioneria",                "region": SUBITO_REGION_SICILIA, "label": "Trapani"},
    {"q": "praticante",                "region": SUBITO_REGION_SICILIA, "label": "Trapani"},
    {"q": "amministrazione ufficio",   "region": SUBITO_REGION_SICILIA, "label": "Trapani"},
    {"q": "part time ufficio",         "region": SUBITO_REGION_SICILIA, "label": "Trapani"},
    {"q": "customer service",          "region": SUBITO_REGION_SICILIA, "label": "Trapani"},
    {"q": "addetto contabilità",       "region": SUBITO_REGION_SICILIA, "label": "Trapani"},
    {"q": "stage",                     "region": SUBITO_REGION_SICILIA, "label": "Trapani"},
    {"q": "tirocinio formativo",       "region": SUBITO_REGION_SICILIA, "label": "Trapani"},
    {"q": "apprendistato",             "region": SUBITO_REGION_SICILIA, "label": "Trapani"},
    
    # Smart Working Italia (nessun region filter → tutto Italia)
    {"q": "smart working",                 "label": "Italia"},
    {"q": "lavoro da casa contabilità",    "label": "Italia"},
    {"q": "remoto back office",            "label": "Italia"},
    {"q": "full remote amministrativo",    "label": "Italia"},
    {"q": "call center da casa",           "label": "Italia"},
    {"q": "data entry remoto",             "label": "Italia"},
    {"q": "inserimento dati",              "label": "Italia"},
]

EXCLUDE_PATTERNS = [
    "auto ", "moto ", "telefono", "cellulare", "tablet", "iphone", "samsung",
    "casa in vendita", "appartamento", "affitto",
    "abbigliamento", "scarpe", "borsa", "borse",
    "console", "playstation", "xbox", "nintendo",
    "bici", "cucina", "divano", "letto", "lavatrice",
    "vendo", "cedo", "regalo",
]

TARGET_KEYWORDS = [
    "amministrativo", "contabilità", "back office", "fatturazione", "segreteria",
    "ufficio", "commercialista", "ragioneria", "contabile", "impiegato",
    "praticante", "stage", "part-time", "part time", "smart working",
    "remoto", "bilancio", "lavoro", "addetto", "assistente", "customer service",
    "amministrazione", "prima nota", "erp", "call center", "data entry",
    "inserimento dati", "tirocinio", "apprendistato",
]

TRAPANI_CITIES = {
    "trapani", "marsala", "mazara", "mazara del vallo", "alcamo",
    "castelvetrano", "erice", "valderice", "paceco", "buseto",
    "petrosino", "salemi", "partanna", "campobello", "pantelleria",
    "favignana", "castellammare del golfo", "calatafimi",
}


def _parse_location(ad: dict, fallback_label: str) -> tuple[str, str]:
    """Estrae città e search_country dall'annuncio Subito."""
    geo = ad.get("geo", {})
    city_obj = geo.get("city", {})
    region_obj = geo.get("region", {})
    town_obj = geo.get("town", {})

    city = (
        city_obj.get("value", "")
        or town_obj.get("value", "")
        or region_obj.get("value", "")
        or fallback_label
    )

    city_lower = city.lower()
    if any(tp in city_lower for tp in TRAPANI_CITIES):
        return city, "Trapani"
    if "sicilia" in city_lower or region_obj.get("short_name", "").upper() in (
        "AG", "CL", "CT", "EN", "ME", "PA", "RG", "SR", "TP"
    ):
        return city, "Sicilia"
    return city, fallback_label


def scrape_subito() -> pd.DataFrame:
    """
    Scraping Subito.it via API JSON ufficiale.
    Nessun HTML parsing, nessun Cloudflare, nessun 403.
    """
    logger.info("=== SCRAPING SUBITO.IT (API JSON hades.subito.it) ===")
    all_results = []

    for search in SUBITO_SEARCHES:
        q = search["q"]
        label = search.get("label", "Italia")

        params: dict = {
            "q": q,
            "category": SUBITO_CATEGORY,
            "start": 0,
            "lim": 25,
            "sort": "date",
        }
        if "region" in search:
            params["region"] = search["region"]

        logger.info(f"Subito API: '{q}' [{label}]")

        for attempt in range(3):          # max 3 tentativi per query
            try:
                # Usa tls_session per bypassare Cloudflare
                resp = tls_session.get(
                    SUBITO_API,
                    params=params,
                    headers=SUBITO_HEADERS,
                    timeout_seconds=30,
                )

                if resp.status_code == 429:
                    logger.warning(f"  -> Rate limit Subito API (429), attendo {10*(attempt+1)}s...")
                    time.sleep(10*(attempt+1))
                    continue

                # Se 403, prova con headers alternativi
                if resp.status_code == 403 and attempt < 2:
                    alt_headers = {**SUBITO_HEADERS, 
                                   "User-Agent": "Subito/1.0 (iOS; iPhone) AppleWebKit/605.1.15"}
                    resp = tls_session.get(
                        SUBITO_API,
                        params=params,
                        headers=alt_headers,
                        timeout_seconds=30,
                    )
                    if resp.status_code == 403:
                        logger.warning(f"  -> HTTP 403 (tentativo {attempt+1}), provo headers alternativi...")
                        continue

                if resp.status_code != 200:
                    logger.warning(f"  -> HTTP {resp.status_code}")
                    break

                data = resp.json()
                ads = data.get("ads", [])

                if not ads:
                    logger.info("  -> 0 annunci")
                    break

                count = 0
                for ad in ads:
                    title = str(ad.get("subject", "")).strip()
                    if not title or len(title) < 5:
                        continue

                    title_lower = title.lower()

                    # Escludi annunci non lavorativi
                    if any(p in title_lower for p in EXCLUDE_PATTERNS):
                        continue

                    # Includi solo annunci con keyword rilevanti
                    body = str(ad.get("body", "")).strip()
                    full_text = f"{title} {body}".lower()
                    if not any(kw in full_text for kw in TARGET_KEYWORDS):
                        continue

                    # URL
                    urls = ad.get("urls", {})
                    job_url = urls.get("default", "") or ad.get("url", "")

                    # Azienda
                    advertiser = ad.get("advertiser", {})
                    company = (
                        advertiser.get("company_name")
                        or advertiser.get("name")
                        or ""
                    )
                    if not company:
                        company = "Subito.it"

                    # Località
                    city, search_country = _parse_location(ad, label)

                    # Data
                    dates = ad.get("dates", {})
                    raw_date = (
                        dates.get("publication_date", "")
                        or dates.get("expiration_date", "")
                    )
                    try:
                        date_str = raw_date[:10] if raw_date else datetime.now().strftime("%Y-%m-%d")
                    except Exception:
                        date_str = datetime.now().strftime("%Y-%m-%d")

                    all_results.append({
                        "title": title[:250],
                        "company": str(company)[:150],
                        "location": city,
                        "search_country": search_country,
                        "job_url": job_url,
                        "official_url": job_url,
                        "description": f"Subito.it | {body[:400]}",
                        "site": "subito.it",
                        "source_type": "subito",
                        "date_posted": date_str,
                    })
                    count += 1

                logger.info(f"  -> {count} annunci rilevanti (di {len(ads)} totali)")
                break   # successo, esci dal loop di retry

            except requests.exceptions.ConnectionError as exc:
                logger.warning(f"  -> Connessione fallita: {exc}")
                break
            except Exception as exc:
                logger.warning(f"  -> Errore Subito API (tentativo {attempt + 1}): {exc}")
                time.sleep(3)

        time.sleep(1.5)

    if not all_results:
        logger.info("Nessun annuncio trovato su Subito.it via API")
        return pd.DataFrame()

    df = pd.DataFrame(all_results)
    df = df[df["job_url"].str.strip() != ""]
    df = df.drop_duplicates(subset=["job_url"], keep="first")
    logger.info(f"Subito.it API: {len(df)} annunci unici")
    return df