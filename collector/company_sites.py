import pandas as pd
import time
from datetime import datetime

from collector.base import BaseCollector
from collector.web_search import search_web_engines
from config import COMPANY_CAREER_SITES, EXCLUDE_KEYWORDS_TITLE, COMPANY_RELEVANCE_KEYWORDS
from utils.text import contains_any
from utils.url import extract_domain

# We will implement is_actual_job_posting in engine.filters later
from engine.filters import is_actual_job_posting

class CompanySitesCollector(BaseCollector):
    def __init__(self):
        super().__init__('CompanySites')

    def collect(self) -> pd.DataFrame:
        df1 = self.scrape_company_sites()
        df2 = self.scrape_italian_portals()
        df3 = self.universal_job_search()
        
        all_dfs = [df for df in [df1, df2, df3] if not df.empty]
        if not all_dfs:
            return pd.DataFrame()
        return pd.concat(all_dfs, ignore_index=True)

    def scrape_company_sites(self) -> pd.DataFrame:
        """
        Scraping siti aziendali/configurati (studi commercialisti, agenzie, enti).
        Utilizza un Multi-Engine robusto invece di DuckDuckGo per garantire il 100% di successo.
        """
        results = []
        for company_cfg in COMPANY_CAREER_SITES:
            company = company_cfg["company"]
            keywords = company_cfg["search_params"]["keywords"]
            domain = extract_domain(company_cfg["url"])
            
            admin_keywords = " OR ".join([
                "amministrativo", "contabilità", "back office", "segreteria", "ufficio",
                "impiegato", "addetto", "ragioneria", "commercialista", "praticante",
                "stage", "tirocinio", "lavoro", "offerta", "annuncio"
            ])
            query = f'site:{domain} ({keywords} OR {admin_keywords}) ("part-time" OR "full-time" OR stage OR tirocinio)'
            self.logger.info(f"Sito aziendale: {company_cfg['label']}")
            
            found_links = search_web_engines(query, num_results=15)
            
            if not found_links:
                self.logger.warning(f"  -> Nessun risultato dai motori per {company_cfg['label']}")
                time.sleep(1)
                continue
                
            found = 0
            for title, href in found_links:
                title_lower = title.lower()

                if not contains_any(title_lower, COMPANY_RELEVANCE_KEYWORDS):
                    continue
                if contains_any(title_lower, EXCLUDE_KEYWORDS_TITLE):
                    continue

                results.append({
                    "title": title,
                    "company": company,
                    "location": company_cfg["country"],
                    "search_country": company_cfg["country"],
                    "job_url_direct": href,
                    "job_url": href,
                    "official_url": href,
                    "description": f"{company_cfg['label']} | query: {keywords}",
                    "site": domain,
                    "source_type": "company_site",
                    "date_posted": datetime.now().strftime("%Y-%m-%d"),
                })
                found += 1
                
            self.logger.info(f"  -> {found} offerte aggiunte")
            time.sleep(1.5)
            
        return pd.DataFrame(results)

    def scrape_italian_portals(self) -> pd.DataFrame:
        italian_portals = [
            {"name": "TrovoLavoro", "domain": "trovolavoro.it"},
        ]

        all_jobs = []
        
        core_queries = [
            '"impiegato amministrativo" Trapani OR Sicilia OR Italia',
            '"back office" Trapani OR Sicilia OR "smart working"',
            '"contabilità" "part-time" OR Trapani OR Sicilia',
            '"amministrazione" "smart working" OR remoto',
            '"call center" "smart working" OR remoto',
            '"data entry" "smart working" OR remoto',
            '"stage" OR "tirocinio" Trapani OR "smart working"',
        ]

        for portal in italian_portals:
            for term in core_queries:
                query = f'site:{portal["domain"]} {term}'
                self.logger.info(f"Portale {portal['name']}: {term[:40]}...")
                
                found_links = search_web_engines(query, num_results=5)
                
                found = 0
                for title, href in found_links:
                    title_lower = title.lower()

                    if not contains_any(title_lower, [
                        "amministrativo", "contabilità", "back office", "fatturazione", 
                        "segreteria", "ufficio", "impiegato", "part-time", "smart working", 
                        "remoto", "ragioneria", "diploma", "stage", "praticante",
                        "call center", "data entry", "assistenza clienti", "customer service",
                        "inserimento dati", "tirocinio", "apprendistato", "inbound", "outbound",
                    ]):
                        continue
                    if contains_any(title_lower, EXCLUDE_KEYWORDS_TITLE):
                        continue

                    all_jobs.append({
                        "title": title[:200],
                        "company": portal["name"],
                        "location": "Italia",
                        "search_country": "Italia",
                        "job_url_direct": href,
                        "job_url": href,
                        "official_url": href,
                        "description": f"{portal['name']} | query: {term}",
                        "site": portal["domain"],
                        "source_type": "italian_portal",
                        "date_posted": datetime.now().strftime("%Y-%m-%d"),
                    })
                    found += 1
                    
                if found > 0:
                    self.logger.info(f"  -> {found} offerte trovate su {portal['name']}")
                    
                time.sleep(1.5)

        return pd.DataFrame(all_jobs)

    def search_universal_web(self) -> list[dict]:
        results = []
        
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
            'site:*.it "amministrazione" Trapani OR Sicilia OR "smart working"',
            'site:*.it "lavoro" "amministrativo" "full remote"',
            'site:*.it "assunzione" "impiegato contabile" Trapani',
            'site:*.it "call center" "lavoro da casa" Italia',
            'site:*.it "data entry" "smart working" remoto',
            'site:*.it "stage" impiegato Trapani',
            'site:*.it "tirocinio" ufficio Trapani',
            'site:paginegialle.it "lavoro" "amministrativo" Trapani',
            'site:paginebianche.it "lavoro" "amministrativo" Trapani',
            'site:bakeca.it "lavoro" "ufficio" Trapani',
        ]
        
        for query in queries:
            found_links = search_web_engines(query, num_results=10)
            
            found = 0
            for title, href in found_links:
                href_lower = href.lower()
                if any(skip in href_lower for skip in [
                    "facebook.com", "twitter.com", "linkedin.com/in/",
                    "youtube.com", "instagram.com", "wikipedia.org",
                    "google.com/search", "bing.com"
                ]):
                    continue
                
                if not is_actual_job_posting(href, title):
                    continue
                
                results.append({
                    "title": title[:200],
                    "job_url_direct": href,
                    "job_url": href,
                    "official_url": href,
                    "description": f"Web search: {query[:80]}",
                    "site": extract_domain(href),
                    "source_type": "universal_search",
                    "location": "Italia",
                    "search_country": "Italia",
                    "company": "",
                    "date_posted": datetime.now().strftime("%Y-%m-%d"),
                })
                found += 1
                if found >= 5:
                    break
                    
            if found > 0:
                self.logger.info(f"Ricerca universale: {found} risultati per query: {query[:60]}")
                
            time.sleep(2)
        
        return results

    def universal_job_search(self) -> pd.DataFrame:
        self.logger.info("=== RICERCA UNIVERSALE (Multi-Engine) ===")
        try:
            results = self.search_universal_web()
            if not results:
                return pd.DataFrame()
            return pd.DataFrame(results)
        except Exception as exc:
            self.logger.warning(f"Errore globale ricerca universale: {exc}")
            return pd.DataFrame()
