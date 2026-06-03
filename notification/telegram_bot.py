import requests
import time
import logging
from pathlib import Path
from config import settings

logger = logging.getLogger("JobHunter.Telegram")

def split_telegram_chunks(text: str, max_len: int = 4000) -> list[str]:
    if len(text) <= max_len:
        return [text]
    chunks = []
    current = ""
    for line in text.splitlines():
        candidate = f"{current}\n{line}".strip()
        if len(candidate) > max_len and current:
            chunks.append(current)
            current = line
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks

def send_telegram_message(text: str):
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        logger.info("Telegram non configurato.")
        return
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    for chunk in split_telegram_chunks(text):
        try:
            response = requests.post(
                url,
                data={
                    "chat_id": settings.TELEGRAM_CHAT_ID,
                    "text": chunk,
                    "disable_web_page_preview": True,
                },
                timeout=30,
            )
            if response.status_code != 200:
                logger.error(f"Telegram message error: {response.text}")
            time.sleep(1)
        except Exception as exc:
            logger.error(f"Errore invio Telegram: {exc}")

def send_telegram_document(file_path: Path, caption: str = ""):
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID or not file_path or not file_path.exists():
        return
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendDocument"
    try:
        with open(file_path, "rb") as handle:
            response = requests.post(
                url,
                data={"chat_id": settings.TELEGRAM_CHAT_ID, "caption": caption[:900]},
                files={"document": (file_path.name, handle)},
                timeout=60,
            )
        if response.status_code != 200:
            logger.error(f"Telegram document error: {response.text}")
    except Exception as exc:
        logger.error(f"Errore invio documento Telegram: {exc}")
