# Watermark

Watermark helps a municipality's Data Protection Officer (DPO) decide whether an urban dataset can be published or must stay in administrative use. It analyses both event-level rows, such as the Roma Capitale WiFi sessions, and aggregated tables, such as the Bologna WiFi crowding data. It measures uniqueness, small cells and linkability with a second dataset, then produces a protected version and a verifiable report.

All essential checks run locally. The app uses the Roma Capitale data, the CSIRT Italia bulletins and the Italian Data Protection Authority (Garante) rulings already included in `data/`.

The interface and the datasets are in Italian.

## Context

Built by a team of two at the Campionato Universitario AI 2026 (AI University Championship), Naples stage, 18 September 2026. Development took about seven hours, with features frozen 90 minutes before the deadline. The drawn keyword was **privacy**. The competition constraint was a product that runs offline, with no paid API and no keys. The project was presented as a live demo.

**Team:** Luigi Caucci ([@lcaucci27](https://github.com/lcaucci27)) and [@luckybros](https://github.com/luckybros).

## Client and stack

**Client:** a municipality acting as data controller. In the demo the case is Roma Capitale, which publishes the data of its public WiFi service DigitRoma. The operational user is the DPO, supported by the open data office and the cybersecurity contact. The decision supported is whether to publish a dataset and with which corrections. The product is not meant for citizens or law enforcement.

| Layer | Technology | Role |
|---|---|---|
| Frontend | Streamlit 1.64.0, Plotly 6.9.0 | Web interface, charts, session state |
| Backend | Python 3.12, `core/` modules in the same process as Streamlit | Privacy rules, linkability, audit and guardrails |
| Data | pandas 2.3.3, numpy 2.5.3, openpyxl 3.1.5 | CSV/XLSX loading and transformations |
| Models | scikit-learn 1.9.1 | TF-IDF, CSIRT impact classification, anomalies, clustering |
| Local AI (optional) | Ollama with `bge-m3` and `qwen2.5:3b` | Semantic search and rewriting of already computed results |
| Persistence | CSV files in `data/` | No database, no cloud service |

Frontend and backend share one process to get a single start command and no network dependency. In production, the `core/` logic would be exposed as a separate API.

## Getting started

Requires Python 3.12.

### Windows PowerShell

```powershell
git clone https://github.com/lcaucci27/watermark-privacy-auditor.git
Set-Location .\watermark-privacy-auditor
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\setup.ps1
.\scripts\run.ps1
```

### macOS

```bash
git clone https://github.com/lcaucci27/watermark-privacy-auditor.git
cd watermark-privacy-auditor
chmod +x scripts/setup.sh scripts/run.sh
./scripts/setup.sh
./scripts/run.sh
```

Open `http://localhost:8501`.

## Demo path

1. **Verifica** (Check) shows the outcome, the most readable evidence and the recommended correction.
2. **Incrocia** (Cross-check) makes the auxiliary knowledge explicit and counts the candidates produced by the second file.
3. **Assistente** (Assistant) interprets requests in Italian, runs the matching checks and lets the user reset the conversation.
4. **Audit completo** (Full audit) runs all checks and generates a file for the DPO.

The central finding is simple: knowing day, time, venue and language makes 99.5% of the sessions in the sample distinguishable. A distinguishable or linkable row does not mean an identified person: the second step needs a dataset or knowledge that actually carries an identity. `LOGINCOUNT`, present in the CSV but not documented in the catalogue, justifies a request for clarification to the data owner, not the attribution of rows to real people.

The **Incrocia** page already includes two official pairs, with no mandatory upload: users/logins by day and zone from the Municipality of Milan, and WiFi crowding/area registry from the Municipality of Bologna. Upload remains available for other municipalities. Rome is not paired with an undocumented second dataset.

The demo samples are large enough to make the comparison visible without slowing the presentation. Milan uses the two complete exports available, with 13,793 and 13,930 rows; Bologna uses 5,000 observations and the full registry of 76 areas. In the Milan cross-check, 12,638 rows match at least one record and 12,205 match exactly one. In the Bologna one, all 5,000 observations receive exactly one area.

## Optional local AI

Without Ollama the app stays usable with scikit-learn models and computed answers. To add semantic search and local rewriting:

```powershell
ollama pull bge-m3
ollama pull qwen2.5:3b
python scripts/setup_local_ai.py
python scripts/precompute_embeddings.py
```

`watermark-dpo:latest` is a specialised local configuration, not a fine-tuning of the weights. The language model receives only the question and aggregated results; the file rows are not included in the prompt. The answer follows a JSON schema and is discarded if it introduces numbers absent from the results.

In the interface the user only chooses between **Watermark · local chatbot** and **Computed results only**. The Qwen 3B base and 7B variants remain in the benchmark script only: they add no product features. BGE-M3 handles search by meaning and TF-IDF handles alert classification; neither is a chatbot.

To repeat the local comparison:

```powershell
python scripts/evaluate_local_llm.py watermark-dpo:latest qwen2.5:3b qwen2.5:7b
```

In the included semantic test, all variants passed 4 of 4 cases with the same guardrails; the 3B base and the Watermark variant took about 52 seconds in total, the 7B about 187. Timings depend on the hardware.

## Product documentation

All in Italian:

- `docs/MUNICIPAL_DATASET_SCENARIOS.md`: municipal pairs and triples, with interpretation limits.
- `docs/BUSINESS_PLAN.md`: client, hypothetical prices, market and pilot KPIs.
- `docs/PRODUCT_ARCHITECTURE.md`: path from local demo to multi-municipality service.

## Repository structure

```text
streamlit_app.py   navigation and configuration
app_pages/         four essential user flows
views/             shared Streamlit components
core/              rules, models, audit and source catalogue
scripts/           reproducible data acquisition and local setup
data/              public samples and versioned offline caches
tests/             regressions for the engine and the demo cross-checks
docs/              sources, architecture, business plan and pitch
assets/            logo and favicon
```

Municipal sources and linkage keys live in `core/municipal_catalog.py`, separate from the UI. To add a municipality, register a source and, if available, the key mapping; the granularity, small-cell and linkability checks stay shared.

## Technical verification

```powershell
python -m compileall -q core views app_pages scripts streamlit_app.py
python -m pip check
python -m pytest -q
git diff --check
```

Domain logic is in `core/`, Streamlit pages in `app_pages/`, shared views in `views/` and project materials in `docs/`.

## Limits

- The semantics of `LOGINCOUNT` must be confirmed by Roma Capitale.
- A semantically relevant CSIRT bulletin does not prove that the installed version is vulnerable.
- The measures describe the available sample; no person is searched for or identified.
- The automatic classification of columns and granularity must be confirmed by the data owner.
- The product supports the DPO's decision; it does not certify anonymity on its own.
