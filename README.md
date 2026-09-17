# Segnale

Segnale è una baseline Streamlit per analizzare dataset tabellari senza servizi remoti. Carica CSV/XLSX, mostra qualità e distribuzioni, addestra modelli locali e rende disponibili metriche, importanza delle variabili, predizioni e anomalie.

## Funzioni disponibili

- classificazione e regressione con Random Forest;
- segmentazione con K-Means;
- rilevazione anomalie con Isolation Forest;
- preprocessing di variabili numeriche e categoriche;
- gestione dei valori mancanti;
- valutazione su test set separato;
- esportazione di risultati e modello;
- dataset offline per provare ogni percorso.

## Struttura

```text
app.py                 Interfaccia Streamlit e flussi di analisi
challenge_config.py    Testi da adattare alla traccia
ml_pipeline.py         Preprocessing, modelli e metriche
.streamlit/config.toml Tema visivo
PRESENTATION_SHEET.md  Decisioni del team, demo e pitch
SLIDES_BRIEF.md        Struttura e testi richiesti per le slide
CONTRIBUTING.md        Regole di modularità, commenti e verifica
setup.ps1              Creazione dell'ambiente riproducibile
run.ps1                Avvio dell'app con l'interprete della repo
setup.sh                Creazione dell'ambiente su macOS
run.sh                  Avvio dell'app su macOS
MACOS_SETUP.md          Handoff completo per il collaboratore Mac
requirements.txt       Dipendenze runtime
```

## Installazione per un collaboratore

Il repository contiene tutto ciò che serve per eseguire l’app, tranne Python e le dipendenze scaricate da `pip`. Dopo aver accettato l’invito GitHub:

```powershell
git clone https://github.com/lcaucci27/hackathon-ai.git
Set-Location .\hackathon-ai
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup.ps1
.\run.ps1
```

La configurazione è verificata con Python 3.12. Dataset riservati, credenziali e istruzioni personali per gli strumenti di sviluppo devono essere trasferiti fuori da Git e non sono necessari per avviare la baseline.

Su macOS usare invece:

```bash
git clone https://github.com/lcaucci27/hackathon-ai.git
cd hackathon-ai
chmod +x setup.sh run.sh
./setup.sh
./run.sh
```

Le istruzioni complete sono in `MACOS_SETUP.md`.

## Avvio con PowerShell

```powershell
py -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r .\requirements.txt
python -m streamlit run .\app.py
```

Se l’attivazione è bloccata:

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
.\.venv\Scripts\python.exe -m streamlit run .\app.py
```

Aprire `http://localhost:8501`. Interrompere il server con `Ctrl+C`.

## Adattamento alla traccia

1. Compilare la sezione “Scheda della traccia” in `PRESENTATION_SHEET.md`.
2. Modificare nome, descrizione e messaggi in `challenge_config.py`.
3. Caricare il dataset e controllare schema, target, valori mancanti e leakage.
4. Scegliere un solo percorso principale: previsione, segmentazione o anomalie.
5. Collegare l’output a una decisione dell’utente finale.
6. Conservare un file piccolo e noto per la demo di riserva.

Dopo la demo, compilare `SLIDES_BRIEF.md` con metriche e screenshot reali prima di generare la presentazione.

Non descrivere correlazioni o feature importance come cause. Le metriche sul test set misurano il comportamento sul campione disponibile; non dimostrano validità su popolazioni o periodi diversi.

## Verifica

```powershell
python -m py_compile .\app.py .\challenge_config.py .\ml_pipeline.py
python -m pip check
```

Per il controllo in-process dell’interfaccia:

```powershell
python -c "from streamlit.testing.v1 import AppTest; app = AppTest.from_file('app.py').run(timeout=120); print(app.exception)"
```

## Scelta del framework

Streamlit resta il framework principale perché il punteggio dipende da uso dei dati, funzionalità e presentazione, non dalla complessità del frontend. La migrazione è giustificata solo se la traccia richiede streaming video continuo, WebSocket a bassa latenza, controllo hardware bidirezionale o un’interfaccia pubblica multiutente. La matrice decisionale è in `PRESENTATION_SHEET.md`.
