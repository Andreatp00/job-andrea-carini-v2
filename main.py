import time
import argparse
import pandas as pd
from datetime import datetime
import logging
from config import settings
from storage.database import Database
from storage.models import RunLog
from collector import (
    JobSpyCollector, SubitoCollector, ConcorsiCollector,
    OpportunitaCollector, CompanySitesCollector
)
from engine import normalize_jobs, filter_and_rank, ai_rank_jobs
from notification import (
    export_reports, generate_text_report, generate_email_html,
    send_telegram_message, send_telegram_document, send_email
)
from utils.logger import setup_logger

def parse_args():
    parser = argparse.ArgumentParser(description="Job Hunter 2.0 - Ricerca lavoro locale")
    parser.add_argument("--no-ai", action="store_true", help="Disabilita il ranking AI con Mistral")
    parser.add_argument("--no-email", action="store_true", help="Disabilita l'invio via email")
    parser.add_argument("--no-telegram", action="store_true", help="Disabilita le notifiche Telegram")
    return parser.parse_args()

def run_collectors():
    collectors = [
        JobSpyCollector(),
        SubitoCollector(),
        ConcorsiCollector(),
        OpportunitaCollector(),
        CompanySitesCollector()
    ]
    
    all_frames = []
    for col in collectors:
        try:
            df = col.collect()
            if not df.empty:
                all_frames.append(df)
        except Exception as e:
            logging.error(f"Errore collector {col.source_type}: {e}")
            
    if not all_frames:
        return pd.DataFrame()
        
    return pd.concat(all_frames, ignore_index=True)

def main():
    args = parse_args()
    logger = setup_logger("JobHunter", settings.LOG_DIR)
    
    start = time.time()
    logger.info("=" * 60)
    logger.info("JOB HUNTER 2.0 — Profilo Back Office / Ragioneria")
    logger.info("Ricerca CV-first con database SQLite, deduplica, e report")
    logger.info("Target: Trapani e provincia + Smart Working Italia")
    logger.info("=" * 60)

    db = Database(settings.DB_PATH)
    
    with db:
        run_id = db.start_run()
        
        # 1. Recupero storico
        previous = db.get_known_fingerprints(days=settings.HISTORY_RETENTION_DAYS)
        logger.info(f"Offerte note da storico (ultimi {settings.HISTORY_RETENTION_DAYS}gg): {len(previous)}")

        # 2. Collect
        db.update_run(run_id, phase="collecting")
        df_all = run_collectors()
        
        if df_all.empty:
            logger.info("Nessuna offerta trovata.")
            db.update_run(run_id, status="completed", phase="reporting")
            return
            
        jobs_collected = len(df_all)

        # 3. Process
        db.update_run(run_id, phase="filtering", jobs_collected=jobs_collected)
        df_all = normalize_jobs(df_all)
        logger.info(f"Offerte normalizzate: {len(df_all)}")

        relevant_df, excluded_df = filter_and_rank(df_all, previous)
        logger.info(f"Offerte rilevanti: {len(relevant_df)}")
        logger.info(f"Offerte escluse: {len(excluded_df)}")

        if not relevant_df.empty:
            for source in relevant_df["source_type"].unique():
                count = (relevant_df["source_type"] == source).sum()
                logger.info(f"  Fonte '{source}': {count} rilevanti")

            if not args.no_ai:
                relevant_df = ai_rank_jobs(relevant_df)

        jobs_relevant = len(relevant_df)

        # 4. Storage & Notification
        db.update_run(run_id, phase="reporting", jobs_relevant=jobs_relevant)
        
        # Save to DB (optional, depending on architecture, we can save all valid jobs here)
        
        xlsx_path, csv_path = export_reports(relevant_df, excluded_df)
        text_report = generate_text_report(relevant_df)
        html_report = generate_email_html(relevant_df)

        if not args.no_telegram:
            send_telegram_message(text_report)
            if xlsx_path:
                send_telegram_document(xlsx_path, f"Report Job Hunter - {datetime.now():%d/%m/%Y}")
                
        if not args.no_email:
            send_email(html_report, xlsx_path)
            
        # Update run log
        db.update_run(run_id, status="completed", completed_at=datetime.now().isoformat())

    elapsed = time.time() - start
    logger.info(f"Esecuzione completata in {elapsed:.0f}s ({elapsed / 60:.1f} min)")

if __name__ == "__main__":
    main()
