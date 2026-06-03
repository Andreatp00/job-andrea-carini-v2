from collector.jobspy_scraper import JobSpyCollector
from collector.subito import SubitoCollector
from collector.concorsi import ConcorsiCollector
from collector.opportunita import OpportunitaCollector
from collector.company_sites import CompanySitesCollector
from collector.web_search import search_web_engines

__all__ = [
    "JobSpyCollector",
    "SubitoCollector",
    "ConcorsiCollector",
    "OpportunitaCollector",
    "CompanySitesCollector",
    "search_web_engines",
]
