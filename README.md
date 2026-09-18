# Watermark

Watermark aiuta il DPO di un Comune a decidere se un dataset urbano può essere pubblicato. Nel caso dimostrativo analizza le sessioni del WiFi pubblico di Roma Capitale, misura quanto siano individuabili, segnala campi con memoria temporale e produce una versione aggregata con gruppi di almeno cinque sessioni.

Tutti i controlli essenziali girano in locale. L’app usa i dati di Roma Capitale, i bollettini CSIRT Italia e i provvedimenti del Garante privacy già inclusi in `data/`.

## Avvio

Richiede Python 3.12.

### Windows PowerShell

```powershell
git clone https://github.com/lcaucci27/hackathon-ai.git
Set-Location .\hackathon-ai
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\setup.ps1
.\scripts\run.ps1
```

### macOS

```bash
git clone https://github.com/lcaucci27/hackathon-ai.git
cd hackathon-ai
chmod +x scripts/setup.sh scripts/run.sh
./scripts/setup.sh
./scripts/run.sh
```

Aprire `http://localhost:8501`.

## Percorso dimostrativo

1. **Verifica** mostra l’esito, le prove più leggibili e la correzione consigliata.
2. **Fai una domanda** interpreta richieste in italiano ed esegue i controlli adatti.
3. **Rapporto** svolge l’audit completo e genera un file per il DPO.

Il dato centrale è semplice: conoscere giorno, ora, sede e lingua rende individuabile il 99,5% delle sessioni del campione. `LOGINCOUNT`, presente nel CSV ma non documentato dal catalogo, conserva memoria nel tempo; questo giustifica la sospensione del campo e una richiesta di chiarimento all’ente, non l’attribuzione delle righe a persone reali.

## IA locale opzionale

Senza Ollama l’app resta utilizzabile con modelli scikit-learn e risposte calcolate. Per aggiungere ricerca semantica e riscrittura locale:

```powershell
ollama pull bge-m3
ollama pull qwen2.5:3b
python scripts/precompute_embeddings.py
```

`qwen2.5:7b` è supportato come alternativa più lenta. Il modello linguistico riceve soltanto la domanda e risultati aggregati; le righe del file non vengono incluse nel prompt.

## Verifica tecnica

```powershell
python -m compileall -q core views app_pages scripts streamlit_app.py
python -m pip check
python -m pytest -q
git diff --check
```

La logica di dominio è in `core/`, le pagine Streamlit in `app_pages/`, le viste condivise in `views/` e i materiali del progetto in `docs/`.

## Limiti

- La semantica di `LOGINCOUNT` deve essere confermata da Roma Capitale.
- Un bollettino CSIRT semanticamente pertinente non dimostra che la versione installata sia vulnerabile.
- Le misure descrivono il campione disponibile; nessuna persona viene cercata o identificata.
