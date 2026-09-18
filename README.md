# Watermark

Watermark aiuta il DPO di un Comune a decidere se un dataset urbano può essere pubblicato o deve restare nell'uso amministrativo. Analizza sia righe di eventi, come le sessioni del WiFi di Roma Capitale, sia tabelle aggregate, come l'affollamento WiFi di Bologna. Misura unicità, celle piccole e collegabilità con un secondo dataset, poi produce una versione protetta e un rapporto verificabile.

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
2. **Incrocia** esplicita la conoscenza ausiliaria e conta i candidati prodotti dal secondo file.
3. **Fai una domanda** interpreta richieste in italiano ed esegue i controlli adatti.
4. **Rapporto** svolge l’audit completo e genera un file per il DPO.

Il dato centrale è semplice: conoscere giorno, ora, sede e lingua rende distinguibile il 99,5% delle sessioni del campione. Una riga distinguibile o collegabile non equivale a una persona identificata: il secondo passaggio richiede un dataset o una conoscenza che porti davvero un'identità. `LOGINCOUNT`, presente nel CSV ma non documentato dal catalogo, giustifica una richiesta di chiarimento all’ente, non l’attribuzione delle righe a persone reali.

La pagina **Incrocia** include già due coppie ufficiali, senza upload obbligatorio: utenti/login per giorno e zona del Comune di Milano, e affollamento/anagrafica aree WiFi del Comune di Bologna. L’upload resta disponibile per altri enti. Roma non viene abbinata a un secondo dataset non documentato.

## IA locale opzionale

Senza Ollama l’app resta utilizzabile con modelli scikit-learn e risposte calcolate. Per aggiungere ricerca semantica e riscrittura locale:

```powershell
ollama pull bge-m3
ollama pull qwen2.5:3b
python scripts/setup_local_ai.py
python scripts/precompute_embeddings.py
```

`watermark-dpo:latest` è una configurazione locale specializzata, non un fine-tuning dei pesi. Il modello linguistico riceve soltanto la domanda e risultati aggregati; le righe del file non vengono incluse nel prompt. La risposta usa uno schema JSON e viene scartata se introduce numeri assenti dai risultati.

Per ripetere il confronto locale:

```powershell
python scripts/evaluate_local_llm.py watermark-dpo:latest qwen2.5:3b qwen2.5:7b
```

Nel test semantico incluso, tutti hanno superato 4 casi su 4 con gli stessi guardrail; il 3B base e la variante Watermark hanno richiesto circa 52 secondi complessivi, il 7B circa 187. I tempi dipendono dall'hardware.

## Materiali di prodotto e pitch

- `docs/MUNICIPAL_DATASET_SCENARIOS.md`: coppie e triple comunali, con limiti interpretativi.
- `docs/BUSINESS_PLAN.md`: committente, prezzi ipotetici, mercato e KPI del pilot.
- `docs/PRODUCT_ARCHITECTURE.md`: passaggio da demo locale a servizio multi-ente.
- `docs/SLIDES_BRIEF.md`: sei slide, prompt visuali e discorso cronometrato a tre minuti.

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
- La classificazione automatica di colonne e granularità deve essere confermata dal titolare del dato.
- Il prodotto supporta la decisione del DPO; non certifica da solo l'anonimato.
