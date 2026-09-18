# Watermark · discorso di 5 minuti sul deck `cuai26.pptx`

Durata totale: 5 minuti. Le indicazioni tra parentesi quadre non vanno pronunciate.

## Slide 1 · Open Data: trasparenza o rischio privacy? · 0:00–0:40

> Ogni Comune deve conciliare due esigenze: pubblicare dati utili e proteggere le persone. Il problema è che togliere nome e cognome spesso non basta. Giorno, ora, luogo e lingua del dispositivo possono creare una combinazione così rara da restringere la ricerca a una sola riga. Oggi questa verifica dipende spesso da controlli manuali e competenze distribuite tra più uffici. Watermark porta il controllo prima della pubblicazione e dà a DPO, responsabile open data e RTD una valutazione comprensibile e documentabile.

**Per noi:** una riga rara non contiene necessariamente un nome. Diventa pericolosa quando qualcuno possiede informazioni esterne compatibili.

## Slide 2 · Il caso Roma · 0:40–1:30

> Questo è il dato che rende concreto il problema. Nel campione WiFi di Roma, il 99,5 per cento delle sessioni ha una combinazione unica di giorno, ora, sede e lingua. In parole semplici, quasi ogni riga si distingue dalle altre. Non affermiamo di avere identificato persone. Affermiamo che chi conosce quei dettagli può restringere fortemente i candidati e vedere gli altri attributi associati alla sessione. Watermark mostra sempre la chiave utilizzata e il limite dell’analisi. Il campo LOGINCOUNT presenta inoltre memoria temporale, ma il suo significato non è documentato: per questo lo segnaliamo come elemento da chiarire con l’ente, non come identità dimostrata.

**Per noi:** “distinguibile” significa che la combinazione non si ripete. “Identificata” richiede un ulteriore collegamento con un nome o un account.

## Slide 3 · Controlli verificabili e spiegazione locale · 1:30–2:20

> Watermark separa il calcolo dalla spiegazione. Il motore verificabile legge lo schema, riconosce se una riga rappresenta un evento o un aggregato, misura unicità e celle piccole, poi prova l’incrocio con un secondo dataset. Qwen 2.5 3B gira in locale e traduce questi risultati in una risposta chiara. Nelle richieste operative usa un formato vincolato con esito, motivo, azione e limite. I numeri vengono controllati e, se il modello fallisce, resta disponibile la risposta calcolata. BGE-M3 serve soltanto a cercare testi simili per significato. Per la gravità degli allarmi usiamo TF-IDF, che nel nostro confronto ha ottenuto 0,743 contro 0,685 degli embedding.

**Per noi:** le regole producono il risultato. Il chatbot lo spiega. Il modello linguistico non decide da solo se pubblicare.

## Slide 4 · L’assistente spiega, non decide · 2:20–3:00

> L’utente può parlare con Watermark in linguaggio naturale. Può salutare, chiedere come funziona oppure formulare una richiesta operativa, per esempio “questo dataset è pubblicabile?” o “correggilo sotto il quindici per cento”. Nei saluti il modello conversa normalmente. Quando la domanda riguarda il dataset, l’agente riconosce l’intento, sceglie il controllo adatto e usa il chatbot locale per spiegare il risultato. Le righe grezze non entrano nel prompt. La cronologia può essere cancellata con un solo comando e nessun dato deve lasciare il computer.

**Per noi:** “specializzato” significa configurato con prompt, formato e controlli del dominio. Non è fine-tunato, perché non abbiamo riaddestrato i pesi del modello.

## Slide 5 · Incrocio Milano e utilità pratica · 3:00–4:05

> Il rischio cresce quando più dataset pubblici possono essere combinati. Nell’esempio Milano, il file degli utenti unici e quello dei login condividono giorno e zona. Su 13.793 righe, 12.205 trovano un solo record nel secondo file: l’88,5 per cento. Il 91,6 per cento trova almeno un collegamento. Questo non attribuisce automaticamente una persona, perché entrambi i file sono aggregati, ma aggiunge informazione su periodo e area. Se il secondo file contenesse account o nominativi, il rischio cambierebbe. Watermark rende esplicita questa ipotesi, mostra le chiavi del collegamento e produce una valutazione scaricabile. Il DPO passa così da un controllo manuale a un processo ripetibile, spiegato e documentato.

**Per noi:** 88,5% significa un solo record compatibile. 91,6% include anche i casi con più candidati. Collegamento tra righe non equivale automaticamente a identità personale.

## Slide 6 · Portabilità, prodotto e richiesta · 4:05–5:00

> La soluzione non è costruita sui nomi delle colonne di un solo Comune. Roma contiene eventi individuali, Bologna celle aggregate e Milano serie per zona. Fonti e mapping sono adattatori separati; il motore comune lavora su granularità, ruoli delle colonne, celle piccole e collegabilità. Streamlit è la console del pilot. Per un prodotto multi-ente aggiungiamo API, PostgreSQL per policy e audit trail, storage cifrato, elaborazioni asincrone e accessi per ruolo. Il committente è il Comune, una società in-house o il gestore pubblico. Proponiamo un pilot di otto-dodici settimane su tre dataset, tra dodici e venticinquemila euro. Misuriamo tempo di revisione, falsi allarmi e correzioni accettate. Cerchiamo un Comune pilota o un partner tecnologico.

**Per noi:** il cliente paga il progetto; DPO, responsabile open data e RTD sono gli utenti. Il prezzo è un’ipotesi da validare, non un listino definitivo.

## Risposte brevi alle domande

**È hardcoded sui tre Comuni?**  
No. I dataset dimostrativi hanno adattatori per fonte e chiavi; granularità, celle piccole e collegabilità sono calcolate dal motore comune.

**L’IA funziona davvero o mostra risposte predefinite?**  
Qwen 2.5 3B genera la spiegazione in locale. I risultati e i numeri arrivano dai controlli eseguiti sul dataset selezionato.

**È fine-tunato?**  
No. È prompt-specializzato: usiamo il modello originale con istruzioni, formato JSON e validazioni. Un fine-tuning richiederebbe casi annotati da DPO.

**Perché usate TF-IDF se avete gli embedding?**  
Per la gravità degli allarmi TF-IDF ha ottenuto 0,743 contro 0,685 degli embedding. Gli embedding restano utili per la ricerca semantica.

**Avete identificato persone?**  
No. Misuriamo rarità e collegabilità in forma aggregata. Non cerchiamo nomi né ricostruiamo profili personali.

**Una riga unica significa una persona identificata?**  
No. Significa distinguibile. Per identificare serve un secondo dato o una conoscenza che colleghi la riga a una persona.

**Perché l’identificazione interna non è sempre un problema?**  
Può essere necessaria per erogare o proteggere un servizio. Servono scopo, base giuridica, accessi controllati e conservazione limitata. La pubblicazione è un contesto diverso.

**I dataset Milano e Bologna sono sintetici?**  
No. Gli esempi principali provengono dai portali ufficiali dei rispettivi Comuni. Lo script risolve e scarica le fonti pubbliche.

**Cosa succede se il chatbot non funziona?**  
L’app mostra comunque la risposta deterministica calcolata. Il modello linguistico è uno strato di spiegazione, non un punto singolo di guasto.

**I dati vengono inviati fuori?**  
No nel percorso locale. Ollama gira sul computer e riceve domanda e risultati aggregati, non le righe grezze.

**Serve un database?**  
Non per la demo monoutente. In produzione serve per utenti, policy versionate, approvazioni e audit trail.

**Chi compra Watermark?**  
Comune, Città metropolitana, società in-house o gestore di un servizio pubblico. Il DPO è lo sponsor metodologico.

**Quanto costa?**  
Il pilot ipotizzato costa 12–25 mila euro per otto-dodici settimane e tre dataset. Il prezzo va validato con clienti e procurement.

**Qual è la differenza rispetto a un tool privacy generico?**  
Watermark controlla la composizione tra open data, distingue eventi e aggregati e produce evidenze pensate per il processo di pubblicazione comunale.

**Il prodotto certifica che un dataset è anonimo?**  
No. Supporta la decisione con misure, assunzioni e correzioni verificabili. La decisione finale resta al titolare e al DPO.

**Come aggiungete un nuovo Comune?**  
Registriamo la fonte e il mapping delle colonne, poi un revisore conferma la semantica. Il motore di rischio non va riscritto.

**Qual è il limite principale oggi?**  
La semantica delle colonne deve essere confermata dall’ente e il modello commerciale va validato con un Comune pilota.
