# Installazione su macOS

Il repository contiene codice, tema, script e dataset di esempio. Servono Git, Python 3.12 e una connessione soltanto durante l’installazione delle dipendenze.

## 1. Accettare l’invito e clonare

```bash
git clone https://github.com/lcaucci27/watermark-privacy-auditor.git
cd watermark-privacy-auditor
```

Se il repository privato non è accessibile, verificare di aver accettato l’invito con lo stesso account usato da Git.

## 2. Verificare Python

```bash
python3.12 --version
```

Se il comando non esiste e Homebrew è già installato:

```bash
brew install python@3.12
```

L’installazione di Homebrew non è richiesta se Python 3.12 è già disponibile.

## 3. Preparare l’ambiente

```bash
chmod +x scripts/setup.sh scripts/run.sh
./scripts/setup.sh
```

Lo script crea `.venv`, installa le versioni presenti in `requirements.txt` e verifica conflitti tra pacchetti.

## 4. Avviare l’app

```bash
./scripts/run.sh
```

Aprire `http://localhost:8501`. Interrompere il server con `Ctrl+C`.

## Avvio manuale equivalente

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip check
python -m streamlit run streamlit_app.py
```

## Verifica prima della gara

```bash
.venv/bin/python -m py_compile streamlit_app.py core/challenge_config.py core/ml_pipeline.py
.venv/bin/python -c "from streamlit.testing.v1 import AppTest; app = AppTest.from_file('streamlit_app.py').run(timeout=120); print(app.exception)"
git status --short
```

Il test deve stampare una lista vuota per le eccezioni. `git status --short` deve restare vuoto dopo un clone pulito.

## Cosa non serve trasferire

- `.venv`: contiene percorsi specifici del computer che l’ha creato;
- chiavi API o `.env`: il percorso principale non li usa;
- cartelle cache Python;
- dataset privati non necessari alla baseline.

I dataset riservati ricevuti durante la gara vanno trasferiti fuori da Git e salvati in `data/private/`.
