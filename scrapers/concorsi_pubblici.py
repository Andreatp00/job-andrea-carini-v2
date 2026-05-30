"""
Scraper per Concorsi Pubblici — PA, Enti Locali, Sicilia
CERCA SPECIFICAMENTE concorsi accessibili con DIPLOMA RAGIONERIA AFM.

Fonti:
- inPA (RSS feed ufficiale — molto più affidabile dello scraping HTML)
- FunzionePubblica.gov.it (RSS/scraping)
- concorsi.it (URL corretto 2025)
- Gazzetta Ufficiale
- Agenzia delle Entrate
- Comune Trapani (SSL bypass)
"""

import logging
import re
import time
from datetime import datetime
from xml.etree import ElementTree as ET

import pandas as pd
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger("JobHunter.Concorsi")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
}

# ─── KEYWORD PER CONCORSI ADATTI A DIPLOMA RAGIONERIA ────────────────────────

TITOLI_RAGIONERIA = [
    "ragioneria", "perito commerciale", "afm", "amministrazione finanza marketing",
    "istituto tecnico commerciale", "istituto tecnico economico", "itc",
    "diploma", "diplomato", "maturità", "maturità commerciale",
    "scuola secondaria superiore", "istruzione secondaria superiore",
    "diploma di scuola media superiore",
]

CATEGORIE_DIPLOMA = [
    "categoria c", "cat. c", "cat c", "categoria d", "cat. d", "cat d",
    "istruttore", "istruttore amministrativo", "istruttore contabile",
    "istruttore direttivo", "istruttore amministrativo contabile",
    "funzionario amministrativo", "funzionario contabile",
    "collaboratore amministrativo", "collaboratore contabile",
    "assistente amministrativo", "operatore amministrativo",
    "impiegato amministrativo", "impiegato contabile",
    "addetto amministrativo", "addetto contabile",
    "esecutore amministrativo", "esecutore contabile",
]

PROFILI_RAGIONERIA = [
    "ragioneria", "contabile", "bilancio", "partita doppia", "iva",
    "imposte", "tributi", "economato", "economico finanziario",
    "finanziario", "amministrativo contabile", "fiscalità",
    "personale", "amministrazione del personale", "stipendi",
    "contabilità pubblica", "ragioneria comunale", "ragioneria provinciale",
]

ESCLUSIONI = [
    "laurea", "laurea magistrale", "laurea triennale", "laurea specialistica",
    "dottorato", "phd", "master universitario",
    "ingegnere", "architetto", "medico", "infermiere", "veterinario",
    "farmacista", "biologo", "chimico", "geologo",
    "professore", "docente", "insegnante", "educatore professionale",
    "assistente sociale", "psicologo",
    "operaio", "autista", "autista di autobus", "idraulico", "elettricista",
    "militare", "polizia", "carabiniere", "vigile del fuoco",
    "agente di polizia", "agente di custodia", "sorvegliante",
    "cuoco", "cameriere", "addetto alle pulizie",
    "dirigente", "dirigente amministrativo",
]

REQUISITI_DIPLOMA = [
    "diploma di ragioneria", "diploma di perito commerciale",
    "diploma di istituto tecnico commerciale", "diploma afm",
    "diploma di maturità commerciale", "ragioneria programmatore",
    "diploma quinquennale", "maturità quinquennale",
    "diploma di scuola secondaria superiore",
    "titolo di studio non inferiore al diploma",
    "almeno il diploma di scuola superiore",
    "possono partecipare i diplomati",
    "è richiesto il diploma",
]

# ─── SITI CONCORSI — URL aggiornati e funzionanti ────────────────────────────
CONCORSI_SITES_SPECIFIC = [
    {
        "name": "inPA - Categoria C",
        "url": "https://www.inpa.gov.it/bandi-e-avvisi/?q=categoria+C+istruttore+amministrativo",
        "query": "categoria C istruttore amministrativo",
        "site": "inpa.gov.it",
        "use_rss": False,
    },
    {
        "name": "inPA - Categoria D",
        "url": "https://www.inpa.gov.it/bandi-e-avvisi/?q=funzionario+amministrativo+diploma",
        "query": "funzionario amministrativo diploma",
        "site": "inpa.gov.it",
        "use_rss": False,
    },
    {
        "name": "inPA - Trapani",
        "url": "https://www.inpa.gov.it/bandi-e-avvisi/?q=Trapani+istruttore+amministrativo",
        "query": "Trapani istruttore amministrativo",
        "site": "inpa.gov.it",
        "use_rss": False,
    },
    {
        "name": "inPA - Sicilia diplomati",
        "url": "https://www.inpa.gov.it/bandi-e-avvisi/?q=Sicilia+diplomati+categoria+C",
        "query": "Sicilia diplomati categoria C",
        "site": "inpa.gov.it",
        "use_rss": False,
    },
    {
        # URL corretto 2025 per concorsi.it (endpoint search aggiornato)
        "name": "Concorsi.it - Categoria C Sicilia",
        "url": "https://www.concorsi.it/cerca?q=categoria+C+istruttore+amministrativo+Sicilia",
        "query": "categoria C istruttore amministrativo Sicilia",
        "site": "concorsi.it",
        "use_rss": False,
    },
    {
        "name": "Concorsi.it - Diplomati",
        "url": "https://www.concorsi.it/cerca?q=diplomati+ragioneria+amministrativo",
        "query": "diplomati ragioneria amministrativo",
        "site": "concorsi.it",
        "use_rss": False,
    },
    {
        "name": "Gazzetta Ufficiale - Concorsi",
        "url": "https://www.gazzettaufficiale.it/concorsi/cerca",
        "query": "diploma istituto tecnico commerciale",
        "site": "gazzettaufficiale.it",
        "use_rss": False,
    },
    {
        "name": "Agenzia Entrate - Concorsi",
        "url": "https://www.agenziaentrate.gov.it/wps/content/Nsilib/Nsi/Concorsi/",
        "query": "diplomati funzionario amministrativo",
        "site": "agenziaentrate.gov.it",
        "use_rss": False,
    },
    {
        # INPS — URL corretto 2025
        "name": "INPS Concorsi",
        "url": "https://www.inps.it/concorsi",
        "query": "diplomati istruttore amministrativo INPS",
        "site": "inps.it",
        "use_rss": False,
    },
    {
        # Funzione Pubblica — portale ufficiale bandi PA
        "name": "FunzionePubblica - Bandi",
        "url": "https://www.funzionepubblica.gov.it/concorsi",
        "query": "istruttore amministrativo diploma",
        "site": "funzionepubblica.gov.it",
        "use_rss": False,
    },
    {
        # Comune Trapani — SSL bypass (certificato con hostname mismatch)
        "name": "Comune Trapani - Bandi",
        "url": "https://comune.trapani.it/bandi-di-concorso/",
        "query": "concorso diplomati istruzione pubblica Trapani",
        "site": "comune.trapani.it",
        "use_rss": False,
        "ssl_verify": False,
    },
    {
        # ASL Trapani — URL corretto senza /concorsi/ (404)
        "name": "ASP Trapani - Avvisi",
        "url": "https://www.asptrapani.it/wp-json/wp/v2/posts?categories=concorsi&per_page=20",
        "query": "concorsi diplomati amministrativi ASP Trapani",
        "site": "asptrapani.it",
        "use_rss": False,
        "is_json": True,
    },
    {
        "name": "InPA - Part-time PA",
        "url": "https://www.inpa.gov.it/bandi-e-avvisi/?q=part+time+diplomati+amministrativo",
        "query": "part time diplomati amministrativo",
        "site": "inpa.gov.it",
        "use_rss": False,
    },
]

# ─── RSS FEEDS — Molto più affidabili dello scraping HTML ────────────────────
RSS_FEEDS = [
    {
        "name": "inPA RSS — Bandi e Avvisi",
        "url": "https://www.inpa.gov.it/feed/bandi-e-avvisi/",
        "site": "inpa.gov.it",
    },
    {
        "name": "FunzionePubblica RSS",
        "url": "https://www.funzionepubblica.gov.it/feed/concorsi",
        "site": "funzionepubblica.gov.it",
    },
    {
        "name": "GazzettaUfficiale RSS Concorsi",
        "url": "https://www.gazzettaufficiale.it/rss/quarta_serie_speciale.xml",
        "site": "gazzettaufficiale.it",
    },
]


# ─── Logica di compatibilità con diploma ─────────────────────────────────────

def _check_diploma_compatibile(title: str, full_text: str) -> tuple[bool, str]:
    """
    Verifica se un concorso è accessibile con DIPLOMA RAGIONERIA AFM.
    Restituisce (compatibile, motivazione).
    """
    text = f"{title} {full_text}".lower()

    if re.search(r"\blaurea\b.{0,40}\b(richiest[ao]|necessari[ao]|obbligatori[ao]|indispensabile|requisito)\b", text):
        return False, "richiede_laurea"

    if re.search(r"\blaurea\s*(triennale|magistrale|specialistica)\b", text):
        return False, "richiede_laurea_tipo"

    if re.search(r"titolo\s+di\s+studio\s*[:;]\s*laurea\b", text) and not re.search(
        r"titolo\s+di\s+studio\s*[:;].{0,30}(diploma|maturità)", text
    ):
        return False, "titolo_laurea"

    cat_c_d = re.search(r"\bcategoria\s*[cd]\b|\bcat\.?\s*[cd]\b", text)
    profilo_ragioneria = any(p in text for p in PROFILI_RAGIONERIA)
    profilo_amm = any(p in text for p in CATEGORIE_DIPLOMA)
    richiede_diploma = any(t in text for t in REQUISITI_DIPLOMA)
    escluso = any(e in text for e in ESCLUSIONI)

    if escluso:
        return False, "ruolo_escluso"

    if cat_c_d:
        return True, "categoria_C_D_diploma"

    if (profilo_ragioneria or profilo_amm) and not re.search(r"\blaurea\b", text):
        return True, "profilo_amministrativo"

    if richiede_diploma and not re.search(r"\blaurea\b", text):
        return True, "richiede_diploma"

    if not re.search(r"\blaurea\b|\bdottorato\b|\bphd\b", text):
        if any(t in text for t in ["amministrativo", "contabile", "ragioneria", "bilancio", "tributi"]):
            return True, "probabile_per_diplomati"

    return False, "non_compatibile"


def _guess_location(full_text: str) -> tuple[str, str]:
    """Estrae città e search_country da un testo libero."""
    text = full_text.lower()
    for city in ["trapani", "palermo", "catania", "messina", "siracusa", "ragusa",
                 "agrigento", "enna", "caltanissetta"]:
        if city in text:
            return city.title(), "Sicilia"
    if "sicilia" in text:
        return "Sicilia", "Sicilia"
    return "Italia", "Italia"


# ─── Parsing RSS ──────────────────────────────────────────────────────────────

def _scrape_rss_feed(feed_cfg: dict) -> list[dict]:
    """Parsa un RSS feed di concorsi pubblici."""
    results = []
    try:
        resp = requests.get(feed_cfg["url"], headers=HEADERS, timeout=20)
        if resp.status_code != 200:
            logger.warning(f"  RSS {feed_cfg['name']}: HTTP {resp.status_code}")
            return []

        try:
            root = ET.fromstring(resp.content)
        except ET.ParseError as e:
            logger.warning(f"  RSS {feed_cfg['name']}: XML parse error: {e}")
            # Fallback: Prova a parsare come HTML e trovare link
            try:
                soup = BeautifulSoup(resp.text, "html.parser")
                for a in soup.find_all("a", href=True):
                    href = a.get("href")
                    if href and any(kw in href.lower() for kw in ["bando", "concorso", "avviso", "selezione"]):
                        title = a.get_text(" ", strip=True) or href
                        full_text = title
                        compatible, reason = _check_diploma_compatibile(title, full_text)
                        if compatible:
                            location, search_country = _guess_location(full_text)
                            date_str = datetime.now().strftime("%Y-%m-%d")
                            results.append({
                                "title": title[:300],
                                "company": feed_cfg["name"],
                                "location": location,
                                "search_country": search_country,
                                "job_url": href,
                                "official_url": href,
                                "description": f"Concorso Pubblico | {feed_cfg['name']} | Diploma OK ({reason}) | {full_text[:300]}",
                                "site": feed_cfg["site"],
                                "source_type": "concorso_pubblico",
                                "date_posted": date_str,
                                "concorso_motivo": reason,
                            })
                if results:
                    logger.info(f"  RSS {feed_cfg['name']} (HTML fallback): {len(results)} concorsi compatibili")
                return results
            except Exception as e2:
                logger.warning(f"  RSS {feed_cfg['name']}: HTML fallback anche fallito: {e2}")
                return []

        # Namespace per Atom e RSS
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        # RSS 2.0 items
        items = root.findall(".//item")
        # Atom feed entries
        if not items:
            items = root.findall(".//atom:entry", ns) or root.findall(".//entry")

        for item in items:
            # Titolo
            title_el = (item.find("title") or item.find("atom:title", ns))
            title = title_el.text.strip() if title_el is not None and title_el.text else ""
            if not title or len(title) < 10:
                continue

            # Descrizione
            desc_el = (
                item.find("description")
                or item.find("summary")
                or item.find("content")
                or item.find("atom:summary", ns)
            )
            description = desc_el.text.strip() if desc_el is not None and desc_el.text else ""

            # URL
            link_el = item.find("link")
            if link_el is not None:
                href = (link_el.text or "").strip()
                if not href:
                    href = link_el.get("href", "")
            else:
                href = ""

            full_text = f"{title} {description}"
            compatible, reason = _check_diploma_compatibile(title, description)
            if not compatible:
                continue

            location, search_country = _guess_location(full_text)

            # Data
            date_el = item.find("pubDate") or item.find("updated") or item.find("published")
            date_str = date_el.text.strip() if date_el is not None and date_el.text else ""
            try:
                from email.utils import parsedate_to_datetime
                date_str = parsedate_to_datetime(date_str).strftime("%Y-%m-%d")
            except Exception:
                date_str = datetime.now().strftime("%Y-%m-%d")

            results.append({
                "title": title[:300],
                "company": feed_cfg["name"],
                "location": location,
                "search_country": search_country,
                "job_url": href or feed_cfg["url"],
                "official_url": href or feed_cfg["url"],
                "description": f"Concorso Pubblico | {feed_cfg['name']} | Diploma OK ({reason}) | {description[:300]}",
                "site": feed_cfg["site"],
                "source_type": "concorso_pubblico",
                "date_posted": date_str,
                "concorso_motivo": reason,
            })

        logger.info(f"  RSS {feed_cfg['name']}: {len(results)} concorsi compatibili")

    except Exception as exc:
        logger.warning(f"  RSS {feed_cfg['name']}: errore: {exc}")

    return results


# ─── Parsing HTML ─────────────────────────────────────────────────────────────

def _parse_concorso_element(el, base_url: str, site_name: str, query: str) -> dict | None:
    """Estrae informazioni da un elemento HTML di un concorso."""
    title_el = el.find(
        ["h2", "h3", "h4", "a", "p", "span", "strong"],
        class_=re.compile(r"title|titolo|name|nome|heading", re.I),
    )
    if not title_el:
        title_el = el.find(["a", "h2", "h3", "h4"])
    if not title_el:
        return None

    title = title_el.get_text(" ", strip=True)
    if not title or len(title) < 15:
        title = el.get_text(" ", strip=True)
        if not title or len(title) < 15:
            return None

    link = el if el.name == "a" and el.get("href") else el.find("a", href=True)
    href = ""
    if link and hasattr(link, "get"):
        href = link.get("href", "")
        if href and not href.startswith("http"):
            if href.startswith("/"):
                from urllib.parse import urlparse
                parsed = urlparse(base_url)
                href = f"{parsed.scheme}://{parsed.netloc}{href}"
            else:
                href = f"{base_url.rstrip('/')}/{href.lstrip('/')}"

    full_text = el.get_text(" ", strip=True)
    compatible, reason = _check_diploma_compatibile(title, full_text)
    if not compatible:
        return None

    location, search_country = _guess_location(full_text)

    ente = site_name
    ente_match = re.search(
        r"(comune|provincia|regione|asl|asp|inps|agenzia|ministero|azienda sanitaria|corte|autorità)"
        r"\s+(?:di\s+|della\s+|dell[' ])?([a-zàèéìòù\s]+?)(?:\s|,|\.|–|-|$)",
        full_text.lower(),
    )
    if ente_match:
        ente = f"{ente_match.group(1).title()} {ente_match.group(2).title()}".strip()

    return {
        "title": title[:300],
        "company": ente,
        "location": location,
        "search_country": search_country,
        "job_url": href or base_url,
        "official_url": href or base_url,
        "description": (
            f"Concorso Pubblico | {site_name} | Diploma OK ({reason}) | {full_text[:300]}"
        ),
        "site": base_url.replace("https://", "").replace("http://", "").split("/")[0],
        "source_type": "concorso_pubblico",
        "date_posted": datetime.now().strftime("%Y-%m-%d"),
        "concorso_motivo": reason,
    }


def _scrape_html_site(site_cfg: dict) -> list[dict]:
    """Scraping HTML di un sito concorsi."""
    results = []
    site_name = site_cfg["name"]
    url = site_cfg["url"]
    ssl_verify = site_cfg.get("ssl_verify", True)

    try:
        resp = requests.get(url, headers=HEADERS, timeout=25, verify=ssl_verify)
        if resp.status_code != 200:
            logger.warning(f"  ❌ {site_name}: HTTP {resp.status_code}")
            return []

        # Se è una risposta JSON (es. WP REST API)
        if site_cfg.get("is_json"):
            try:
                data = resp.json()
                for post in (data if isinstance(data, list) else []):
                    title = post.get("title", {}).get("rendered", "")
                    body = BeautifulSoup(
                        post.get("content", {}).get("rendered", ""), "html.parser"
                    ).get_text(" ")
                    link = post.get("link", url)
                    compatible, reason = _check_diploma_compatibile(title, body)
                    if compatible:
                        location, sc = _guess_location(f"{title} {body}")
                        results.append({
                            "title": title[:300],
                            "company": site_name,
                            "location": location,
                            "search_country": sc,
                            "job_url": link,
                            "official_url": link,
                            "description": f"Concorso | {site_name} | {body[:300]}",
                            "site": site_cfg["site"],
                            "source_type": "concorso_pubblico",
                            "date_posted": datetime.now().strftime("%Y-%m-%d"),
                            "concorso_motivo": reason,
                        })
                return results
            except Exception:
                pass

        soup = BeautifulSoup(resp.text, "html.parser")

        # Selettori specifici per inPA
        if "inpa.gov.it" in url:
            selectors = [
                ".bandi-avvisi-item", ".single-bandi-container",
                "article.bando", "div.bando-item", "li.bando",
                "div[class*='bandi']", "article",
            ]
        else:
            selectors = [
                "a[href*='bando']", "a[href*='concorso']", "a[href*='avviso']",
                "div[class*='bando']", "div[class*='concorso']", "div[class*='avviso']",
                "article[class*='bando']", "article[class*='concorso']",
                "tr[class*='bando']", "tr[class*='concorso']",
                "div.card", "div.item", "li.list-item",
                "div[class*='risultato']", "div[class*='result']",
                "table tr", ".listing tr",
            ]

        found_elements = []
        for selector in selectors:
            elements = soup.select(selector)
            if elements and len(elements) > 1:  # Ignora se solo 1 (nav link)
                found_elements = elements
                logger.info(f"  📦 {site_name}: selettore '{selector}': {len(elements)} elementi")
                break

        if not found_elements:
            # Fallback: cerca link con parole chiave di concorso nell'href/testo
            found_elements = [
                a for a in soup.find_all("a", href=True)
                if any(kw in (a.get("href", "") + a.get_text()).lower()
                       for kw in ["bando", "concorso", "avviso", "selezione", "istruttore"])
            ]
            if found_elements:
                logger.info(f"  📦 {site_name}: fallback link: {len(found_elements)}")

        for el in found_elements[:50]:  # max 50 elementi per sito
            parsed = _parse_concorso_element(el, url, site_name, site_cfg.get("query", ""))
            if parsed:
                results.append(parsed)

    except requests.exceptions.SSLError as exc:
        logger.warning(f"  ❌ {site_name}: SSL error — {exc}. Riprovo con verify=False...")
        try:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            resp = requests.get(url, headers=HEADERS, timeout=25, verify=False)
            if resp.status_code == 200:
                return _scrape_html_site({**site_cfg, "ssl_verify": False})
        except Exception as exc2:
            logger.warning(f"  ❌ {site_name}: fallback SSL anche fallito: {exc2}")
    except requests.exceptions.ConnectionError as exc:
        logger.warning(f"  ❌ {site_name}: DNS/connessione fallita — {exc}")
    except Exception as exc:
        logger.warning(f"  ❌ {site_name}: errore: {exc}")

    return results


# ─── Entry point ─────────────────────────────────────────────────────────────

def scrape_concorsi() -> pd.DataFrame:
    """
    Scraping dei principali portali di concorsi pubblici.
    Usa RSS feed quando disponibile (più affidabile), HTML come fallback.
    """
    logger.info("=" * 60)
    logger.info("SCRAPING CONCORSI PUBBLICI — Solo per Diplomati Ragioneria AFM")
    logger.info("=" * 60)

    all_results: list[dict] = []

    # ── 1. RSS Feeds (più affidabili, nessun JS rendering) ────────────────────
    logger.info("📡 Parsing RSS feed concorsi...")
    for feed_cfg in RSS_FEEDS:
        logger.info(f"🔍 RSS: {feed_cfg['name']}")
        results = _scrape_rss_feed(feed_cfg)
        all_results.extend(results)
        time.sleep(1.5)

    # ── 2. Scraping HTML siti specifici ───────────────────────────────────────
    logger.info("🌐 Scraping HTML siti concorsi...")
    for site_cfg in CONCORSI_SITES_SPECIFIC:
        logger.info(f"🔍 {site_cfg['name']}: {site_cfg.get('query', '')}")
        results = _scrape_html_site(site_cfg)

        # Deduplica locale per sito
        seen = set()
        unique = []
        for item in results:
            key = f"{item['title'][:80]}|{item['job_url']}"
            if key not in seen:
                seen.add(key)
                unique.append(item)

        all_results.extend(unique)
        logger.info(f"  ✅ {len(unique)} concorsi compatibili con Diploma Ragioneria AFM")
        time.sleep(2)

    # ── 3. Deduplicazione finale ──────────────────────────────────────────────
    if not all_results:
        logger.info("⚠️ Nessun concorso pubblico trovato per Diploma Ragioneria AFM")
        return pd.DataFrame()

    df = pd.DataFrame(all_results)
    df = df.drop_duplicates(subset=["title", "job_url"])

    logger.info(f"\n{'=' * 60}")
    logger.info(f"✅ TOTALE CONCORSI COMPATIBILI: {len(df)}")
    for loc in df["search_country"].value_counts().index:
        count = (df["search_country"] == loc).sum()
        logger.info(f"   {loc}: {count}")
    for motivo in df["concorso_motivo"].value_counts().index:
        count = (df["concorso_motivo"] == motivo).sum()
        logger.info(f"   Tipo '{motivo}': {count}")
    logger.info(f"{'=' * 60}")

    return df