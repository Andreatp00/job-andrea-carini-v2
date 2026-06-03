"""
Gestore del database SQLite per il sistema Job Hunter 2.0.

Fornisce un'interfaccia ad alto livello per tutte le operazioni CRUD
sulle tabelle principali: jobs, evaluations, applications, notifications, runs.
Supporta context manager, recupero da crash e deduplicazione tramite fingerprint.
"""

import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from storage.models import Application, Evaluation, Job, RunLog

logger = logging.getLogger("JobHunter.Database")

# ── Schema SQL ──────────────────────────────────────────────────────────────

_SCHEMA_SQL = """\
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fingerprint TEXT UNIQUE NOT NULL,
    url TEXT,
    url_direct TEXT,
    title TEXT NOT NULL,
    company TEXT,
    location TEXT,
    description TEXT,
    source TEXT NOT NULL,
    source_type TEXT,
    search_country TEXT,
    country_label TEXT,
    date_posted TEXT,
    date_collected TEXT NOT NULL DEFAULT (datetime('now')),
    raw_data TEXT
);

CREATE TABLE IF NOT EXISTS evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES jobs(id),
    keyword_score REAL DEFAULT 0,
    geo_score REAL DEFAULT 0,
    level_score REAL DEFAULT 0,
    office_score REAL DEFAULT 0,
    part_time_score REAL DEFAULT 0,
    tech_bonus REAL DEFAULT 0,
    rule_score REAL DEFAULT 0,
    ai_score REAL,
    final_score REAL NOT NULL,
    match_grade TEXT,
    role_family TEXT,
    company_tier TEXT,
    modality TEXT,
    excluded BOOLEAN DEFAULT 0,
    exclude_reason TEXT,
    second_chance BOOLEAN DEFAULT 0,
    evaluated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES jobs(id),
    method TEXT NOT NULL,
    platform TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    failure_reason TEXT,
    applied_at TEXT,
    notes TEXT,
    screenshot_path TEXT
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES jobs(id),
    channel TEXT NOT NULL,
    sent_at TEXT NOT NULL DEFAULT (datetime('now')),
    report_path TEXT
);

CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT,
    status TEXT DEFAULT 'running',
    phase TEXT,
    jobs_collected INTEGER DEFAULT 0,
    jobs_relevant INTEGER DEFAULT 0,
    jobs_applied INTEGER DEFAULT 0,
    error_log TEXT
);

CREATE INDEX IF NOT EXISTS idx_jobs_fingerprint ON jobs(fingerprint);
CREATE INDEX IF NOT EXISTS idx_jobs_collected ON jobs(date_collected);
CREATE INDEX IF NOT EXISTS idx_evaluations_score ON evaluations(final_score DESC);
CREATE INDEX IF NOT EXISTS idx_applications_job ON applications(job_id);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
"""


class Database:
    """Gestore del database SQLite per Job Hunter 2.0.

    Utilizzo con context manager::

        with Database("data/jobs.db") as db:
            db.insert_job(job)
    """

    def __init__(self, db_path: str | Path) -> None:
        """Apre (o crea) il database e applica le migrazioni.

        Args:
            db_path: percorso del file SQLite.
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._connect()
        self._create_tables()
        logger.info("Database inizializzato: %s", self.db_path)

    # ── Connessione e lifecycle ──────────────────────────────────────────

    def _connect(self) -> None:
        """Crea la connessione SQLite con le impostazioni ottimali."""
        self._conn = sqlite3.connect(str(self.db_path), timeout=30)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")

    def _create_tables(self) -> None:
        """Crea tutte le tabelle e gli indici se non esistono."""
        self._conn.executescript(_SCHEMA_SQL)
        self._conn.commit()

    def close(self) -> None:
        """Chiude la connessione al database."""
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.debug("Connessione al database chiusa")

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    # ── Jobs ─────────────────────────────────────────────────────────────

    def insert_job(self, job: Job) -> int:
        """Inserisce un'offerta di lavoro nel database.

        Usa INSERT OR IGNORE sul fingerprint per evitare duplicati.

        Args:
            job: istanza di Job da inserire.

        Returns:
            L'id della riga inserita, oppure l'id esistente se il
            fingerprint era già presente.
        """
        cursor = self._conn.execute(
            """
            INSERT OR IGNORE INTO jobs
                (fingerprint, url, url_direct, title, company, location,
                 description, source, source_type, search_country,
                 country_label, date_posted, date_collected, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job.fingerprint,
                job.url,
                job.url_direct,
                job.title,
                job.company,
                job.location,
                job.description,
                job.source,
                job.source_type,
                job.search_country,
                job.country_label,
                job.date_posted,
                job.date_collected,
                job.raw_data,
            ),
        )
        self._conn.commit()

        if cursor.lastrowid and cursor.rowcount > 0:
            return cursor.lastrowid

        # Il fingerprint esisteva già: recupera l'id esistente
        row = self._conn.execute(
            "SELECT id FROM jobs WHERE fingerprint = ?",
            (job.fingerprint,),
        ).fetchone()
        return row["id"] if row else 0

    def get_job_by_fingerprint(self, fingerprint: str) -> Optional[Job]:
        """Recupera un'offerta di lavoro tramite il suo fingerprint.

        Args:
            fingerprint: hash univoco dell'offerta.

        Returns:
            Istanza di Job oppure None se non trovata.
        """
        row = self._conn.execute(
            "SELECT * FROM jobs WHERE fingerprint = ?",
            (fingerprint,),
        ).fetchone()
        return self._row_to_job(row) if row else None

    def get_known_fingerprints(self, days: int = 60) -> set[str]:
        """Restituisce i fingerprint delle offerte raccolte negli ultimi N giorni.

        Args:
            days: numero di giorni da considerare (default 60).

        Returns:
            Set di fingerprint noti.
        """
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        rows = self._conn.execute(
            "SELECT fingerprint FROM jobs WHERE date_collected >= ?",
            (cutoff,),
        ).fetchall()
        return {row["fingerprint"] for row in rows}

    @staticmethod
    def _row_to_job(row: sqlite3.Row) -> Job:
        """Converte una riga del database in un'istanza di Job."""
        return Job(
            id=row["id"],
            fingerprint=row["fingerprint"],
            url=row["url"] or '',
            url_direct=row["url_direct"] or '',
            title=row["title"],
            company=row["company"] or '',
            location=row["location"] or '',
            description=row["description"] or '',
            source=row["source"],
            source_type=row["source_type"] or '',
            search_country=row["search_country"] or '',
            country_label=row["country_label"] or '',
            date_posted=row["date_posted"] or '',
            date_collected=row["date_collected"] or '',
            raw_data=row["raw_data"],
        )

    # ── Evaluations ──────────────────────────────────────────────────────

    def insert_evaluation(self, evaluation: Evaluation) -> int:
        """Inserisce una valutazione nel database.

        Args:
            evaluation: istanza di Evaluation da inserire.

        Returns:
            L'id della riga inserita.
        """
        cursor = self._conn.execute(
            """
            INSERT INTO evaluations
                (job_id, keyword_score, geo_score, level_score, office_score,
                 part_time_score, tech_bonus, rule_score, ai_score,
                 final_score, match_grade, role_family, company_tier,
                 modality, excluded, exclude_reason, second_chance,
                 evaluated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                evaluation.job_id,
                evaluation.keyword_score,
                evaluation.geo_score,
                evaluation.level_score,
                evaluation.office_score,
                evaluation.part_time_score,
                evaluation.tech_bonus,
                evaluation.rule_score,
                evaluation.ai_score,
                evaluation.final_score,
                evaluation.match_grade,
                evaluation.role_family,
                evaluation.company_tier,
                evaluation.modality,
                int(evaluation.excluded),
                evaluation.exclude_reason,
                int(evaluation.second_chance),
                evaluation.evaluated_at,
            ),
        )
        self._conn.commit()
        return cursor.lastrowid

    # ── Applications ─────────────────────────────────────────────────────

    def insert_application(self, application: Application) -> int:
        """Inserisce una candidatura nel database.

        Args:
            application: istanza di Application da inserire.

        Returns:
            L'id della riga inserita.
        """
        cursor = self._conn.execute(
            """
            INSERT INTO applications
                (job_id, method, platform, status, failure_reason,
                 applied_at, notes, screenshot_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                application.job_id,
                application.method,
                application.platform,
                application.status,
                application.failure_reason,
                application.applied_at,
                application.notes,
                application.screenshot_path,
            ),
        )
        self._conn.commit()
        return cursor.lastrowid

    def get_application_by_job_id(self, job_id: int) -> Optional[Application]:
        """Recupera la candidatura associata a un'offerta di lavoro.

        Args:
            job_id: id dell'offerta di lavoro.

        Returns:
            Istanza di Application oppure None se non trovata.
        """
        row = self._conn.execute(
            "SELECT * FROM applications WHERE job_id = ?",
            (job_id,),
        ).fetchone()
        if not row:
            return None
        return Application(
            id=row["id"],
            job_id=row["job_id"],
            method=row["method"],
            platform=row["platform"],
            status=row["status"] or 'pending',
            failure_reason=row["failure_reason"] or '',
            applied_at=row["applied_at"] or '',
            notes=row["notes"] or '',
            screenshot_path=row["screenshot_path"] or '',
        )

    # ── Run logs ─────────────────────────────────────────────────────────

    def start_run(self) -> int:
        """Crea un nuovo record di esecuzione.

        Returns:
            L'id della nuova esecuzione.
        """
        cursor = self._conn.execute(
            "INSERT INTO runs (started_at, status) VALUES (?, 'running')",
            (datetime.now().isoformat(),),
        )
        self._conn.commit()
        logger.info("Nuova esecuzione avviata (run_id=%d)", cursor.lastrowid)
        return cursor.lastrowid

    def update_run(self, run_id: int, **kwargs) -> None:
        """Aggiorna i campi di un record di esecuzione.

        Args:
            run_id: id dell'esecuzione da aggiornare.
            **kwargs: coppie campo=valore da aggiornare. I campi validi sono:
                completed_at, status, phase, jobs_collected, jobs_relevant,
                jobs_applied, error_log.
        """
        valid_fields = {
            "completed_at", "status", "phase",
            "jobs_collected", "jobs_relevant", "jobs_applied",
            "error_log",
        }
        updates = {k: v for k, v in kwargs.items() if k in valid_fields}
        if not updates:
            return

        set_clause = ", ".join(f"{col} = ?" for col in updates)
        values = list(updates.values()) + [run_id]
        self._conn.execute(
            f"UPDATE runs SET {set_clause} WHERE id = ?",  # noqa: S608
            values,
        )
        self._conn.commit()

    def get_last_incomplete_run(self) -> Optional[RunLog]:
        """Recupera l'ultima esecuzione non completata (per recupero da crash).

        Returns:
            Istanza di RunLog oppure None se non ci sono esecuzioni incomplete.
        """
        row = self._conn.execute(
            "SELECT * FROM runs WHERE status = 'running' ORDER BY id DESC LIMIT 1",
        ).fetchone()
        if not row:
            return None
        return RunLog(
            id=row["id"],
            started_at=row["started_at"] or '',
            completed_at=row["completed_at"] or '',
            status=row["status"] or 'running',
            phase=row["phase"] or '',
            jobs_collected=row["jobs_collected"] or 0,
            jobs_relevant=row["jobs_relevant"] or 0,
            jobs_applied=row["jobs_applied"] or 0,
            error_log=row["error_log"] or '',
        )
