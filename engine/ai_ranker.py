import json
import time
import pandas as pd
import logging
from config import settings
from utils.text import normalize_text
from utils.fingerprint import grade_from_score

logger = logging.getLogger("JobHunter.AIRanker")

def _parse_json_response(content: str) -> list:
    text = normalize_text(content)
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else parts[0]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()
    try:
        start = text.find("[")
        end = text.rfind("]") + 1
        if start != -1 and end != 0:
            return json.loads(text[start:end])
        return json.loads(text)
    except json.JSONDecodeError as exc:
        logger.warning(f"Errore parsing JSON risposta AI: {exc}\nContenuto: {text[:200]}...")
        return []

def ai_rank_jobs(df: pd.DataFrame) -> pd.DataFrame:
    if not settings.MISTRAL_API_KEY or df.empty:
        return df

    try:
        from openai import OpenAI
    except Exception as exc:
        logger.warning(f"Client Mistral non disponibile: {exc}")
        return df

    client = OpenAI(base_url="https://api.mistral.ai/v1", api_key=settings.MISTRAL_API_KEY)
    enriched = df.copy()
    enriched["ai_score"] = pd.NA
    enriched["ai_reason"] = ""

    BATCH_SIZE = 30
    DELAY_BETWEEN = 4
    MAX_RETRIES = 3
    total_batches = (len(enriched) + BATCH_SIZE - 1) // BATCH_SIZE
    consecutive_429 = 0

    for batch_num, start in enumerate(range(0, len(enriched), BATCH_SIZE), 1):
        batch = enriched.iloc[start:start + BATCH_SIZE]
        jobs_summary = []
        for idx, row in batch.iterrows():
            jobs_summary.append(
                {
                    "idx": str(idx),
                    "title": normalize_text(row.get("title")),
                    "company": normalize_text(row.get("company")),
                    "location": normalize_text(row.get("location")),
                    "country": normalize_text(row.get("search_country")),
                    "description_snippet": normalize_text(row.get("description"))[:550],
                    "rule_score": float(row.get("rule_score", 0)),
                    "role_family": normalize_text(row.get("role_family")),
                }
            )

        prompt = f"""Sei un assistente AI specializzato nel recruiting e nella ricerca lavoro.
Il candidato si chiama Andrea Carini, ha 25 anni, Diplomato Ragioniere (Istituto Tecnico Economico), con oltre 6 anni di esperienza in:
- Gestione operativa punto vendita, supporto clienti e chiusura cassa
- Contabilità generale, prima nota (ERP: SAP Business One, Teamsystem, Zucchetti)
- Gestione ordini, logistica, inventario (WMS, ERP) e spedizioni
- Gestione e-commerce e siti web (WordPress, Shopify, WooCommerce)

Ha disponibilità immediata ed è automunito. Cerca lavoro come:
- Impiegato amministrativo / Addetto back office / Contabilità
- Addetto logistica / Gestione ordini e spedizioni
- Customer service back office
- Segreteria amministrativa

Regole per il ranking (0-100):
- +20 se è a Trapani o provincia
- +15 se è in Sicilia
- +20 se smart working / remoto / lavoro da casa / full remote
- +15 se non richiede laurea, basta il diploma
- +10/15 se il ruolo è coerente con la logistica, magazzino, ERP o contabilità
- Premia stage/praticantato (fa esperienza)
- Penalizza fortemente se richiede laurea
- Penalizza ruoli troppo senior (responsabile, dirigente, capo)

Valuta le offerte fornite. Restituisci SOLO un JSON array nel formato esatto (senza altre parole):
[{{ "idx": "id", "ai_score": 85, "reason": "Motivazione di massimo 10 parole" }}]

Offerte da valutare:
{json.dumps(jobs_summary, ensure_ascii=False, indent=2)}"""

        success = False
        for retry in range(MAX_RETRIES):
            try:
                logger.info(f"  AI Ranking batch {batch_num}/{total_batches} ({len(batch)} offerte)...")
                response = client.chat.completions.create(
                    model=settings.MISTRAL_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=4000,
                )
                parsed = _parse_json_response(response.choices[0].message.content)
                mapping = {item["idx"]: item for item in parsed}
                applied = 0
                for idx in batch.index:
                    item = mapping.get(str(idx))
                    if item:
                        enriched.loc[idx, "ai_score"] = item.get("ai_score")
                        enriched.loc[idx, "ai_reason"] = normalize_text(item.get("reason"))
                        applied += 1
                logger.info(f"  AI Ranking batch {batch_num}: {applied}/{len(batch)} scored")
                consecutive_429 = 0
                success = True
                break

            except Exception as exc:
                exc_str = str(exc)
                if "429" in exc_str or "rate_limit" in exc_str.lower():
                    consecutive_429 += 1
                    wait = min(15 * (2 ** retry), 60)
                    logger.info(
                        f"  AI Ranking batch {batch_num}: rate limit (429), "
                        f"attendo {wait}s (tentativo {retry + 1}/{MAX_RETRIES})..."
                    )
                    time.sleep(wait)
                else:
                    logger.info(f"  AI Ranking batch {batch_num} skippato: {exc}")
                    break

        if not success and consecutive_429 >= 3:
            remaining = total_batches - batch_num
            logger.info(
                f"  AI Ranking: {consecutive_429} rate limit consecutivi, "
                f"skip {remaining} batch rimanenti (rule_score usato come fallback)"
            )
            break

        if batch_num < total_batches:
            time.sleep(DELAY_BETWEEN)

    enriched["ai_score"] = pd.to_numeric(enriched["ai_score"], errors="coerce")
    enriched["final_score"] = enriched.apply(
        lambda row: round((row["rule_score"] * 0.6) + (row["ai_score"] * 0.4), 1)
        if pd.notna(row["ai_score"]) else round(float(row["rule_score"]), 1),
        axis=1,
    )
    enriched["match_grade"] = enriched["final_score"].apply(grade_from_score)
    if "source_priority" in enriched.columns:
        enriched = enriched.sort_values(["final_score", "source_priority"], ascending=[False, False]).reset_index(drop=True)
    else:
        enriched = enriched.sort_values(["final_score"], ascending=[False]).reset_index(drop=True)
        
    return enriched
