import pandas as pd
from datetime import datetime
from utils.text import normalize_text
from config import settings

def generate_text_report(df: pd.DataFrame) -> str:
    today = datetime.now().strftime("%d/%m/%Y")
    if df.empty:
        return f"📋 REPORT JOB HUNTER - {today}\n\nNessuna nuova offerta realmente nuova rispetto allo storico."

    trapani = int((df["search_country"] == "Trapani").sum())
    sicilia = int((df["search_country"] == "Sicilia").sum())
    italia = int(len(df) - trapani - sicilia)
    top = int((df["final_score"] >= settings.TOP_MATCH_SCORE).sum())
    good = int(((df["final_score"] >= settings.MEDIUM_MATCH_MIN) & (df["final_score"] < settings.TOP_MATCH_SCORE)).sum())

    lines = [
        f"📋 REPORT JOB HUNTER - {today}",
        f"🔍 Profilo: Diplomato Ragioneria AFM | Back Office / Contabilità",
        f"📍 Zona: Trapani e provincia + Smart Working Italia",
        "",
        f"Nuove offerte: {len(df)}",
        f"Top match (≥{settings.TOP_MATCH_SCORE}): {top} | Buone: {good}",
        f"📍 Trapani: {trapani} | Sicilia: {sicilia} | Italia/Smart: {italia}",
        "",
        "🏆 PRIME OFFERTE:",
    ]

    for idx, (_, row) in enumerate(df.head(10).iterrows(), start=1):
        emoji = "🔥" if row.get("final_score", 0) >= settings.TOP_MATCH_SCORE else "⭐"
        lines.append(
            f"{emoji} {idx}. [{row.get('match_grade')}] {normalize_text(row.get('title'))} | "
            f"{normalize_text(row.get('company'))} | {normalize_text(row.get('search_country'))} | "
            f"score {row.get('final_score')}"
        )

    lines.append("")
    lines.append("📊 Legenda: 🔥 Top match | ⭐ Buona corrispondenza")
    lines.append("📎 Allego file Excel con Top_Match, All_Relevant, Borderline ed Esclusi_Audit.")
    lines.append("💡 Consiglio: dai priorità alle offerte a Trapani e provincia!")
    return "\n".join(lines)


def generate_email_html(df: pd.DataFrame) -> str:
    today = datetime.now().strftime("%d/%m/%Y")
    if df.empty:
        return f"<h2>Report Job Hunter - {today}</h2><p>Nessuna nuova offerta.</p>"

    rows = []
    for _, row in df.head(25).iterrows():
        emoji = "🔥" if row.get("final_score", 0) >= settings.TOP_MATCH_SCORE else "⭐"
        rows.append(
            f"""
            <tr>
                <td style="padding:6px;border-bottom:1px solid #ddd;">{emoji} {row.get('match_grade')}</td>
                <td style="padding:6px;border-bottom:1px solid #ddd;">{normalize_text(row.get('title'))}</td>
                <td style="padding:6px;border-bottom:1px solid #ddd;">{normalize_text(row.get('company'))}</td>
                <td style="padding:6px;border-bottom:1px solid #ddd;">{normalize_text(row.get('search_country'))}</td>
                <td style="padding:6px;border-bottom:1px solid #ddd;">{row.get('final_score')}</td>
                <td style="padding:6px;border-bottom:1px solid #ddd;">{normalize_text(row.get('why_match'))}</td>
            </tr>
            """
        )

    trapani = int((df["search_country"] == "Trapani").sum())
    sicilia = int((df["search_country"] == "Sicilia").sum())

    return f"""
    <html>
        <body style="font-family:Arial,sans-serif;">
            <h2>📋 Report Job Hunter - {today}</h2>
            <p><strong>Profilo:</strong> Diplomato Ragioneria AFM | Back Office / Contabilità</p>
            <p><strong>📍 Zona:</strong> Trapani e provincia + Smart Working Italia</p>
            <hr>
            <p>Nuove offerte: <strong>{len(df)}</strong> 
               (Trapani: {trapani}, Sicilia: {sicilia}, Italia/Smart: {len(df) - trapani - sicilia})</p>
            <table style="border-collapse:collapse;width:100%;">
                <thead>
                    <tr style="background:#f5f5f5;">
                        <th style="padding:6px;text-align:left;">Classe</th>
                        <th style="padding:6px;text-align:left;">Posizione</th>
                        <th style="padding:6px;text-align:left;">Azienda</th>
                        <th style="padding:6px;text-align:left;">Zona</th>
                        <th style="padding:6px;text-align:left;">Score</th>
                        <th style="padding:6px;text-align:left;">Perché</th>
                    </tr>
                </thead>
                <tbody>{''.join(rows)}</tbody>
            </table>
            <p><strong>Legenda:</strong> 🔥 Top match (≥{settings.TOP_MATCH_SCORE}) | ⭐ Buona corrispondenza</p>
            <p>📎 In allegato il file Excel completo con tracker candidature.</p>
            <p><em>💡 Consiglio: dai priorità alle offerte a Trapani e provincia!</em></p>
        </body>
    </html>
    """
