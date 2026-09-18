# Discorso Watermark e note per i relatori

Durata totale: 3 minuti. Le parti tra parentesi quadre sono indicazioni per chi parla e non vanno pronunciate.

## Slide 1 · Il problema · 0:00–0:24

### Discorso

> Un Comune deve rendere i dati utili senza rendere riconoscibili le persone. Togliere nome e cognome non basta: luogo, giorno, ora e altri dettagli possono formare una combinazione rara. Il controllo oggi dipende spesso da verifiche manuali. Watermark porta questa decisione prima della pubblicazione, nelle mani di DPO, responsabile open data e RTD.

### Cosa indicare

[Indicare la riga corallo quando si dice “combinazione rara”. Chiudere guardando la giuria, non lo schermo.]

### Spiegazione per noi

- **Combinazione rara:** anche senza nome, quattro dettagli insieme possono descrivere una sola riga.
- **DPO:** il responsabile che sorveglia il rispetto della protezione dei dati.
- **Open Data Officer:** chi prepara e pubblica i dataset dell’ente.
- Il problema non è conservare dati necessari dentro l’amministrazione. Il problema è pubblicarli oltre lo scopo senza ridurre il rischio.

### Frase da non usare

Non dire “il dataset identifica tutti”. Dire: “può rendere distinguibile una riga e facilitare un’identificazione quando esiste altra conoscenza”.

## Slide 2 · La prova su Roma · 0:24–0:52

### Discorso

> Sul campione WiFi di Roma, il 99,5 per cento delle sessioni ha una combinazione unica di giorno, ora, sede e lingua. Detto semplicemente: quasi ogni riga si distingue dalle altre. Non stiamo dicendo di avere identificato una persona. Diciamo che chi possiede informazioni compatibili può restringere molto i candidati. Watermark rende sempre visibile questa assunzione.

### Cosa indicare

[Indicare prima il 99,5%, poi il grafico. Fare una breve pausa prima di “non stiamo dicendo”.]

### Spiegazione per noi

- **99,5% distinguibile:** circa 995 righe su 1.000 hanno una combinazione che non si ripete.
- **Non significa identificato:** manca ancora un nome, un account o una conoscenza esterna che colleghi quella riga a una persona.
- Esempio semplice: sapere che una persona era in una sede a una certa ora può permettere di trovare la sua riga. Senza questa informazione esterna vediamo soltanto una riga rara.
- `LOGINCOUNT` mostra memoria nel tempo, ma Roma Capitale non ne documenta il significato. Va presentato come segnale da chiarire, non come identificativo personale dimostrato.

### Risposta rapida se contestano il dato

> Il 99,5% misura l’unicità nel campione e sotto una chiave esplicita. Non misura quante persone siano state realmente identificate.

## Slide 3 · Come funziona l’IA · 0:52–1:25

### Discorso

> L’IA non decide da sola se un dataset è anonimo. Il motore verificabile riconosce lo schema, misura righe rare e celle piccole, e simula l’incrocio con un secondo file. Qwen 2.5 3B gira in locale e trasforma questi risultati in una risposta chiara per il DPO. Nelle richieste operative usa un formato controllato e non può cambiare i numeri. Per saluti e conversazione risponde direttamente, sempre sul computer. Le righe grezze non entrano nel chatbot.

### Cosa indicare

[Seguire il flusso da CSV a decisione. Sullo screenshot indicare la frase “risposta generata sul computer”.]

### Spiegazione per noi

- **Motore verificabile:** codice normale con regole e formule ripetibili. Produce i numeri mostrati.
- **Qwen 2.5 3B:** il chatbot locale, circa 3,1 miliardi di parametri. Spiega il risultato, ma non calcola la decisione privacy.
- **JSON vincolato:** per le risposte operative il modello deve riempire campi precisi: esito, motivo, azione e limite.
- **BGE-M3:** non è un chatbot. Trasforma testi in vettori per trovare norme e bollettini simili per significato.
- **TF-IDF:** classifica la gravità degli allarmi in base alle parole. Nel confronto ha ottenuto 0,743 contro 0,685 degli embedding, quindi resta il modello principale.
- Se Ollama non risponde, Watermark mostra comunque il risultato calcolato.

### Risposta rapida sul fine-tuning

> È prompt-specializzato, non abbiamo modificato i pesi. È una scelta verificabile finché non avremo casi annotati da DPO per un eventuale fine-tuning.

## Slide 4 · Uso pratico e incrocio Milano · 1:25–2:05

### Discorso

> Prima dichiaro lo scopo: uso interno o pubblicazione. Identificare un utente per erogare un servizio non è automaticamente un errore. Per l’open data, Watermark controlla unicità e celle sotto cinque. Nell’esempio Milano, utenti e login condividono giorno e zona: 12.205 righe su 13.793 trovano un solo record. Il secondo file aggiunge informazioni sul periodo e sull’area, ma non attribuisce una persona. Infine scarico la valutazione per il DPO.

### Cosa indicare

[Indicare “Giorno + Zona”, poi 88,5%, poi la frase “non identifica una persona”, infine il pulsante di download.]

### Spiegazione per noi

- **Incrocio:** si cercano righe con gli stessi valori sulle chiavi scelte.
- **88,5% uno a uno:** per 12.205 righe del primo file esiste esattamente una riga compatibile nel secondo.
- **91,6% con almeno un collegamento:** include anche i casi in cui il secondo file contiene più candidati.
- I due file Milano sono entrambi aggregati. L’incrocio arricchisce zona e giorno, ma non trasferisce nomi.
- Se il secondo file contenesse account o nominativi, lo stesso collegamento avrebbe un rischio molto maggiore. Il toggle dell’app rende esplicita questa ipotesi.

### Risposta rapida sul valore pratico

> Il DPO vede subito quali chiavi creano il collegamento, quanto è esteso e quale assunzione serve perché diventi un rischio di identificazione.

## Slide 5 · Portabilità e architettura · 2:05–2:35

### Discorso

> La portabilità è già provata su tre schemi reali: eventi individuali a Roma, celle aggregate a Bologna e serie per zona a Milano. Le fonti e le chiavi comunali sono configurazioni separate dalla logica di controllo, quindi il motore non dipende dai nomi di queste colonne. Streamlit è la console del pilot. Un prodotto multi-ente aggiunge API, PostgreSQL per policy e audit trail, storage cifrato, elaborazioni asincrone e accessi per ruolo.

### Cosa indicare

[Indicare “Cella aggregata” e l’esito Bologna. Poi seguire lo stack dal pilot verso API e database.]

### Spiegazione per noi

- **Non hardcoded:** gli URL, i file e le coppie di chiavi sono nel catalogo degli adattatori. Le regole comuni lavorano su ruoli delle colonne e granularità.
- **Bologna compatibile:** le 5.000 osservazioni sono celle aggregate e nessun valore positivo di affollamento è sotto cinque.
- **PostgreSQL:** serve in produzione per utenti, enti, policy versionate, approvazioni e cronologia delle decisioni. Non serve alla demo locale.
- **Storage cifrato:** conserva eventuali file nel perimetro del cliente.
- **Worker asincroni:** eseguono controlli pesanti senza bloccare l’interfaccia.
- **OIDC e RBAC:** login aziendale e permessi diversi per DPO, revisore e amministratore.

### Risposta rapida sulla generalizzazione

> Per aggiungere un Comune registriamo la fonte e il mapping delle colonne. Un revisore conferma il significato dello schema, mentre il motore di rischio resta invariato.

## Slide 6 · Committente e business · 2:35–3:00

### Discorso

> Il committente è il Comune, una società in-house o il gestore del servizio. Gli utenti sono DPO, responsabile open data e RTD. Il primo acquisto è un pilot di otto-dodici settimane su tre dataset, tra dodici e venticinquemila euro. Consegniamo audit, regole riutilizzabili e integrazione. Misuriamo il tempo di revisione, i falsi allarmi e le correzioni accettate. Cerchiamo un Comune pilota o un partner tecnologico.

### Cosa indicare

[Indicare durata e prezzo. Chiudere sulla richiesta di partner e mantenere il contatto visivo.]

### Spiegazione per noi

- **Committente:** chi firma e paga il contratto. Può essere il Comune, una società in-house o il gestore pubblico.
- **Utente:** chi usa Watermark ogni giorno. Principalmente DPO, responsabile open data, data steward e RTD.
- **Pilot:** progetto limitato con tre dataset reali. Serve a misurare valore e falsi allarmi prima di comprare una licenza annuale.
- **€12–25 mila:** ipotesi commerciale da validare, non un prezzo di listino già venduto.
- Il risultato acquistabile non è soltanto un punteggio: comprende rapporto, policy riutilizzabili e integrazione nel flusso di pubblicazione.

### Chiusura

> Watermark porta una verifica ripetibile prima della pubblicazione e lascia al DPO una decisione motivata, scaricabile e applicabile a dataset diversi.

## Ripasso da 30 secondi

1. Roma dimostra che togliere i nomi può non bastare.
2. Milano dimostra che due open data possono arricchirsi a vicenda.
3. Bologna dimostra che il motore distingue eventi individuali e dati aggregati.
4. Le regole calcolano, il chatbot locale spiega.
5. Il cliente compra un controllo prima della pubblicazione, con evidenze per il DPO.

## Parole da usare con precisione

- Dire **distinguibile** o **collegabile** quando non esiste un’identità.
- Dire **identificabile** solo quando un secondo dato o una conoscenza possono attribuire la riga a una persona.
- Dire **prompt-specializzato**, non fine-tuned.
- Dire **supporto alla decisione**, non certificazione automatica dell’anonimato.
- Dire **prezzo da validare**, non listino definitivo.
