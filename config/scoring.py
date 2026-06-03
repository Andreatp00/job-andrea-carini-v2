"""
Sistema di scoring e keyword per la rilevanza degli annunci.

Contiene le liste di parole chiave per:
- Rilevanza aziendale
- Esclusione titoli e testi
- Punteggi profilo
- Livello master (diploma)
- Famiglie di ruoli
- Indicatori aziende preferite e startup
"""

# ============================================================
# KEYWORD PER RELEVANZA (per descrizioni annunci)
# ============================================================
COMPANY_RELEVANCE_KEYWORDS: list[str] = [
    "amministrativo", "contabilità", "fatturazione", "segreteria", "ufficio",
    "back office", "ragioneria", "commercialista", "gestionali", "e-commerce",
    "wordpress", "amministrazione", "contabile", "bilancio", "partita doppia",
    "iva", "dichiarazione", "cassa", "fatture", "ordini", "acquisti",
    "customer service", "servizio clienti", "praticante", "stage",
    "categoria c", "categoria d", "diplomati", "istruttore amministrativo",
    "funzionario amministrativo", "concorso pubblico", "impiegato",
    "addetto", "assistente", "operatore", "part-time", "tempo parziale",
    "remoto", "smart working", "lavoro da casa", "da remoto", "telelavoro",
    "flessibile", "mezza giornata", "mattina", "pomeriggio", "full remote", "100% remote", "lavoro agile",
    "call center", "data entry", "inserimento dati", "help desk", "assistenza clienti",
    "tirocinio", "tirocinio formativo", "apprendistato", "junior", "senza esperienza", "inbound", "outbound",
]

EXCLUDE_KEYWORDS_TITLE: list[str] = [
    "laurea", "laureato", "ingegnere", "architetto", "medico", "infermiere",
    "dirigente", "direttore", "capo", "responsabile", "senior", "vice presidente",
    "magazziniere", "operaio", "cameriere", "barista", "cuoco", "pizzaiolo",
    "commesso", "venditore", "promoter", "agente di commercio",
    "programmatore", "sviluppatore", "informatico", "tecnico informatico",
    "elettricista", "idraulico", "manutenzione", "autista", "fattorino",
    "corriere", "magazzino", "logistica", "carrellista", "montatore",
    "meccanico", "pulizie", "oss", "badante", "cantiere", "muratore",
]

EXCLUDE_KEYWORDS_TEXT: list[str] = [
    "laurea richiesta", "laurea in", "laurea magistrale", "laurea triennale",
    "titolo di studio superiore al diploma",
    "esperienza di almeno 10 anni",
    "turni notturni", "lavoro notturno", "notturno",
    "si richiede patente c", "patente c", "carta di qualificazione",
]

# ============================================================
# SISTEMA DI SCORING
# ============================================================

# Parole chiave del profilo per punteggio
PROFILE_KEYWORDS_SCORES: list[tuple[str, int]] = [
    # 15 punti — competenze chiave
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
    ("magazzino", 15),
    ("ordini", 15),
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
    ("commercialista", 15),
    ("categoria c", 15),
    ("categoria d", 15),
    ("concorso pubblico", 15),
    ("istruttore amministrativo", 15),
    ("diplomati", 15),

    # 8 punti — competenze di contorno
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

    # 5 punti — competenze di base
    ("addetto", 5),
    ("impiegato", 5),
    ("assistente", 5),
    ("operatore", 5),
    ("sportello", 5),
    ("front office", 5),
    ("classificazione", 5),
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
        "back office", "segreteria", "segreterio", "archiviazione",
        "protocollo", "gestione documentale", "customer service",
        "servizio clienti", "assistente amministrativo",
    ],
    "ecommerce_acquisti": [
        "e-commerce", "wordpress", "ordini", "acquisti", "logistica",
        "fornitori", "magazzino ufficio",
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
]

STARTUP_KEYWORDS: list[str] = [
    "startup", "start-up", "scale-up",
]
