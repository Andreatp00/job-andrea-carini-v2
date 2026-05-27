import os

# ============================================================
# CONFIGURAZIONE BOT RICERCA LAVORO — Back Office / Ragioneria
# Profilo: Diplomato Ragioneria AFM, 25 anni, Trapani
# ============================================================

# --- Telegram (INSERISCI I TUOI QUI) ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# --- Email ---
EMAIL_RECIPIENT = os.environ.get("EMAIL_RECIPIENT", "")
EMAIL_SENDER = os.environ.get("EMAIL_SENDER", "")
EMAIL_APP_PASSWORD = os.environ.get("EMAIL_APP_PASSWORD", "")
EMAIL_SMTP_SERVER = "smtp.gmail.com"
EMAIL_SMTP_PORT = 587

# --- AI (opzionale) ---
MISTRAL_API_KEY = os.environ.get("OPENAI_API_KEY", "")
MISTRAL_MODEL = os.environ.get("MISTRAL_MODEL", "open-mixtral-8x7b")

# ============================================================
# PROFILO CANDIDATO
# ============================================================
PROFILE = {
    "name": "",
    "headline": "Diplomato Ragioneria AFM | 4 anni esperienza (Vendite, Back Office, WordPress) | 25 anni | Trapani",
    "degree": "Diploma Ragioneria - Indirizzo AFM (Amministrazione, Finanza, Marketing)",
    "university_status": "Studente Universitario (Cerca Part-Time)",
    "age": 25,
    "location": "Trapani, Sicilia",
    "mobility": ["Trapani e provincia", "Sicilia", "Smart Working / Remoto Italia"],
    "languages": ["Italiano madrelingua", "Inglese (in apprendimento)"],
    "experience_years": 4,
    "experience_roles": [
        "Addetto vendite e assistenza clienti",
        "Gestione cassa, fatturazione, resi, chiusura/apertura",
        "Gestione e-commerce WordPress (WooCommerce)",
        "Sviluppo aziendale e back office amministrativo",
    ],
    "soft_skills": [
        "Gestionali aziendali",
        "Fatturazione elettronica",
        "Contabilità di base",
        "WordPress / E-commerce",
        "Pacchetto Office (Excel, Word)",
        "Precisione e gestione cassa",
        "Affiancamento e apprendimento rapido",
    ],
    "target_roles": [
        "Addetto/a back office part-time",
        "Impiegato/a amministrativo/a part-time",
        "Addetto/a contabilità part-time",
        "Segretario/a amministrativo/a",
        "Addetto/a fatturazione",
        "Praticante studio commercialista",
        "Addetto/a e-commerce e amministrazione",
        "Customer service back office",
        "Istruttore amministrativo (Concorsi C)",
        "Addetto/a gestione documentale",
    ],
}

# ============================================================
# TERMINI DI RICERCA — Portali (LinkedIn, Indeed, Subito)
# ============================================================
SEARCH_TERMS = [
    # Back office / Amministrativo / Ragioneria - Trapani e Provincia
    "\"back office\" Trapani part-time",
    "\"back office\" Marsala part-time",
    "\"impiegato amministrativo\" Trapani part-time",
    "\"addetto contabilità\" Trapani diploma",
    "\"fatturazione\" Trapani part-time",
    "\"segreteria\" Trapani part-time",
    "\"ragioneria\" Trapani diploma",
    "\"praticante\" studio commercialista Trapani",
    "\"ufficio\" Trapani part-time",
    "\"amministrativo\" Alcamo part-time",
    "\"back office\" Mazara del Vallo",
    
    # WordPress / E-commerce (Data Entry / Admin)
    "\"wordpress\" back office Italia remoto",
    "\"ecommerce\" amministrativo remoto",
    "\"data entry\" Trapani",
    "\"gestione ordini\" wordpress remoto",
    
    # Smart working / Remoto Italia (Part-time / Diploma)
    "\"smart working\" amministrativo part-time",
    "\"remoto\" back office diploma",
    "\"lavoro da casa\" contabilità part-time",
    "\"telelavoro\" amministrazione Italia",
    "\"customer service\" remoto part-time",
    "\"assistente virtuale\" amministrativo",
    
    # Keyword generiche per smart working "basta che paghino"
    "\"smart working\" senza esperienza diploma",
    "\"remoto\" part-time diplomato",
]

GOOGLE_SEARCH_TERMS = [
    "\"lavoro\" back office Trapani Marsala \"part-time\" diploma",
    "\"offerta lavoro\" ragioneria AFM Trapani provincia senza laurea",
    "\"smart working\" impiegato amministrativo part-time Italia",
    "\"stage\" ufficio Trapani diploma",
    "concorsi pubblici Trapani categoria C diplomati",
    "\"lavoro da casa\" gestione ordini wordpress",
]

# ============================================================
# RICERCHE GEOGRAFICHE — Solo Italia con focus Trapani
# ============================================================
COUNTRY_SEARCHES = [
    {"country_indeed": "Italy", "location": "Trapani", "label": "Trapani"},
    {"country_indeed": "Italy", "location": "Sicily", "label": "Sicilia"},
    {"country_indeed": "Italy", "location": "Italy", "label": "Italia (Smart Working)"},
]

INCLUDED_COUNTRIES = {"Italia", "Trapani", "Sicilia"}
EXCLUDED_COUNTRIES = set()

# ============================================================
# SITI AZIENDALI — Trapani, agenzie interinali, smart working
# ============================================================
COMPANY_CAREER_SITES = [
    # --- Studi Commercialisti e Professionisti Trapani ---
    {"company": "Studio Commercialista Trapani", "country": "Trapani", "url": "https://www.commercialistitrapani.it/", "search_params": {"keywords": "collaboratore ragioneria"}, "label": "Commercialisti TP"},
    {"company": "Ordine Commercialisti Trapani", "country": "Trapani", "url": "https://www.odcectrapani.it/", "search_params": {"keywords": "lavoro praticante"}, "label": "ODCEC Trapani"},

    # --- Agenzie per il Lavoro (sede Trapani o che cercano in Sicilia) ---
    {"company": "Adecco", "country": "Trapani", "url": "https://www.adecco.it/ricerca-lavoro/trapani/", "search_params": {"keywords": "impiegato amministrativo part-time back office"}, "label": "Adecco Trapani"},
    {"company": "Manpower", "country": "Trapani", "url": "https://www.manpower.it/cerca-lavoro/trapani/", "search_params": {"keywords": "amministrativo contabilità ufficio"}, "label": "Manpower Trapani"},
    {"company": "Randstad", "country": "Trapani", "url": "https://www.randstad.it/trovare-lavoro/trapani/", "search_params": {"keywords": "impiegato amministrazione back office"}, "label": "Randstad Trapani"},
    {"company": "Gi Group", "country": "Trapani", "url": "https://www.gigroup.it/offerte-lavoro/trapani/", "search_params": {"keywords": "amministrativo contabilità segreteria"}, "label": "Gi Group Trapani"},
    {"company": "Openjobmetis", "country": "Trapani", "url": "https://www.openjobmetis.it/offerte-lavoro/trapani/", "search_params": {"keywords": "ufficio amministrazione contabilità"}, "label": "Openjobmetis TP"},
    {"company": "Synergie Italia", "country": "Trapani", "url": "https://www.synergie-italia.it/offerte-di-lavoro/trapani/", "search_params": {"keywords": "impiegato amministrativo"}, "label": "Synergie TP"},
    {"company": "Etjca", "country": "Trapani", "url": "https://www.etjca.it/offerte-lavoro/trapani/", "search_params": {"keywords": "amministrativo contabilità"}, "label": "Etjca TP"},
    {"company": "Humangest", "country": "Trapani", "url": "https://www.humangest.it/cerca-lavoro/trapani/", "search_params": {"keywords": "amministrativo back office"}, "label": "Humangest TP"},

    # --- Smart Working / Remoto Italia ---
    {"company": "Adecco Remote", "country": "Italia", "url": "https://www.adecco.it/ricerca-lavoro/smart-working/", "search_params": {"keywords": "back office amministrativo contabilità remoto"}, "label": "Adecco Smart Working"},
    {"company": "Randstad Remote", "country": "Italia", "url": "https://www.randstad.it/trovare-lavoro/smart-working/", "search_params": {"keywords": "amministrativo contabilità"}, "label": "Randstad Smart Working"},
    {"company": "Jobtech", "country": "Italia", "url": "https://www.jobtech.it/offerte/remote/", "search_params": {"keywords": "amministrativo back office"}, "label": "Jobtech Remote"},

    # --- Siti generali remoti Italia ---
    {"company": "Remote.co", "country": "Italia", "url": "https://remote.co/remote-jobs/", "search_params": {"keywords": "administrative assistant data entry customer service"}, "label": "Remote.co"},
    {"company": "Working Nomads", "country": "Italia", "url": "https://www.workingnomads.com/jobs?category=admin-support", "search_params": {"keywords": "remote administrative assistant"}, "label": "Working Nomads"},
    {"company": "We Work Remotely", "country": "Italia", "url": "https://weworkremotely.com/categories/remote-admin-jobs", "search_params": {"keywords": "remote admin assistant"}, "label": "We Work Remotely"},
    {"company": "FlexJobs", "country": "Italia", "url": "https://www.flexjobs.com/remote-jobs/entry-level/", "search_params": {"keywords": "administrative data entry customer service"}, "label": "FlexJobs"},

    # --- Enti locali Trapani ---
    {"company": "Comune di Trapani", "country": "Trapani", "url": "https://www.comune.trapani.it/", "search_params": {"keywords": "concorso assunzione diplomati"}, "label": "Comune Trapani"},
    {"company": "Provincia Trapani", "country": "Trapani", "url": "https://www.provincia.trapani.it/", "search_params": {"keywords": "concorso categoria C diplomati"}, "label": "Provincia Trapani"},
    {"company": "Libero Consorzio Trapani", "country": "Trapani", "url": "https://www.liberoconsorziotrapani.it/", "search_params": {"keywords": "concorso pubblica amministrazione"}, "label": "Libero Consorzio TP"},
]

# ============================================================
# OPPORTUNITÀ PER GIOVANI 18-35 — Formazione gratuita, corsi, bandi
# ============================================================
OPPORTUNITA_SITES = [
    # Formazione gratuita finanziata
    {"name": "Garanzia Giovani Sicilia", "url": "https://www.garanziagiovani.gov.it/Pagine/default.aspx", "tipo": "formazione", "descrizione": "Programma europeo per giovani NEET 16-29: corsi gratuiti, tirocini, bonus"},
    {"name": "Garanzia Occupabilità Lavoratori (GOL)", "url": "https://www.anpal.gov.it/garanzia-di-occupabilita-dei-lavoratori-gol", "tipo": "formazione", "descrizione": "Programma di formazione professionale gratuito finanziato dal PNRR"},
    {"name": "Fondimpresa - Formazione Finanziata", "url": "https://www.fondimpresa.it/", "tipo": "formazione", "descrizione": "Formazione gratuita finanziata dai fondi interprofessionali per lavoratori"},
    {"name": "Fondazione ITS Sicilia", "url": "https://www.its-sicilia.it/", "tipo": "formazione", "descrizione": "Corsi ITS post-diploma gratuiti con borse di studio (durata 2 anni)"},
    {"name": "Scuola Superiore Sant'Anna - Corsi gratuiti", "url": "https://www.santannapisa.it/it/formazione/corsi", "tipo": "formazione", "descrizione": "Corsi di alta formazione gratuiti per diplomati"},
    
    # Inglese gratis / finanziato
    {"name": "British Council - Learn English Free", "url": "https://learnenglish.britishcouncil.org/", "tipo": "inglese", "descrizione": "Corsi di inglese gratuiti online con esercizi e podcast"},
    {"name": "BBC Learning English", "url": "https://www.bbc.co.uk/learningenglish/", "tipo": "inglese", "descrizione": "Corsi di inglese gratuiti della BBC (tutti i livelli)"},
    {"name": "Duolingo", "url": "https://www.duolingo.com/course/en/it/Impara-l-inglese", "tipo": "inglese", "descrizione": "App gratuita per imparare l'inglese (100% gratis, no pubblicità)"},
    {"name": "Open English - Corsi finanziati", "url": "https://www.openenglish.com/it/", "tipo": "inglese", "descrizione": "Corsi di inglese finanziati da fondi interprofessionali e regionali"},
    {"name": "Corso Inglese Gratuito - Regione Sicilia", "url": "https://www.regione.sicilia.it/istruzione-formazione/", "tipo": "inglese", "descrizione": "Corsi di lingua inglese finanziati dalla Regione Sicilia per giovani"},
    
    # Bandi e contributi per giovani
    {"name": "Borse di Studio Regione Sicilia", "url": "https://www.regione.sicilia.it/istruzione-formazione/diritto-allo-studio", "tipo": "bando", "descrizione": "Borse di studio regionali per studenti universitari siciliani"},
    {"name": "Bonus Giovani 2024", "url": "https://www.inps.it/it/it/dettaglio-news-page.news.2023.12.bonus-assunzioni-giovani-under-35.html", "tipo": "bando", "descrizione": "Bonus assunzioni under 35 - sgravi contributivi per aziende che assumono giovani"},
    {"name": "Sostegno per l'affitto giovani", "url": "https://www.regione.sicilia.it/istruzione-formazione/diritto-allo-studio", "tipo": "bando", "descrizione": "Contributo affitto per studenti universitari fuori sede"},
    {"name": "Nuova Garanzia Giovani 2024", "url": "https://www.garanziagiovani.gov.it/", "tipo": "bando", "descrizione": "Misure di politica attiva per giovani 16-29: formazione, tirocini, incentivi"},
    
    # Opportunità finanziate da privati / UE
    {"name": "Erasmus+ Giovani", "url": "https://www.erasmusplus.it/", "tipo": "ue", "descrizione": "Scambi giovanili e volontariato europeo finanziati dall'UE (18-30 anni)"},
    {"name": "Corpo Europeo di Solidarietà", "url": "https://europeansolidaritycorps.europa.eu/it", "tipo": "ue", "descrizione": "Volontariato retribuito all'estero per giovani 18-30, spese coperte dall'UE"},
    {"name": "DiscoverEU", "url": "https://europa.eu/youth/discovereu_it", "tipo": "ue", "descrizione": "Pass Interrail gratuito per viaggiare in Europa a 18 anni"},
    {"name": "Eurodesk Italy", "url": "https://www.eurodesk.it/", "tipo": "ue", "descrizione": "Portale ufficiale UE per l'orientamento sui programmi europei per i giovani (scambi, volontariato, lavoro)"},
    {"name": "Salto-Youth", "url": "https://www.salto-youth.net/", "tipo": "ue", "descrizione": "Bandi per scambi giovanili e formazione non formale finanziati dall'UE (spese coperte)"},
    {"name": "EURES - Lavoro in Europa", "url": "https://ec.europa.eu/eures/", "tipo": "ue", "descrizione": "Offerte di lavoro, tirocinio e apprendistato in tutta Europa per giovani"},
    {"name": "Fondo per il Finanziamento Startup Giovanili", "url": "https://www.mimit.gov.it/it/incentivi/incentivi-per-le-startup", "tipo": "ue", "descrizione": "Contributi a fondo perduto per avviare un'attività under 35"},
    
    # Tirocini e formazione Palermo (se ne vale la pena)
    {"name": "Centro per l'Impiego Palermo", "url": "https://www.regione.sicilia.it/istituzioni/regione/strutture-regionali/assessorato-famiglia-politiche-sociali-lavoro/dipartimento-lavoro/centri-impiego/palermo", "tipo": "tirocinio", "descrizione": "Offerte di lavoro e tirocini amministrativi in provincia di Palermo"},
    {"name": "Formazione Palermo - Corsi Gratuiti", "url": "https://www.comune.palermo.it/", "tipo": "formazione", "descrizione": "Bandi per corsi di formazione professionale gratuiti nel comune di Palermo"},
    
    # Tirocini retribuiti
    {"name": "Tirocini Retribuiti Regione Sicilia", "url": "https://www.regione.sicilia.it/lavoro/tirocini", "tipo": "tirocinio", "descrizione": "Tirocini formativi retribuiti finanziati dalla Regione Sicilia per giovani"},
    {"name": "Stage in PA - Portale tirocini", "url": "https://tirocini.formez.it/", "tipo": "tirocinio", "descrizione": "Tirocini curriculari e extracurriculari nella Pubblica Amministrazione"},
    {"name": "Garanzia Giovani - Tirocini", "url": "https://www.garanziagiovani.gov.it/tirocini/", "tipo": "tirocinio", "descrizione": "Tirocini retribuiti per giovani 16-29 (indennità + contributi)"},
    
    # Agevolazioni studio universitario
    {"name": "ERSU Sicilia", "url": "https://www.ersu.it/", "tipo": "universita", "descrizione": "Borse di studio, alloggi e mense per studenti universitari in Sicilia"},
    {"name": "UNIPA - Opportunità studenti", "url": "https://www.unipa.it/studenti/borse-di-studio-e-agevolazioni/", "tipo": "universita", "descrizione": "Agevolazioni economiche per studenti dell'Università di Palermo"},
]

# ============================================================
# KEYWORD PER RELEVANZA (per descrizioni annunci)
# ============================================================
COMPANY_RELEVANCE_KEYWORDS = [
    "amministrativo", "contabilità", "fatturazione", "segreteria", "ufficio",
    "back office", "ragioneria", "commercialista", "gestionali", "e-commerce",
    "wordpress", "amministrazione", "contabile", "bilancio", "partita doppia",
    "iva", "dichiarazione", "cassa", "fatture", "ordini", "acquisti",
    "customer service", "servizio clienti", "praticante", "stage",
    "categoria c", "categoria d", "diplomati", "istruttore amministrativo",
    "funzionario amministrativo", "concorso pubblico", "impiegato",
    "addetto", "assistente", "operatore", "part-time", "tempo parziale",
    "remoto", "smart working", "lavoro da casa", "da remoto", "telelavoro",
    "flessibile", "mezza giornata", "mattina", "pomeriggio",
]

EXCLUDE_KEYWORDS_TITLE = [
    "laurea", "laureato", "ingegnere", "architetto", "medico", "infermiere",
    "dirigente", "direttore", "capo", "responsabile", "senior", "vice presidente",
    "magazziniere", "operaio", "cameriere", "barista", "cuoco", "pizzaiolo",
    "commesso", "venditore", "promoter", "agente di commercio",
    "programmatore", "sviluppatore", "informatico", "tecnico informatico",
    "elettricista", "idraulico", "manutenzione", "autista", "fattorino",
    "corriere", "magazzino", "logistica", "carrellista", "montatore",
]

EXCLUDE_KEYWORDS_TEXT = [
    "laurea richiesta", "laurea in", "laurea magistrale", "laurea triennale",
    "titolo di studio superiore al diploma",
    "esperienza di almeno 5 anni", "esperienza minima 5 anni",
    "esperienza di almeno 10 anni",
    "full-time esclusivo", "disponibilità full time esclusiva",
    "turni notturni", "lavoro notturno", "notturno",
    "si richiede patente c", "patente c", "carta di qualificazione",
]

# ============================================================
# SISTEMA DI SCORING
# ============================================================

# Parole chiave del profilo per punteggio
PROFILE_KEYWORDS_SCORES = [
    # 15 punti — competenze chiave
    ("back office", 15),
    ("contabilità", 15),
    ("fatturazione", 15),
    ("fattura elettronica", 15),
    ("gestionali", 15),
    ("partita doppia", 15),
    ("bilancio", 15),
    ("iva", 15),
    ("segreteria", 15),
    ("wordpress", 15),
    ("e-commerce", 15),
    ("commercialista", 15),
    ("categoria c", 15),
    ("categoria d", 15),
    ("concorso pubblico", 15),
    ("istruttore amministrativo", 15),
    ("funzionario amministrativo", 15),
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
MASTER_LEVEL_KEYWORDS = [
    "diploma", "diplomato", "ragioneria", "istituto tecnico", 
    "scuola superiore", "diploma superiore", "istruzione secondaria",
    "qualifica professionale", "perito commerciale", "afm",
    "amministrazione finanza marketing", "maturità",
    "entry level", "junior", "prima esperienza", "neodiplomato",
    "senza laurea", "non richiede laurea", "basti il diploma",
    "0-2 anni", "0-3 anni", "0-1 anni", "1-2 anni",
    "part-time", "tempo parziale", "mezza giornata",
]

ROLE_FAMILY_KEYWORDS = {
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
# SCORE SOGLIE E PUNTEGGI
# ============================================================
HOURS_OLD = 120
RESULTS_WANTED = 50
MINIMUM_RELEVANT_SCORE = 30
TOP_MATCH_SCORE = 70
MEDIUM_MATCH_MIN = 50
MEDIUM_MATCH_MAX = 69
BORDERLINE_SCORE = 35
HISTORY_RETENTION_DAYS = 60

# ============================================================
# AZIENDE PREFERITE
# ============================================================
PREFERRED_COMPANY_INDICATORS = [
    "commercialista", "studio", "revisione", "bilancio", "contabilità",
    "back office", "segreteria", "amministrazione", "tributario",
    "agenzia entrate", "inps", "comune", "provincia", "regione",
    "asl", "azienda sanitaria", "ente pubblico", "amministrazione pubblica",
    "adecco", "manpower", "randstad", "gi group", "openjobmetis",
    "synergie", "etjca", "humangest",
]

STARTUP_KEYWORDS = [
    "startup", "start-up", "scale-up",
]

# ============================================================
# TRAPIANI — Keyword locali
# ============================================================
LOCALITY_KEYWORDS = {
    "trapani": ["trapani", "valderice", "paceco", "erice", "custonaci", "san vito", "alcamo", "marsala", "mazara", "castelvetrano"],
    "sicilia": ["sicilia", "sicily", "palermo", "catania", "messina", "siracusa", "ragusa", "enna", "caltanissetta", "agrigento"],
}