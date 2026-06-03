import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from pathlib import Path
from datetime import datetime
import logging
from config import settings

logger = logging.getLogger("JobHunter.Email")

def send_email(html_content: str, attachment_path: Path | None = None):
    if not settings.EMAIL_SENDER or not settings.EMAIL_APP_PASSWORD:
        logger.info("Email non configurata.")
        return
    try:
        message = MIMEMultipart()
        message["Subject"] = f"Job Hunter Report - {datetime.now():%d/%m/%Y}"
        message["From"] = settings.EMAIL_SENDER
        message["To"] = settings.EMAIL_RECIPIENT
        message.attach(MIMEText(html_content, "html", "utf-8"))

        if attachment_path and attachment_path.exists():
            with open(attachment_path, "rb") as handle:
                attachment = MIMEApplication(handle.read(), _subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            attachment.add_header("Content-Disposition", "attachment", filename=attachment_path.name)
            message.attach(attachment)

        with smtplib.SMTP(settings.EMAIL_SMTP_SERVER, settings.EMAIL_SMTP_PORT) as server:
            server.starttls()
            server.login(settings.EMAIL_SENDER, settings.EMAIL_APP_PASSWORD)
            server.sendmail(settings.EMAIL_SENDER, settings.EMAIL_RECIPIENT, message.as_string())

        logger.info("Email inviata")
    except Exception as exc:
        logger.error(f"Errore email: {exc}")
