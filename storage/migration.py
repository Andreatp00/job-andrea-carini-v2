"""
Migrazione dal formato JSON legacy al database SQLite.

Gestisce l'importazione dei dati dai file JSON storici (seen_jobs.json
e job_history.json) nella nuova struttura del database relazionale.
"""

import json
import logging
from hashlib import sha1
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from storage.database import Database
from storage.models import Job

logger = logging.getLogger("JobHunter.Migration")


def _canonicalize_url(url: str) -> str:
    """Normalizza un URL rimuovendo parametri UTM e frammenti.

    Replica la logica di canonicalize_url() dal modulo principale
    per garantire la coerenza dei fingerprint durante la migrazione.

    Args:
        url: URL da normalizzare.

    Returns:
        URL canonicalizzato.
    """
    url = url.strip() if url else ''
    if not url or url in {"#", "N/A"}:
        return ''
    try:
        parsed = urlparse(url)
        query = [
            (k, v)
            for k, v in parse_qsl(parsed.query, keep_blank_values=True)
            if not k.lower().startswith("utm_")
        ]
        clean = parsed._replace(query=urlencode(query), fragment="")
        return urlunparse(clean)
    except Exception:
        return url


def _fingerprint_from_url(url: str) -> str:
    """Calcola il fingerprint SHA1 da un URL canonicalizzato.

    Args:
        url: URL da cui calcolare il fingerprint.

    Returns:
        Hash SHA1 esadecimale.
    """
    canonical = _canonicalize_url(url).lower()
    return sha1(canonical.encode("utf-8")).hexdigest()


def _load_json(path: Path, default):
    """Carica un file JSON con gestione errori.

    Args:
        path: percorso del file JSON.
        default: valore di default se il file non esiste o non è valido.

    Returns:
        Contenuto del file JSON o il valore di default.
    """
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception as exc:
        logger.warning("Errore lettura JSON %s: %s", path, exc)
        return default


def migrate_from_json(db: Database, base_dir: Path) -> None:
    """Migra i dati dai file JSON legacy al database SQLite.

    Legge seen_jobs.json e job_history.json e inserisce i fingerprint
    nella tabella jobs. Gestisce entrambi i formati legacy:

    - **seen_jobs.json**: dizionario ``{url: data_invio}``
    - **job_history.json**: dizionario ``{fingerprint: {job_url, sent_at, source, ...}}``

    Args:
        db: istanza del Database già inizializzata.
        base_dir: directory radice del progetto (dove si trova seen_jobs.json).
    """
    seen_file = base_dir / "seen_jobs.json"
    data_dir = base_dir / "data"
    history_file = data_dir / "job_history.json"

    migrated = 0
    skipped = 0

    # ── 1. Migra seen_jobs.json ──────────────────────────────────────────
    legacy_seen: dict = _load_json(seen_file, {})
    if isinstance(legacy_seen, dict) and legacy_seen:
        logger.info(
            "Migrazione seen_jobs.json: %d voci trovate", len(legacy_seen)
        )
        for job_url, sent_at in legacy_seen.items():
            fp = _fingerprint_from_url(job_url)
            canonical = _canonicalize_url(job_url)

            job = Job(
                fingerprint=fp,
                title="(migrato da seen_jobs.json)",
                source="legacy_seen_file",
                url=canonical,
                date_collected=sent_at if isinstance(sent_at, str) else "",
            )
            result_id = db.insert_job(job)
            if result_id:
                migrated += 1
            else:
                skipped += 1

        logger.info(
            "seen_jobs.json completato: %d migrati, %d già presenti",
            migrated,
            skipped,
        )
    else:
        logger.info("seen_jobs.json non trovato o vuoto — skip")

    # ── 2. Migra job_history.json ────────────────────────────────────────
    history: dict = _load_json(history_file, {})
    if isinstance(history, dict) and history:
        hist_migrated = 0
        hist_skipped = 0
        logger.info(
            "Migrazione job_history.json: %d voci trovate", len(history)
        )
        for fingerprint, entry in history.items():
            if not isinstance(entry, dict):
                continue

            job_url = entry.get("job_url", "")
            sent_at = entry.get("sent_at", "")
            source = entry.get("source", "legacy_history")

            # Usa il fingerprint come chiave (è già calcolato)
            job = Job(
                fingerprint=fingerprint,
                title=entry.get("title", "(migrato da job_history.json)"),
                source=source,
                company=entry.get("company", ""),
                location=entry.get("location", ""),
                url=_canonicalize_url(job_url) if job_url else "",
                date_collected=sent_at if isinstance(sent_at, str) else "",
            )
            result_id = db.insert_job(job)
            if result_id:
                hist_migrated += 1
            else:
                hist_skipped += 1

        logger.info(
            "job_history.json completato: %d migrati, %d già presenti",
            hist_migrated,
            hist_skipped,
        )
        migrated += hist_migrated
        skipped += hist_skipped
    else:
        logger.info("job_history.json non trovato o vuoto — skip")

    logger.info(
        "Migrazione JSON → SQLite completata: %d totali migrati, %d già presenti",
        migrated,
        skipped,
    )
