"""
Sistema di scoring e keyword per la rilevanza degli annunci.

AGGIORNATO per riflettere il CV completo di Andrea Carini:
- Sviluppo aziendale, brand design, e-commerce
- Contabilità, logistica, gestione ordini
- Call center, data entry, assistenza clienti (smart working)
- Concorsi pubblici e bandi giovani
"""

# ============================================================
# KEYWORD PER RELEVANZA (per descrizioni annunci)
# ============================================================
COMPANY_RELEVANCE_KEYWORDS: list[str] = [
    # Amministrazione e contabilità
    "amministrativo", "contabilità", "fatturazione", "segreteria", "ufficio",
    "back office", "ragioneria", "commercialista", "gestionali", "contabile",
    "bilancio", "partita doppia", "iva", "dichiarazione", "fatture",
    "amministrazione", "cassa", "prima nota",
    # E-commerce e web
    "e-commerce", "ecommerce", "wordpress", "shopify", "woocommerce",
    "seo", "social media", "marketing digitale", "web marketing",
    "gestione ordini", "shop online", "content creator", "copywriter",
    # Logistica e ordini
    "ordini", "acquisti", "logistica", "gestione magazzino", "spedizioni",
    "inventario", "fornitori",
    # Customer service e call center
    "customer service", "servizio clienti", "assistenza clienti",
    "call center", "inbound", "outbound", "operatore telefonico",
    "help desk", "supporto clienti", "supporto tecnico",
    # Data entry
    "data entry", "inserimento dati",
    # Assistente e booking
    "assistente virtuale", "virtual assistant", "booking", "prenotazioni",
    "moderatore",
    # Concorsi
    "praticante", "stage", "tirocinio", "apprendistato",
    "categoria c", "categoria d", "diplomati", "istruttore amministrativo",
    "funzionario amministrativo", "concorso pubblico", "concorso",
    # Generico
    "impiegato", "addetto", "assistente", "operatore",
    "part-time", "tempo parziale", "remoto", "smart working",
    "lavoro da casa", "da remoto", "telelavoro", "full remote",
    "100% remote", "lavoro agile",
    # Design e brand
    "graphic design", "brand", "illustrator", "canva", "photoshop",
    "identità visiva",
]

# ============================================================
# KEYWORD DI ESCLUSIONE — SOLO ruoli veramente incompatibili
# ============================================================
EXCLUDE_KEYWORDS_TITLE: list[str] = [
    # Laurea specifica richiesta nel TITOLO
    "ingegnere", "architetto", "medico", "infermiere", "avvocato",
    "biologo", "chimico", "farmacista", "psicologo", "fisioterapista",
    # Troppo senior
    "dirigente", "direttore", "vice presidente", "cfo", "cto", "ceo",
    # Lavori manuali/fisici incompatibili
    "operaio", "cameriere", "barista", "cuoco", "pizzaiolo",
    "elettricista", "idraulico", "manutenzione", "fattorino",
    "corriere", "carrellista", "montatore",
    "meccanico", "pulizie", "oss", "badante", "cantiere", "muratore",
    # IT puro (programmazione vera)
    "programmatore", "sviluppatore", "developer", "devops",
    "tecnico informatico", "system administrator",
]

# NOTA: Rimossi da esclusione rispetto a prima:
# - "logistica" → Andrea ha esperienza in logistica e gestione ordini
# - "magazzino" → Andrea ha esperienza in gestione magazzino
# - "commesso" → Andrea ha esperienza vendita B2B/B2C
# - "venditore" → Andrea ha esperienza vendita
# - "promoter" → potrebbe essere smart working
# - "agente di commercio" → potrebbe essere interessante
# - "responsabile" → troppo generico, ci sono "responsabile back office" che vanno bene
# - "capo" → troppo generico
# - "senior" → troppo generico, ci sono junior/senior call center

EXCLUDE_KEYWORDS_TEXT: list[str] = [
    "laurea richiesta", "laurea in", "laurea magistrale", "laurea triennale",
    "titolo di studio superiore al diploma",
    "esperienza di almeno 10 anni",
    "turni notturni", "lavoro notturno",
    "si richiede patente c", "patente c", "carta di qualificazione",
]

# ============================================================
# SISTEMA DI SCORING
# ============================================================
PROFILE_KEYWORDS_SCORES: list[tuple[str, int]] = [
    # 15 punti — competenze CORE del CV
    ("back office", 15),
    ("contabilità", 15),
    ("prima nota", 15),
    ("fatturazione", 15),
    ("sap business one", 15),
    ("sap", 15),
    ("teamsystem", 15),
    ("zucchetti", 15),
    ("erp", 15),
    ("wms", 15),
    ("crm", 15),
    ("logistica", 15),
    ("gestione ordini", 15),
    ("spedizioni", 15),
    ("gestionali", 15),
    ("partita doppia", 15),
    ("bilancio", 15),
    ("iva", 15),
    ("segreteria", 15),
    ("wordpress", 15),
    ("shopify", 15),
    ("woocommerce", 15),
    ("e-commerce", 15),
    ("ecommerce", 15),
    ("commercialista", 15),
    ("categoria c", 15),
    ("categoria d", 15),
    ("concorso pubblico", 15),
    ("istruttore amministrativo", 15),
    ("diplomati", 15),
    # Nuove competenze dal CV
    ("brand design", 15),
    ("illustrator", 15),
    ("social media", 15),
    ("web marketing", 15),
    ("seo", 15),
    ("gestione fornitori", 15),
    ("b2b", 15),
    ("b2c", 15),
    
    # 8 punti — competenze secondarie
    ("ragioneria", 8),
    ("amministrazione", 8),
    ("amministrativo", 8),
    ("praticante", 8),
    ("stage ufficio", 8),
    ("ordini", 8),
    ("acquisti", 8),
    ("gestionale aziendale", 8),
    ("pacchetto office", 8),
    ("excel", 8),
    ("word", 8),
    ("rendicontazione", 8),
    ("dichiarazione dei redditi", 8),
    # Call center e customer service
    ("call center", 8),
    ("customer service", 8),
    ("assistenza clienti", 8),
    ("servizio clienti", 8),
    ("help desk", 8),
    ("supporto clienti", 8),
    ("operatore telefonico", 8),
    ("inbound", 8),
    ("outbound", 8),
    # Data entry
    ("data entry", 8),
    ("inserimento dati", 8),
    # Design
    ("canva", 8),
    ("photoshop", 8),
    ("graphic design", 8),
    # E-commerce operations
    ("shop online", 8),
    ("gestione magazzino", 8),
    ("inventario", 8),
    
    # 5 punti — competenze di base
    ("addetto", 5),
    ("impiegato", 5),
    ("assistente", 5),
    ("operatore", 5),
    ("sportello", 5),
    ("front office", 5),
    ("archiviazione", 5),
    ("protocollo", 5),
    ("pec", 5),
    ("pubblica amministrazione", 5),
    ("enti locali", 5),
    ("comune", 5),
    ("provincia", 5),
    ("regione", 5),
    ("concorso", 5),
    ("graduatoria", 5),
    ("tempo indeterminato", 5),
    ("assistente virtuale", 5),
    ("virtual assistant", 5),
    ("booking", 5),
    ("prenotazioni", 5),
    ("moderatore", 5),
    ("content creator", 5),
    ("copywriter", 5),
    ("tirocinio", 5),
    ("stage", 5),
    ("apprendistato", 5),
]

# Livello master = diploma adatto
MASTER_LEVEL_KEYWORDS: list[str] = [
    "diploma", "diplomato", "ragioneria", "istituto tecnico",
    "scuola superiore", "diploma superiore", "istruzione secondaria",
    "qualifica professionale", "perito commerciale", "afm",
    "amministrazione finanza marketing", "maturità",
    "entry level", "junior", "prima esperienza", "neodiplomato",
    "senza laurea", "non richiede laurea", "basti il diploma",
    "0-2 anni", "0-3 anni", "0-1 anni", "1-2 anni",
    "part-time", "tempo parziale", "mezza giornata",
]

ROLE_FAMILY_KEYWORDS: dict[str, list[str]] = {
    "amministrazione_contabilita": [
        "contabilità", "bilancio", "partita doppia", "iva", "fattura",
        "commercialista", "ragioneria", "dichiarazione dei redditi",
        "amministrazione", "contabile",
    ],
    "back_office_segreteria": [
        "back office", "segreteria", "archiviazione",
        "protocollo", "gestione documentale",
        "assistente amministrativo",
    ],
    "customer_service_call_center": [
        "call center", "customer service", "servizio clienti",
        "assistenza clienti", "help desk", "supporto clienti",
        "operatore telefonico", "inbound", "outbound",
    ],
    "data_entry": [
        "data entry", "inserimento dati", "trascrizione",
    ],
    "ecommerce_web_social": [
        "e-commerce", "ecommerce", "wordpress", "shopify", "woocommerce",
        "ordini", "acquisti", "logistica", "fornitori",
        "social media", "seo", "web marketing", "content creator",
        "brand design", "graphic design",
    ],
    "concorsi_pubblici": [
        "concorso pubblico", "categoria c", "categoria d", "istruttore",
        "funzionario", "pubblica amministrazione", "comune", "provincia",
        "asl", "inps", "agenzia entrate",
    ],
}

# ============================================================
# AZIENDE PREFERITE
# ============================================================
PREFERRED_COMPANY_INDICATORS: list[str] = [
    "commercialista", "studio", "revisione", "bilancio", "contabilità",
    "back office", "segreteria", "amministrazione", "tributario",
    "agenzia entrate", "inps", "comune", "provincia", "regione",
    "asl", "azienda sanitaria", "ente pubblico", "amministrazione pubblica",
    # Agenzie interinali (cercano sempre smart working)
    "adecco", "manpower", "randstad", "gi group", "openjobmetis",
    "synergie", "etjca", "humangest", "lavorint", "umana",
]

STARTUP_KEYWORDS: list[str] = [
    "startup", "start-up", "scale-up",
]
