"""
Scraper per Subito.it — Annunci di lavoro Trapani e provincia
Subito è molto usato a Trapani per annunci di lavoro locali.
"""

import logging
import re
import time
from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger("JobHunter.Subito")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Referer": "https://www.subito.it/",
    "Connection": "keep-alive",
}

# Sessione globale per mantenere i cookie
session = requests.Session()

# Query di ricerca su Subito.it per Trapani e Provincia
SUBITO_SEARCHES = [
    # Back office / Amministrativo
    {"query": "back office", "location": "trapani"},
    {"query": "impiegato amministrativo", "location": "trapani"},
    {"query": "contabilità", "location": "trapani"},
    {"query": "fatturazione", "location": "trapani"},
    {"query": "segreteria", "location": "trapani"},
    {"query": "commercialista", "location": "trapani"},
    {"query": "ragioneria", "location": "trapani"},
    {"query": "praticante", "location": "trapani"},
    {"query": "amministrazione", "location": "trapani"},
    
    # Provincia Trapani
    {"query": "back office", "location": "marsala"},
    {"query": "amministrativo", "location": "marsala"},
    {"query": "contabilità", "location": "mazara"},
    {"query": "ufficio", "location": "alcamo"},
    {"query": "amministrativo", "location": "castelvetrano"},
    
    # Part-time
    {"query": "part time ufficio", "location": "trapani"},
    {"query": "part time amministrazione", "location": "trapani"},
    {"query": "tempo parziale ufficio", "location": "trapani"},
    
    # Smart working / Remoto
    {"query": "smart working amministrativo", "location": "italia"},
    {"query": "lavoro da casa contabilità", "location": "italia"},
    {"query": "remoto back office", "location": "italia"},
    {"query": "telelavoro amministrazione", "location": "italia"},
]


def _build_subito_url(query: str, location: str) -> str:
    """
    Costruisce URL di ricerca Subito.it
    """
    q = query.lower().replace(" ", "-")
    
    if location == "trapani":
        return f"https://www.subito.it/annunci-sicilia/vendita/?q={q}&region=Trapani"
    elif location == "marsala":
        return f"https://www.subito.it/annunci-sicilia/vendita/?q={q}&region=Trapani&city=Marsala"
    elif location == "mazara":
        return f"https://www.subito.it/annunci-sicilia/vendita/?q={q}&region=Trapani&city=Mazara-del-vallo"
    elif location == "alcamo":
        return f"https://www.subito.it/annunci-sicilia/vendita/?q={q}&region=Trapani&city=Alcamo"
    elif location == "castelvetrano":
        return f"https://www.subito.it/annunci-sicilia/vendita/?q={q}&region=Trapani&city=Castelvetrano"
    elif location == "italia":
        return f"https://www.subito.it/annunci-italia/vendita/?q={q}"
    else:
        return f"https://www.subito.it/annunci-italia/vendita/?q={q}&region=Trapani"


def _parse_subito_items(html: str, query: str, location: str) -> list[dict]:
    """Parsa la pagina HTML di Subito e restituisce una lista di annunci."""
    results = []
    soup = BeautifulSoup(html, "html.parser")
    
    # Subito.it usa varie classi per gli annunci. Cerchiamo i più comuni.
    items = soup.select("article, div.items__item, a.item__link, [class*='card'], [class*='item-card']")
    
    # Se non trova con selettori generici, prova con link
    if not items:
        # Cerca i link agli annunci
        for link in soup.find_all("a", href=re.compile(r"/annunci-.*/vendita/")):
            title_tag = link.find("h2") or link.find("h3") or link.find("p", class_=re.compile(r"title"))
            price_tag = link.find("p", class_=re.compile(r"price")) or link.find("span", class_=re.compile(r"price"))
            location_tag = link.find("p", class_=re.compile(r"location")) or link.find("span", class_=re.compile(r"location"))
            
            title = title_tag.get_text(strip=True) if title_tag else ""
            price = price_tag.get_text(strip=True) if price_tag else ""
            loc_text = location_tag.get_text(strip=True) if location_tag else location
            
            href = link.get("href", "")
            if href and not href.startswith("http"):
                href = f"https://www.subito.it{href}" if href.startswith("/") else href
            
            if title and len(title) > 5:
                results.append({
                    "title": title,
                    "company": "Subito.it",
                    "location": loc_text,
                    "search_country": "Trapani" if location != "italia" else "Italia",
                    "job_url": href,
                    "official_url": href,
                    "description": f"Subito.it | query: {query} | {price}",
                    "site": "subito.it",
                    "source_type": "subito",
                    "date_posted": datetime.now().strftime("%Y-%m-%d"),
                })
    
    return results


def scrape_subito() -> pd.DataFrame:
    """
    Scraping principale di Subito.it per Trapani e provincia.
    """
    logger.info("=== SCRAPING SUBITO.IT (Trapani e provincia) ===")
    all_results = []
    
    for search in SUBITO_SEARCHES:
        query = search["query"]
        location = search["location"]
        url = _build_subito_url(query, location)
        
        logger.info(f"Subito: '{query}' in {location}")
        
        try:
            response = session.get(url, headers=HEADERS, timeout=20)
            if response.status_code == 200:
                items = _parse_subito_items(response.text, query, location)
                for item in items:
                    # Controllo base: escludere se contiene keyword di altri settori
                    title_lower = item["title"].lower()
                    exclude_patterns = [
                        "auto", "moto", "telefono", "cellulare", "tablet",
                        "casa", "appartamento", "affitto", "vendita casa",
                        "abbigliamento", "scarpe", "borsa",
                        "console", "playstation", "xbox",
                    ]
                    if any(p in title_lower for p in exclude_patterns):
                        continue
                    
                    all_results.append(item)
                
                logger.info(f"  -> {len(items)} annunci trovati")
            else:
                logger.warning(f"  -> HTTP {response.status_code}")
                
        except Exception as exc:
            logger.warning(f"  -> Errore Subito: {exc}")
        
        time.sleep(2)  ## Delay per non essere bloccati
    
    if not all_results:
        logger.info("Nessun annuncio trovato su Subito.it")
        return pd.DataFrame()
    
    df = pd.DataFrame(all_results)
    df = df.drop_duplicates(subset=["title", "location", "job_url"])
    logger.info(f"Subito.it: totale {len(df)} annunci unici")
    return df