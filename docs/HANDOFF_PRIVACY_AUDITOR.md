# Handoff · Watermark Privacy & Security Auditor

Stato al 18/09/2026, tappa di Napoli. Keyword sorteggiata: **privacy**. Tempo totale di sviluppo: circa 7 ore, con congelamento delle funzioni 90 minuti prima della consegna.

Istruzioni per Claude Code: leggi prima `CLAUDE.md`, poi questo file, poi `git status`. Le decisioni sotto sono già state approvate o sono in attesa di approvazione come indicato: non riaprirle senza un fatto nuovo.

## Committente e stack (da dichiarare sempre: slide, pitch, README, risposte alla giuria)

**Committente: un Comune, nel ruolo di titolare del trattamento dei dati.** Nella demo il caso è Roma Capitale, che pubblica ogni giorno i dati del WiFi pubblico DigitRoma.
- Utente operativo: il **DPO** (responsabile della protezione dei dati) del Comune, affiancato dall'ufficio open data e dal referente per la cybersicurezza.
- Decisione supportata: pubblicare o no un dataset, e con quali correzioni; quali sistemi aggiornare per primi.
- Non è un prodotto per cittadini né per forze dell'ordine.

**Stack tecnologico** (tutto locale, nessuna API a pagamento, nessuna chiamata di rete durante l'uso):

| Livello | Tecnologia | Ruolo |
|---|---|---|
| Frontend | Streamlit 1.64 (Python), tema in `.streamlit/config.toml`, Material Symbols | Interfaccia web, widget, stato di sessione |
| Grafici | Plotly 6.9 | Grafici interattivi e mappa |
| Backend | Python 3.12, nello stesso processo di Streamlit (moduli `core/`) | Logica di audit, separata dalla UI |
| Dati | pandas 2.3, numpy, openpyxl | Caricamento CSV/XLSX/JSON, trasformazioni |
| IA / ML | scikit-learn 1.9: TF-IDF, regressione logistica, Random Forest, NMF, K-Means, Isolation Forest | Modello di impatto CSIRT, attacco di inferenza, ricerca nei provvedimenti, anomalie |
| Raccolta dati | Python standard library (`urllib`), script `scripts/fetch_data.py` | Scarica CSIRT, Garante, Roma WiFi prima della demo in `data/` |
| Persistenza | File CSV locali in `data/`, modello esportabile con joblib | Nessun database, nessun cloud |

Frontend e backend girano nello stesso processo Python: Streamlit fa da server web e da interfaccia. È una scelta per la gara (un solo comando di avvio, funziona offline); in produzione la logica di `core/` si esporrebbe come API separata.

## La falla, per filo e per segno

**Oggetto.** Dataset open data di Roma Capitale "Sessioni anonimizzate di navigazione web riscontrate nel sistema WiFi di Roma Capitale", licenza CC-BY, un CSV al giorno. Ogni riga è una sessione di un utente autenticato su DigitRomaWiFi o DRWIFI_SECURE.

**Cosa dichiara l'ente.** La descrizione ufficiale della risorsa elenca: durata, data, orario di inizio e fine, sede, lingua del client. **`LOGINCOUNT` non è documentata** da nessuna parte (descrizione del dataset, descrizione della risorsa, metadati). Contatto dell'ente: info.opendata@comune.roma.it.

**Cosa pubblica in più, per ogni sessione:**
- orario al secondo (`STARTTIME`, `ENDTIME`);
- indirizzo della sede al numero civico (`DUG`, `DUF`, `CIVICO`);
- lingua del dispositivo (`DTLN`);
- `LOGINCOUNT`, un intero da 1 a oltre 100.000.

**La falla.** `LOGINCOUNT` si comporta come **il numero cumulativo di accessi dello stesso utente**. Tra due sessioni della stessa persona cambia di poche unità e sale sempre nel tempo. Quindi funziona come **pseudonimo persistente**: permette di collegare le sessioni di una persona tra ore e giorni. Ciascuna sessione riporta luogo al civico e orario al secondo.

Nei termini del Gruppo di lavoro Articolo 29 (Parere 05/2014 sulle tecniche di anonimizzazione), un dataset è anonimo solo se impedisce tre cose: **individuazione** (singling out), **correlabilità** (linkability) e **deduzione** (inference). Qui falliscono le prime due. Per il considerando 26 del GDPR, dati collegabili a una persona con mezzi ragionevoli sono dati **pseudonimizzati**, quindi ancora personali, non anonimi.

**Prove.** Misurate su 13 file consecutivi, dal 31/08 al 17/09/2026: 21.531 sessioni, 128 sedi. Ogni test è confrontato con un'ipotesi nulla in cui i valori di `LOGINCOUNT` sono mescolati a caso (seed 42).

| Test | Previsione se è un contatore per utente | Reale | Nulla |
|---|---|---|---|
| T2 · ordine nel tempo | Nella stessa sede e lingua, tra due valori che differiscono di 1-3, il più alto arriva dopo | **92,8%** (23.930/25.790) | 49,8% |
| T1 · continuità tra giorni | Un valore di oggi riappare domani nella stessa sede e lingua, aumentato di 0-5 | **35,8%** | 11,3% |
| T3 · esclusione dell'ipotesi "contatore di sede" | Se fosse un contatore della sede, dentro la sede crescerebbe sempre | cresce solo nel **49%** dei passi (63 sedi) | – |
| Individuazione | Sessioni uniche su giorno, orario al secondo, sede e lingua | **98,8%** | – |
| Correzione | Sessioni uniche su giorno, ora, municipio e lingua | **4,0%** | – |

Spike precedente (01/01 e 02/04/2026, 1.803 sessioni): 270 coppie (v, v+1) nella stessa sede e lingua contro 1 nel confronto casuale.

**Cosa NON affermiamo:**
- non conosciamo la definizione ufficiale di `LOGINCOUNT`: la nostra è l'unica spiegazione coerente con i tre test, non una conferma dell'ente;
- non abbiamo identificato nessuna persona e non mostriamo traiettorie individuali, solo misure aggregate;
- non sosteniamo che il Comune abbia violato la legge: segnaliamo un rischio tecnico e una correzione semplice.

**Correzione proposta:**
1. rimuovere `LOGINCOUNT`, oppure sostituirlo con fasce (1, 2-10, 11-100, >100);
2. orario per fasce di un'ora;
3. municipio al posto del civico;
4. rimisurare: le sessioni uniche passano dal 98,8% al 4,0%.

**In una frase per la giuria:** "Roma pubblica ogni giorno i dati del WiFi pubblico come anonimi. Una colonna non documentata funziona da pseudonimo e permette di seguire la stessa persona tra giorni e luoghi. Watermark la trova da solo, la misura e propone la correzione."

## Traccia ufficiale

Focus: sicurezza dei dati IoT, tutela delle identità digitali nelle smart city, protezione delle infrastrutture critiche. Prototipare un "Privacy & Security Auditor" per infrastrutture smart che analizzi flussi di telemetria o termini d'uso di servizi urbani per identificare pattern di leak di dati personali o scostamenti rispetto alle policy GDPR.

- Dataset principale: CSIRT Italia, allarmi e bollettini (https://www.acn.gov.it/portale/csirt-italia/alert-e-bollettini).
- Dataset integrativi: Garante Privacy, provvedimenti su smart meter, videosorveglianza urbana, dati biometrici nella PA (https://www.garanteprivacy.it/).

Valutazione: 5 criteri da 10 punti (tema, uso dei dati, originalità, funzionalità con IA reale e adattiva, presentazione). L'IA deve stare dentro il prodotto; il vibe coding non conta.

## Fatti verificati sulle fonti

Nessuna delle due fonti pubblica un CSV. Il dataset va costruito da pagine web, prima della gara o all'inizio, poi l'app lavora offline su `data/`.

**CSIRT (ACN)**
- RSS con gli ultimi 50 bollettini: `https://www.acn.gov.it/portale/feedrss/-/journal/rss/20119/723192` (titolo, link, descrizione, data).
- Pagina bollettino `https://www.acn.gov.it/portale/w/<slug>` con campi strutturati: **Tipologia** (multi-valore, es. "Authentication Bypass"), **Impatto sistemico** (es. "Alto (66.41)": classe + punteggio → target supervisionato), prodotti e versioni affette, CVE, data pubblicazione, argomenti.
- La paginazione dell'elenco è JavaScript: `?start=`, `?delta=`, `?page=` non funzionano. Oltre 50 bollettini serve il browser.
- Rischio leakage: il punteggio ACN deriva da CVSS, patch, PoC, diffusione; il testo spesso contiene "gravità critica". Rimuovere quelle frasi prima di addestrare.

**Garante**
- Testo completo in HTML: `https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/<id>`.
- Verificato: docweb 1712680, Provvedimento videosorveglianza 8 aprile 2010 (~60k caratteri). Punto 4.5: le webcam turistiche "devono avvenire con modalità che rendano non identificabili i soggetti ripresi".
- `/temi/videosorveglianza` elenca 6 docweb, `/temi/biometria` 1, `/temi/smart-meter` è 404. La ricerca del sito non restituisce risultati via HTTP semplice: gli ID vanno raccolti a mano.

**Roma WiFi (dataset aggiuntivo scelto)**
- "Sessioni anonimizzate di navigazione web riscontrate nel sistema WiFi di Roma Capitale", Anno 2026, 252 CSV giornalieri. API: `https://dati.comune.roma.it/catalog/api/3/action/package_show?id=de455e3a-d8ef-48a0-a725-832234c7217c`.
- Colonne: `STARTDATE, STARTTIME, ENDDATE, ENDTIME, DURATION, DOWNLOAD, UPLOAD, DOMAIN, LOGINCOUNT, MUNICIPIO, DUG, DUF, CIVICO, LOCALITA, SERVICEPROFILE, DTLN`.
- Spike su 2 giorni (01/01 e 02/04/2026, 1.803 sessioni, 32 sedi):
  - `LOGINCOUNT` non è un contatore di sede (dentro una sede cresce solo nel 35-47% dei casi); si comporta come contatore di login **per utente**: 270 coppie (v, v+1) nella stessa sede e lingua contro 1 nel confronto casuale (v, v+1000). Es. Circonvallazione Trionfale 19: 10116 → 10118 in 10 sessioni in 6 minuti.
  - Conseguenza: pseudonimo persistente, collegabile tra giorni e sedi (172 valori in più sedi lo stesso giorno).
  - Unicità su (orario al secondo, sede, lingua): 99,7%. Su (ora, municipio, lingua): 7,2%.
  - È un'inferenza statistica non confermata dall'ente. Non identificare persone; riportare solo misure aggregate; presentarla come segnalazione costruttiva.

**Scartati**
- Insecam: illegale (art. 615-ter c.p.) e autogol etico.
- Webcam pubbliche (SkylineWebcams, opencctv, ilMeteo): inquadrature larghe, volti ~10-15 px anche a Trevi, quindi già conformi al punto 4.5; inoltre richiedono consenso pubblicitario. Utile solo come slide ("verificate, conformi").
- Open data Napoli: nulla di pertinente (videosorveglianza, sensori, wifi = 0 risultati).

## Design approvato (18/09/2026)

Prodotto: **Watermark, auditor per il DPO comunale**. Percorso demo:

1. **Dati pubblicati (Roma WiFi)**: rischio re-identificazione sulle colonne reali; test automatico "pseudonimo nascosto" (colonne che si comportano come contatori per utente); correzione (fasce orarie, municipio invece del civico, rimozione `LOGINCOUNT`) e rimisura; mappa hotspot.
2. **Minacce (CSIRT)**: modello TF-IDF + regressione logistica su "Impatto sistemico", applicato ad hotspot, controller WiFi, captive portal.
3. **Norme (Garante)**: passaggi citati alla lettera su anonimizzazione, localizzazione, WiFi pubblico.
4. **Dati**: `scripts/fetch_data.py` (solo stdlib `urllib`, pausa tra richieste) scarica CSIRT (RSS + pagine), Garante (lista docweb), alcuni giorni Roma WiFi in `data/`.

## Codice già scritto (non committato prima di questo handoff)

- `core/privacy.py`: classificazione colonne (identificativo diretto / quasi-identificativo / sensibile, per nome e formato dei valori), rischio prosecutor, k-anonimato con generalizzazione + soppressione, l-diversità, attacco di inferenza Random Forest, dataset sintetico `synthetic_residents` (seed 42).
- `core/text_corpus.py`: TF-IDF con stopword italiane, ricerca coseno, passaggi estrattivi, classificatore testuale, NMF, estrazione CVE/CVSS, tassonomia asset urbani.
- `views/corpus_loader.py`, `views/threats_tab.py`, `views/rules_tab.py`, `views/telemetry_tab.py`: schede Streamlit; `streamlit_app.py` ora ha le schede Minacce, Norme, Telemetria prima di quelle originali.
- Verifiche fatte: `py_compile` OK, `AppTest` sull'intero flusso senza eccezioni, `git diff --check` OK. Bug corretti: regex CVSS che catturava la versione, titolo corpus scelto sulla colonna sbagliata.

## Prossimi passi, in ordine

1. Scrivere `scripts/fetch_data.py` e popolare `data/`.
2. Adattare `corpus_loader` ai campi reali CSIRT (Impatto sistemico come etichetta e punteggio; togliere frasi di gravità dal testo).
3. Aggiungere a `core/privacy.py` il test "pseudonimo nascosto" e la scheda Roma WiFi con prima/dopo.
4. Collegare le tre schede nel percorso demo; congelare; screenshot e CSV di riserva; pitch.

## Identità (aggiunta)

- Nome: **Watermark** (in italiano "filigrana"). Una filigrana è un segno nascosto nella carta, visibile solo in controluce: come `LOGINCOUNT` nei dati "anonimi" di Roma WiFi.
- Logo: griglia 3×3 di record in acquamarina `#1F6B69`, uno in corallo `#A63F2E` (il record che si distingue dagli altri, cioè re-identificabile), su avorio `#F7F3E8` con bordo antracite `#17282B`.
- File: `assets/logo.svg` (segno + nome), `assets/logo_mark.svg`, `assets/logo_mark.png`, `assets/favicon.png`. Collegati in `streamlit_app.py` con `st.logo` e `page_icon`; testi in `core/challenge_config.py`.

## Stato al 18/09/2026 ore 12:30 (interfaccia v2)

**Interfaccia** (`streamlit_app.py` + `app_pages/`), navigazione in alto:
1. **Assistente** (`app_pages/assistente.py`): chat in italiano. `core/assistant.py` riconosce l'intenzione (TF-IDF a n-grammi di caratteri + vicino più simile; soglia % letta dalla frase) e `views/assistant_answers.py` esegue gli strumenti mostrando i passaggi (`st.status(type="step")`). Intenzioni: verifica, correggi, minacce, norme, spiega, rapporto, allarme (testo incollato), aiuto, cerca.
2. **Rapporto per il DPO** (`views/audit_tab.py`): agente `core/audit_agent.py`, cinque controlli, rapporto Markdown scaricabile.
3. **Strumenti avanzati** (`app_pages/avanzate.py`): le schede statistiche precedenti, invariate.

**IA, tutta locale:**
- Modello di impatto CSIRT (`core/threat_model.py`): TF-IDF + regressione logistica su 819 bollettini (777 con impatto: Alto 340, Medio 255, Critico 182). Frasi di gravità, CVSS e anni delle CVE rimossi dal testo. Validazione temporale: addestrato fino al 03/08/2026, testato sui 195 successivi, accuratezza bilanciata 0,74 contro 0,33 della classe più frequente. Senza/con gravità dichiarata: 0,67/0,69. Spiegazione per parola con `explain`.
- Ottimizzatore privacy-utilità (`core/privacy_optimizer.py`): 36 versioni del dataset; rischio = sessioni uniche su tutte le righe; utilità = R² in validazione incrociata di un gradient boosting che stima il traffico. Con soglia 15%: "orario al 3 ore · civico · contatore in fasce", rischio 14,7%, utilità 91%. Risultati salvati in `data/.varianti_*.csv` (esclusi da Git).
- Test pseudonimi (`core/linkability.py`): su 14 giorni LOGINCOUNT 92,8% contro 49,8%.

**LLM opzionale** (`core/llm.py`, `requirements-llm.txt`): spento di default. Si attiva solo con `pip install -r requirements-llm.txt` e `ANTHROPIC_API_KEY`. Modello `claude-opus-5` con fallback lato server su `claude-opus-4-8`. Riceve solo domanda e riassunto aggregato, mai righe del dataset.

**Percorso demo (3 minuti):** Assistente → "Questo dataset è pubblicabile?" → "Perché è un problema?" → "Correggilo sotto il 15%" → "Quali sistemi sono a rischio?" → incollare un allarme CSIRT → "Fammi il rapporto".
Prima del pitch: avviare l'app e fare una volta "Correggilo" per popolare la cache (circa 45 secondi alla prima esecuzione).
