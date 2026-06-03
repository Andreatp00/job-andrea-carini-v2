"""
Termini di ricerca e configurazione geografica.

Contiene le liste di termini per i portali lavoro, Google,
le ricerche per nazione, i siti aziendali e le opportunità giovani.
"""

# ============================================================
# TERMINI DI RICERCA — Portali (LinkedIn, Indeed, Subito)
# ============================================================
SEARCH_TERMS: list[str] = [
    # Back office / Amministrativo / Ragioneria - Trapani e Provincia
    "\"back office\" Trapani",
    "\"impiegato amministrativo\" Trapani",
    "\"addetto contabilità\" Trapani diploma",
    "\"fatturazione\" Trapani",
    "\"segreteria\" Trapani",
    "\"ragioneria\" Trapani",
    "\"praticante\" studio commercialista Trapani",
    "\"amministrativo\" Alcamo",
    "\"back office\" Mazara del Vallo",

    # Smart working Vari / Call Center / Data Entry / Assistenza
    "\"smart working\" Italia",
    "\"call center\" remoto",
    "\"assistenza clienti\" smart working",
    "\"help desk\" remoto",
    "\"data entry\" lavoro da casa",
    "\"inserimento dati\" remoto",
    "\"customer service\" remoto",
    "\"assistente virtuale\" remoto",

    # Stage / Tirocini Formativi (Senza esperienza)
    "\"stage\" formativo Trapani",
    "\"tirocinio\" impiegato Trapani",
    "\"apprendistato\" ufficio Trapani",
    "\"stage\" smart working",
    "\"nessuna esperienza\" remoto",

    # Concorsi e Opportunità Giovani
    "concorsi pubblici Trapani categoria C diplomati",
    "concorsi pubblici Palermo categoria C",
    "bando giovani sicilia formazione gratuita",
]

GOOGLE_SEARCH_TERMS: list[str] = [
    "\"lavoro\" back office Trapani Marsala diploma",
    "\"offerta lavoro\" ragioneria AFM Trapani provincia senza laurea",
    "\"smart working\" impiegato amministrativo Italia",
    "\"lavoro logistica\" magazzino Trapani",
    "concorsi pubblici Trapani categoria C diplomati",
    "concorsi pubblici Palermo categoria C",
    "bando giovani sicilia formazione gratuita",
    "\"lavoro da casa\" gestione ordini wordpress",
]

# ============================================================
# RICERCHE GEOGRAFICHE — Solo Italia con focus Trapani
# ============================================================
COUNTRY_SEARCHES: list[dict] = [
    {"country_indeed": "Italy", "location": "Trapani", "label": "Trapani"},
    {"country_indeed": "Italy", "location": "Sicily", "label": "Sicilia"},
    {"country_indeed": "Italy", "location": "Italy", "label": "Italia (Smart Working)"},
]

INCLUDED_COUNTRIES: set[str] = {"Italia", "Trapani", "Sicilia", "Palermo"}
EXCLUDED_COUNTRIES: set[str] = set()

# ============================================================
# SITI AZIENDALI — Trapani, agenzie interinali, smart working
# ============================================================
COMPANY_CAREER_SITES: list[dict] = [
    # --- Studi Commercialisti e Professionisti Trapani ---
    {"company": "Studio Commercialista Trapani", "country": "Trapani", "url": "https://www.commercialistitrapani.it/", "search_params": {"keywords": "collaboratore ragioneria"}, "label": "Commercialisti TP"},
    {"company": "Ordine Commercialisti Trapani", "country": "Trapani", "url": "https://www.odcectrapani.it/", "search_params": {"keywords": "lavoro praticante"}, "label": "ODCEC Trapani"},

    # --- Enti locali Trapani ---
    {"company": "Comune di Trapani", "country": "Trapani", "url": "https://www.comune.trapani.it/", "search_params": {"keywords": "concorso assunzione diplomati"}, "label": "Comune Trapani"},
    {"company": "Provincia Trapani", "country": "Trapani", "url": "https://www.provincia.trapani.it/", "search_params": {"keywords": "concorso categoria C diplomati"}, "label": "Provincia Trapani"},
    {"company": "Libero Consorzio Trapani", "country": "Trapani", "url": "https://www.liberoconsorziotrapani.it/", "search_params": {"keywords": "concorso pubblica amministrazione"}, "label": "Libero Consorzio TP"},
]

# ============================================================
# OPPORTUNITÀ PER GIOVANI 18-35 — Formazione gratuita, corsi, bandi
# ============================================================
OPPORTUNITA_SITES: list[dict] = [
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
