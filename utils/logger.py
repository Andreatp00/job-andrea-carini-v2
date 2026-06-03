"""
Configurazione centralizzata del logging.

Crea logger con doppio handler: file (con nome giornaliero) e stderr,
replicando la configurazione originale di ``job_hunter.py``.
"""

import logging
from datetime import datetime
from pathlib import Path


def setup_logger(
    name: str = "JobHunter",
    log_dir: str | Path = "logs",
    level: int = logging.INFO,
) -> logging.Logger:
    """Configura e restituisce un logger con handler su file e stderr.

    Il file di log viene creato nella directory *log_dir* con nome
    ``job_hunter_YYYYMMDD.log`` basato sulla data corrente.

    Se il logger ha già handler configurati, viene restituito così com'è
    per evitare duplicazioni.

    Args:
        name: Nome del logger (default ``"JobHunter"``).
        log_dir: Directory per i file di log (default ``"logs"``).
        level: Livello minimo di logging (default ``logging.INFO``).

    Returns:
        Logger configurato con doppio handler.
    """
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    logger = logging.getLogger(name)

    # Evita di aggiungere handler multipli se chiamato più volte
    if logger.handlers:
        return logger

    logger.setLevel(level)

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    # Handler file giornaliero
    file_handler = logging.FileHandler(
        log_path / f"job_hunter_{datetime.now():%Y%m%d}.log",
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    # Handler stderr (console)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger
