"""
Termini di ricerca e configurazione geografica.

MASSIMIZZATI per coprire:
- Trapani e provincia (in presenza)
- Palermo città (in presenza, se vale la pena)
- TUTTI i lavori smart working/remoto in Italia
- Concorsi pubblici accessibili con diploma
- Bandi giovani, europei, nazionali
"""

# ============================================================
# TERMINI DI RICERCA — Portali (LinkedIn, Indeed via JobSpy)
# ============================================================
SEARCH_TERMS: list[str] = [
    # ═══ TRAPANI IN PRESENZA ═══
    '"back office" Trapani',
    '"impiegato amministrativo" Trapani',
    '"contabilità" Trapani',
    '"fatturazione" Trapani',
    '"segreteria" Trapani',
    '"ragioneria" Trapani',
    '"praticante" "studio commercialista" Trapani',
    '"amministrativo" Alcamo',
    '"back office" "Mazara del Vallo"',
    '"impiegato" Marsala',
    '"ufficio" Trapani diploma',
    '"addetto" Trapani',
    '"logistica" Trapani',
    '"gestione ordini" Trapani',
    '"punto vendita" Trapani',

    # ═══ PALERMO IN PRESENZA ═══
    '"back office" Palermo',
    '"impiegato amministrativo" Palermo',
    '"contabilità" Palermo diploma',
    '"segreteria" Palermo',

    # ═══ SMART WORKING / REMOTO — QUALSIASI LAVORO ═══
    # Amministrativo remoto
    '"smart working" "impiegato amministrativo"',
    '"back office" remoto',
    '"back office" "smart working"',
    '"contabilità" "smart working"',
    '"segreteria" "lavoro da casa"',
    '"amministrativo" "full remote"',
    
    # Call center e customer service
    '"call center" remoto',
    '"call center" "smart working"',
    '"call center" "lavoro da casa"',
    '"call center inbound" remoto',
    '"call center outbound" remoto',
    '"operatore telefonico" remoto',
    '"operatore telefonico" "smart working"',
    '"customer service" remoto',
    '"customer service" "smart working"',
    '"assistenza clienti" remoto',
    '"assistenza clienti" "lavoro da casa"',
    '"help desk" remoto',
    '"supporto clienti" remoto',
    
    # Data entry e inserimento dati
    '"data entry" remoto',
    '"data entry" "smart working"',
    '"data entry" "lavoro da casa"',
    '"inserimento dati" remoto',
    '"inserimento dati" "smart working"',
    
    # E-commerce, social, web
    '"e-commerce" remoto',
    '"e-commerce" "smart working"',
    '"social media manager" remoto',
    '"social media" "smart working"',
    '"gestione ordini" remoto',
    '"gestione ordini online" "smart working"',
    '"wordpress" remoto',
    '"shopify" remoto',
    '"content creator" remoto',
    '"copywriter" remoto',
    '"seo" "smart working"',
    
    # Assistente virtuale e booking
    '"assistente virtuale" remoto',
    '"virtual assistant" remoto',
    '"booking" remoto',
    '"prenotazioni" "smart working"',
    '"moderatore" remoto',
    
    # Generico smart working
    '"smart working" Italia diploma',
    '"lavoro da casa" Italia',
    '"full remote" Italia',
    '"100% remoto" Italia',
    '"lavoro agile" Italia',
    'remoto "senza esperienza"',
    'remoto "prima esperienza"',
    '"telelavoro" Italia',

    # ═══ STAGE E TIROCINI ═══
    '"stage" Trapani',
    '"tirocinio" Trapani',
    '"apprendistato" Trapani',
    '"stage" "smart working"',
    '"tirocinio" remoto',
    '"stage" amministrativo',
    '"nessuna esperienza" remoto',
    '"prima esperienza" "smart working"',

    # ═══ CONCORSI PUBBLICI ═══
    'concorsi pubblici Trapani diplomati',
    'concorsi pubblici Palermo "categoria C"',
    'concorsi pubblici Sicilia diplomati',
    'concorsi pubblici "istruttore amministrativo" Sicilia',
    '"bando" "diplomati" Sicilia',
    '"concorso" "amministrativo" Trapani',
]

GOOGLE_SEARCH_TERMS: list[str] = [
    '"lavoro" back office Trapani Marsala diploma',
    '"offerta lavoro" ragioneria AFM Trapani provincia senza laurea',
    '"smart working" impiegato amministrativo Italia',
    '"lavoro da casa" call center Italia',
    '"data entry" "lavoro da casa" Italia',
    '"customer service" remoto Italia',
    '"social media manager" remoto Italia',
    '"e-commerce" gestione ordini remoto',
    '"assistente virtuale" remoto Italia',
    '"operatore telefonico" "smart working" Italia',
    'concorsi pubblici Trapani categoria C diplomati',
    'concorsi pubblici Sicilia diplomati 2026',
    'bando giovani sicilia formazione gratuita 2026',
    '"lavoro da casa" "senza esperienza" Italia',
    '"wordpress" "smart working" Italia',
    'bandi europei giovani 2026 Italia',
    '"corpo europeo solidarietà" 2026',
    '"garanzia giovani" Sicilia 2026',
]

# ============================================================
# RICERCHE GEOGRAFICHE — Focus Trapani + Sicilia + Italia remoto
# ============================================================
COUNTRY_SEARCHES: list[dict] = [
    {"country_indeed": "Italy", "location": "Trapani", "label": "Trapani"},
    {"country_indeed": "Italy", "location": "Palermo", "label": "Palermo"},
    {"country_indeed": "Italy", "location": "Sicily", "label": "Sicilia"},
    {"country_indeed": "Italy", "location": "Italy", "label": "Italia (Smart Working)"},
]

INCLUDED_COUNTRIES: set[str] = {"Italia", "Trapani", "Sicilia", "Sicilia (altra)", "Palermo", "Europa", "Italia (Smart Working)"}
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

    # --- Agenzie interinali (cercano sempre per tutta Italia + remoto) ---
    {"company": "Adecco", "country": "Italia", "url": "https://www.adecco.it/", "search_params": {"keywords": "back office smart working remoto"}, "label": "Adecco Remoto"},
    {"company": "Randstad", "country": "Italia", "url": "https://www.randstad.it/", "search_params": {"keywords": "call center smart working remoto"}, "label": "Randstad Remoto"},
    {"company": "ManpowerGroup", "country": "Italia", "url": "https://www.manpower.it/", "search_params": {"keywords": "data entry smart working remoto"}, "label": "Manpower Remoto"},
    {"company": "GiGroup", "country": "Italia", "url": "https://www.gigroup.it/", "search_params": {"keywords": "impiegato smart working remoto"}, "label": "GiGroup Remoto"},
]

# ============================================================
# OPPORTUNITÀ PER GIOVANI 18-35 — Formazione, corsi, bandi, UE
# ============================================================
OPPORTUNITA_SITES: list[dict] = [
    # ═══ Formazione gratuita finanziata ═══
    {"name": "Garanzia Giovani Sicilia", "url": "https://www.garanziagiovani.gov.it/Pagine/default.aspx", "tipo": "formazione", "descrizione": "Programma europeo per giovani NEET 16-29: corsi gratuiti, tirocini, bonus"},
    {"name": "Garanzia Occupabilità Lavoratori (GOL)", "url": "https://www.anpal.gov.it/garanzia-di-occupabilita-dei-lavoratori-gol", "tipo": "formazione", "descrizione": "Programma di formazione professionale gratuito finanziato dal PNRR"},
    {"name": "Fondimpresa - Formazione Finanziata", "url": "https://www.fondimpresa.it/", "tipo": "formazione", "descrizione": "Formazione gratuita finanziata dai fondi interprofessionali per lavoratori"},
    {"name": "Fondazione ITS Sicilia", "url": "https://www.its-sicilia.it/", "tipo": "formazione", "descrizione": "Corsi ITS post-diploma gratuiti con borse di studio (durata 2 anni)"},
    {"name": "Scuola Superiore Sant'Anna - Corsi gratuiti", "url": "https://www.santannapisa.it/it/formazione/corsi", "tipo": "formazione", "descrizione": "Corsi di alta formazione gratuiti per diplomati"},

    # ═══ Inglese gratis / finanziato ═══
    {"name": "British Council - Learn English Free", "url": "https://learnenglish.britishcouncil.org/", "tipo": "inglese", "descrizione": "Corsi di inglese gratuiti online con esercizi e podcast"},
    {"name": "BBC Learning English", "url": "https://www.bbc.co.uk/learningenglish/", "tipo": "inglese", "descrizione": "Corsi di inglese gratuiti della BBC (tutti i livelli)"},
    {"name": "Duolingo", "url": "https://www.duolingo.com/course/en/it/Impara-l-inglese", "tipo": "inglese", "descrizione": "App gratuita per imparare l'inglese (100% gratis, no pubblicità)"},
    {"name": "Open English - Corsi finanziati", "url": "https://www.openenglish.com/it/", "tipo": "inglese", "descrizione": "Corsi di inglese finanziati da fondi interprofessionali e regionali"},
    {"name": "Corso Inglese Gratuito - Regione Sicilia", "url": "https://www.regione.sicilia.it/istruzione-formazione/", "tipo": "inglese", "descrizione": "Corsi di lingua inglese finanziati dalla Regione Sicilia per giovani"},

    # ═══ Bandi e contributi per giovani — NAZIONALI ═══
    {"name": "Borse di Studio Regione Sicilia", "url": "https://www.regione.sicilia.it/istruzione-formazione/diritto-allo-studio", "tipo": "bando", "descrizione": "Borse di studio regionali per studenti universitari siciliani"},
    {"name": "Bonus Giovani Under 35", "url": "https://www.inps.it/", "tipo": "bando", "descrizione": "Bonus assunzioni under 35 - sgravi contributivi per aziende che assumono giovani"},
    {"name": "Nuova Garanzia Giovani 2026", "url": "https://www.garanziagiovani.gov.it/", "tipo": "bando", "descrizione": "Misure di politica attiva per giovani 16-29: formazione, tirocini, incentivi"},
    {"name": "Resto al Sud 2.0", "url": "https://www.invitalia.it/cosa-facciamo/creiamo-nuove-aziende/resto-al-sud", "tipo": "bando", "descrizione": "Finanziamento a fondo perduto per avviare attività al Sud per under 56"},
    {"name": "SELFIEmployment", "url": "https://www.invitalia.it/cosa-facciamo/creiamo-nuove-aziende/selfiemployment", "tipo": "bando", "descrizione": "Prestiti a tasso zero per giovani NEET che vogliono avviare un'attività"},
    {"name": "Bandi MISE / MIMIT Startup", "url": "https://www.mimit.gov.it/it/incentivi", "tipo": "bando", "descrizione": "Incentivi e contributi per startup e nuove imprese giovanili"},
    {"name": "ON - Oltre Nuove Imprese a Tasso Zero", "url": "https://www.invitalia.it/cosa-facciamo/creiamo-nuove-aziende/nuove-imprese-a-tasso-zero", "tipo": "bando", "descrizione": "Finanziamenti agevolati per giovani under 35 e donne che creano impresa"},

    # ═══ Opportunità EUROPEE ═══
    {"name": "Erasmus+ Giovani", "url": "https://www.erasmusplus.it/", "tipo": "ue", "descrizione": "Scambi giovanili e volontariato europeo finanziati dall'UE (18-30 anni)"},
    {"name": "Corpo Europeo di Solidarietà", "url": "https://europeansolidaritycorps.europa.eu/it", "tipo": "ue", "descrizione": "Volontariato retribuito all'estero per giovani 18-30, spese coperte dall'UE"},
    {"name": "DiscoverEU", "url": "https://europa.eu/youth/discovereu_it", "tipo": "ue", "descrizione": "Pass Interrail gratuito per viaggiare in Europa a 18 anni"},
    {"name": "Eurodesk Italy", "url": "https://www.eurodesk.it/", "tipo": "ue", "descrizione": "Portale ufficiale UE per orientamento sui programmi europei per i giovani"},
    {"name": "Salto-Youth", "url": "https://www.salto-youth.net/", "tipo": "ue", "descrizione": "Bandi per scambi giovanili e formazione non formale finanziati dall'UE"},
    {"name": "EURES - Lavoro in Europa", "url": "https://ec.europa.eu/eures/", "tipo": "ue", "descrizione": "Offerte di lavoro, tirocinio e apprendistato in tutta Europa per giovani"},
    {"name": "European Youth Portal", "url": "https://youth.europa.eu/", "tipo": "ue", "descrizione": "Portale ufficiale UE con tutte le opportunità per i giovani europei"},
    {"name": "EU Careers - EPSO", "url": "https://epso.europa.eu/", "tipo": "ue", "descrizione": "Concorsi per lavorare nelle istituzioni europee (anche per diplomati)"},

    # ═══ Tirocini e formazione Sicilia ═══
    {"name": "Centro per l'Impiego Palermo", "url": "https://www.regione.sicilia.it/istituzioni/regione/strutture-regionali/assessorato-famiglia-politiche-sociali-lavoro/dipartimento-lavoro/centri-impiego/palermo", "tipo": "tirocinio", "descrizione": "Offerte di lavoro e tirocini amministrativi in provincia di Palermo"},
    {"name": "Formazione Palermo - Corsi Gratuiti", "url": "https://www.comune.palermo.it/", "tipo": "formazione", "descrizione": "Bandi per corsi di formazione professionale gratuiti nel comune di Palermo"},
    {"name": "Tirocini Retribuiti Regione Sicilia", "url": "https://www.regione.sicilia.it/lavoro/tirocini", "tipo": "tirocinio", "descrizione": "Tirocini formativi retribuiti finanziati dalla Regione Sicilia per giovani"},
    {"name": "Stage in PA - Portale tirocini", "url": "https://tirocini.formez.it/", "tipo": "tirocinio", "descrizione": "Tirocini curriculari e extracurriculari nella Pubblica Amministrazione"},
    {"name": "Garanzia Giovani - Tirocini", "url": "https://www.garanziagiovani.gov.it/tirocini/", "tipo": "tirocinio", "descrizione": "Tirocini retribuiti per giovani 16-29 (indennità + contributi)"},

    # ═══ Agevolazioni studio ═══
    {"name": "ERSU Sicilia", "url": "https://www.ersu.it/", "tipo": "universita", "descrizione": "Borse di studio, alloggi e mense per studenti universitari in Sicilia"},
    {"name": "UNIPA - Opportunità studenti", "url": "https://www.unipa.it/studenti/borse-di-studio-e-agevolazioni/", "tipo": "universita", "descrizione": "Agevolazioni economiche per studenti dell'Università di Palermo"},
]
