import pandas as pd
import time

from collector.base import BaseCollector
from config import COUNTRY_SEARCHES
from config import settings

# Query divise in LOCALI (cercate per ogni location) e REMOTE (cercate solo una volta per Italia)
LOCAL_QUERIES = [
    # Trapani e provincia
    '"back office" Trapani',
    '"impiegato amministrativo" Trapani',
    '"contabilità" Trapani',
    '"fatturazione" Trapani',
    '"segreteria" Trapani',
    '"ragioneria" Trapani',
    '"praticante" "studio commercialista" Trapani',
    '"amministrativo" Alcamo',
    '"back office" "Mazara del Vallo"',
    '"impiegato" Marsala',
    '"addetto" Trapani',
    '"logistica" Trapani',
    '"gestione ordini" Trapani',
    '"stage" Trapani',
    '"tirocinio" Trapani',
    '"apprendistato" Trapani',
    '"concorso" "amministrativo" Trapani',
    # Banche e creditizio Trapani/Palermo
    '"sportello bancario" Trapani',
    '"impiegato bancario" Trapani',
    '"banca" tirocinio Trapani',
    '"sportello bancario" Palermo',
    '"impiegato bancario" Palermo',
    '"banca" tirocinio Palermo',
    '"assicurazione" tirocinio Trapani',
    # Formazione/tirocini locali
    '"tirocinio formativo" Trapani',
    '"formazione gratuita" Trapani',
    '"formazione gratuita" Palermo',
    # Palermo
    '"back office" Palermo',
    '"impiegato amministrativo" Palermo',
    '"contabilità" Palermo',
    '"segreteria" Palermo',
]

REMOTE_QUERIES = [
    # Smart working admin
    '"back office" remoto',
    '"back office" "smart working"',
    '"impiegato amministrativo" "smart working"',
    '"contabilità" "smart working"',
    '"amministrativo" "full remote"',
    # Call center
    '"call center" remoto',
    '"call center" "smart working"',
    '"call center" "lavoro da casa"',
    '"operatore telefonico" remoto',
    '"customer service" remoto',
    '"assistenza clienti" remoto',
    '"assistenza clienti" "smart working"',
    '"help desk" remoto',
    '"supporto clienti" remoto',
    # Data entry
    '"data entry" remoto',
    '"data entry" "smart working"',
    '"inserimento dati" remoto',
    # E-commerce, social, web
    '"e-commerce" remoto',
    '"social media manager" remoto',
    '"gestione ordini" remoto',
    '"wordpress" remoto',
    '"content creator" remoto',
    '"copywriter" remoto',
    # Assistente e booking
    '"assistente virtuale" remoto',
    '"booking" remoto',
    # Generico smart working
    '"smart working" Italia diploma',
    '"lavoro da casa" Italia',
    '"full remote" Italia',
    'remoto "senza esperienza"',
    'remoto "prima esperienza"',
    # Stage remoti
    '"stage" "smart working"',
    '"tirocinio" remoto',
    '"stage" amministrativo remoto',
    # Concorsi
    'concorsi pubblici Trapani diplomati',
    'concorsi pubblici Palermo "categoria C"',
    'concorsi pubblici Sicilia diplomati',
    '"bando" "diplomati" Sicilia',

    # ═══ BANCHE / CREDITIZIO / ASSICURATIVO ═══
    '"sportello bancario" tirocinio',
    '"sportello bancario" "senza esperienza"',
    '"impiegato bancario" tirocinio',
    '"impiegato bancario" "prima esperienza"',
    '"operatore bancario" stage',
    '"settore bancario" tirocinio formativo',
    '"settore creditizio" tirocinio',
    '"settore creditizio" "senza esperienza"',
    '"settore assicurativo" tirocinio',
    '"settore assicurativo" "prima esperienza"',
    '"consulente assicurativo" junior',
    '"agente assicurativo" formazione',
    '"back office bancario"',
    '"back office assicurativo"',
    '"addetto credito" tirocinio',
    '"analista credito" junior',
    '"impiegato assicurativo"',
    '"banca" tirocinio diplomati',
    '"istituto credito" stage',
    '"filiale bancaria" stage',

    # ═══ LAVORI CON FORMAZIONE GRATUITA / SENZA ESPERIENZA ═══
    '"formazione gratuita" lavoro',
    '"formazione retribuita" lavoro',
    '"tirocinio formativo" "senza esperienza"',
    '"tirocinio retribuito" "senza esperienza"',
    '"nessuna esperienza richiesta" formazione',
    '"corso gratuito" lavoro giovani',
    '"formazione pagata" tirocinio',
    '"academy" lavoro junior',
    '"academy" "neoassunti"',
    '"percorso formativo" lavoro',
    '"inserimento lavorativo" formazione',
    '"si offre formazione" impiegato',
]


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

        # Solo LinkedIn e Indeed (Glassdoor e ZipRecruiter danno 403)
        WORKING_SITES = ["indeed", "linkedin"]

        # 1. Query LOCALI: cercate solo per Trapani e Sicilia
        local_locations = [
            {"country_indeed": "Italy", "location": "Trapani", "label": "Trapani"},
            {"country_indeed": "Italy", "location": "Sicily", "label": "Sicilia"},
        ]
        
        total_local = len(LOCAL_QUERIES) * len(local_locations)
        total_remote = len(REMOTE_QUERIES)
        total = total_local + total_remote
        counter = 0

        self.logger.info(f"=== RICERCHE LOCALI ({total_local} query) ===")
        for country_cfg in local_locations:
            for term in LOCAL_QUERIES:
                counter += 1
                label = country_cfg["label"]
                self.logger.info(f"[{counter}/{total}] Locale: '{term}' in {label}")
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
                    self.logger.warning(f"  -> Errore: {exc}")
                time.sleep(2)

        # 2. Query REMOTE: cercate UNA SOLA VOLTA per tutta Italia
        self.logger.info(f"=== RICERCHE SMART WORKING ({total_remote} query, solo Italia) ===")
        italy_cfg = {"country_indeed": "Italy", "location": "Italy", "label": "Italia (Smart Working)"}
        
        for term in REMOTE_QUERIES:
            counter += 1
            self.logger.info(f"[{counter}/{total}] Remoto: '{term}'")
            try:
                jobs = scrape_jobs(
                    site_name=WORKING_SITES,
                    search_term=term,
                    location=italy_cfg["location"],
                    country_indeed=italy_cfg["country_indeed"],
                    hours_old=settings.HOURS_OLD,
                    results_wanted=settings.RESULTS_WANTED,
                    linkedin_fetch_description=True,
                    verbose=0,
                )
                if len(jobs) > 0:
                    jobs["search_country"] = italy_cfg["label"]
                    jobs["source_type"] = jobs.get("site", "portal")
                    jobs["location"] = jobs.get("location", italy_cfg["location"])
                    all_jobs.append(jobs)
                    self.logger.info(f"  -> {len(jobs)} offerte raccolte")
            except Exception as exc:
                self.logger.warning(f"  -> Errore: {exc}")
            time.sleep(2)

        if not all_jobs:
            return pd.DataFrame()

        return pd.concat(all_jobs, ignore_index=True)
