# Segnale

Baseline Streamlit offline per analizzare dataset tabellari durante il contest. Carica CSV/XLSX, controlla qualità e distribuzioni, addestra modelli locali e restituisce metriche, predizioni, segmenti o anomalie.

## Avvio rapido

### Windows PowerShell

```powershell
git clone https://github.com/lcaucci27/hackathon-ai.git
Set-Location .\hackathon-ai
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\setup.ps1
.\scripts\run.ps1
```

### macOS Bash o zsh

```bash
git clone https://github.com/lcaucci27/hackathon-ai.git
cd hackathon-ai
chmod +x scripts/setup.sh scripts/run.sh
./scripts/setup.sh
./scripts/run.sh
```

Aprire `http://localhost:8501`. Interrompere il server con `Ctrl+C`. La configurazione è verificata con Python 3.12; su macOS, se manca, eseguire `brew install python@3.12`.

## Dove si trova cosa

```text
streamlit_app.py            Interfaccia e flusso della demo
core/
├── challenge_config.py     Nome, testi e messaggi da adattare alla traccia
└── ml_pipeline.py          Preprocessing, modelli, metriche ed esportazione
docs/
├── PRESENTATION_SHEET.md   Decisioni, roadmap, demo e copione del pitch
├── SLIDES_BRIEF.md         Struttura pronta per produrre le sei slide
└── MACOS_SETUP.md          Installazione dettagliata per il collaboratore Mac
scripts/
├── setup.ps1 / run.ps1     Preparazione e avvio su Windows
└── setup.sh / run.sh       Preparazione e avvio su macOS
.streamlit/config.toml      Tema visivo
requirements.txt            Versioni Python riproducibili
CONTRIBUTING.md             Regole di sviluppo e controlli minimi
```

## Cosa modificare domani

1. Compilare `docs/PRESENTATION_SHEET.md` appena viene annunciata la traccia.
2. Aggiornare nome e messaggi in `core/challenge_config.py`.
3. Caricare il dataset e verificare target, schema, valori mancanti e leakage.
4. Scegliere un solo percorso principale: previsione, segmentazione o anomalie.
5. Collegare l'output a una decisione concreta dell'utente.
6. Inserire metriche e screenshot reali in `docs/SLIDES_BRIEF.md`.

Non descrivere correlazioni o feature importance come cause. Le metriche sul test set misurano il comportamento sul campione disponibile, non la validità su popolazioni o periodi diversi.

## Funzioni già disponibili

- classificazione e regressione con Random Forest;
- segmentazione con K-Means;
- rilevazione anomalie con Isolation Forest;
- preprocessing numerico e categorico;
- imputazione dei valori mancanti;
- valutazione su test set separato;
- esportazione di risultati e modello;
- dataset offline per provare ogni percorso.

## Verifica

PowerShell:

```powershell
.\.venv\Scripts\python.exe -m py_compile .\streamlit_app.py .\core\challenge_config.py .\core\ml_pipeline.py
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -c "from streamlit.testing.v1 import AppTest; app = AppTest.from_file('streamlit_app.py').run(timeout=120); print(app.exception)"
git diff --check
```

macOS:

```bash
.venv/bin/python -m py_compile streamlit_app.py core/challenge_config.py core/ml_pipeline.py
.venv/bin/python -m pip check
.venv/bin/python -c "from streamlit.testing.v1 import AppTest; app = AppTest.from_file('streamlit_app.py').run(timeout=120); print(app.exception)"
git diff --check
```

Il test dell'interfaccia deve stampare una lista vuota.

## Confini della soluzione

Streamlit resta adatto finché il flusso consiste in upload, filtri, grafici, training locale, acquisizione singola da camera o aggiornamenti periodici. Valutare un backend separato solo per video continuo, WebSocket a bassa latenza, hardware bidirezionale, task persistenti o molti utenti concorrenti. La matrice completa è in `docs/PRESENTATION_SHEET.md`.

Dataset riservati, credenziali e configurazioni personali non vanno committati. Salvare i dati privati della gara in `data/private/`, già esclusa da Git.
