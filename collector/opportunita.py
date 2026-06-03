from datetime import datetime
import pandas as pd

from collector.base import BaseCollector
from config import OPPORTUNITA_SITES

class OpportunitaCollector(BaseCollector):
    def __init__(self):
        super().__init__('Opportunita')

    def collect(self) -> pd.DataFrame:
        self.logger.info("=" * 60)
        self.logger.info("OPPORTUNITÀ GIOVANI 18-35 — Formazione gratuita, Inglese, Bandi, UE")
        self.logger.info("=" * 60)
        
        results = []
        
        for site in OPPORTUNITA_SITES:
            name = site["name"]
            tipo = site["tipo"]
            url = site["url"]
            descrizione = site.get("descrizione", "")
            
            tipo_label = {
                "formazione": "🎓 Formazione Gratuita Finanziata",
                "inglese": "🇬🇧 Inglese Gratuito / Finanziato",
                "bando": "💰 Bandi e Contributi per Giovani",
                "ue": "🌍 Opportunità Unione Europea",
                "tirocinio": "💼 Tirocini Retribuiti",
                "universita": "📚 Agevolazioni Studio Universitario",
            }.get(tipo, tipo)
            
            desc_lower = descrizione.lower()
            title_lower = name.lower()
            
            if "online" in desc_lower or "online" in title_lower or " app " in desc_lower or "sito" in desc_lower or "web" in desc_lower:
                modality = "Online / Smart"
            else:
                modality = "In Sede"

            if "sicilia" in desc_lower or "sicilia" in title_lower or "er su" in title_lower or "unipa" in title_lower:
                location = "Sicilia"
                if "trapani" in desc_lower or "trapani" in title_lower:
                    location = "Trapani"
                elif "palermo" in desc_lower or "palermo" in title_lower:
                    location = "Palermo"
            elif "ue" in tipo or "europe" in title_lower or "erasmus" in title_lower or "eu " in title_lower or "euro" in title_lower:
                location = "Europa"
            else:
                location = "Italia"
            
            results.append({
                "title": name,
                "company": tipo_label,
                "location": location,
                "search_country": location,
                "modality": modality,
                "job_url": url,
                "official_url": url,
                "description": descrizione,
                "site": url.replace("https://", "").replace("http://", "").split("/")[0],
                "source_type": "opportunita_giovani",
                "date_posted": datetime.now().strftime("%Y-%m-%d"),
                "opportunita_tipo": tipo,
                "opportunita_tipo_label": tipo_label,
            })
            
            self.logger.info(f"  ✅ {tipo_label}: {name} - {url}")
        
        if not results:
            self.logger.info("Nessuna opportunità configurata")
            return pd.DataFrame()
        
        df = pd.DataFrame(results)
        self.logger.info(f"\n✅ TOTALE OPPORTUNITÀ: {len(df)}")
        
        for tipo in df["opportunita_tipo_label"].unique():
            count = (df["opportunita_tipo_label"] == tipo).sum()
            self.logger.info(f"   {tipo}: {count}")
        
        self.logger.info("=" * 60)
        return df
