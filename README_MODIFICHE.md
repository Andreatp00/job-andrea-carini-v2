# Report Modifiche — 3 Giugno 2026

## Cosa è stato rimosso

### 1. `scrapers/agenzie_lavoro.py` — FILE ELIMINATO
- Intero scraper per agenzie lavoro (Gi Group, Randstad, Manpower, Adecco, Openjobmetis, Synergie, Humangest, Etjca)
- **Motivo:** I parser HTML e pattern URL non funzionavano. Ogni agenzia ha struttura diversa e le pagine caricano offerte via JS. I fix già tentati (pattern URL, scraping pagina, validazione location) non hanno mai prodotto risultati utili.

### 2. `config.py` — RIMOSSO da `COMPANY_CAREER_SITES`:
- Adecco, Manpower, Randstad, Gi Group, Openjobmetis, Synergie, Etjca, Humangest (agenzie)
- Injob, InfoJobs, Monster, Corriere Lavoro (aggregatori)
- Adecco Remote, Randstad Remote, Jobtech (remote)
- Remote.co, Working Nomads, We Work Remotely, FlexJobs (siti inglesi)

**RIMASTI:** Studi commercialisti Trapani, ODCEC Trapani, Comune Trapani, Provincia Trapani, Libero Consorzio TP

### 3. `config.py` — PULITO `PREFERRED_COMPANY_INDICATORS`
- Rimosse le agenzie (adecco, manpower, randstad, gi group, openjobmetis, synergie, etjca, humangest, injob, infojobs, monster)

### 4. `job_hunter.py` — RIMOSSO da `main()`:
- `df_agenzie = scrape_agenzie_lavoro()` e relativo `logger.info()`
- `df_agenzie` dal `frames` list

### 5. `job_hunter.py` — RIDOTTO `scrape_italian_portals()`:
- RIMOSSI: Jobrapido, Neuvoo, Jobsora, Injob, InfoJobs
- RIMASTO: Solo TrovoLavoro
- **Motivo:** Jobrapido/Neuvoo/Jobsora davano risultati non pertinenti (corsi, blog), link di redirect non validi, o pagine generiche

## Cosa è stato aggiunto

### Ricerca Universale — Nuove query:
- `site:paginegialle.it "lavoro" "amministrativo" Trapani`
- `site:paginebianche.it "lavoro" "amministrativo" Trapani`
- `site:bakeca.it "lavoro" "ufficio" Trapani`

## Fonti ATTIVE ora

| Fonte | Stato | Note |
|-------|-------|------|
| **LinkedIn** (JobSpy) | ✅ Attivo | 86 offerte nell'ultimo run |
| **Indeed** (JobSpy) | ✅ Attivo | 9 offerte nell'ultimo run |
| **Subito.it** | ✅ Attivo | Molto usato a Trapani |
| **Aziende dirette** | ✅ Attivo | Studi commercialisti, enti locali |
| **Concorsi Pubblici** | ✅ Attivo | |
| **Opportunità Giovani** | ✅ Attivo | Formazione, bandi, tirocini |
| **TrovoLavoro** | ✅ Attivo | |
| **Ricerca Universale** | ✅ Attivo | Inclusi PagineGialle, PagineBianche, Bakeca |
| **Agenzie Lavoro** | ❌ RIMOSSO | Gi Group, Randstad, Manpower, ecc. - non funzionavano |
| **Jobrapido/Jobsora** | ❌ RIMOSSO | Risultati non pertinenti |

## Commit effettuato
```
81969e7 — Rimosso scraper agenzie lavoro e aggregatori inutili. Aggiunte Pagine Gialle/Bianche/Bakeca nella ricerca universale. Pulizia config.
Branch: main → main (push riuscito)
```

---

# Analisi Struttura e Consigli di Miglioramento

## Stato attuale del sistema

Il bot ha una **struttura solida** nelle sue fondamenta:
- Pipeline: raccolta → normalizzazione → fingerprint/deduplica → filtraggio/ranking → report → notifica
- Multi-engine search (Bing → Yahoo → Ecosia) come backbone per ricerca web
- JobSpy per LinkedIn/Indeed (API strutturate)
- Subito.it e concorsi pubblici con scraper dedicati
- Sistema di scoring e AI ranking con Mistral
- Filtri geografici stringenti (Trapani-only + Smart Working)

## Punti di forza esistenti

| Componente | Valutazione | Perché |
|-----------|-------------|--------|
| Deduplicazione con `_smart_fingerprint` | ✅ Ottimo | Rileva URL LinkedIn generici e usa titolo+azienda come fallback |
| Validazione location | ✅ Ottimo | Filtraggio geografico multi-livello molto robusto |
| Multi-Engine search | ✅ Buono | Bing→Yahoo→Ecosia copre bene i fallimenti |
| Sistema di scoring | ✅ Buono | Pesi ben bilanciati per keyword, geo, seniority |
| Second chance | ✅ Interessante | Recupera offerte borderline con keyword critiche |

## Debolezze attuali

### 1. Dipendenza dal Multi-Engine per ricerca web
- **Problema:** Bing/Yahoo possono cambiare struttura HTML, rompendo il parser BeautifulSoup
- **Rischio:** Se un motore cambia, si perde una fonte importante
- **Soluzione proposta:** Aggiungere un motore di ricerca aggiuntivo come fallback (Google via API o Brave Search API)

### 2. JobSpy è un wrapper Python
- **Problema:** JobSpy è una libreria di terze parti che potrebbe non essere aggiornata
- LinkedIn cambia spesso struttura e blocca gli scraper
- **Rischio:** Se LinkedIn blocca JobSpy, si perde la fonte più produttiva (86/199 offerte)
- **Soluzione proposta:** Avere un fallback LinkedIn via Multi-Engine search (già parzialmente coperto da universal_search)

### 3. AI Ranking con Mistral
- **Problema:** Il prompt AI è lungo (richiede molti token) e c'è rate limiting
- 7 batch per 199 offerte = 14+ minuti solo per AI ranking
- **Miglioramento:** Ridurre il prompt AI, usare un modello più veloce, o fare AI solo su Top 50

### 4. Scraping HTML statico vs JS
- **Problema:** Subito.it e siti aziendali caricano contenuti via JavaScript
- `tls_session.get()` non esegue JS → potrebbe ricevere pagine vuote
- **Soluzione proposta:** Playwright o Selenium per siti critici (Subito in primis)

### 5. Timing e performance
- **Problema:** Il bot impiega 14+ minuti per eseguire
- Colpa dei delay forzati (1.5s-2s per ogni query) e AI ranking batch
- **Miglioramento:** Parallelizzare le fonti indipendenti con `ThreadPoolExecutor`

## Consigli prioritari (per massimo impatto)

### 🔴 Priorità ALTA

#### 1. Aggiungere Telegram come canale di feedback interattivo
- **Ora:** Solo notifica passiva (messaggio + file Excel)
- **Miglioramento:** Bot Telegram con bottoni "Apri link", "Segna come candidata", "Non pertinente"
- L'utente potrebbe scartare/subire offerte direttamente da Telegram
- Il feedback servirebbe a migliorare lo scoring automatico

#### 2. Cache delle offerte viste (locale persistente)
- **Ora:** `seen_jobs.json` e `job_history.json` funzionano
- **Miglioramento:** SQLite invece di JSON per query più veloci e ricerca per data/keyword
- Aggiungere campo `user_feedback` (candidata/salta) per training futuro

#### 3. Notifiche push per offerte TOP (score ≥ 80)
- **Ora:** Singolo report giornaliero
- **Miglioramento:** Se durante il run viene trovata un'offerta con score ≥ 80, inviare notifica immediata Telegram "🔥 OFFERTA TOP TROVATA!"

### 🟡 Priorità MEDIA

#### 4. Aggiungere Indeed scraping diretto (fallback se JobSpy fallisce)
- Usare `search_web_engines()` con query `site:it.indeed.com` per avere un fallback

#### 5. Migliorare la ricerca universale con più domini specifici
| Sito | Perché |
|------|--------|
| `lavoro.corriere.it` | Annunci locali |
| `lavoro.repubblica.it` | Annunci locali |
| `lavoro.lasicilia.it` | Giornale locale Trapani |
| `trovit.it` | Aggregatore ma funziona |
| `adzuna.it` | Motore ricerca lavoro |

#### 6. Salvataggio HTML delle pagine analizzate (debug mode)
- Quando una fonte non produce risultati, salvare l'HTML ricevuto
- Utile per debug quando qualcosa si rompe

### 🟢 Priorità BASSA

#### 7. Dashboard web leggera (Flask o Streamlit)
- Mostrare offerte in tempo reale, statistiche, storico
- Permettere all'utente di filtrare, cercare, marcare come candidata

#### 8. Training automatico dello scoring
- Usare il feedback dell'utente (candidata/salta) per aggiustare pesi keyword
- ML leggero: se l'utente candida sempre offerte con "contabilità" → alza il peso

#### 9. Export CV personalizzato per ogni offerta
- Generare lettera di presentazione personalizzata con AI (Mistral)
- Allegare al report Excel o inviare separatamente

## Roadmap consigliata

```
Fase 1 (subito)     → Cache SQLite + notifiche TOP + Indeed fallback
Fase 2 (1-2 settimane) → Telegram interattivo + parallelizzazione run
Fase 3 (1 mese)     → Playwright per Subito + AI ranking ottimizzato
Fase 4 (2-3 mesi)   → Dashboard web + training scoring
```

## Conclusione

La struttura è **buona** per un bot Python monolitico. I punti di forza sono:
- Pipeline ben definita (raccolta → normalizzazione → ranking → report)
- Filtri geografici robusti (fondamentali per Trapani-only)
- Second-chance che recupera offerte borderline
- Multi-Engine search che garantisce sempre risultati

I punti da migliorare sono:
- **Performance:** parallelizzare le fonti, ottimizzare AI ranking
- **Resilienza:** fallback per LinkedIn/Indeed se JobSpy muore
- **Interattività:** dare all'utente modo di interagire con le offerte
- **Dati persistenti:** SQLite > JSON per storia e feedback
