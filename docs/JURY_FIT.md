# Watermark: corrispondenza con i criteri della giuria

Fonte dei criteri: [Guida ufficiale AI2B](https://ai2b.games/regolamento/guida) e [Regolamento, art. 8 bis e 8 ter](https://ai2b.games/regolamento).

La giuria assegna fino a 10 punti per ciascuna delle cinque aree. L'obiettivo non è mostrare tutte le funzioni, ma una prova memorabile per criterio.

## 1. Aderenza al tema

**Cosa chiede la giuria:** coerenza con la keyword e bisogno reale del territorio.

**Nostra prova:** un Comune deve decidere se un flusso di telemetria smart-city dichiarato anonimo sia pubblicabile. Watermark misura individuazione, potenziale correlabilità e rischio cumulativo prima della diffusione.

**Da mostrare:** pagina “Verifica”, badge “Da correggere”, 99,5% di sessioni individuabili.

**Claim:** “Aiutiamo il DPO comunale a fermare una pubblicazione rischiosa prima che diventi un incidente privacy.”

## 2. Utilizzo dei dati

**Cosa chiede la giuria:** il dataset deve essere il cuore della logica; occorre estrarre valore nascosto.

**Nostra prova:** il sistema legge i CSV ufficiali, ricostruisce timestamp e sedi, misura il k-anonimato, individua automaticamente colonne intere ad alta cardinalità e verifica il loro ordinamento temporale. LOGINCOUNT è presente nei dati ma assente dalla documentazione del catalogo.

**Prove quantitative principali:**

- giorno e orario al secondo isolano il 96,1% delle sessioni;
- giorno, ora, sede e lingua isolano il 99,5%;
- ordine di LOGINCOUNT: 92,7% medio su 13 giorni contro 49,5% permutato;
- Wilcoxon appaiato sui giorni: p = 0,00012;
- continuità tra giorni consecutivi: 32,1% contro 9,3% permutato;
- test a permutazione: p ≈ 0,002 con 500 permutazioni;
- solo 7 sedi su 64 hanno un forte trend crescente: non è spiegato come semplice contatore di sede.

**Da mostrare:** curva “informazioni conosciute → sessioni individuabili” e pannello “Validazione statistica”.

## 3. Originalità e innovazione

**Cosa chiede la giuria:** idea distinta e uso creativo dell'AI.

**Nostra prova:** Watermark non cerca soltanto nomi, e-mail o codici fiscali. Cerca “filigrane” statistiche: colonne apparentemente innocue che conservano memoria e possono rendere collegabili le righe. Il nome del prodotto rappresenta precisamente questa funzione.

**Elemento memorabile:** il campo non documentato viene scoperto dai valori e dal tempo, non da una blacklist di nomi di colonna.

## 4. Funzionalità, AI e integrazione

**Cosa chiede la giuria:** flusso funzionante, UX fluida, AI reale e adattiva.

**Nostro flusso completo:**

```text
CSV pubblico → preprocessing → scoperta del rischio → validazione statistica
→ ricerca semantica su CSIRT/Garante → correzione → CSV e rapporto scaricabili
```

**Dove si trova l'AI:**

- il rilevatore analizza automaticamente tutte le colonne intere candidate, non soltanto LOGINCOUNT;
- il modello di utilità apprende quanto traffico resta stimabile nelle 36 trasformazioni privacy;
- il classificatore CSIRT stima l'impatto dei bollettini su dati temporalmente successivi;
- l'assistente locale interpreta la domanda e seleziona gli strumenti;
- la ricerca semantica recupera passaggi pertinenti del Garante con fonte visibile.

Il classificatore CSIRT è valutato con separazione temporale: addestramento fino al 3 agosto 2026, test sui 195 bollettini successivi, accuratezza bilanciata 0,743 contro 0,333 della classe più frequente. Questa è la metrica ML da citare quando la giuria domanda dove sia l'AI.

**Rischio da evitare nel pitch:** presentare come AI un semplice p-value. La statistica prova la falla; l'AI orchestra la scoperta, confronta correzioni e collega fonti diverse.

## 5. Qualità della presentazione

**Cosa chiede la giuria:** chiarezza, pitch breve e risposte tecniche/business.

**Percorso consigliato, massimo cinque minuti:**

1. **Problema, 30 secondi:** aprire il CSV ufficiale e indicare LOGINCOUNT non documentato.
2. **Prova, 60 secondi:** mostrare 99,5%, 92,7% contro 49,5% e continuità 32,1% contro 9,3%.
3. **Prodotto, 90 secondi:** eseguire “Verifica”, mostrare una domanda all'assistente e generare il rapporto.
4. **Azione, 45 secondi:** scaricare il CSV aggregato con k ≥ 5.
5. **Limite, 20 secondi:** la semantica di LOGINCOUNT deve essere confermata da Roma Capitale; nessuna persona è stata identificata.

## Risposta pronta alla domanda più difficile

**“Avete dimostrato che LOGINCOUNT identifica l'utente?”**

No. Abbiamo dimostrato tre proprietà più limitate ma operative: non è casuale, non si comporta come un contatore della sede e conserva continuità nel tempo molto oltre l'atteso sotto permutazione. Questo basta per sospendere il campo e chiedere il data dictionary; non basta per attribuire sessioni a persone reali.

## Valutazione onesta dello stato

| Criterio | Stato | Rischio residuo |
|---|---|---|
| Tema | Forte | Esplicitare subito utente e decisione |
| Dati | Molto forte | Non sovrainterpretare LOGINCOUNT |
| Originalità | Forte | Far vedere la scoperta automatica, non solo raccontarla |
| Funzionalità/AI | Buono | Mostrare almeno una funzione ML adattiva durante la demo |
| Presentazione | Buono | Cronometrare e tenere gli strumenti avanzati fuori dal percorso principale |
