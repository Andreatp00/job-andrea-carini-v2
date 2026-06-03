"""
Package di persistenza per Job Hunter 2.0.

Esporta il gestore del database e i modelli dati principali.
"""

from storage.database import Database
from storage.models import Application, Evaluation, Job, RunLog

__all__ = [
    "Database",
    "Job",
    "Evaluation",
    "Application",
    "RunLog",
]
