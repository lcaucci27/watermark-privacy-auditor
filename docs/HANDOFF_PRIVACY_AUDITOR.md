# Handoff · Segnale Privacy & Security Auditor

Stato al 18/09/2026, tappa di Napoli. Keyword sorteggiata: **privacy**. Tempo totale di sviluppo: circa 7 ore, con congelamento delle funzioni 90 minuti prima della consegna.

Istruzioni per Claude Code: leggi prima `CLAUDE.md`, poi questo file, poi `git status`. Le decisioni sotto sono già state approvate o sono in attesa di approvazione come indicato: non riaprirle senza un fatto nuovo.

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

## Design proposto (in attesa di approvazione finale)

Prodotto: **Segnale, auditor per il DPO comunale**. Percorso demo:

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
