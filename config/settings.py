"""
Impostazioni generali dell'applicazione.

Carica le variabili d'ambiente tramite dotenv e definisce
la classe Settings con tutti i parametri di configurazione.
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class Settings:
    """Configurazione centralizzata dell'applicazione."""

    # --- Telegram ---
    TELEGRAM_BOT_TOKEN: str = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.environ.get("TELEGRAM_CHAT_ID", "")

    # --- Email ---
    EMAIL_RECIPIENT: str = os.environ.get("EMAIL_RECIPIENT", "")
    EMAIL_SENDER: str = os.environ.get("EMAIL_SENDER", "")
    EMAIL_APP_PASSWORD: str = os.environ.get("EMAIL_APP_PASSWORD", "")
    EMAIL_SMTP_SERVER: str = "smtp.gmail.com"
    EMAIL_SMTP_PORT: int = 587

    # --- AI (opzionale) ---
    MISTRAL_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
    MISTRAL_MODEL: str = os.environ.get("MISTRAL_MODEL", "open-mixtral-8x7b")

    # --- Percorsi ---
    BASE_DIR: Path = Path(__file__).parent.parent
    LOG_DIR: Path = BASE_DIR / "logs"
    DATA_DIR: Path = BASE_DIR / "data"
    REPORT_DIR: Path = DATA_DIR / "reports"
    DB_PATH: Path = DATA_DIR / "jobs.db"

    # --- Scraping ---
    HOURS_OLD: int = 120
    RESULTS_WANTED: int = 50
    HISTORY_RETENTION_DAYS: int = 60

    # --- Soglie punteggio ---
    MINIMUM_RELEVANT_SCORE: int = 20
    TOP_MATCH_SCORE: int = 70
    MEDIUM_MATCH_MIN: int = 50
    MEDIUM_MATCH_MAX: int = 69
    BORDERLINE_SCORE: int = 30


settings = Settings()
