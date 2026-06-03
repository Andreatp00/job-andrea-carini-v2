"""
Pacchetto config — Job Hunter 2.0.

Riesporta tutti i simboli pubblici dai sotto-moduli per
consentire import diretti, ad es.:

    from config import settings, PROFILE, SEARCH_TERMS
"""

from config.settings import settings
from config.profile import PROFILE
from config.search_terms import (
    SEARCH_TERMS,
    GOOGLE_SEARCH_TERMS,
    COUNTRY_SEARCHES,
    INCLUDED_COUNTRIES,
    EXCLUDED_COUNTRIES,
    COMPANY_CAREER_SITES,
    OPPORTUNITA_SITES,
)
from config.scoring import (
    COMPANY_RELEVANCE_KEYWORDS,
    EXCLUDE_KEYWORDS_TITLE,
    EXCLUDE_KEYWORDS_TEXT,
    PROFILE_KEYWORDS_SCORES,
    MASTER_LEVEL_KEYWORDS,
    ROLE_FAMILY_KEYWORDS,
    PREFERRED_COMPANY_INDICATORS,
    STARTUP_KEYWORDS,
)
from config.geo_data import (
    LOCALITY_KEYWORDS,
    TRAPANI_TOWNS,
    SICILIA_CITIES,
    PALERMO_TOWNS,
    WRONG_REGIONS,
    SMART_WORKING_KEYWORDS,
)

__all__ = [
    # settings
    "settings",
    # profilo
    "PROFILE",
    # termini di ricerca
    "SEARCH_TERMS",
    "GOOGLE_SEARCH_TERMS",
    "COUNTRY_SEARCHES",
    "INCLUDED_COUNTRIES",
    "EXCLUDED_COUNTRIES",
    "COMPANY_CAREER_SITES",
    "OPPORTUNITA_SITES",
    # scoring
    "COMPANY_RELEVANCE_KEYWORDS",
    "EXCLUDE_KEYWORDS_TITLE",
    "EXCLUDE_KEYWORDS_TEXT",
    "PROFILE_KEYWORDS_SCORES",
    "MASTER_LEVEL_KEYWORDS",
    "ROLE_FAMILY_KEYWORDS",
    "PREFERRED_COMPANY_INDICATORS",
    "STARTUP_KEYWORDS",
    # geo
    "LOCALITY_KEYWORDS",
    "TRAPANI_TOWNS",
    "SICILIA_CITIES",
    "PALERMO_TOWNS",
    "WRONG_REGIONS",
    "SMART_WORKING_KEYWORDS",
]
