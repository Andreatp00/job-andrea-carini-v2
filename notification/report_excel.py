import pandas as pd
import csv
from pathlib import Path
from datetime import datetime
import logging
from config import settings

logger = logging.getLogger("JobHunter.ReportExcel")

def build_tracker_sheet(df: pd.DataFrame) -> pd.DataFrame:
    tracker = df.copy()
    tracker["Da_Valutare"] = "SI"
    tracker["Da_Candidare"] = ""
    tracker["Candidata"] = ""
    tracker["Data_Candidatura"] = ""
    tracker["Follow_Up"] = ""
    tracker["Colloquio"] = ""
    tracker["Esito"] = ""
    tracker["Note"] = ""
    return tracker[
        [
            "title", "company", "search_country", "location", "modality", "final_score", "match_grade",
            "why_match", "job_url", "Da_Valutare", "Da_Candidare", "Candidata",
            "Data_Candidatura", "Follow_Up", "Colloquio", "Esito", "Note",
        ]
    ].rename(
        columns={
            "title": "Posizione",
            "company": "Azienda/Ente",
            "search_country": "Zona",
            "location": "Località",
            "modality": "Modalità",
            "final_score": "Score",
            "match_grade": "Classe",
            "why_match": "Perché",
            "job_url": "URL",
        }
    )

def export_reports(relevant_df: pd.DataFrame, excluded_df: pd.DataFrame) -> tuple[Path | None, Path | None]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = settings.REPORT_DIR / f"jobs_relevant_{timestamp}.csv"
    xlsx_path = settings.REPORT_DIR / f"jobs_report_{timestamp}.xlsx"

    if relevant_df.empty:
        return None, None

    top_df = relevant_df[relevant_df["final_score"] >= settings.TOP_MATCH_SCORE].copy()
    borderline_df = relevant_df[
        (relevant_df["final_score"] >= settings.BORDERLINE_SCORE) & (relevant_df["final_score"] < settings.TOP_MATCH_SCORE)
    ].copy()

    export_columns = [
        "title", "company", "search_country", "location", "modality", "role_family", "company_tier",
        "source_type", "site", "final_score", "rule_score", "ai_score", "match_grade",
        "why_match", "matched_keywords", "job_url",
    ]

    # Fill missing columns with pd.NA or "" to avoid KeyErrors
    for df in [relevant_df, top_df, borderline_df]:
        if not df.empty:
            for col in export_columns:
                if col not in df.columns:
                    df[col] = ""

    relevant_df.to_csv(csv_path, index=False, quoting=csv.QUOTE_NONNUMERIC, escapechar="\\")

    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        if not top_df.empty:
            top_df.reindex(columns=export_columns).to_excel(writer, index=False, sheet_name="Top_Match")
        relevant_df.reindex(columns=export_columns).to_excel(writer, index=False, sheet_name="All_Relevant")
        if not borderline_df.empty:
            borderline_df.reindex(columns=export_columns).to_excel(writer, index=False, sheet_name="Borderline")
        if not excluded_df.empty:
            excluded_cols = ["title", "company", "search_country", "location", "source_type", "excluded_reason", "job_url"]
            for col in excluded_cols:
                if col not in excluded_df.columns:
                    excluded_df[col] = ""
            excluded_df.reindex(columns=excluded_cols).to_excel(writer, index=False, sheet_name="Esclusi_Audit")
        if not relevant_df.empty:
            build_tracker_sheet(relevant_df).to_excel(writer, index=False, sheet_name="Tracker_Candidature")

    logger.info(f"CSV salvato: {csv_path}")
    logger.info(f"Excel salvato: {xlsx_path}")
    return xlsx_path, csv_path
