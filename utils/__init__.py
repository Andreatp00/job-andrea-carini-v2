"""
Package ``utils`` — Funzioni di utilità per Job Hunter 2.0.

Ri-esporta le funzioni più utilizzate dai sotto-moduli per comodità
di importazione::

    from utils import normalize_text, canonicalize_url, fingerprint_job
"""

from utils.text import normalize_text, contains_any
from utils.url import canonicalize_url, extract_domain, extract_real_url_from_redirect
from utils.fingerprint import fingerprint_job, grade_from_score, source_priority
from utils.http import get_tls_session, get_headers
from utils.logger import setup_logger

__all__ = [
    # text
    "normalize_text",
    "contains_any",
    # url
    "canonicalize_url",
    "extract_domain",
    "extract_real_url_from_redirect",
    # fingerprint
    "fingerprint_job",
    "grade_from_score",
    "source_priority",
    # http
    "get_tls_session",
    "get_headers",
    # logger
    "setup_logger",
]
