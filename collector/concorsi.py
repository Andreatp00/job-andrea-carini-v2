import logging
import re
import time
from datetime import datetime
from xml.etree import ElementTree as ET

import pandas as pd
import requests
from bs4 import BeautifulSoup

from collector.base import BaseCollector

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
        "name": "INPS Concorsi",
        "url": "https://www.inps.it/concorsi",
        "query": "diplomati istruttore amministrativo INPS",
        "site": "inps.it",
        "use_rss": False,
    },
    {
        "name": "FunzionePubblica - Bandi",
        "url": "https://www.funzionepubblica.gov.it/concorsi",
        "query": "istruttore amministrativo diploma",
        "site": "funzionepubblica.gov.it",
        "use_rss": False,
    },
    {
        "name": "Comune Trapani - Bandi",
        "url": "https://comune.trapani.it/bandi-di-concorso/",
        "query": "concorso diplomati istruzione pubblica Trapani",
        "site": "comune.trapani.it",
        "use_rss": False,
        "ssl_verify": False,
    },
    {
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

def _check_diploma_compatibile(title: str, full_text: str) -> tuple[bool, str]:
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
    text = full_text.lower()
    for city in ["trapani", "palermo", "catania", "messina", "siracusa", "ragusa",
                 "agrigento", "enna", "caltanissetta"]:
        if city in text:
            return city.title(), "Sicilia"
    if "sicilia" in text:
        return "Sicilia", "Sicilia"
    return "Italia", "Italia"


class ConcorsiCollector(BaseCollector):
    def __init__(self):
        super().__init__('Concorsi')
        self.HEADERS = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
        }

    def collect(self) -> pd.DataFrame:
        self.logger.info("=" * 60)
        self.logger.info("SCRAPING CONCORSI PUBBLICI — Solo per Diplomati Ragioneria AFM")
        self.logger.info("=" * 60)

        all_results: list[dict] = []

        self.logger.info("📡 Parsing RSS feed concorsi...")
        for feed_cfg in RSS_FEEDS:
            self.logger.info(f"🔍 RSS: {feed_cfg['name']}")
            results = self._scrape_rss_feed(feed_cfg)
            all_results.extend(results)
            time.sleep(1.5)

        self.logger.info("🌐 Scraping HTML siti concorsi...")
        for site_cfg in CONCORSI_SITES_SPECIFIC:
            self.logger.info(f"🔍 {site_cfg['name']}: {site_cfg.get('query', '')}")
            results = self._scrape_html_site(site_cfg)

            seen = set()
            unique = []
            for item in results:
                key = f"{item['title'][:80]}|{item['job_url']}"
                if key not in seen:
                    seen.add(key)
                    unique.append(item)

            all_results.extend(unique)
            self.logger.info(f"  ✅ {len(unique)} concorsi compatibili con Diploma Ragioneria AFM")
            time.sleep(2)

        if not all_results:
            self.logger.info("⚠️ Nessun concorso pubblico trovato per Diploma Ragioneria AFM")
            return pd.DataFrame()

        df = pd.DataFrame(all_results)
        df = df.drop_duplicates(subset=["title", "job_url"])

        self.logger.info(f"\n{'=' * 60}")
        self.logger.info(f"✅ TOTALE CONCORSI COMPATIBILI: {len(df)}")
        return df

    def _scrape_rss_feed(self, feed_cfg: dict) -> list[dict]:
        results = []
        try:
            resp = requests.get(feed_cfg["url"], headers=self.HEADERS, timeout=20)
            if resp.status_code != 200:
                self.logger.warning(f"  RSS {feed_cfg['name']}: HTTP {resp.status_code}")
                return []

            try:
                root = ET.fromstring(resp.content)
            except ET.ParseError as e:
                self.logger.warning(f"  RSS {feed_cfg['name']}: XML parse error: {e}")
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
                        self.logger.info(f"  RSS {feed_cfg['name']} (HTML fallback): {len(results)} concorsi compatibili")
                    return results
                except Exception as e2:
                    self.logger.warning(f"  RSS {feed_cfg['name']}: HTML fallback anche fallito: {e2}")
                    return []

            ns = {"atom": "http://www.w3.org/2005/Atom"}
            items = root.findall(".//item")
            if not items:
                items = root.findall(".//atom:entry", ns) or root.findall(".//entry")

            for item in items:
                title_el = (item.find("title") or item.find("atom:title", ns))
                title = title_el.text.strip() if title_el is not None and title_el.text else ""
                if not title or len(title) < 10:
                    continue

                desc_el = (
                    item.find("description")
                    or item.find("summary")
                    or item.find("content")
                    or item.find("atom:summary", ns)
                )
                description = desc_el.text.strip() if desc_el is not None and desc_el.text else ""

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

            self.logger.info(f"  RSS {feed_cfg['name']}: {len(results)} concorsi compatibili")

        except Exception as exc:
            self.logger.warning(f"  RSS {feed_cfg['name']}: errore: {exc}")

        return results

    def _parse_concorso_element(self, el, base_url: str, site_name: str, query: str) -> dict | None:
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

    def _scrape_html_site(self, site_cfg: dict) -> list[dict]:
        results = []
        site_name = site_cfg["name"]
        url = site_cfg["url"]
        ssl_verify = site_cfg.get("ssl_verify", True)

        try:
            resp = requests.get(url, headers=self.HEADERS, timeout=25, verify=ssl_verify)
            if resp.status_code != 200:
                self.logger.warning(f"  ❌ {site_name}: HTTP {resp.status_code}")
                return []

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
                                "site": site_cfg.get("site", ""),
                                "source_type": "concorso_pubblico",
                                "date_posted": datetime.now().strftime("%Y-%m-%d"),
                                "concorso_motivo": reason,
                            })
                    return results
                except Exception:
                    pass

            soup = BeautifulSoup(resp.text, "html.parser")

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
                if elements and len(elements) > 1:
                    found_elements = elements
                    self.logger.info(f"  📦 {site_name}: selettore '{selector}': {len(elements)} elementi")
                    break

            if not found_elements:
                found_elements = [
                    a for a in soup.find_all("a", href=True)
                    if any(kw in (a.get("href", "") + a.get_text()).lower()
                           for kw in ["bando", "concorso", "avviso", "selezione", "istruttore"])
                ]
                if found_elements:
                    self.logger.info(f"  📦 {site_name}: fallback link: {len(found_elements)}")

            for el in found_elements[:50]:
                parsed = self._parse_concorso_element(el, url, site_name, site_cfg.get("query", ""))
                if parsed:
                    results.append(parsed)

        except requests.exceptions.SSLError as exc:
            self.logger.warning(f"  ❌ {site_name}: SSL error — {exc}. Riprovo con verify=False...")
            try:
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                resp = requests.get(url, headers=self.HEADERS, timeout=25, verify=False)
                if resp.status_code == 200:
                    return self._scrape_html_site({**site_cfg, "ssl_verify": False})
            except Exception as exc2:
                self.logger.warning(f"  ❌ {site_name}: fallback SSL anche fallito: {exc2}")
        except requests.exceptions.ConnectionError as exc:
            self.logger.warning(f"  ❌ {site_name}: DNS/connessione fallita — {exc}")
        except Exception as exc:
            self.logger.warning(f"  ❌ {site_name}: errore: {exc}")

        return results
