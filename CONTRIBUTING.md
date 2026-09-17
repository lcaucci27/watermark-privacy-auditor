# Regole di sviluppo

## Confini dei moduli

- `app.py` compone l’interfaccia e collega le azioni dell’utente alle funzioni di dominio.
- `challenge_config.py` contiene testi e identità da adattare alla traccia.
- `ml_pipeline.py` contiene preprocessing, modelli, metriche e serializzazione.
- Nuove pipeline autonome vanno in moduli dedicati, per esempio `text_pipeline.py`, `vision_pipeline.py` o `timeseries_pipeline.py`.
- La presentazione non deve contenere formule di preprocessing o addestramento replicate dalla pipeline.

Estrarre una funzione quando una regola di dominio deve essere testata senza Streamlit, quando lo stesso blocco viene usato due volte o quando il nome della funzione rende il flusso più leggibile del codice inline.

## Nomi e lingua

- Identificatori Python in inglese, coerenti con pandas e scikit-learn.
- Testi visibili e messaggi di errore in italiano.
- Commenti e docstring in italiano.
- Nomi specifici: `target_column` è preferibile a `value`; `test_predictions` è preferibile a `result` quando il contesto non è immediato.

## Commenti utili

Un commento deve spiegare una ragione, un vincolo o un caso limite che il codice non rende evidente.

Commento utile:

```python
# Lo split stratificato richiede almeno due righe per classe; con classi singole
# manteniamo lo split casuale per restituire un errore interpretabile dal modello.
stratify = y if y.value_counts().min() >= 2 else None
```

Commento inutile:

```python
# Divide i dati
X_train, X_test = train_test_split(X, y)
```

Non usare commenti per tradurre ogni istruzione in prosa. Aggiornare o rimuovere un commento quando cambia il comportamento che descrive.

## Regole per la GUI

- Un controllo deve avere un’etichetta che descriva il dato modificato.
- Un errore deve indicare quale input correggere.
- Una metrica deve specificare dataset o campione a cui si riferisce.
- Una spiegazione deve distinguere correlazione, importanza predittiva e causalità.
- Preferire elementi Streamlit nativi; usare CSS solo su classi stabili generate con `key`.
- Non usare `use_container_width`; usare `width="stretch"` o `width="content"`.
- Non aggiungere dipendenze remote al percorso principale.

## Verifica minima

```powershell
.\.venv\Scripts\python.exe -m py_compile .\app.py .\challenge_config.py .\ml_pipeline.py
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -c "from streamlit.testing.v1 import AppTest; app = AppTest.from_file('app.py').run(timeout=120); print(app.exception)"
git diff --check
```

Per una modifica a una pipeline, eseguire almeno un dataset coerente con il caso cambiato. Per una modifica alla GUI, controllare il percorso interessato da caricamento a download.

Su macOS gli stessi controlli usano l’interprete della repository:

```bash
.venv/bin/python -m py_compile app.py challenge_config.py ml_pipeline.py
.venv/bin/python -m pip check
.venv/bin/python -c "from streamlit.testing.v1 import AppTest; app = AppTest.from_file('app.py').run(timeout=120); print(app.exception)"
git diff --check
```

## Criterio di completamento

Una modifica è pronta quando il comportamento è verificato, i messaggi indicano limiti reali, il percorso offline resta disponibile e il diff non include file privati, cache o dati della gara.
