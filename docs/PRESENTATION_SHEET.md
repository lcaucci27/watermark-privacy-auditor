# Sheet di preparazione

Questo documento raccoglie le decisioni da prendere dopo l’annuncio della traccia e il materiale da usare nella presentazione. Compilarlo prima di aggiungere funzioni.

## Scheda della traccia

| Campo | Risposta del team |
|---|---|
| Keyword o tema |  |
| Utente principale |  |
| Decisione che deve prendere |  |
| Problema osservabile |  |
| Dataset assegnato |  |
| Unità di analisi |  |
| Target, se disponibile |  |
| Metrica tecnica |  |
| Metrica operativa |  |
| Vincolo più rilevante |  |
| Output mostrato in demo |  |

La frase guida deve contenere soggetto, azione e risultato misurabile:

> Segnale aiuta **[utente]** a **[decisione]** usando **[dataset]**; il risultato viene misurato con **[metrica]**.

Se uno dei quattro campi resta vuoto, l’idea non è ancora pronta per lo sviluppo.

## Scelta del percorso tecnico

| Dati e obiettivo | Percorso iniziale | Modifica richiesta |
|---|---|---|
| Target categorico | Random Forest classifier | Selezionare target; verificare sbilanciamento e leakage |
| Target numerico continuo | Random Forest regressor | Selezionare target; controllare distribuzione ed errori |
| Nessun target, segmenti | K-Means | Scegliere numero di cluster; descrivere i profili |
| Nessun target, eventi rari | Isolation Forest | Definire quota attesa; validare manualmente i primi casi |
| Serie temporale | Baseline con lag e split temporale | Aggiungere ordinamento, feature temporali e `TimeSeriesSplit` |
| Testi o documenti | Ricerca locale TF-IDF | Aggiungere parser, chunking, risultati con fonte visibile |
| Immagini | Modello preaddestrato locale | Aggiungere preprocessing e anteprima dell’immagine |
| Sensori o eventi periodici | Lettura batch o polling | Aggiornare a intervalli; conservare snapshot per la demo |

Partire dal percorso più semplice che produce una metrica verificabile. Aggiungere modelli più complessi solo se migliorano un errore osservato.

## Quando Streamlit basta

Streamlit copre il caso previsto se l’interazione consiste in upload, filtri, grafici, training, chat locale, acquisizione singola da camera o aggiornamenti periodici. È adatto a una demo locale con un operatore e consente di cambiare dataset o target senza separare frontend e backend.

## Quando Streamlit non basta

Non migrare l’intera applicazione durante la gara. Aggiungere un backend separato solo se compare almeno uno di questi requisiti:

- flusso video continuo con elaborazione frame per frame;
- WebSocket o aggiornamenti inferiori al secondo;
- controllo bidirezionale di hardware o attuatori;
- più utenti concorrenti con ruoli e autenticazione;
- task lunghi che devono continuare dopo la chiusura della pagina;
- interfaccia mobile o consumer con layout non riproducibile in Streamlit.

Strategia di estensione:

1. Conservare `core/ml_pipeline.py` come logica di dominio.
2. Esporre solo le funzioni necessarie tramite FastAPI.
3. Tenere Streamlit come console operativa, salvo requisito esplicito di frontend diverso.
4. Usare Gradio solo per una demo centrata su audio, webcam o confronto diretto tra input e output multimediale.

## Controlli sul dataset

- [ ] Il file si apre da un avvio pulito.
- [ ] Ogni riga e colonna ha un significato noto.
- [ ] Il target è disponibile al momento della decisione simulata.
- [ ] Identificatori e duplicati del target sono esclusi.
- [ ] Le classi e i valori mancanti sono quantificati.
- [ ] La divisione training/test rispetta tempo, gruppi o soggetti quando necessario.
- [ ] Il dataset mostrato in demo non contiene dati personali non necessari.
- [ ] È disponibile un campione piccolo per il percorso di riserva.

## Criteri della giuria

| Criterio | Prova da mostrare | Stato |
|---|---|---|
| Aderenza al tema | Keyword presente nel problema, nel flusso e nel risultato | ☐ |
| Uso dei dati | Colonne reali visibili; preprocessing spiegato | ☐ |
| Originalità | Una scelta o funzione specifica del dominio | ☐ |
| Funzionalità e integrazione | Percorso completo da file a output | ☐ |
| Presentazione | Demo entro tre minuti con fallback | ☐ |

## Scaletta da tre minuti

### 0:00–0:25 · Problema

Dire:

> **[utente]** deve decidere **[decisione]**. Oggi usa **[processo attuale]**, che produce **[costo o rischio misurabile]**.

Mostrare una sola schermata o un solo dato che dimostri il problema.

### 0:25–0:45 · Proposta

Dire:

> Segnale usa **[dataset]** per produrre **[output]** prima di **[momento della decisione]**.

Non presentare un elenco di funzioni.

### 0:45–1:50 · Demo

1. Caricare o selezionare il dataset.
2. Mostrare una caratteristica concreta dei dati.
3. Eseguire il modello.
4. Mostrare metrica, output e importanza delle variabili.
5. Tradurre il risultato in una decisione.

Input predefinito della demo: **[compilare]**

Risultato atteso: **[compilare]**

Tempo massimo del calcolo: **[compilare]**

### 1:50–2:20 · Metodo e limite

Dire:

> Il modello viene addestrato in locale. La metrica **[nome]** vale **[valore]** sul campione di test. Il limite principale è **[limite]**; lo verificheremmo con **[dato o test successivo]**.

Non affermare causalità o validità generale se i dati non le dimostrano.

### 2:20–2:45 · Valore operativo

Dire:

> L’utente usa l’output per **[azione]**. Misureremmo l’effetto con **[KPI]** in un pilot di **[durata o perimetro]**.

### 2:45–3:00 · Chiusura

Dire:

> Il prossimo passo è **[pilot concreto]** con **[responsabile o partner]**.

Chiudere qui. Non ricapitolare la presentazione.

## Domande probabili della giuria

**Perché questo modello?**

Rispondere con baseline, dimensione del dataset, tempo di training e metrica. Non usare “più potente” senza confronto.

**Come evitate errori o bias?**

Citare separazione training/test, class balance, colonne escluse, limiti del dataset e controllo umano sull’azione.

**Dove sta l’intelligenza artificiale?**

Indicare algoritmo, input, output adattivo e parametro appreso dai dati. Evitare definizioni generiche.

**Cosa succede con dati nuovi?**

Spiegare gestione delle categorie sconosciute, imputazione e necessità di monitorare il degrado delle metriche.

**Perché non un modello generativo?**

La scelta dipende dal compito: per dati tabellari e target misurabile, un modello supervisionato locale fornisce metriche verificabili, latenza stabile e nessuna dipendenza di rete.

## Piano orario

| Ora | Uscita richiesta |
|---|---|
| 09:50–10:20 | Scheda della traccia compilata; percorso scelto |
| 10:20–11:10 | Dataset caricato; qualità e target verificati |
| 11:10–12:30 | Baseline con metrica |
| 12:30–13:00 | Primo percorso completo nell’interfaccia |
| 14:00–14:45 | Funzione distintiva legata al dominio |
| 14:45–15:20 | Errori gestiti; demo offline verificata |
| 15:20–16:00 | Pitch e schermate di riserva |
| 16:00–16:30 | Tre prove cronometrate; nessuna nuova funzione |

## Checklist prima dello stop

- [ ] Repository pulito e ultimo commit disponibile a entrambi i membri.
- [ ] Applicazione avviabile con un solo comando PowerShell.
- [ ] Percorso principale verificato senza rete.
- [ ] Nessuna chiave, file privato o dato personale nel repository.
- [ ] Dataset di demo e risultato atteso disponibili localmente.
- [ ] Screenshot o registrazione breve del percorso riuscito.
- [ ] Presentazione entro 2:45 durante almeno due prove.
- [ ] Una persona presenta; una persona controlla demo e fallback.
