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

## File modificati
- `job_hunter.py` — main() pulito, scrape_italian_portals() ridotto, search_universal_web() esteso
- `config.py` — COMPANY_CAREER_SITES ridotto, PREFERRED_COMPANY_INDICATORS pulito
- `scrapers/agenzie_lavoro.py` — ELIMINATO

## Commit consigliato
```
git add .
git commit -m "Rimosso scraper agenzie lavoro e aggregatori inutili. Aggiunte Pagine Gialle/Bianche/Bakeca nella ricerca universale. Pulizia config."
git push