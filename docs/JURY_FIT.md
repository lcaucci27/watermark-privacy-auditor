# Mappa interna sui 50 punti della giuria

Questo file guida refinement, demo e risposte. Non trasformarlo in una slide con i cinque criteri: la giuria deve vedere le prove nel racconto, non una checklist.

## Aderenza al tema

Bisogno reale: un Comune deve pubblicare dati utili senza esporre combinazioni riconoscibili. Il contesto territoriale è dimostrato con fonti ufficiali di Roma, Milano e Bologna. Il decisore è il DPO con responsabile open data e RTD.

Prova da mostrare: schermata Roma con il 99,5% di sessioni distinguibili e correzione proposta.

Frase: “Watermark controlla un open data prima che il Comune lo renda pubblico.”

## Utilizzo dei dati

I CSV alimentano direttamente ogni decisione. Watermark ricostruisce tempo e luogo, misura combinazioni rare, scopre il comportamento temporale di `LOGINCOUNT`, distingue eventi da aggregati e collega serie diverse.

Prove:

- Roma: 99,5% delle sessioni distinguibili con giorno, ora, sede e lingua.
- Milano: 12.205 righe su 13.793 collegate una a una fra utenti e login usando giorno e zona.
- Bologna: 5.000 celle orarie collegate all’anagrafica di 76 aree tramite `codice_zona ↔ id`.
- Gravità CSIRT: TF-IDF ottiene 0,743 di accuratezza bilanciata contro 0,685 degli embedding.

Interpretazione da mantenere: un record raro o collegato non equivale automaticamente a una persona identificata.

## Originalità e innovazione

L’elemento distintivo non è un chatbot. Watermark cerca filigrane statistiche e rischi di composizione che restano dopo la rimozione di nomi ed e-mail. Il secondo dataset rende esplicita la conoscenza dell’attaccante. Il motore adatta il test a eventi individuali, celle aggregate e colonne equivalenti con nomi diversi.

Prova da mostrare: schermata `Incrocia` su Milano e, nelle domande, mapping Bologna `codice_zona ↔ id`.

## Funzionalità e integrazione

Percorso funzionante:

```text
selezione fonte
controllo privacy
incrocio con secondo dataset
correzione o soppressione
rapporto scaricabile
spiegazione locale opzionale
```

L’IA ha ruoli verificabili:

- TF-IDF classifica l’impatto CSIRT perché supera gli embedding nel test temporale.
- BGE-M3 recupera passaggi semanticamente vicini nelle fonti.
- Qwen 2.5 3B riscrive risultati già calcolati in JSON; guardrail controllano numeri e citazioni.
- Il fallback deterministico mantiene l’app utilizzabile senza Ollama.

Prova da mostrare: badge dell’esito, confronto Milano già configurato e download della valutazione. Tenere l’assistente come screenshot di supporto, non come centro della demo.

## Qualità della presentazione

Il pitch dura 180 secondi. Ogni slide ha una tesi, una prova visiva e una frase operativa. Gli screenshot reali sostituiscono una demo live fragile. Il deck include problema, prova Roma, architettura IA, incrocio Milano, portabilità e proposta commerciale.

I placeholder e le istruzioni per Claude PowerPoint sono in `docs/CLAUDE_POWERPOINT_PROMPTS.md`; la sequenza degli screenshot è in `docs/DEMO_SCREENSHOT_PLAN.md`.

## Committente e utilità aziendale

Committente contrattuale: Comune, Città metropolitana, società in-house o gestore di servizio pubblico. Sponsor: DPO. Buyer economico: Direzione innovazione, Segreteria generale o RTD. Utenti: DPO, open data officer e data steward.

Utilità:

- impedire una pubblicazione rischiosa prima che diventi un incidente;
- ridurre verifiche manuali ripetitive;
- produrre una motivazione riutilizzabile nell’istruttoria;
- applicare la stessa policy a più uffici e cataloghi;
- mantenere file e modelli nel perimetro tecnico dell’ente.

Offerta iniziale: pilot di 8–12 settimane su tre dataset, €12–25 mila, con audit, policy pack e integrazione. Prezzo da validare con procurement e interviste.

## Domande difficili

**Avete identificato persone?** No. Misuriamo distinguibilità e collegabilità sotto ipotesi dichiarate.

**È un fine-tuning?** No. Qwen 2.5 3B usa istruzioni di dominio, schema JSON, retry e guardrail. Un LoRA richiede prima casi annotati da DPO.

**È hardcoded sui tre Comuni?** No. I cataloghi e i mapping sono adattatori; granularità, ruoli delle colonne, k-anonimato, small-cell check e collegabilità vivono nel motore comune.

**Serve un database?** Non per la demo locale. Il prodotto multi-ente richiede PostgreSQL per utenti, policy versionate, approvazioni e audit trail.
