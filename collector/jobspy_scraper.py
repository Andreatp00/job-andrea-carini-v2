import pandas as pd
import time

from collector.base import BaseCollector
from config import SEARCH_TERMS, COUNTRY_SEARCHES
from config import settings

class JobSpyCollector(BaseCollector):
    def __init__(self):
        super().__init__('JobSpy')
        
    def collect(self) -> pd.DataFrame:
        """Scraping portali classici (LinkedIn, Indeed) con JobSpy."""
        try:
            from jobspy import scrape_jobs
        except Exception as exc:
            self.logger.warning(f"JobSpy non disponibile: {exc}")
            return pd.DataFrame()

        all_jobs = []
        total = len(SEARCH_TERMS) * len(COUNTRY_SEARCHES)
        counter = 0

        WORKING_SITES = ["indeed", "linkedin"]

        for country_cfg in COUNTRY_SEARCHES:
            for term in SEARCH_TERMS:
                counter += 1
                label = country_cfg["label"]
                self.logger.info(f"[{counter}/{total}] Portali: '{term}' in {label}")
                try:
                    jobs = scrape_jobs(
                        site_name=WORKING_SITES,
                        search_term=term,
                        location=country_cfg["location"],
                        country_indeed=country_cfg["country_indeed"],
                        hours_old=settings.HOURS_OLD,
                        results_wanted=settings.RESULTS_WANTED,
                        linkedin_fetch_description=True,
                        verbose=0,
                    )
                    if len(jobs) > 0:
                        jobs["search_country"] = label
                        jobs["source_type"] = jobs.get("site", "portal")
                        jobs["location"] = jobs.get("location", country_cfg["location"])
                        all_jobs.append(jobs)
                        self.logger.info(f"  -> {len(jobs)} offerte raccolte")
                except Exception as exc:
                    self.logger.warning(f"  -> Errore portali: {exc}")
                time.sleep(2)

        self.logger.info("Google Jobs: SKIPPATO (uso Multi-Engine fallback)")

        if not all_jobs:
            return pd.DataFrame()

        return pd.concat(all_jobs, ignore_index=True)
