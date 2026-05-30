#!/usr/bin/env python3
"""
🔍 JOB HUNTER BOT — Profilo Back Office / Ragioneria
Candidato: Diplomato Ragioneria AFM, 4 anni esperienza amministrativa, 25 anni, Trapani
Cerca ogni giorno su LinkedIn, Indeed, Google Jobs, Subito.it, Agenzie Lavoro, Concorsi Pubblici
"""

import csv
import json
import logging
import re
import smtplib
import sys
import time
from datetime import datetime, timedelta
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from hashlib import sha1
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse, quote

import pandas as pd
import requests
import tls_client

# Sessione stealth per bypassare Cloudflare (Subito, DDG, Company sites)
tls_session = tls_client.Session(client_identifier="chrome_120")
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent))
from config import *

BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"
REPORT_DIR = DATA_DIR / "reports"
LOG_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)
REPORT_DIR.mkdir(exist_ok=True)
SEEN_FILE = BASE_DIR / "seen_jobs.json"
HISTORY_FILE = DATA_DIR / "job_history.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / f"job_hunter_{datetime.now():%Y%m%d}.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("JobHunter")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
}


def normalize_text(value) -> str:
    text = "" if value is None else str(value)
    if text.lower() == "nan":
        return ""
    return re.sub(r"\s+", " ", text).strip()


def contains_any(text: str, keywords: list[str]) -> bool:
    text = normalize_text(text).lower()
    return any(keyword.lower() in text for keyword in keywords)


def canonicalize_url(url: str) -> str:
    url = normalize_text(url)
    if not url or url in {"#", "N/A"}:
        return ""
    try:
        parsed = urlparse(url)
        query = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if not k.lower().startswith("utm_")]
        clean = parsed._replace(query=urlencode(query), fragment="")
        return urlunparse(clean)
    except Exception:
        return url


def extract_domain(url: str) -> str:
    match = re.search(r"https?://(?:www\.)?([^/]+)", normalize_text(url))
    return match.group(1) if match else normalize_text(url)


def fingerprint_job(row: dict) -> str:
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


def _smart_fingerprint(row: dict, full_df) -> str:
    """
    Fingerprint intelligente che rileva URL generici/duplicati di LinkedIn.
    
    Problema: JobSpy/LinkedIn spesso ritorna lo STESSO URL (es. /jobs/view/4415255278)
    per molte offerte diverse nella stessa ricerca. Se usiamo quell'URL come fingerprint,
    la deduplicazione eliminerebbe offerte reali diverse.
    
    Soluzione: Se un URL appare 3+ volte nel dataset → è un URL generico/fallback →
    usa titolo+azienda come fingerprint invece dell'URL.
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


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return default


def save_json(path: Path, payload):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def load_job_history() -> dict:
    cutoff = (datetime.now() - timedelta(days=HISTORY_RETENTION_DAYS)).isoformat()
    history = load_json(HISTORY_FILE, {})
    history = {key: value for key, value in history.items() if value.get("sent_at", "") > cutoff}

    legacy = load_json(SEEN_FILE, {})
    if isinstance(legacy, dict):
        for job_url, sent_at in legacy.items():
            history.setdefault(
                sha1(canonicalize_url(job_url).lower().encode("utf-8")).hexdigest(),
                {"job_url": canonicalize_url(job_url), "sent_at": sent_at, "source": "legacy_seen_file"},
            )

    return history


def load_previous_report_fingerprints() -> set[str]:
    known = set()
    for folder in [DATA_DIR, REPORT_DIR]:
        if not folder.exists():
            continue
        for path in sorted(folder.glob("*")):
            if path.suffix.lower() not in {".csv", ".xlsx"}:
                continue
            try:
                if path.suffix.lower() == ".csv":
                    df = pd.read_csv(path)
                else:
                    df = pd.read_excel(path, sheet_name="All_Relevant")
            except Exception:
                continue
            if df.empty:
                continue
            for _, row in df.iterrows():
                known.add(fingerprint_job(row.to_dict()))
    return known


def known_fingerprints() -> set[str]:
    history = load_job_history()
    known = set(history.keys())
    known.update(load_previous_report_fingerprints())
    return known


def infer_country_label(location: str, existing_label: str = "") -> str:
    label = normalize_text(existing_label)
    location_text = normalize_text(location).lower()
    if label:
        return label
    
    # Se nel testo c'è Trapani o provincia
    for loc_keyword, loc_label in [
        ("trapani", "Trapani"),
        ("valderice", "Trapani"),
        ("paceco", "Trapani"),
        ("erice", "Trapani"),
        ("custonaci", "Trapani"),
        ("marsala", "Trapani"),
        ("mazara", "Trapani"),
        ("alcamo", "Trapani"),
        ("castelvetrano", "Trapani"),
        ("san vito lo capo", "Trapani"),
        ("sicilia", "Sicilia"),
        ("sicily", "Sicilia"),
        ("palermo", "Sicilia"),
        ("catania", "Sicilia"),
        ("sardegna", "Italia"),
        ("italia", "Italia"),
        ("italy", "Italia"),
        ("smart working", "Italia"),
        ("remoto", "Italia"),
        ("remote", "Italia"),
        ("lavoro da casa", "Italia"),
        ("da remoto", "Italia"),
        ("telelavoro", "Italia"),
    ]:
        if loc_keyword in location_text:
            return loc_label
    
    # Italia generica
    if any(reg in location_text for reg in ["italia", "italy", "italiano", "nazionale"]):
        return "Italia"
    
    return "Italia"


def scrape_portals() -> pd.DataFrame:
    """Scraping portali classici (LinkedIn, Indeed, Google Jobs) con JobSpy."""
    try:
        from jobspy import scrape_jobs
    except Exception as exc:
        logger.warning(f"JobSpy non disponibile: {exc}")
        return pd.DataFrame()

    all_jobs = []
    total = len(SEARCH_TERMS) * len(COUNTRY_SEARCHES)
    counter = 0

    for country_cfg in COUNTRY_SEARCHES:
        for term in SEARCH_TERMS:
            counter += 1
            label = country_cfg["label"]
            logger.info(f"[{counter}/{total}] Portali: '{term}' in {label}")
            try:
                jobs = scrape_jobs(
                    site_name=["indeed", "linkedin"],
                    search_term=term,
                    location=country_cfg["location"],
                    country_indeed=country_cfg["country_indeed"],
                    hours_old=HOURS_OLD,
                    results_wanted=RESULTS_WANTED,
                    linkedin_fetch_description=True,
                    verbose=0,
                )
                if len(jobs) > 0:
                    jobs["search_country"] = label
                    jobs["source_type"] = jobs.get("site", "portal")
                    jobs["location"] = jobs.get("location", country_cfg["location"])
                    all_jobs.append(jobs)
                    logger.info(f"  -> {len(jobs)} offerte raccolte")
            except Exception as exc:
                logger.warning(f"  -> Errore portali: {exc}")
            time.sleep(1)

    for term in GOOGLE_SEARCH_TERMS:
        logger.info(f"Google Jobs: '{term}'")
        try:
            jobs = scrape_jobs(
                site_name=["google"],
                google_search_term=term,
                results_wanted=RESULTS_WANTED,
                hours_old=HOURS_OLD,
                verbose=0,
            )
            if len(jobs) > 0:
                jobs["source_type"] = "google"
                jobs["search_country"] = "Italia"
                all_jobs.append(jobs)
                logger.info(f"  -> {len(jobs)} offerte Google")
        except Exception as exc:
            logger.warning(f"  -> Errore Google Jobs: {exc}")
        time.sleep(1)

    if not all_jobs:
        return pd.DataFrame()

    return pd.concat(all_jobs, ignore_index=True)


def scrape_company_sites() -> pd.DataFrame:
    """
    Scraping siti aziendali/configurati (studi commercialisti, agenzie, enti).
    Usa DuckDuckGo GET (non POST) con query site: corretta — elimina HTTP 202.
    """
    results = []
    for company_cfg in COMPANY_CAREER_SITES:
        company = company_cfg["company"]  # FIX: era company_name (NameError)
        keywords = company_cfg["search_params"]["keywords"]
        domain = extract_domain(company_cfg["url"])
        # FIX: query usa site:domain + keywords corretti (non la stringa hardcoded sbagliata)
        query = f'site:{domain} ({keywords}) (lavoro OR stage OR "part-time" OR concorso OR assunzione)'
        logger.info(f"Sito aziendale: {company_cfg['label']}")
        try:
            # FIX: GET invece di POST — DuckDuckGo HTML risponde 202 su POST da bot
            ddg_url = f"https://html.duckduckgo.com/html/?q={quote(query)}&kl=it-it"
            response = tls_session.get(
                ddg_url,
                headers=HEADERS,
                timeout_seconds=30,
            )
            # Gestisci 202 (queued) con retry
            if response.status_code == 202:
                logger.debug(f"  -> DuckDuckGo 202 queued, retry in 3s...")
                time.sleep(3)
                response = tls_session.get(ddg_url, headers=HEADERS, timeout_seconds=30)
            if response.status_code != 200:
                logger.warning(f"  -> risposta {response.status_code}")
                continue
            soup = BeautifulSoup(response.text, "html.parser")
            links = soup.select("a.result__a")[:8]
            found = 0
            for link in links:
                title = normalize_text(link.get_text(" ", strip=True))
                href = normalize_text(link.get("href"))
                title_lower = title.lower()

                if not contains_any(title_lower, COMPANY_RELEVANCE_KEYWORDS):
                    continue
                if contains_any(title_lower, EXCLUDE_KEYWORDS_TITLE):
                    continue

                results.append(
                    {
                        "title": title,
                        "company": company,
                        "location": company_cfg["country"],
                        "search_country": company_cfg["country"],
                        "job_url": href,
                        "official_url": href,
                        "description": f"{company_cfg['label']} | query: {keywords}",
                        "site": domain,
                        "source_type": "company_site",
                        "date_posted": datetime.now().strftime("%Y-%m-%d"),
                    }
                )
                found += 1
            logger.info(f"  -> {found} risultati grezzi")
        except Exception as exc:
            logger.warning(f"  -> Errore sito aziendale: {exc}")
        time.sleep(1.5)
    return pd.DataFrame(results)


def scrape_italian_portals() -> pd.DataFrame:
    """
    Scraping di portali italiani specifici non coperti da jobspy.
    NB: Bakeca rimosso — blocca tutte le richieste con HTTP 403.
    """
    # FIX: rimosso Bakeca (HTTP 403 su 100% delle richieste, nessuna API alternativa)
    italian_portals = [
        {
            "name": "TrovoLavoro",
            "base_url": "https://www.trovolavoro.it",
            "search_endpoint": "/offerte",
            "query_param": "q",
            "location_param": "luogo",
            "locations": ["Trapani", "Sicilia", "Italia"],
        },
        {
            "name": "Jobrapido",
            "base_url": "https://it.jobrapido.com",
            "search_endpoint": "/offerte-di-lavoro",
            "query_param": "q",
            "location_param": "l",
            "locations": ["Trapani", "Sicilia", "Italia"],
        },
        {
            "name": "Neuvoo",
            "base_url": "https://neuvoo.it",
            "search_endpoint": "/",
            "query_param": "q",
            "location_param": "l",
            "locations": ["Trapani", "Sicilia", "Italia"],
        },
        {
            "name": "Jobsora",
            "base_url": "https://it.jobsora.com",
            "search_endpoint": "/",
            "query_param": "q",
            "location_param": "l",
            "locations": ["Trapani", "Sicilia", "Italia"],
        },
        {
            "name": "Injob",
            "base_url": "https://www.injob.com",
            "search_endpoint": "/it/offerte-lavoro",
            "query_param": "keyword",
            "location_param": "location",
            "locations": ["Trapani", "Sicilia", "Italia"],
        },
        {
            "name": "InfoJobs",
            "base_url": "https://www.infojobs.it",
            "search_endpoint": "/offerte-lavoro",
            "query_param": "keyword",
            "location_param": "provinceOrCountry",
            "locations": ["Trapani", "Palermo", "Catania"],
        },
    ]

    all_jobs = []

    for portal in italian_portals:
        for search_term in SEARCH_TERMS[:15]:  # prime 15 query per velocità
            for location in portal["locations"]:
                try:
                    base = portal["base_url"]
                    endpoint = portal["search_endpoint"]

                    query_params = [
                        f"{portal['query_param']}={quote(search_term)}",
                        f"{portal['location_param']}={quote(location)}",
                    ]
                    url = f"{base}{endpoint}?{'&'.join(query_params)}"

                    logger.info(f"Portale {portal['name']}: '{search_term}' in {location}")

                    # FIX: try/except corretto (era try senza except)
                    try:
                        response = tls_session.get(url, headers=HEADERS, timeout_seconds=25)
                    except Exception as req_exc:
                        logger.warning(f"  -> Connessione fallita {portal['name']}: {req_exc}")
                        continue

                    if response.status_code != 200:
                        logger.warning(f"  -> HTTP {response.status_code}")
                        continue

                    soup = BeautifulSoup(response.text, "html.parser")

                    job_links = soup.select(
                        "a[href*='/offerte/'], a[href*='/lavoro/'], a[href*='/job/']"
                    )
                    job_links += soup.select("a[href*='dettaglio']")

                    found = 0
                    for link in job_links[:5]:
                        href = link.get("href", "")
                        title = normalize_text(link.get_text(" ", strip=True))

                        if not href or not title or len(title) < 5:
                            continue

                        if href.startswith("/"):
                            href = f"{base}{href}"
                        elif not href.startswith("http"):
                            continue

                        title_lower = title.lower()
                        if not contains_any(title_lower, [
                            "amministrativo", "contabilità", "back office", "fatturazione",
                            "segreteria", "ufficio", "impiegato", "part-time", "smart working",
                            "remoto", "ragioneria", "diploma", "praticante",
                        ]):
                            continue

                        if contains_any(title_lower, EXCLUDE_KEYWORDS_TITLE):
                            continue

                        all_jobs.append({
                            "title": title[:200],
                            "company": portal["name"],
                            "location": location,
                            "search_country": location if location in ["Trapani", "Sicilia"] else "Italia",
                            "job_url": href,
                            "official_url": href,
                            "description": f"{portal['name']} | query: {search_term}",
                            "site": base.replace("https://", "").replace("www.", ""),
                            "source_type": "italian_portal",
                            "date_posted": datetime.now().strftime("%Y-%m-%d"),
                        })
                        found += 1

                    if found > 0:
                        logger.info(f"  -> {found} offerte trovate")

                except Exception as exc:
                    logger.warning(f"  -> Errore {portal['name']}: {exc}")

                time.sleep(2)

    if not all_jobs:
        return pd.DataFrame()

    return pd.DataFrame(all_jobs)


def is_actual_job_posting(url: str, title: str) -> bool:
    """Verifica che il link sia effettivamente un annuncio di lavoro e non un articolo di blog."""
    text = f"{url} {title}".lower()
    
    # Escludi domini editoriali/wiki
    if any(skip in url.lower() for skip in [
        "notizia", "news", "blog", "giornale", "wikipedia", "ilsole24ore", 
        "corriere.it", "repubblica.it", "today.it", "ansa.it"
    ]):
        return False
        
    # Deve contenere parole tipiche da annuncio
    job_markers = [
        "candidati", "candidatura", "job", "career", "lavoro", "posizione", 
        "assunzione", "concorso", "bando", "offerta", "opportunita"
    ]
    return any(marker in text for marker in job_markers)


def search_duckduckgo() -> list[dict]:
    """
    Cerca su DuckDuckGo per trovare offerte di lavoro su tutti i siti .it
    Restituisce una lista di risultati grezzi da parsare.
    """
    results = []
    
    # Query di ricerca specifiche per questo profilo
    # Crea query che cercano su tutti i siti .it
    queries = [
        'site:*.it "back office" part-time Trapani',
        'site:*.it "impiegato amministrativo" diploma',
        'site:*.it "contabilità" "part-time" Sicilia',
        'site:*.it "segreteria" "smart working"',
        'site:*.it "praticante" "studio commercialista" Trapani',
        'site:*.it "addetto" "ufficio" diploma',
        'site:*.it "fatturazione" "tempo parziale"',
        'site:*.it "ragioneria" "stage"',
        'site:*.it "concorsi pubblici" "categoria C" diplomati',
        'site:*.it "back office" remoto Italia',
        'site:*.it "amministrazione" "injob" Trapani OR Sicilia OR "smart working"',
        'site:*.it "lavoro" "amministrativo" "full remote"',
        'site:*.it "assunzione" "impiegato contabile" Trapani',
    ]
    
    for query in queries:
        try:
            url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
            response = tls_session.post(
                "https://html.duckduckgo.com/html/",
                data={"q": query, "kl": "it-it"},
                headers=HEADERS,
                timeout_seconds=30,
            )
            
            if response.status_code != 200:
                logger.warning(f"DuckDuckGo HTTP {response.status_code} per: {query[:50]}")
                continue
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Cerca tutti i link nei risultati
            result_links = soup.select("a.result__a, a[class*='result__url'], [class*='result-link']")
            
            found = 0
            for link in result_links[:10]:  # Max 10 per query
                href = link.get("href", "")
                title = normalize_text(link.get_text(" ", strip=True))
                
                if not href or not title or len(title) < 5:
                    continue
                
                # Filtra URL non rilevanti
                href_lower = href.lower()
                if any(skip in href_lower for skip in [
                    "facebook.com", "twitter.com", "linkedin.com/in/",
                    "youtube.com", "instagram.com", "wikipedia.org",
                    "google.com/search", "bing.com"
                ]):
                    continue
                
                # Completa URL se necessario
                if href.startswith("http"):
                    pass  # OK
                elif href.startswith("//"):
                    href = f"https:{href}"
                elif href.startswith("/"):
                    # Prova a ricostruire l'URL
                    continue  # Salta, non sappiamo il dominio
                else:
                    continue
                
                # Filtra per keyword rilevanti e verifica che sia una vera candidatura
                title_lower = title.lower()
                if not is_actual_job_posting(href, title):
                    continue
                
                # Non escludere ancora qui, lascia che il filtro principale decida
                # Aggiungi il risultato
                results.append({
                    "title": title[:200],
                    "job_url": href,
                    "official_url": href,
                    "description": f"DuckDuckGo search: {query[:80]}",
                    "site": extract_domain(href),
                    "source_type": "duckduckgo",
                    "location": "Italia",  # Sarà determinato in normalize_jobs
                    "search_country": "Italia",
                    "company": "",
                    "date_posted": datetime.now().strftime("%Y-%m-%d"),
                })
                found += 1
                
                if found >= 5:  # Max 5 per query
                    break
                    
            if found > 0:
                logger.info(f"DuckDuckGo: {found} risultati per query: {query[:60]}")
                
        except Exception as exc:
            logger.warning(f"Errore DuckDuckGo: {exc}")
        
        time.sleep(3)  # Delay più lungo per evitare ban
    
    return results


def universal_job_search() -> pd.DataFrame:
    """
    Ricerca universale su TUTTI i portali possibili.
    Usa DuckDuckGo per trovare offerte che non sono coperte dai portali specifici.
    """
    logger.info("=== RICERCA UNIVERSALE (DuckDuckGo) ===")
    
    try:
        results = search_duckduckgo()
        
        if not results:
            return pd.DataFrame()
        
        df = pd.DataFrame(results)
        df = df.drop_duplicates(subset=["job_url"], keep="first")
        logger.info(f"Ricerca universale: {len(df)} risultati unici")
        return df
        
    except Exception as exc:
        logger.warning(f"Errore ricerca universale: {exc}")
        return pd.DataFrame()


def normalize_jobs(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalizza e deduplica le offerte di lavoro.
    IMPORTANTE: Preferisce job_url_direct (URL diretto all'annuncio) su job_url
    (che LinkedIn/JobSpy spesso riempie con URL generici tipo /jobs/view/XXX).
    """
    if df.empty:
        return df

    work = df.copy()
    
    # Standardizza nomi colonne
    if hasattr(work, 'columns'):
        work.columns = [normalize_text(column).lower() for column in work.columns]

    # ── FIX: Preferisci SEMPRE job_url_direct (URL specifico) su job_url (generico) ──
    # JobSpy restituisce:
    #   - job_url: spesso un URL LinkedIn generico (es. /jobs/view/4415255278)
    #              che è LO STESSO per tutte le offerte della stessa ricerca → BUG DUPLICATI
    #   - job_url_direct: l'URL effettivo dell'annuncio sul sito dell'azienda → CORRETTO
    if "job_url_direct" in work.columns:
        # Usa job_url_direct come URL primario quando non è vuoto
        work["job_url"] = work.apply(
            lambda row: (normalize_text(row.get("job_url_direct", ""))
                        or normalize_text(row.get("job_url", ""))),
            axis=1,
        )
    elif "job_url" not in work.columns:
        if "url" in work.columns:
            work["job_url"] = work["url"]
        else:
            work["job_url"] = ""

    for column in [
        "title", "company", "location", "description", "site",
        "source_type", "search_country", "date_posted", "job_url",
    ]:
        if column not in work.columns:
            work[column] = ""

    work["title"] = work["title"].apply(normalize_text)
    work["company"] = work["company"].apply(normalize_text)
    work["location"] = work["location"].apply(normalize_text)
    work["description"] = work["description"].apply(normalize_text)
    work["site"] = work["site"].apply(normalize_text)
    work["source_type"] = work["source_type"].apply(normalize_text)
    work["search_country"] = [
        infer_country_label(loc, label)
        for loc, label in zip(work["location"], work["search_country"])
    ]
    work["official_url"] = work["job_url"].apply(canonicalize_url)
    work["job_url"] = work["job_url"].apply(canonicalize_url)
    work["source_priority"] = [
        source_priority(source_type, site)
        for source_type, site in zip(work["source_type"], work["site"])
    ]

    # ── Deduplicazione multi-livello ────────────────────────────────────────
    # 1. Fingerprint basato su URL quando l'URL è unico e significativo
    # 2. Fingerprint basato su titolo+azienda+location quando l'URL è generico/duplicato
    work["job_fingerprint"] = work.apply(
        lambda row: _smart_fingerprint(row.to_dict(), work), axis=1
    )
    work = work.sort_values(["job_fingerprint", "source_priority"], ascending=[True, False])
    work = work.drop_duplicates(subset=["job_fingerprint"], keep="first")

    # ── Safety net: elimina righe con URL identici (ulteriore protezione) ──
    # Se 30 righe diverse hanno comunque lo stesso URL → tieni solo la migliore
    work = work.sort_values(["source_priority"], ascending=[False])
    non_empty_url = work["job_url"].str.strip() != ""
    # Tra quelle con URL non vuoto, drop duplicate per URL
    deduped_url = work[non_empty_url].drop_duplicates(subset=["job_url"], keep="first")
    # Unisci con quelle senza URL
    work = pd.concat([deduped_url, work[~non_empty_url]], ignore_index=True)

    return work.reset_index(drop=True)


def is_trapani_area(location: str) -> bool:
    """Verifica se la località è in provincia di Trapani."""
    loc = normalize_text(location).lower()
    trapani_areas = [
        "trapani", "valderice", "paceco", "erice", "custonaci", 
        "san vito", "alcamo", "marsala", "mazara", "castelvetrano",
        "buseto", "calatafimi", "campobello", "fulgatore",
        "petrosino", "salemi", "partanna", "castellammare",
        "pantelleria", "favignana", "gibellina", "vita", "salaparuta", "poggioreale",
    ]
    return any(area in loc for area in trapani_areas)


def is_wrong_region(location: str) -> bool:
    """Rileva se la località è palesemente in un'altra regione (es. Veneto, Lombardia)."""
    loc = normalize_text(location).lower()
    wrong_regions = [
        "veneto", "lombardia", "piemonte", "emilia", "toscana", "lazio", 
        "campania", "puglia", "calabria", "marche", "umbria", "abruzzo",
        "venezia", "milano", "torino", "bologna", "firenze", "roma", "napoli", "bari",
        "vicenza", "treviso", "padova", "verona", "brescia", "bergamo",
    ]
    # Se contiene una di queste MA NON contiene Trapani/Sicilia
    if any(reg in loc for reg in wrong_regions):
        if not is_trapani_area(location) and not is_sicily_area(location):
            return True
            
    # Controlla anche casi in cui viene citata Milano e basta nel titolo o chiaramente nella location
    return False

def has_strict_wrong_region_in_text(title: str, description: str) -> bool:
    """Controlla se il testo indica esplicitamente una regione sbagliata come sede prevalente."""
    text = f"{title} {description}".lower()
    
    # Se è chiaramente smart working, perdoniamo
    if is_smart_working("", description, title):
        return False
        
    # Se il titolo contiene esplicitamente una città palesemente lontana
    title_lower = title.lower()
    strict_wrong = ["milano", "roma", "torino", "bologna", "firenze", "venezia", "lombardia", "veneto", "emilia"]
    for w in strict_wrong:
        if re.search(rf"\b{w}\b", title_lower):
            return True
            
    # Check "sede di lavoro: Milano", "trasferimento a Milano" o simili
    if re.search(r"(sede di lavoro|sede|lavoro|location)[:\-\s]*(milano|roma|torino|bologna|firenze|venezia|lombardia|veneto|emilia|padova|verona|brescia|bergamo)", text):
        return True
        
    if re.search(r"(disponibilità al trasferimento|trasferimento richiesto a)\s*(milano|roma|torino|bologna|firenze|venezia|lombardia|veneto|emilia|nord italia)", text):
        return True
        
    return False



def is_sicily_area(location: str) -> bool:
    """Verifica se la località è in Sicilia."""
    loc = normalize_text(location).lower()
    sicily_areas = [
        "sicilia", "sicily", "catania", "messina", "siracusa",
        "ragusa", "enna", "caltanissetta", "agrigento",
    ]
    return any(area in loc for area in sicily_areas)

def is_palermo_area(location: str) -> bool:
    """Verifica se la località è Palermo o provincia."""
    loc = normalize_text(location).lower()
    palermo_areas = ["palermo", "bagheria", "monreale", "carini", "partinico", "termini imerese"]
    return any(area in loc for area in palermo_areas)


def is_smart_working(location: str, description: str, title: str) -> bool:
    """Verifica se l'annuncio è per smart working / remoto."""
    text = f"{location} {description} {title}".lower()
    smart_keywords = [
        "smart working", "remoto", "remote", "lavoro da casa", "work from home",
        "da remoto", "telelavoro", "home office", "da casa", "full remote", "100% remote", "lavoro agile"
    ]
    return any(kw in text for kw in smart_keywords)


def is_italy_only_location(location: str) -> bool:
    """Verifica se la location è generica Italia senza specifiche regionali."""
    loc = normalize_text(location).lower()
    italy_keywords = ["italia", "italy", "nazionale", "tutta italia", "tutta italia"]
    return any(kw in loc for kw in italy_keywords)


def is_allowed_location(location: str, search_country: str = "") -> bool:
    """
    Determina se una località è permessa per questo profilo.
    Permesso: Trapani, Sicilia, Smart Working/Remoto/Italia (solo se search_country è Trapani/Sicilia)
    Escluso: Tutte le altre città/regioni italiane e estere
    """
    loc = normalize_text(location).lower()
    
    # Se è Trapani o Sicilia -> permesso
    if is_trapani_area(location) or is_sicily_area(location) or is_palermo_area(location):
        return True
    
    # Se contiene keyword di smart working -> permesso
    if is_smart_working(location, "", ""):
        return True
    
    # Se la location è generica "Italia" ma il search_country specifica Trapani/Sicilia/Palermo
    if is_italy_only_location(location):
        country = normalize_text(search_country).lower()
        if country in ["trapani", "sicilia", "palermo"]:
            return True
        # Se non è smart working e non è Trapani/Sicilia -> NON permesso
        return False
    
    # Se la location contiene altre città/regioni italiane NON in Sicilia
    # e non è smart working -> NON permesso
    other_cities = [
        "milano", "roma", "torino", "bologna", "firenze", "napoli", "bari",
        "venezia", "verona", "genova", "trieste", "trento", "bolzano",
        "parma", "modena", "reggio emilia", "ravenna", "rimini",
        "lombardia", "piemonte", "emilia", "toscana", "lazio", 
        "campania", "puglia", "calabria", "marche", "umbria", "abruzzo",
        "veneto", "liguria", "friuli", "valle d'aosta", "sardegna",
        "bergamo", "brescia", "padova", "vicenza", "treviso",
        "mantova", "cremona", "lecco", "lodi", "sondrio", "varese",
        "obi", "novara", "monza", "brianza", "comasco", "varesotto",
    ]
    if any(city in loc for city in other_cities):
        return False
    
    # Se non si capisce la location, ma non è evidentemente sbagliata,
    # verifica se contiene "italia" senza altre specifiche
    if "italia" in loc or "italy" in loc:
        return True  # Accetta location generiche Italia
    
    # Default: accetta (per non escludere offerte valide con location non standard)
    return True


def classify_role_family(full_text: str) -> str:
    for family, keywords in ROLE_FAMILY_KEYWORDS.items():
        if contains_any(full_text, keywords):
            return family
    if contains_any(full_text, ["amministrativo", "contabilità", "fattura", "segreteria", "ufficio"]):
        return "amministrazione_generale"
    if contains_any(full_text, ["concorso", "pubblico", "categoria", "inpa"]):
        return "concorsi_pubblici"
    return "other"


def infer_company_tier(company: str, source_type: str, full_text: str) -> str:
    company_text = normalize_text(company).lower()
    
    # Enti pubblici e PA
    if contains_any(company_text, ["comune", "provincia", "regione", "asl", "inps", "agenzia", "ente"]):
        return "A"
    # Studi commercialisti
    if contains_any(company_text, ["commercialista", "studio", "commerciale"]):
        return "A"
    # Agenzie per il lavoro
    if contains_any(company_text, ["adecco", "manpower", "randstad", "gi group", "openjobmetis", "synergie", "etjca", "humangest"]):
        return "A"
    # Altre aziende preferite
    if contains_any(company_text, PREFERRED_COMPANY_INDICATORS):
        return "A"
    if source_type in ("subito", "concorso_pubblico", "company_site"):
        return "A"
    if contains_any(full_text, ["multinazionale", "grande azienda", "corporate"]):
        return "B"
    return "C"


def compute_keyword_score(full_text: str) -> tuple[int, list[str]]:
    score_15 = 0
    score_8 = 0
    score_5 = 0
    hits = []

    for keyword, points in PROFILE_KEYWORDS_SCORES:
        if keyword.lower() in full_text:
            if points == 15 and score_15 < 60:
                score_15 += points
            elif points == 8 and score_8 < 40:
                score_8 += points
            elif points == 5 and score_5 < 25:
                score_5 += points
            hits.append(keyword)

    score_15 = min(score_15, 60)
    score_8 = min(score_8, 40)
    score_5 = min(score_5, 25)

    return score_15 + score_8 + score_5, hits[:8]


def detect_language_fit(full_text: str) -> tuple[bool, bool, bool]:
    """Per questo profilo, l'italiano è la lingua richiesta. Inglese non necessario."""
    english_ok = contains_any(full_text, ["english", "inglese", "english speaking"])
    # Se richiede altre lingue escludiamo
    other_lang_required = contains_any(full_text, [
        "french required", "german required", "spagnolo richiesto",
        "francese richiesto", "tedesco richiesto",
    ])
    local_language_plus = False  # Non rilevante per italiano
    return english_ok, other_lang_required, local_language_plus


def evaluate_job(row: pd.Series, previous_fingerprints: set[str]) -> dict:
    title = normalize_text(row.get("title"))
    company = normalize_text(row.get("company"))
    location = normalize_text(row.get("location"))
    description = normalize_text(row.get("description"))
    country = infer_country_label(location, row.get("search_country", ""))
    full_text = f"{title} {company} {location} {description}".lower()
    fingerprint = normalize_text(row.get("job_fingerprint"))
    source_type = normalize_text(row.get("source_type") or row.get("site"))

    if fingerprint in previous_fingerprints:
        return {"excluded": True, "excluded_reason": "gia_presente_nello_storico"}

    if country in EXCLUDED_COUNTRIES:
        return {"excluded": True, "excluded_reason": "paese_escluso"}

    if country and country not in INCLUDED_COUNTRIES:
        return {"excluded": True, "excluded_reason": "paese_fuori_scope"}

    # Filtro stretto sulla località per evitare falsi positivi
    # Usa il nuovo sistema di filtraggio geografico proattivo
    if not is_allowed_location(location, row.get("search_country", "")):
        return {"excluded": True, "excluded_reason": "localita_non_pertinente"}
    
    # Controllo aggiuntivo con il vecchio sistema per sicurezza
    if is_wrong_region(location) and not is_smart_working(location, description, title):
        return {"excluded": True, "excluded_reason": "localita_non_pertinente_wrong_region"}
        
    # Nuovo controllo stringente nel testo
    if has_strict_wrong_region_in_text(title, description):
        return {"excluded": True, "excluded_reason": "sede_lavoro_esplicita_in_regione_errata"}

    if contains_any(title, EXCLUDE_KEYWORDS_TITLE):
        return {"excluded": True, "excluded_reason": "titolo_non_compatibile"}

    if contains_any(full_text, EXCLUDE_KEYWORDS_TEXT):
        return {"excluded": True, "excluded_reason": "testo_non_compatibile"}

    # Se richiede laurea, escludi
    if re.search(r"\blaurea\b.{0,30}\b(richiesta|richiesto|necessaria|obbligatoria|indispensabile)\b", full_text):
        return {"excluded": True, "excluded_reason": "richiede_laurea"}
    
    if re.search(r"\blaurea\b", full_text) and not re.search(r"\b(diploma|diplomato|non richiede|senza)\b", full_text):
        # Controllo più fine: se "laurea" nel testo ma nessuna delle esclusioni
        if not contains_any(full_text, ["diploma", "diplomato", "non richiede laurea", "senza laurea", "basti il diploma"]):
            return {"excluded": True, "excluded_reason": "probabilmente_richiede_laurea"}

    # Se richiede troppo seniority
    if re.search(r"\b([5-9]|[1-9][0-9])\+?\s*(?:anni?|years?)\b|>\s*[45]\s*(?:anni?|years?)", full_text):
        return {"excluded": True, "excluded_reason": "troppo_senior"}

    # Se è un ruolo tecnico/non amministrativo
    if contains_any(title, ["operaio", "cameriere", "barista", "cuoco", "pizzaiolo", 
                            "commesso", "venditore", "autista", "elettricista", "idraulico"]):
        return {"excluded": True, "excluded_reason": "ruolo_non_compatibile"}

    role_family = classify_role_family(full_text)
    company_tier = infer_company_tier(company, source_type, full_text)

    keyword_score_raw, hits = compute_keyword_score(full_text)

    english_ok, other_lang_required, local_plus = detect_language_fit(full_text)

    if other_lang_required:
        return {"excluded": True, "excluded_reason": "richiede_altra_lingua"}

    # --- Punteggio ---
    
    # Livello diploma: premia se non richiede laurea o se specifica diploma
    level_score = 0
    if contains_any(full_text, MASTER_LEVEL_KEYWORDS):
        level_score += 20
    if re.search(r"\b(diploma|diplomato|ragioneria|afm|maturità)\b", full_text):
        level_score += 15
    if re.search(r"\b(0[-–]?[234]|1[-–]?[234])\s*(?:anni?|years?)\b", full_text) or contains_any(title, ["junior", "entry", "prima esperienza", "neodiplomato"]):
        level_score += 10
    # Esperienza di 4 anni: premia se chiede 2-4 anni
    if re.search(r"\b([23][-–]?[45])\s*(?:anni?|years?)\b|\b[234]\s*(?:anni?|years?)\b", full_text):
        level_score += 10

    # Punteggio part-time / smart working
    part_time_score = 0
    if contains_any(full_text, ["part-time", "part time", "tempo parziale", "mezza giornata", "20 ore", "25 ore", "30 ore"]):
        part_time_score += 10  # Leggero bonus per il part-time, ma ha disponibilità immediata anche full-time
    
    if is_smart_working(location, description, title):
        part_time_score += 20
    
    # Bonus WordPress / E-commerce (skill specifica)
    tech_bonus = 0
    if contains_any(full_text, ["wordpress", "ecommerce", "e-commerce", "woocommerce", "shopify", "gestione ordini"]):
        tech_bonus += 20

    # Punteggio ufficio / ragioneria
    office_score = 0
    if contains_any(full_text, [
        "amministrativo", "contabilità", "fatturazione", "segreteria", "ufficio",
        "commercialista", "ragioneria", "contabile", "bilancio", "partita doppia",
    ]):
        office_score += 20

    # Punteggio geografico
    geo_score = 0
    if is_trapani_area(location):
        geo_score += 30  # Trapani è la priorità assoluta
    elif country == "Trapani":
        geo_score += 30
    elif is_palermo_area(location) or country == "Palermo":
        geo_score += 10  # Palermo ammissibile ma punteggio minore
    elif is_sicily_area(location) or country == "Sicilia":
        geo_score += 15
    elif country == "Italia" and is_smart_working(location, description, title):
        geo_score += 20
    elif country == "Italia":
        geo_score += 5
    
    # Bonus specifico per Trapani nel testo
    if "trapani" in full_text or "marsala" in full_text or "erice" in full_text or "alcamo" in full_text:
        geo_score += 10

    rule_score = keyword_score_raw + geo_score + level_score + office_score + part_time_score + tech_bonus
    final_score = min(100, rule_score)

    if final_score < MINIMUM_RELEVANT_SCORE:
        return {"excluded": True, "excluded_reason": "sotto_soglia_pertinenza"}

    why_parts = []
    if part_time_score >= 40:
        why_parts.append("PART-TIME OK")
    if geo_score >= 30:
        why_parts.append("ZONA TRAPANI")
    if tech_bonus > 0:
        why_parts.append("WordPress/E-comm")
    if hits:
        why_parts.append(", ".join(hits[:2]))

    smart = is_smart_working(location, description, title)
    modality = "Smart Working" if smart else "In Sede"

    return {
        "excluded": False,
        "excluded_reason": "",
        "country": country or row.get("search_country", ""),
        "modality": modality,
        "role_family": role_family,
        "company_tier": company_tier,
        "english_ok": english_ok,
        "native_language_required": False,
        "local_language_plus": local_plus,
        "keyword_score": keyword_score_raw,
        "technical_score": keyword_score_raw,
        "level_score": level_score,
        "function_score": office_score,
        "company_score": 0,
        "language_score": 0,
        "geo_score": geo_score,
        "part_time_score": part_time_score,
        "source_score": 0,
        "rule_score": rule_score,
        "final_score": final_score,
        "match_grade": grade_from_score(final_score),
        "why_match": " | ".join(why_parts[:4]),
        "matched_keywords": ", ".join(hits),
        "apply_status": "new",
    }


def evaluate_job_second_chance(row: pd.Series, evaluation: dict) -> dict:
    """
    Valutazione secondaria per offerte che sono state escluse
    ma potrebbero essere rilevanti per questo profilo.
    
    Questo ogni la possibilità a offerte borderline che contengono
    keyword critiche per il profilo Back Office / Ragioneria.
    """
    title = normalize_text(row.get("title"))
    description = normalize_text(row.get("description"))
    full_text = f"{title} {description}".lower()
    
    # Controlla se contiene keyword CRITICHE per questo profilo
    critical_keywords = [
        "back office", "amministrativo", "contabilità", "fatturazione",
        "segreteria", "ufficio", "impiegato", "part-time", "smart working",
        "remoto", "ragioneria", "diploma", "praticante", "studio commercialista",
        "concorsi pubblici", "categoria c", "categoria d", "trapani", "sicilia",
        "addetto contabilità", "assistente amministrativo", "gestione documentale"
    ]
    
    # Se contiene almeno 2 keyword critiche, NON escludere e assegna score minimo
    matching_keywords = [kw for kw in critical_keywords if kw in full_text]
    if len(matching_keywords) >= 2:
        logger.info(f"Second chance: '{title[:50]}' - matched {len(matching_keywords)} keywords: {matching_keywords[:3]}")
        return {
            "excluded": False,
            "excluded_reason": "",
            "final_score": 25,  # Score minimo per superare la soglia
            "match_grade": "C",
            "why_match": f"Second chance - {', '.join(matching_keywords[:3])}"
        }
    
    return evaluation


def filter_and_rank(df: pd.DataFrame, previous_fingerprints: set[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    relevant_rows = []
    excluded_rows = []

    for _, row in df.iterrows():
        row_dict = row.to_dict()
        evaluation = evaluate_job(row, previous_fingerprints)
        
        # Se escluso, prova la second chance
        if evaluation.get("excluded"):
            evaluation = evaluate_job_second_chance(row, evaluation)
        
        merged = {**row_dict, **evaluation}
        if evaluation.get("excluded"):
            excluded_rows.append(merged)
        else:
            relevant_rows.append(merged)

    relevant_df = pd.DataFrame(relevant_rows)
    excluded_df = pd.DataFrame(excluded_rows)

    if not relevant_df.empty:
        relevant_df["search_country"] = relevant_df["country"].replace("", pd.NA).fillna(relevant_df.get("search_country", ""))
        relevant_df = relevant_df.sort_values(["final_score", "source_priority"], ascending=[False, False]).reset_index(drop=True)

    if not excluded_df.empty:
        excluded_df = excluded_df.sort_values("excluded_reason").reset_index(drop=True)

    return relevant_df, excluded_df


def _parse_json_response(content: str):
    text = normalize_text(content)
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else parts[0]
        text = re.sub(r"^json", "", text).strip()
    return json.loads(text)


def ai_rank_jobs(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ranking AI con Mistral. Gestisce il rate limiting con:
    - Batch grandi (30 job) per ridurre le chiamate API
    - Delay fisso tra batch (4s)
    - Backoff esponenziale su 429 (15s → 30s → 60s)
    """
    if not MISTRAL_API_KEY or df.empty:
        return df

    try:
        from openai import OpenAI
    except Exception as exc:
        logger.warning(f"Client Mistral non disponibile: {exc}")
        return df

    client = OpenAI(base_url="https://api.mistral.ai/v1", api_key=MISTRAL_API_KEY)
    enriched = df.copy()
    enriched["ai_score"] = pd.NA
    enriched["ai_reason"] = ""

    BATCH_SIZE = 30          # Batch grandi → meno chiamate API (prima era 15)
    DELAY_BETWEEN = 4        # Secondi tra batch (prima era 0)
    MAX_RETRIES = 3          # Max retry per batch su 429
    total_batches = (len(enriched) + BATCH_SIZE - 1) // BATCH_SIZE
    consecutive_429 = 0      # Contatore 429 consecutivi

    for batch_num, start in enumerate(range(0, len(enriched), BATCH_SIZE), 1):
        batch = enriched.iloc[start:start + BATCH_SIZE]
        jobs_summary = []
        for idx, row in batch.iterrows():
            jobs_summary.append(
                {
                    "idx": str(idx),
                    "title": normalize_text(row.get("title")),
                    "company": normalize_text(row.get("company")),
                    "location": normalize_text(row.get("location")),
                    "country": normalize_text(row.get("search_country")),
                    "description_snippet": normalize_text(row.get("description"))[:550],
                    "rule_score": float(row.get("rule_score", 0)),
                    "role_family": normalize_text(row.get("role_family")),
                }
            )

        prompt = f"""Sei un assistente AI specializzato nel recruiting e nella ricerca lavoro.
Il candidato si chiama Andrea Carini, ha 25 anni, Diplomato Ragioniere (Istituto Tecnico Economico), con oltre 6 anni di esperienza in:
- Gestione operativa punto vendita, supporto clienti e chiusura cassa
- Contabilità generale, prima nota (ERP: SAP Business One, Teamsystem, Zucchetti)
- Gestione ordini, logistica, inventario (WMS, ERP) e spedizioni
- Gestione e-commerce e siti web (WordPress, Shopify, WooCommerce)

Ha disponibilità immediata ed è automunito. Cerca lavoro come:
- Impiegato amministrativo / Addetto back office / Contabilità
- Addetto logistica / Gestione ordini e spedizioni
- Customer service back office
- Segreteria amministrativa

Regole per il ranking (0-100):
- +20 se è a Trapani o provincia
- +15 se è in Sicilia
- +20 se smart working / remoto / lavoro da casa / full remote
- +15 se non richiede laurea, basta il diploma
- +10/15 se il ruolo è coerente con la logistica, magazzino, ERP o contabilità
- Premia stage/praticantato (fa esperienza)
- Penalizza fortemente se richiede laurea
- Penalizza ruoli troppo senior (responsabile, dirigente, capo)

Valuta le offerte fornite. Restituisci SOLO un JSON array nel formato esatto (senza altre parole):
[{{ "idx": "id", "ai_score": 85, "reason": "Motivazione di massimo 10 parole" }}]

Offerte da valutare:
{json.dumps(jobs_summary, ensure_ascii=False, indent=2)}"""

        # Retry con backoff esponenziale su 429
        success = False
        for retry in range(MAX_RETRIES):
            try:
                logger.info(f"  AI Ranking batch {batch_num}/{total_batches} ({len(batch)} offerte)...")
                response = client.chat.completions.create(
                    model=MISTRAL_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=4000,
                )
                parsed = _parse_json_response(response.choices[0].message.content)
                mapping = {item["idx"]: item for item in parsed}
                applied = 0
                for idx in batch.index:
                    item = mapping.get(str(idx))
                    if item:
                        enriched.loc[idx, "ai_score"] = item.get("ai_score")
                        enriched.loc[idx, "ai_reason"] = normalize_text(item.get("reason"))
                        applied += 1
                logger.info(f"  AI Ranking batch {batch_num}: {applied}/{len(batch)} scored")
                consecutive_429 = 0
                success = True
                break

            except Exception as exc:
                exc_str = str(exc)
                if "429" in exc_str or "rate_limit" in exc_str.lower():
                    consecutive_429 += 1
                    # Backoff esponenziale: 15s, 30s, 60s
                    wait = min(15 * (2 ** retry), 60)
                    logger.info(
                        f"  AI Ranking batch {batch_num}: rate limit (429), "
                        f"attendo {wait}s (tentativo {retry + 1}/{MAX_RETRIES})..."
                    )
                    time.sleep(wait)
                else:
                    logger.info(f"  AI Ranking batch {batch_num} skippato: {exc}")
                    break

        if not success and consecutive_429 >= 3:
            # Se 3+ batch consecutivi falliscono per rate limit, ferma l'AI ranking
            remaining = total_batches - batch_num
            logger.info(
                f"  AI Ranking: {consecutive_429} rate limit consecutivi, "
                f"skip {remaining} batch rimanenti (rule_score usato come fallback)"
            )
            break

        # Delay tra batch per evitare rate limiting
        if batch_num < total_batches:
            time.sleep(DELAY_BETWEEN)

    enriched["ai_score"] = pd.to_numeric(enriched["ai_score"], errors="coerce")
    enriched["final_score"] = enriched.apply(
        lambda row: round((row["rule_score"] * 0.6) + (row["ai_score"] * 0.4), 1)
        if pd.notna(row["ai_score"]) else round(float(row["rule_score"]), 1),
        axis=1,
    )
    enriched["match_grade"] = enriched["final_score"].apply(grade_from_score)
    enriched = enriched.sort_values(["final_score", "source_priority"], ascending=[False, False]).reset_index(drop=True)
    return enriched


def build_tracker_sheet(df: pd.DataFrame) -> pd.DataFrame:
    tracker = df.copy()
    tracker["Da_Valutare"] = "SI"
    tracker["Da_Candidare"] = ""
    tracker["Candidata"] = ""
    tracker["Data_Candidatura"] = ""
    tracker["Follow_Up"] = ""
    tracker["Colloquio"] = ""
    tracker["Esito"] = ""
    tracker["Note"] = ""
    return tracker[
        [
            "title", "company", "search_country", "location", "modality", "final_score", "match_grade",
            "why_match", "job_url", "Da_Valutare", "Da_Candidare", "Candidata",
            "Data_Candidatura", "Follow_Up", "Colloquio", "Esito", "Note",
        ]
    ].rename(
        columns={
            "title": "Posizione",
            "company": "Azienda/Ente",
            "search_country": "Zona",
            "location": "Località",
            "modality": "Modalità",
            "final_score": "Score",
            "match_grade": "Classe",
            "why_match": "Perché",
            "job_url": "URL",
        }
    )


def export_reports(relevant_df: pd.DataFrame, excluded_df: pd.DataFrame) -> tuple[Path | None, Path | None]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = REPORT_DIR / f"jobs_relevant_{timestamp}.csv"
    xlsx_path = REPORT_DIR / f"jobs_report_{timestamp}.xlsx"

    if relevant_df.empty:
        return None, None

    top_df = relevant_df[relevant_df["final_score"] >= TOP_MATCH_SCORE].copy()
    borderline_df = relevant_df[
        (relevant_df["final_score"] >= BORDERLINE_SCORE) & (relevant_df["final_score"] < TOP_MATCH_SCORE)
    ].copy()

    export_columns = [
        "title", "company", "search_country", "location", "modality", "role_family", "company_tier",
        "source_type", "site", "final_score", "rule_score", "ai_score", "match_grade",
        "why_match", "matched_keywords", "job_url",
    ]

    relevant_df.to_csv(csv_path, index=False, quoting=csv.QUOTE_NONNUMERIC, escapechar="\\")

    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        if not top_df.empty:
            top_df.reindex(columns=export_columns).to_excel(writer, index=False, sheet_name="Top_Match")
        relevant_df.reindex(columns=export_columns).to_excel(writer, index=False, sheet_name="All_Relevant")
        if not borderline_df.empty:
            borderline_df.reindex(columns=export_columns).to_excel(writer, index=False, sheet_name="Borderline")
        if not excluded_df.empty:
            excluded_df.reindex(
                columns=["title", "company", "search_country", "location", "source_type", "excluded_reason", "job_url"]
            ).to_excel(writer, index=False, sheet_name="Esclusi_Audit")
        if not relevant_df.empty:
            build_tracker_sheet(relevant_df).to_excel(writer, index=False, sheet_name="Tracker_Candidature")

    logger.info(f"CSV salvato: {csv_path}")
    logger.info(f"Excel salvato: {xlsx_path}")
    return xlsx_path, csv_path


def generate_text_report(df: pd.DataFrame) -> str:
    today = datetime.now().strftime("%d/%m/%Y")
    if df.empty:
        return f"📋 REPORT JOB HUNTER - {today}\n\nNessuna nuova offerta realmente nuova rispetto allo storico."

    trapani = int((df["search_country"] == "Trapani").sum())
    sicilia = int((df["search_country"] == "Sicilia").sum())
    italia = int(len(df) - trapani - sicilia)
    top = int((df["final_score"] >= TOP_MATCH_SCORE).sum())
    good = int(((df["final_score"] >= 50) & (df["final_score"] < TOP_MATCH_SCORE)).sum())
    part_time = int(df.get("part_time_score", pd.Series([0] * len(df))).fillna(0).sum() > 0)

    lines = [
        f"📋 REPORT JOB HUNTER - {today}",
        f"🔍 Profilo: Diplomato Ragioneria AFM | Back Office / Contabilità",
        f"📍 Zona: Trapani e provincia + Smart Working Italia",
        "",
        f"Nuove offerte: {len(df)}",
        f"Top match (≥{TOP_MATCH_SCORE}): {top} | Buone: {good}",
        f"📍 Trapani: {trapani} | Sicilia: {sicilia} | Italia/Smart: {italia}",
        "",
        "🏆 PRIME OFFERTE:",
    ]

    for idx, (_, row) in enumerate(df.head(10).iterrows(), start=1):
        emoji = "🔥" if row.get("final_score", 0) >= TOP_MATCH_SCORE else "⭐"
        lines.append(
            f"{emoji} {idx}. [{row.get('match_grade')}] {normalize_text(row.get('title'))} | "
            f"{normalize_text(row.get('company'))} | {normalize_text(row.get('search_country'))} | "
            f"score {row.get('final_score')}"
        )

    lines.append("")
    lines.append("📊 Legenda: 🔥 Top match | ⭐ Buona corrispondenza")
    lines.append("📎 Allego file Excel con Top_Match, All_Relevant, Borderline ed Esclusi_Audit.")
    lines.append("💡 Consiglio: dai priorità alle offerte a Trapani e provincia!")
    return "\n".join(lines)


def generate_email_html(df: pd.DataFrame) -> str:
    today = datetime.now().strftime("%d/%m/%Y")
    if df.empty:
        return f"<h2>Report Job Hunter - {today}</h2><p>Nessuna nuova offerta.</p>"

    rows = []
    for _, row in df.head(25).iterrows():
        emoji = "🔥" if row.get("final_score", 0) >= TOP_MATCH_SCORE else "⭐"
        rows.append(
            f"""
            <tr>
                <td style="padding:6px;border-bottom:1px solid #ddd;">{emoji} {row.get('match_grade')}</td>
                <td style="padding:6px;border-bottom:1px solid #ddd;">{normalize_text(row.get('title'))}</td>
                <td style="padding:6px;border-bottom:1px solid #ddd;">{normalize_text(row.get('company'))}</td>
                <td style="padding:6px;border-bottom:1px solid #ddd;">{normalize_text(row.get('search_country'))}</td>
                <td style="padding:6px;border-bottom:1px solid #ddd;">{row.get('final_score')}</td>
                <td style="padding:6px;border-bottom:1px solid #ddd;">{normalize_text(row.get('why_match'))}</td>
            </tr>
            """
        )

    trapani = int((df["search_country"] == "Trapani").sum())
    sicilia = int((df["search_country"] == "Sicilia").sum())

    return f"""
    <html>
        <body style="font-family:Arial,sans-serif;">
            <h2>📋 Report Job Hunter - {today}</h2>
            <p><strong>Profilo:</strong> Diplomato Ragioneria AFM | Back Office / Contabilità</p>
            <p><strong>📍 Zona:</strong> Trapani e provincia + Smart Working Italia</p>
            <hr>
            <p>Nuove offerte: <strong>{len(df)}</strong> 
               (Trapani: {trapani}, Sicilia: {sicilia}, Italia/Smart: {len(df) - trapani - sicilia})</p>
            <table style="border-collapse:collapse;width:100%;">
                <thead>
                    <tr style="background:#f5f5f5;">
                        <th style="padding:6px;text-align:left;">Classe</th>
                        <th style="padding:6px;text-align:left;">Posizione</th>
                        <th style="padding:6px;text-align:left;">Azienda</th>
                        <th style="padding:6px;text-align:left;">Zona</th>
                        <th style="padding:6px;text-align:left;">Score</th>
                        <th style="padding:6px;text-align:left;">Perché</th>
                    </tr>
                </thead>
                <tbody>{''.join(rows)}</tbody>
            </table>
            <p><strong>Legenda:</strong> 🔥 Top match (≥{TOP_MATCH_SCORE}) | ⭐ Buona corrispondenza</p>
            <p>📎 In allegato il file Excel completo con tracker candidature.</p>
            <p><em>💡 Consiglio: dai priorità alle offerte a Trapani e provincia!</em></p>
        </body>
    </html>
    """


def split_telegram_chunks(text: str, max_len: int = 4000) -> list[str]:
    if len(text) <= max_len:
        return [text]
    chunks = []
    current = ""
    for line in text.splitlines():
        candidate = f"{current}\n{line}".strip()
        if len(candidate) > max_len and current:
            chunks.append(current)
            current = line
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def send_telegram_message(text: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.info("Telegram non configurato.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    for chunk in split_telegram_chunks(text):
        try:
            response = requests.post(
                url,
                data={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": chunk,
                    "disable_web_page_preview": True,
                },
                timeout=30,
            )
            if response.status_code != 200:
                logger.error(f"Telegram message error: {response.text}")
            time.sleep(1)
        except Exception as exc:
            logger.error(f"Errore invio Telegram: {exc}")


def send_telegram_document(file_path: Path, caption: str = ""):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID or not file_path or not file_path.exists():
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    try:
        with open(file_path, "rb") as handle:
            response = requests.post(
                url,
                data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption[:900]},
                files={"document": (file_path.name, handle)},
                timeout=60,
            )
        if response.status_code != 200:
            logger.error(f"Telegram document error: {response.text}")
    except Exception as exc:
        logger.error(f"Errore invio documento Telegram: {exc}")


def send_email(html_content: str, attachment_path: Path | None = None):
    if not EMAIL_SENDER or not EMAIL_APP_PASSWORD:
        logger.info("Email non configurata.")
        return
    try:
        message = MIMEMultipart()
        message["Subject"] = f"Job Hunter Report - {datetime.now():%d/%m/%Y}"
        message["From"] = EMAIL_SENDER
        message["To"] = EMAIL_RECIPIENT
        message.attach(MIMEText(html_content, "html", "utf-8"))

        if attachment_path and attachment_path.exists():
            with open(attachment_path, "rb") as handle:
                attachment = MIMEApplication(handle.read(), _subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            attachment.add_header("Content-Disposition", "attachment", filename=attachment_path.name)
            message.attach(attachment)

        with smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_APP_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, message.as_string())

        logger.info("Email inviata")
    except Exception as exc:
        logger.error(f"Errore email: {exc}")


def update_history(df: pd.DataFrame, report_path: Path | None):
    if df.empty:
        return
    history = load_job_history()
    sent_at = datetime.now().isoformat()

    for _, row in df.iterrows():
        fingerprint = row.get("job_fingerprint")
        if not fingerprint:
            continue
        history[fingerprint] = {
            "title": normalize_text(row.get("title")),
            "company": normalize_text(row.get("company")),
            "job_url": canonicalize_url(row.get("job_url")),
            "search_country": normalize_text(row.get("search_country")),
            "sent_at": sent_at,
            "report_file": report_path.name if report_path else "",
        }

    save_json(HISTORY_FILE, history)

    legacy_seen = {
        canonicalize_url(row.get("job_url")): sent_at
        for _, row in df.iterrows()
        if canonicalize_url(row.get("job_url"))
    }
    save_json(SEEN_FILE, legacy_seen)


def main():
    start = time.time()
    logger.info("=" * 60)
    logger.info("JOB HUNTER BOT — Profilo Back Office / Ragioneria")
    logger.info("Ricerca CV-first con storico, deduplica, ranking e report Excel")
    logger.info(f"Target: Trapani e provincia + Smart Working Italia")
    logger.info("=" * 60)

    previous = known_fingerprints()
    logger.info(f"Offerte gia' note da storico/report precedenti: {len(previous)}")

    # Raccolta offerte da TUTTE le fonti
    df_portals = scrape_portals()
    logger.info(f"Portali classici (LinkedIn/Indeed/Google): {len(df_portals) if not df_portals.empty else 0}")

    df_company = scrape_company_sites()
    logger.info(f"Siti aziendali: {len(df_company) if not df_company.empty else 0}")
    
    # Scraping Subito.it (molto usato a Trapani)
    try:
        from scrapers.subito_it import scrape_subito
        df_subito = scrape_subito()
        logger.info(f"Subito.it: {len(df_subito) if not df_subito.empty else 0}")
    except Exception as exc:
        logger.warning(f"Errore Subito.it: {exc}")
        df_subito = pd.DataFrame()
    
    # Scraping Agenzie per il Lavoro
    try:
        from scrapers.agenzie_lavoro import scrape_agenzie_lavoro
        df_agenzie = scrape_agenzie_lavoro()
        logger.info(f"Agenzie lavoro: {len(df_agenzie) if not df_agenzie.empty else 0}")
    except Exception as exc:
        logger.warning(f"Errore agenzie lavoro: {exc}")
        df_agenzie = pd.DataFrame()
    
    # Scraping Concorsi Pubblici
    try:
        from scrapers.concorsi_pubblici import scrape_concorsi
        df_concorsi = scrape_concorsi()
        logger.info(f"Concorsi pubblici: {len(df_concorsi) if not df_concorsi.empty else 0}")
    except Exception as exc:
        logger.warning(f"Errore concorsi: {exc}")
        df_concorsi = pd.DataFrame()
    
    # Scraping Opportunità Giovani (formazione gratuita, inglese, bandi, UE, tirocini)
    try:
        from scrapers.opportunita.formazione_gratuita import scrape_opportunita
        df_opportunita = scrape_opportunita()
        logger.info(f"Opportunità giovani: {len(df_opportunita) if not df_opportunita.empty else 0}")
    except Exception as exc:
        logger.warning(f"Errore opportunità: {exc}")
        df_opportunita = pd.DataFrame()

    # Scraping Portali Italiani aggiuntivi (Bakeca, TrovoLavoro, Jobrapido, ecc.)
    try:
        df_italian_portals = scrape_italian_portals()
        logger.info(f"Portali italiani (Bakeca, TrovoLavoro, ecc.): {len(df_italian_portals) if not df_italian_portals.empty else 0}")
    except Exception as exc:
        logger.warning(f"Errore portali italiani: {exc}")
        df_italian_portals = pd.DataFrame()

    # Ricerca Universale (DuckDuckGo) - cerca su TUTTI i siti .it
    try:
        df_universal = universal_job_search()
        logger.info(f"Ricerca universale (DuckDuckGo): {len(df_universal) if not df_universal.empty else 0}")
    except Exception as exc:
        logger.warning(f"Errore ricerca universale: {exc}")
        df_universal = pd.DataFrame()

    frames = [
        frame for frame in [
            df_portals, df_company, df_subito, df_agenzie, df_concorsi, df_opportunita, df_italian_portals, df_universal
        ] if not frame.empty
    ]

    if not frames:
        text = generate_text_report(pd.DataFrame())
        html = generate_email_html(pd.DataFrame())
        send_telegram_message(text)
        send_email(html)
        logger.info("Nessuna offerta grezza trovata da nessuna fonte")
        return

    df_all = normalize_jobs(pd.concat(frames, ignore_index=True))
    logger.info(f"Offerte grezze normalizzate e deduplicate: {len(df_all)}")

    relevant_df, excluded_df = filter_and_rank(df_all, previous)
    logger.info(f"Offerte rilevanti nuove: {len(relevant_df)}")
    logger.info(f"Offerte escluse/audit: {len(excluded_df)}")

    # Statistiche per fonte
    if not relevant_df.empty:
        for source in relevant_df["source_type"].unique():
            count = (relevant_df["source_type"] == source).sum()
            logger.info(f"  Fonte '{source}': {count} rilevanti")

    if not relevant_df.empty:
        relevant_df = ai_rank_jobs(relevant_df)

    xlsx_path, csv_path = export_reports(relevant_df, excluded_df)
    text_report = generate_text_report(relevant_df)
    html_report = generate_email_html(relevant_df)

    send_telegram_message(text_report)
    if xlsx_path:
        send_telegram_document(xlsx_path, f"Report Job Hunter Back Office - {datetime.now():%d/%m/%Y}")
    send_email(html_report, xlsx_path)

    update_history(relevant_df, xlsx_path)

    elapsed = time.time() - start
    logger.info(f"Ricerca completata in {elapsed:.0f}s ({elapsed / 60:.1f} min)")
    if csv_path:
        logger.info(f"Backup CSV disponibile: {csv_path}")


if __name__ == "__main__":
    main()