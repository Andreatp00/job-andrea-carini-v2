# 🔍 Job Hunter Bot — Back Office / Ragioneria Trapani

Bot automatico di ricerca lavoro per profilo **Diplomato Ragioneria AFM | 4 anni esperienza amministrativa | 25 anni | Trapani**.

Cerca ogni giorno alle **08:00** su:
- **Subito.it** (molto usato a Trapani) — priorità massima
- **LinkedIn, Indeed, Google Jobs**
- **Agenzie per il Lavoro** — Adecco, Manpower, Randstad, Gi Group, Openjobmetis, Synergie, Humangest
- **Siti Aziendali** — studi commercialisti Trapani, enti locali
- **Concorsi Pubblici** — inPA, Concorsi.it, Gazzetta Ufficiale, Sicilia Concorsi, ASL Trapani, Agenzia Entrate, INPS

Filtra per:
- ✅ **Back office / Amministrativo / Contabilità / Segreteria**
- ✅ **Part-time** (perché studi all'università)
- ✅ **Smart Working / Remoto**
- ✅ **Solo diploma richiesto** (nessuna laurea)
- ✅ **Stage e tirocinio** inclusi (per fare esperienza in studi commercialisti)
- ✅ **Concorsi pubblici categoria C/D** per diplomati

Priorità geografica:
1. 🔴 **Trapani e provincia** (massima priorità)
2. 🟠 **Sicilia**
3. 🟢 **Smart Working / Remoto Italia**

## Setup (una volta sola)

### 1. Installa le dipendenze

```bash
pip install -r requirements.txt
```

### 2. Aggiungi i Secrets su GitHub (se usi GitHub Actions)

Vai su **Settings → Secrets and variables → Actions → New repository secret** e aggiungi:

| Nome Secret | Valore |
|---|---|
| `TELEGRAM_BOT_TOKEN` | *(il tuo token bot Telegram)* |
| `TELEGRAM_CHAT_ID` | *(il tuo chat ID Telegram)* |
| `EMAIL_SENDER` | *(email mittente)* |
| `EMAIL_APP_PASSWORD` | *(password app Gmail)* |
| `EMAIL_RECIPIENT` | *(email destinatario report)* |
| `OPENAI_API_KEY` | *(opzionale - per ranking AI Mistral)* |

### 3. Configura il profilo

Apri `config.py` e personalizza `PROFILE` con i tuoi dati.

### 4. Avvia il bot

```bash
python job_hunter.py
```

## Struttura del progetto

```
job-2.0--main/
├── config.py                     # Profilo candidato, keyword, siti, punteggi
├── job_hunter.py                 # Motore principale del bot
├── scrapers/
│   ├── __init__.py
│   ├── subito_it.py              # ✅ Scraper Subito.it (Trapani)
│   ├── concorsi_pubblici.py      # ✅ Scraper concorsi pubblici PA
│   └── agenzie_lavoro.py         # ✅ Scraper agenzie interinali
├── data/
│   └── reports/                  # Report Excel/CSV generati
├── logs/                         # Log giornalieri
├── requirements.txt
└── README.md
```

## Funzionamento

1. **Raccolta**: cerca su Subito.it, LinkedIn, Indeed, Google Jobs, agenzie lavoro, siti aziendali e portali concorsi
2. **Normalizzazione**: standardizza e deduplica le offerte
3. **Filtraggio**: esclude ruoli non amministrativi, quelli che richiedono laurea o troppa esperienza
4. **Scoring**: assegna punteggio basato su keyword, localizzazione, part-time/smart working
5. **Ranking AI** (opzionale): se configurata API Mistral, riordina con AI
6. **Report**: genera file Excel con Top_Match, All_Relevant, Borderline, Esclusi_Audit e Tracker Candidature
7. **Notifica**: invia report su Telegram e/o email con allegato Excel

## Siti monitorati

### 🔴 Trapani e provincia (Subito.it)
- Ricerche: back office, impiegato amministrativo, contabilità, fatturazione, segreteria, commercialista, ragioneria, praticante, part-time

### 🟠 Portali classici (LinkedIn, Indeed, Google Jobs)
- Ricerche geografiche: Trapani, Sicilia, Italia (smart working)

### 🟢 Agenzie per il Lavoro
- Adecco, Manpower, Randstad, Gi Group, Openjobmetis, Synergie, Humangest
- Ricerche a Trapani e Smart Working

### 🔵 Concorsi Pubblici
- inPA (Portale Unico PA), Concorsi.it, Gazzetta Ufficiale
- Sicilia Concorsi, PA Sicilia, ASL Trapani
- Comune Trapani, Agenzia delle Entrate, INPS

### 🟣 Siti Aziendali
- Studi commercialisti Trapani, Ordine Commercialisti Trapani
- Siti remoti: Remote.co, Working Nomads, We Work Remotely, FlexJobs

## Personalizzazione

Modifica `config.py` per:
- `PROFILE`: i tuoi dati personali
- `SEARCH_TERMS`: termini di ricerca su LinkedIn/Indeed
- `GOOGLE_SEARCH_TERMS`: termini per Google Jobs
- `SUBITO_SEARCHES`: ricerche su Subito.it (in `scrapers/subito_it.py`)
- `CONCORSI_SITES`: portali concorsi da monitorare
- `PROFILE_KEYWORDS_SCORES`: keyword e punteggi per lo scoring
- `EXCLUDE_KEYWORDS_TITLE/TEXT`: cosa escludere

---

## 📝 Storico Modifiche & Risoluzione Problemi

### 🔴 Problemi Risolti

#### 1. **HTTP 429 Too Many Requests - Google Jobs su GitHub Actions** (01/06/2026)

**Problema:**
- GitHub Actions usa IP condivisi che Google rate-limiterà dopo poche richieste
- JobSpy tentava di accedere a Google Jobs per ogni termine di ricerca
- Risultato: **HTTP 429 Error** per tutte le richieste Google Jobs
- **0 offerte raccolte da Google Jobs** (bloccato completamente)

**Sintomi:**
```
Errore portali: HTTPSConnectionPool(host='www.google.com', port=443): 
Max retries exceeded with url: /sorry/index?continue=https://www.google.com/search... 
(Caused by ResponseError('too many 429 error responses'))
```

**Soluzione Applicata:**
- ✅ Rimosso `"google"` da `WORKING_SITES` in `scrape_portals()` → usa solo LinkedIn + Indeed
- ✅ Aumentato `time.sleep()` da 1s a 2s tra le richieste JobSpy
- ✅ Aggiunto delay iniziale di 15s nel workflow GitHub Actions
- ✅ Rimosso loop `GOOGLE_SEARCH_TERMS` (causava 429)
- ✅ **Nessuna perdita di copertura**: LinkedIn e Indeed funzionano + Multi-Engine copre Google

**Commit:** `c9d5174` - fix: risolto errore HTTP 429 Google Jobs su GitHub Actions

**File modificati:**
- `job_hunter.py` (linee 292-325)
- `.github/workflows/job_hunter_daily.yml` (aggiunto step delay iniziale)

**Risultato:**
- ✅ Nessun errore 429
- ✅ LinkedIn e Indeed funzionanti
- ✅ Tutte le altre fonti attive (Subito.it, agenzie, concorsi, Multi-Engine)
- ✅ Report completi generati

---

#### 2. **Errore 'unexpected keyword argument timeout' - Subito.it API** (Precedente)

**Problema:**
- Parametro `timeout` non supportato nella chiamata API di Subito.it

**Soluzione:**
- Rimosso parametro `timeout` non valido

**Commit:** `76b0944` - fix: risolto errore 'unexpected keyword argument timeout' in Subito.it API

---

#### 3. **Errori 403/404/202 - DuckDuckGo & Cloudflare** (Precedente)

**Problema:**
- DuckDuckGo bloccava con HTTP 202
- Alcuni siti con Cloudflare restituivano 403
- Glassdoor e ZipRecruiter non accessibili

**Soluzione:**
- ✅ Implementato **Multi-Engine Search System** (Bing → Yahoo → Ecosia)
- ✅ Rimosso DuckDuckGo come dipendenza principale
- ✅ Aggiunto fallback automatico per tutti gli scraper

**Commit:** `6b3ddf3` - fix: risolto errori critici 403/404/202 - Multi-Engine, Subito.it API

---

### 📊 Cronologia Commit

| Data | Commit | Descrizione | Problema Risolto |
|------|--------|-------------|------------------|
| 01/06/2026 | [`c9d5174`](https://github.com/Andreatp00/job-andrea-carini-v2/commit/c9d5174) | Fix HTTP 429 Google Jobs | Google Jobs bloccato su GitHub Actions |
| 27/05/2026 | [`76b0944`](https://github.com/Andreatp00/job-andrea-carini-v2/commit/76b0944) | Fix timeout Subito.it | Parametro timeout non valido |
| 27/05/2026 | [`6b3ddf3`](https://github.com/Andreatp00/job-andrea-carini-v2/commit/6b3ddf3) | Multi-Engine + Cloudflare | DuckDuckGo 202, Cloudflare 403 |
| 27/05/2026 | [`5f93eca`](https://github.com/Andreatp00/job-andrea-carini-v2/commit/5f93eca) | Filtri migliorati | Espansione ricerca smart working |
| 27/05/2026 | [`47574b1`](https://github.com/Andreatp00/job-andrea-carini-v2/commit/47574b1) | Multi-Engine architettura | Blocco HTTP 301/403 |

---

### 🛠️ Configurazione Attuale (Dopo Fix)

**Fonti Attive:**
- ✅ **Subito.it** - API JSON ufficiale (hades.subito.it) - **Priorità massima**
- ✅ **LinkedIn** - Via JobSpy (funziona su GitHub Actions)
- ✅ **Indeed** - Via JobSpy (funziona su GitHub Actions)
- ✅ **Agenzie Lavoro** - 12 agenzie con fallback Multi-Engine
- ✅ **Concorsi Pubblici** - 12+ fonti (RSS + scraping)
- ✅ **Opportunità Giovani** - 40+ fonti (formazione, bandi, tirocini)
- ✅ **Siti Aziendali** - 20+ siti con Multi-Engine
- ✅ **Portali Italiani** - 6 portali con Multi-Engine
- ✅ **Ricerca Universale** - Multi-Engine su tutto il web .it

**Fonti Disabilitate (e perché):**
- ❌ **Google Jobs** - HTTP 429 su GitHub Actions IP condivisi
  - *Notare: Le ricerche Google sono coperte da Multi-Engine (Bing/Yahoo/Ecosia)*
- ❌ **Glassdoor** - Cloudflare 403
- ❌ **ZipRecruiter** - Cloudflare 403
- ❌ **DuckDuckGo** - HTTP 202

**Timing Ottimizzato:**
- Delay tra richieste JobSpy: **2 secondi** (era 1s)
- Delay iniziale GitHub Actions: **15 secondi**
- Timeout richieste HTTP: **30 secondi**

---

### 💡 Consigli per Deployment

1. **Testa il fix:**
   ```bash
   git pull origin main
   python job_hunter.py
   ```

2. **Lancia manualmente su GitHub Actions:**
   - Vai su **Actions** → **Job Hunter Bot - Ricerca Giornaliera** → **Run workflow**

3. **Verifica i log:**
   - Cerca l'assenza di errori `429` o `too many requests`
   - Controlla che LinkedIn e Indeed mostrino offerte raccolte

4. **Se vuoi ripristinare Google Jobs in futuro:**
   - Serve un **IP dedicato** o **proxy rotante**
   - Oppure usare **GitHub Actions con IP statico** (funzionalità enterprise)