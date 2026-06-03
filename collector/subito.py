import pandas as pd
import requests
import time
from datetime import datetime

from collector.base import BaseCollector
from collector.web_search import search_web_engines
from config import EXCLUDE_KEYWORDS_TITLE
from utils.text import contains_any
from utils.http import get_tls_session

class SubitoCollector(BaseCollector):
    def __init__(self):
        super().__init__('Subito')
        self.tls_session = get_tls_session()
        
        self.SUBITO_API = "https://hades.subito.it/v1/search/classifieds"
        self.SUBITO_CATEGORY = 29
        self.SUBITO_REGION_SICILIA = 11

        self.SUBITO_HEADERS = {
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

        self.SUBITO_SEARCHES = [
            {"q": "back office",               "region": self.SUBITO_REGION_SICILIA, "label": "Trapani"},
            {"q": "impiegato amministrativo",  "region": self.SUBITO_REGION_SICILIA, "label": "Trapani"},
            {"q": "contabilità",               "region": self.SUBITO_REGION_SICILIA, "label": "Trapani"},
            {"q": "fatturazione ufficio",      "region": self.SUBITO_REGION_SICILIA, "label": "Trapani"},
            {"q": "segreteria",                "region": self.SUBITO_REGION_SICILIA, "label": "Trapani"},
            {"q": "ragioneria",                "region": self.SUBITO_REGION_SICILIA, "label": "Trapani"},
            {"q": "praticante",                "region": self.SUBITO_REGION_SICILIA, "label": "Trapani"},
            {"q": "amministrazione ufficio",   "region": self.SUBITO_REGION_SICILIA, "label": "Trapani"},
            {"q": "part time ufficio",         "region": self.SUBITO_REGION_SICILIA, "label": "Trapani"},
            {"q": "customer service",          "region": self.SUBITO_REGION_SICILIA, "label": "Trapani"},
            {"q": "addetto contabilità",       "region": self.SUBITO_REGION_SICILIA, "label": "Trapani"},
            {"q": "stage",                     "region": self.SUBITO_REGION_SICILIA, "label": "Trapani"},
            {"q": "tirocinio formativo",       "region": self.SUBITO_REGION_SICILIA, "label": "Trapani"},
            {"q": "apprendistato",             "region": self.SUBITO_REGION_SICILIA, "label": "Trapani"},
            
            {"q": "smart working",                 "label": "Italia"},
            {"q": "lavoro da casa contabilità",    "label": "Italia"},
            {"q": "remoto back office",            "label": "Italia"},
            {"q": "full remote amministrativo",    "label": "Italia"},
            {"q": "call center da casa",           "label": "Italia"},
            {"q": "data entry remoto",             "label": "Italia"},
            {"q": "inserimento dati",              "label": "Italia"},
        ]

        self.EXCLUDE_PATTERNS = [
            "auto ", "moto ", "telefono", "cellulare", "tablet", "iphone", "samsung",
            "casa in vendita", "appartamento", "affitto",
            "abbigliamento", "scarpe", "borsa", "borse",
            "console", "playstation", "xbox", "nintendo",
            "bici", "cucina", "divano", "letto", "lavatrice",
            "vendo", "cedo", "regalo",
        ]

        self.TARGET_KEYWORDS = [
            "amministrativo", "contabilità", "back office", "fatturazione", "segreteria",
            "ufficio", "commercialista", "ragioneria", "contabile", "impiegato",
            "praticante", "stage", "part-time", "part time", "smart working",
            "remoto", "bilancio", "lavoro", "addetto", "assistente", "customer service",
            "amministrazione", "prima nota", "erp", "call center", "data entry",
            "inserimento dati", "tirocinio", "apprendistato",
        ]

        self.TRAPANI_CITIES = {
            "trapani", "marsala", "mazara", "mazara del vallo", "alcamo",
            "castelvetrano", "erice", "valderice", "paceco", "buseto",
            "petrosino", "salemi", "partanna", "campobello", "pantelleria",
            "favignana", "castellammare del golfo", "calatafimi",
        }

    def collect(self) -> pd.DataFrame:
        self.logger.info("=== SCRAPING SUBITO.IT (API JSON hades.subito.it) ===")
        all_results = []

        for search in self.SUBITO_SEARCHES:
            q = search["q"]
            label = search.get("label", "Italia")

            params = {
                "q": q,
                "category": self.SUBITO_CATEGORY,
                "start": 0,
                "lim": 25,
                "sort": "date",
            }
            if "region" in search:
                params["region"] = search["region"]

            self.logger.info(f"Subito API: '{q}' [{label}]")

            for attempt in range(3):
                try:
                    resp = self.tls_session.get(
                        self.SUBITO_API,
                        params=params,
                        headers=self.SUBITO_HEADERS,
                        timeout_seconds=30,
                    )

                    if resp.status_code == 429:
                        self.logger.warning(f"  -> Rate limit Subito API (429), attendo {10*(attempt+1)}s...")
                        time.sleep(10*(attempt+1))
                        continue

                    if resp.status_code == 403 and attempt < 2:
                        alt_headers = {**self.SUBITO_HEADERS, 
                                       "User-Agent": "Subito/1.0 (iOS; iPhone) AppleWebKit/605.1.15"}
                        resp = self.tls_session.get(
                            self.SUBITO_API,
                            params=params,
                            headers=alt_headers,
                            timeout_seconds=30,
                        )
                        if resp.status_code == 403:
                            self.logger.warning(f"  -> HTTP 403 (tentativo {attempt+1}), provo headers alternativi...")
                            continue

                    if resp.status_code != 200:
                        self.logger.warning(f"  -> HTTP {resp.status_code}")
                        break

                    data = resp.json()
                    ads = data.get("ads", [])

                    if not ads:
                        self.logger.info("  -> 0 annunci")
                        break

                    count = 0
                    for ad in ads:
                        title = str(ad.get("subject", "")).strip()
                        if not title or len(title) < 5:
                            continue

                        title_lower = title.lower()

                        if any(p in title_lower for p in self.EXCLUDE_PATTERNS):
                            continue

                        body = str(ad.get("body", "")).strip()
                        full_text = f"{title} {body}".lower()
                        if not any(kw in full_text for kw in self.TARGET_KEYWORDS):
                            continue

                        urls = ad.get("urls", {})
                        job_url = urls.get("default", "") or ad.get("url", "")

                        advertiser = ad.get("advertiser", {})
                        company = (
                            advertiser.get("company_name")
                            or advertiser.get("name")
                            or ""
                        )
                        if not company:
                            company = "Subito.it"

                        city, search_country = self._parse_location(ad, label)

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

                    self.logger.info(f"  -> {count} annunci rilevanti (di {len(ads)} totali)")
                    break

                except requests.exceptions.ConnectionError as exc:
                    self.logger.warning(f"  -> Connessione fallita: {exc}")
                    break
                except Exception as exc:
                    self.logger.warning(f"  -> Errore Subito API (tentativo {attempt + 1}): {exc}")
                    time.sleep(3)

            time.sleep(1.5)

        if not all_results:
            self.logger.warning("Subito.it API fallita completamente, uso FALLBACK Multi-Engine...")
            return self._scrape_subito_fallback()

        df = pd.DataFrame(all_results)
        df = df[df["job_url"].str.strip() != ""]
        df = df.drop_duplicates(subset=["job_url"], keep="first")
        self.logger.info(f"Subito.it API: {len(df)} annunci unici")
        return df

    def _parse_location(self, ad: dict, fallback_label: str) -> tuple[str, str]:
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
        if any(tp in city_lower for tp in self.TRAPANI_CITIES):
            return city, "Trapani"
        if "sicilia" in city_lower or region_obj.get("short_name", "").upper() in (
            "AG", "CL", "CT", "EN", "ME", "PA", "RG", "SR", "TP"
        ):
            return city, "Sicilia"
        return city, fallback_label

    def _scrape_subito_fallback(self) -> pd.DataFrame:
        self.logger.info("=== SUBITO.IT FALLBACK: Multi-Engine Search ===")
        all_results = []
        
        for search in self.SUBITO_SEARCHES:
            q = search["q"]
            label = search.get("label", "Italia")
            
            base_query = f'site:subito.it "{q}"'
            
            if label == "Trapani":
                geo_keywords = " OR ".join(["Trapani", "Marsala", "Alcamo", "Mazara", "Erice", "Paceco", "Valderice"])
                base_query += f" ({geo_keywords})"
            
            work_keywords = " OR ".join([
                "lavoro", "offerta", "annuncio", "cerco", "assumo",
                "impiegato", "amministrativo", "contabilità", "ufficio"
            ])
            base_query += f" ({work_keywords})"
            
            self.logger.info(f"Fallback query: {base_query[:80]}...")
            results = search_web_engines(base_query, num_results=15)
            
            if not results:
                self.logger.warning(f"  -> Nessun risultato fallback per '{q}'")
                continue
            
            found_count = 0
            for title, href in results:
                title_lower = title.lower()
                
                if any(p in title_lower for p in self.EXCLUDE_PATTERNS):
                    continue
                
                if not any(kw in title_lower for kw in self.TARGET_KEYWORDS):
                    continue
                
                search_country = label
                title_lower_for_geo = title.lower()
                if any(tp in title_lower_for_geo for tp in self.TRAPANI_CITIES):
                    search_country = "Trapani"
                elif "sicilia" in title_lower_for_geo:
                    search_country = "Sicilia"
                
                all_results.append({
                    "title": title[:250],
                    "company": "Subito.it",
                    "location": "Trapani" if search_country == "Trapani" else "Italia",
                    "search_country": search_country,
                    "job_url": href,
                    "official_url": href,
                    "description": f"Subito.it Fallback | Query: {q}",
                    "site": "subito.it",
                    "source_type": "subito_fallback",
                    "date_posted": datetime.now().strftime("%Y-%m-%d"),
                })
                found_count += 1
            
            self.logger.info(f"  -> {found_count} annunci da fallback per '{q}'")
            time.sleep(1.5)
        
        if not all_results:
            self.logger.warning("Nessun annuncio trovato su Subito.it (API + Fallback)")
            return pd.DataFrame()
        
        df = pd.DataFrame(all_results)
        df = df[df["job_url"].str.strip() != ""]
        df = df.drop_duplicates(subset=["job_url"], keep="first")
        self.logger.info(f"Subito.it Fallback: {len(df)} annunci unici")
        return df
