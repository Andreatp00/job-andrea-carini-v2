"""
Modelli dati per il livello di persistenza.

Definisce le dataclass che rappresentano le entità principali
del sistema: offerte di lavoro, valutazioni, candidature e log di esecuzione.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Job:
    """Rappresenta un'offerta di lavoro raccolta dai vari scraper."""

    fingerprint: str
    title: str
    source: str
    company: str = ''
    location: str = ''
    description: str = ''
    url: str = ''
    url_direct: str = ''
    source_type: str = ''
    search_country: str = ''
    country_label: str = ''
    date_posted: str = ''
    date_collected: str = field(default_factory=lambda: datetime.now().isoformat())
    raw_data: Optional[str] = None
    id: Optional[int] = None


@dataclass
class Evaluation:
    """Valutazione di un'offerta di lavoro con punteggi multipli."""

    job_id: int
    final_score: float
    keyword_score: float = 0.0
    geo_score: float = 0.0
    level_score: float = 0.0
    office_score: float = 0.0
    part_time_score: float = 0.0
    tech_bonus: float = 0.0
    rule_score: float = 0.0
    ai_score: Optional[float] = None
    match_grade: str = ''
    role_family: str = ''
    company_tier: str = ''
    modality: str = ''
    excluded: bool = False
    exclude_reason: str = ''
    second_chance: bool = False
    evaluated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    id: Optional[int] = None


@dataclass
class Application:
    """Registra una candidatura inviata per un'offerta di lavoro."""

    job_id: int
    method: str       # auto, semi-auto, manual
    platform: str     # linkedin, indeed, subito, altro
    status: str = 'pending'  # pending, sent, failed, skipped
    failure_reason: str = ''
    applied_at: str = ''
    notes: str = ''
    screenshot_path: str = ''
    id: Optional[int] = None


@dataclass
class RunLog:
    """Log di una singola esecuzione del bot."""

    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ''
    status: str = 'running'       # running, completed, crashed
    phase: str = ''               # collecting, filtering, applying, reporting
    jobs_collected: int = 0
    jobs_relevant: int = 0
    jobs_applied: int = 0
    error_log: str = ''
    id: Optional[int] = None
