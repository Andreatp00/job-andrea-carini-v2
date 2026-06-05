import re
import pandas as pd
from utils.text import normalize_text, contains_any
from utils.fingerprint import grade_from_score
from config import (
    settings,
    INCLUDED_COUNTRIES, EXCLUDED_COUNTRIES,
    ROLE_FAMILY_KEYWORDS, PREFERRED_COMPANY_INDICATORS,
    PROFILE_KEYWORDS_SCORES, MASTER_LEVEL_KEYWORDS
)
from engine.geo import (
    infer_country_label, is_allowed_location, is_wrong_region,
    has_strict_wrong_region_in_text, has_wrong_location_in_text,
    get_location_from_url, is_smart_working, is_trapani_area,
    is_palermo_area, is_sicily_area, is_sicily_other, has_vitto_alloggio,
    has_valid_training
)
from engine.filters import (
    is_english_text, contains_any,
    check_degree_requirement, check_seniority_requirement,
    check_excluded_keywords, check_manual_role_blacklist,
    detect_language_fit
)

def classify_role_family(full_text: str) -> str:
    for family, keywords in ROLE_FAMILY_KEYWORDS.items():
        if contains_any(full_text, keywords):
            return family
    if contains_any(full_text, ["amministrativo", "contabilità", "fattura", "segreteria", "ufficio"]):
        return "amministrazione_generale"
    if contains_any(full_text, ["concorso", "pubblico", "categoria", "inpa"]):
        return "concorsi_pubblici"
    return "other"

def infer_company_tier(company: str, source_type: str, full_text: str) -> str:
    company_text = normalize_text(company).lower()
    
    if contains_any(company_text, ["comune", "provincia", "regione", "asl", "inps", "agenzia", "ente"]):
        return "A"
    if contains_any(company_text, ["commercialista", "studio", "commerciale"]):
        return "A"
    if contains_any(company_text, ["adecco", "manpower", "randstad", "gi group", "openjobmetis", "synergie", "etjca", "humangest"]):
        return "A"
    if contains_any(company_text, PREFERRED_COMPANY_INDICATORS):
        return "A"
    if source_type in ("subito", "concorso_pubblico", "company_site"):
        return "A"
    if contains_any(full_text, ["multinazionale", "grande azienda", "corporate"]):
        return "B"
    return "C"

def compute_keyword_score(full_text: str) -> tuple[int, list[str]]:
    score_15 = 0
    score_8 = 0
    score_5 = 0
    hits = []

    for keyword, points in PROFILE_KEYWORDS_SCORES:
        if keyword.lower() in full_text:
            if points == 15 and score_15 < 60:
                score_15 += points
            elif points == 8 and score_8 < 40:
                score_8 += points
            elif points == 5 and score_5 < 25:
                score_5 += points
            hits.append(keyword)

    score_15 = min(score_15, 60)
    score_8 = min(score_8, 40)
    score_5 = min(score_5, 25)

    return score_15 + score_8 + score_5, hits[:8]

def compute_geo_score(location: str, title: str, desc: str, country: str) -> int:
    geo_score = 0
    full_text = f"{title} {location} {desc}".lower()
    
    if is_trapani_area(location) or country == "Trapani":
        geo_score += 30
    elif is_palermo_area(location) or country == "Palermo":
        geo_score += 10
    elif is_smart_working(location, desc, title):
        geo_score += 20
    elif has_valid_training(desc, title):
        # Formazione valida: diamo un buon punteggio geografico anche se lontana
        geo_score += 15
    elif is_sicily_other(location) or country == "Sicilia (altra)":
        # Altre città siciliane: punteggio basso, solo se con vitto/alloggio
        if has_vitto_alloggio(desc, title):
            geo_score += 10
        else:
            geo_score += 0
    elif country == "Italia":
        geo_score += 5
    
    if "trapani" in full_text or "marsala" in full_text or "erice" in full_text or "alcamo" in full_text:
        geo_score += 10
        
    return geo_score

def compute_level_score(full_text: str) -> int:
    level_score = 0
    if contains_any(full_text, MASTER_LEVEL_KEYWORDS):
        level_score += 20
    if re.search(r"\b(diploma|diplomato|ragioneria|afm|maturità)\b", full_text):
        level_score += 15
    if re.search(r"\b(0[-–]?[234]|1[-–]?[234])\s*(?:anni?|years?)\b", full_text) or contains_any(full_text, ["junior", "entry", "prima esperienza", "neodiplomato"]):
        level_score += 10
    if re.search(r"\b([23][-–]?[45])\s*(?:anni?|years?)\b|\b[234]\s*(?:anni?|years?)\b", full_text):
        level_score += 10
    return level_score

def compute_modality_score(location: str, desc: str, title: str) -> int:
    part_time_score = 0
    full_text = f"{location} {desc} {title}".lower()
    if contains_any(full_text, ["part-time", "part time", "tempo parziale", "mezza giornata", "20 ore", "25 ore", "30 ore"]):
        part_time_score += 10
    
    if is_smart_working(location, desc, title):
        part_time_score += 20
        
    return part_time_score

def evaluate_job(row: pd.Series, previous_fingerprints: set[str]) -> dict:
    title = normalize_text(row.get("title"))
    company = normalize_text(row.get("company"))
    location = normalize_text(row.get("location"))
    description = normalize_text(row.get("description"))
    country = infer_country_label(location, row.get("search_country", ""))
    full_text = f"{title} {company} {location} {description}".lower()
    fingerprint = normalize_text(row.get("job_fingerprint"))
    source_type = normalize_text(row.get("source_type") or row.get("site"))

    if fingerprint in previous_fingerprints:
        return {"excluded": True, "excluded_reason": "gia_presente_nello_storico"}

    if country in EXCLUDED_COUNTRIES:
        return {"excluded": True, "excluded_reason": "paese_escluso"}

    if country and country not in INCLUDED_COUNTRIES:
        return {"excluded": True, "excluded_reason": "paese_fuori_scope"}

    if not is_allowed_location(location, row.get("search_country", ""), description, title):
        return {"excluded": True, "excluded_reason": "localita_non_pertinente"}
    
    if is_wrong_region(location) and not is_smart_working(location, description, title) and not has_valid_training(description, title):
        return {"excluded": True, "excluded_reason": "localita_non_pertinente_wrong_region"}
        
    if has_strict_wrong_region_in_text(title, description) and not has_valid_training(description, title):
        return {"excluded": True, "excluded_reason": "sede_lavoro_esplicita_in_regione_errata"}

    if has_wrong_location_in_text(title, description, location):
        return {"excluded": True, "excluded_reason": "localita_testuale_non_pertinente"}
    
    job_url = row.get("job_url", "")
    url_location = get_location_from_url(job_url)
    if url_location and not is_allowed_location(url_location, row.get("search_country", "")):
        if not is_smart_working(location, description, title):
            return {"excluded": True, "excluded_reason": "url_non_pertinente"}
    
    if is_english_text(full_text):
        return {"excluded": True, "excluded_reason": "testo_in_inglese"}
    
    if contains_any(full_text, [
        "english required", "english mandatory", "fluent english required",
        "inglese richiesto", "inglese obbligatorio", "conoscenza inglese obbligatoria",
        "english speaking required", "must speak english", "english is a must",
        "must have english", "excellent english", "business english required"
    ]):
        return {"excluded": True, "excluded_reason": "inglese_richiesto"}

    reason = check_excluded_keywords(title, description)
    if reason:
        return {"excluded": True, "excluded_reason": reason}

    reason = check_degree_requirement(full_text)
    if reason:
        return {"excluded": True, "excluded_reason": reason}

    reason = check_seniority_requirement(full_text)
    if reason:
        return {"excluded": True, "excluded_reason": reason}

    reason = check_manual_role_blacklist(title)
    if reason:
        return {"excluded": True, "excluded_reason": reason}

    role_family = classify_role_family(full_text)
    company_tier = infer_company_tier(company, source_type, full_text)

    keyword_score_raw, hits = compute_keyword_score(full_text)

    english_ok, other_lang_required, local_plus = detect_language_fit(full_text)

    if other_lang_required:
        return {"excluded": True, "excluded_reason": "richiede_altra_lingua"}

    level_score = compute_level_score(full_text)
    part_time_score = compute_modality_score(location, description, title)
    geo_score = compute_geo_score(location, title, description, country)
    
    tech_bonus = 0
    if contains_any(full_text, ["wordpress", "ecommerce", "e-commerce", "woocommerce", "shopify", "gestione ordini"]):
        tech_bonus += 20

    office_score = 0
    if contains_any(full_text, [
        "amministrativo", "contabilità", "fatturazione", "segreteria", "ufficio",
        "commercialista", "ragioneria", "contabile", "bilancio", "partita doppia",
    ]):
        office_score += 20

    rule_score = keyword_score_raw + geo_score + level_score + office_score + part_time_score + tech_bonus
    final_score = min(100, rule_score)

    if final_score < settings.MINIMUM_RELEVANT_SCORE:
        return {"excluded": True, "excluded_reason": "sotto_soglia_pertinenza"}

    why_parts = []
    if part_time_score >= 40:
        why_parts.append("PART-TIME OK")
    if geo_score >= 30:
        why_parts.append("ZONA TRAPANI")
    if tech_bonus > 0:
        why_parts.append("WordPress/E-comm")
    if hits:
        why_parts.append(", ".join(hits[:2]))

    smart = is_smart_working(location, description, title)
    modality = "Smart Working" if smart else "In Sede"

    return {
        "excluded": False,
        "excluded_reason": "",
        "country": country or row.get("search_country", ""),
        "modality": modality,
        "role_family": role_family,
        "company_tier": company_tier,
        "english_ok": english_ok,
        "native_language_required": False,
        "local_language_plus": local_plus,
        "keyword_score": keyword_score_raw,
        "technical_score": keyword_score_raw,
        "level_score": level_score,
        "function_score": office_score,
        "company_score": 0,
        "language_score": 0,
        "geo_score": geo_score,
        "part_time_score": part_time_score,
        "source_score": 0,
        "rule_score": rule_score,
        "final_score": final_score,
        "match_grade": grade_from_score(final_score),
        "why_match": " | ".join(why_parts[:4]),
        "matched_keywords": ", ".join(hits),
        "apply_status": "new",
    }

def evaluate_job_second_chance(row: pd.Series, evaluation: dict) -> dict:
    source_type = normalize_text(row.get("source_type"))
    company = normalize_text(row.get("company")).lower()
    desc = normalize_text(row.get("description")).lower()
    
    # 1. Se proviene da canali diretti, rivalutiamo alcune esclusioni
    is_direct = source_type in ["subito", "concorso_pubblico", "company_site"]
    
    # 2. Se è uno studio di commercialista / consulenza
    is_studio = contains_any(company, ["commercialista", "studio", "consulenza", "elaborazione dati"]) or \
                contains_any(desc, ["studio commercialista", "centro elaborazione dati"])
                
    # 3. Keyword core super forti
    has_core_keywords = contains_any(desc, ["ragioneria", "partita doppia", "prima nota", "fatturazione elettronica"])

    # Applica seconda chance solo per esclusioni leggere (es. richiede laurea) se ci sono altri segnali forti
    if evaluation.get("excluded_reason") in ["probabilmente_richiede_laurea", "richiede_laurea", "sotto_soglia_pertinenza"]:
        if is_direct or is_studio or has_core_keywords:
            evaluation["excluded"] = False
            evaluation["excluded_reason"] = f"RECUPERATO: {evaluation['excluded_reason']} ma ha segnali positivi"
            # Assegna un punteggio base per farlo apparire
            if evaluation["final_score"] < settings.MEDIUM_MATCH_MIN:
                evaluation["final_score"] = settings.MEDIUM_MATCH_MIN
            evaluation["match_grade"] = grade_from_score(evaluation["final_score"])
    
    # Non recuperiamo mai su paese/regione sbagliati o ruoli non compatibili o lingua

    return evaluation

def filter_and_rank(df: pd.DataFrame, previous_fingerprints: set[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    if df.empty:
        return df, pd.DataFrame()

    evaluations = df.apply(lambda row: evaluate_job(row, previous_fingerprints), axis=1)
    eval_df = pd.DataFrame(evaluations.tolist())
    
    # Applica il recupero (second chance)
    for idx, row in df.iterrows():
        eval_row = eval_df.iloc[idx].to_dict()
        if eval_row.get("excluded", False):
            new_eval = evaluate_job_second_chance(row, eval_row)
            for k, v in new_eval.items():
                eval_df.at[idx, k] = v

    result_df = pd.concat([df.reset_index(drop=True), eval_df.reset_index(drop=True)], axis=1)
    result_df = result_df.loc[:, ~result_df.columns.duplicated()]

    excluded_df = result_df[result_df["excluded"] == True]
    relevant_df = result_df[result_df["excluded"] == False]

    if not relevant_df.empty:
        relevant_df = relevant_df.sort_values(
            by=["final_score", "date_posted"],
            ascending=[False, False]
        )

    return relevant_df, excluded_df
