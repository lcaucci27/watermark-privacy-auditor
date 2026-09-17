# Regole di sviluppo

## Confini dei moduli

- `streamlit_app.py` compone l'interfaccia e collega le azioni dell'utente alle funzioni di dominio.
- `core/challenge_config.py` contiene testi e identità da adattare alla traccia.
- `core/ml_pipeline.py` contiene preprocessing, modelli, metriche e serializzazione.
- Le nuove pipeline autonome vanno in `core/`, per esempio `text_pipeline.py`, `vision_pipeline.py` o `timeseries_pipeline.py`.
- I materiali per demo e presentazione vanno in `docs/`; gli script operativi vanno in `scripts/`.

Estrarre una funzione quando una regola deve essere testata senza Streamlit, quando un blocco viene usato due volte o quando il nome della funzione rende il flusso più leggibile del codice inline.

## Nomi e lingua

- Identificatori Python in inglese, coerenti con pandas e scikit-learn.
- Testi visibili e messaggi di errore in italiano.
- Commenti e docstring in italiano.
- Nomi specifici: `target_column` è preferibile a `value`; `test_predictions` è preferibile a `result` quando il contesto non è immediato.

## Commenti utili

Un commento spiega una ragione, un vincolo o un caso limite che il codice non rende evidente.

```python
# Lo split stratificato richiede almeno due righe per classe; con classi singole
# manteniamo lo split casuale per restituire un errore interpretabile dal modello.
stratify = y if y.value_counts().min() >= 2 else None
```

Non tradurre ogni istruzione in prosa. Aggiornare o rimuovere il commento quando cambia il comportamento.

## Regole per la GUI

- Ogni controllo deve dichiarare quale dato modifica.
- Ogni errore deve indicare quale input correggere.
- Ogni metrica deve specificare dataset o campione a cui si riferisce.
- Distinguere correlazione, importanza predittiva e causalità.
- Preferire elementi Streamlit nativi; usare CSS solo quando il tema non basta.
- Non usare `use_container_width`; usare `width="stretch"` o `width="content"`.
- Non aggiungere dipendenze remote al percorso principale.

## Verifica minima

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

Per una modifica alla pipeline, eseguire almeno un dataset coerente con il caso cambiato. Per una modifica alla GUI, controllare il percorso interessato da caricamento a download.

Una modifica è pronta quando il comportamento è verificato, i messaggi indicano limiti reali, il percorso offline resta disponibile e il diff non include file privati, cache o dati della gara.
