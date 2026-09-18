# Prompt per Claude in PowerPoint

Uso consigliato: incollare prima il prompt di setup, poi un prompt slide per volta. Dopo che Claude ha creato la slide, sostituire i placeholder tra parentesi quadre con gli asset reali. Il discorso completo e i tempi sono in `docs/SLIDES_BRIEF.md`.

## 0 · Setup del deck

```text
Imposta una presentazione Watermark 16:9 di sei slide per aziende e pubbliche amministrazioni. Non aggiungere slide. Crea uno schema diapositiva coerente con margini del 6%, titolo sempre in alto a sinistra e footer fonti in basso. Usa soltanto: avorio #F7F3E8 come fondo, antracite #17282B per testo e linee, acquamarina #1F6B69 per prodotto e azioni corrette, acquamarina chiaro #D9EBE7 per aree secondarie, corallo #A63F2E per rischio, oro #B3872C per business e decisioni. Titoli Georgia Bold, corpo Inter o Arial. Titoli 30–34 pt, numeri chiave 72–110 pt, corpo minimo 24 pt, footer 11–12 pt. Mantieni al massimo 35 parole visibili per slide. Non inventare numeri, clienti, risparmi, certificazioni o conclusioni legali. Evita foto stock, gradienti, ombre pesanti, cervelli AI, robot, scudi, razzi, strette di mano, trofei e dashboard dense. Mantieni tutti i placeholder tra parentesi quadre esattamente come scritti.
```

## 1 · Problema

```text
Crea la slide 1 con layout 40/60 e palette vincolante: #F7F3E8, #17282B, #1F6B69, #D9EBE7, #A63F2E, #B3872C. Titolo a sinistra: “Un dataset senza nomi può ancora rendere riconoscibile una persona”. Sotto: “Il Comune deve decidere prima della pubblicazione” e “Committente: ente o gestore pubblico”. In basso: “DPO · Open Data Officer · RTD”. Inserisci [LOGO_WATERMARK] piccolo in alto a destra. Nella parte destra costruisci una visuale editoriale: una riga con data, ora, luogo e lingua forma una combinazione distintiva; una singola riga corallo emerge da una matrice acquamarina. Nessun altro testo. Footer: “GDPR art. 5 · Garante privacy, Trasparenza online”. La slide deve spiegare il problema in tre secondi anche senza relatore.
```

Note relatore, 24 s:

> Un Comune deve rendere i dati utili senza rendere riconoscibili le persone. Togliere nome e cognome non basta: luogo, giorno, ora e altri dettagli possono formare una combinazione rara. Il controllo oggi dipende spesso da verifiche manuali. Watermark porta questa decisione prima della pubblicazione, nelle mani di DPO, responsabile open data e RTD.

## 2 · Prova Roma

```text
Crea la slide 2 con palette esatta #F7F3E8, #17282B, #1F6B69, #D9EBE7, #A63F2E, #B3872C e layout 35/65. Titolo: “Nel campione Roma, il 99,5% delle sessioni è distinguibile”. A sinistra mostra “99,5%” in corallo, almeno 96 pt; sotto scrivi “giorno + ora + sede + lingua” e “Distinguibile non significa identificata”. A destra lascia un frame dominante etichettato [SCREENSHOT_VERIFICA_ROMA]. Prepara due callout, [CALLOUT_BADGE_DA_CORREGGERE] e [CALLOUT_GRAFICO_RARITA]. Inserisci [FONTE_ROMA_WIFI] nel footer e “[SEMANTICA LOGINCOUNT DA CONFERMARE]” in 11 pt. Non ricreare l’interfaccia: mantieni il placeholder finché non ricevi lo screenshot.
```

Note relatore, 28 s:

> Sul campione WiFi di Roma, il 99,5 per cento delle sessioni ha una combinazione unica di giorno, ora, sede e lingua. Detto semplicemente: quasi ogni riga si distingue dalle altre. Non stiamo dicendo di avere identificato una persona. Diciamo che chi possiede informazioni compatibili può restringere molto i candidati. Watermark mostra sempre questa assunzione, invece di nasconderla dietro una percentuale.

## 3 · Prodotto e IA

```text
Crea la slide 3 con palette esatta #F7F3E8, #17282B, #1F6B69, #D9EBE7, #A63F2E, #B3872C. Titolo: “Controlli verificabili e spiegazione locale”. Usa il 70% della larghezza per un unico flusso orizzontale: “CSV”, “Regole privacy”, “Test di collegabilità”, “Qwen 2.5 3B locale”, “Decisione DPO”. Usa connessioni lineari senza frecce testuali. Rendi il blocco regole più grande del blocco LLM. Mostra che al modello entrano soltanto risultati verificati. Nel 30% destro lascia [SCREENSHOT_ASSISTENTE_LOCALE], con un solo callout sul limite dichiarato. Sotto inserisci “JSON vincolato”, “numeri verificati” e “fonti preservate”. Footer: “Prompt specializzato, non fine-tuning dei pesi. Embedding solo per ricerca”.
```

Note relatore, 33 s:

> Qui l’IA non decide se un dataset è anonimo. Il motore deterministico classifica lo schema, misura righe rare e celle piccole, e simula l’incrocio con un secondo file. Solo dopo, Qwen 2.5 3B gira in locale e traduce i risultati per il DPO. L’output è JSON vincolato; numeri e fonti vengono controllati. Se fallisce, resta visibile la risposta calcolata. Le righe grezze non entrano nel prompt.

## 4 · Demo e utilità pratica

```text
Crea la slide 4 con palette esatta #F7F3E8, #17282B, #1F6B69, #D9EBE7, #A63F2E, #B3872C e layout 30/70. Titolo: “In meno di un minuto il DPO vede rischio, incrocio e correzione”. A sinistra tre passi grandi: “1 Dichiara lo scopo”, “2 Verifica e incrocia”, “3 Scarica la valutazione”. A destra lascia un frame dominante etichettato [SCREENSHOT_INCROCIO_MILANO]. Sul frame prepara solo tre callout: [CALLOUT_88_5_PERCENTO], [CALLOUT_NON_IDENTIFICA], [CALLOUT_DOWNLOAD]. Nella fascia inferiore scrivi: “Milano, Giorno + Zona, 12.205 collegamenti uno a uno su 13.793”. Footer: “Comune di Milano, OpenWifiMilano”. Non creare una UI fittizia: mantieni il placeholder finché non ricevi lo screenshot reale.
```

Note relatore, 40 s:

> Prima dichiaro lo scopo: uso interno o pubblicazione. Identificare un utente per erogare un servizio non è automaticamente un errore. Per l’open data, Watermark controlla unicità e celle sotto cinque. Nell’esempio Milano, utenti e login condividono giorno e zona: 12.205 righe su 13.793 trovano un solo record. Il file aggiunge informazioni sul periodo e sull’area, ma non attribuisce una persona. Infine scarico la valutazione.

## 5 · Portabilità e architettura

```text
Crea la slide 5 con palette esatta #F7F3E8, #17282B, #1F6B69, #D9EBE7, #A63F2E, #B3872C e layout 40/60. Titolo: “Un motore comune, policy diverse per ogni ente”. A sinistra lascia [SCREENSHOT_VERIFICA_BOLOGNA] con callout su “Cella aggregata” e sull’esito. A destra mostra tre input, “Roma eventi”, “Bologna celle aggregate” e “Milano serie per zona”, che entrano nello stesso motore. Sotto mostra lo stack di prodotto: “Console pilot”, “API”, “PostgreSQL e audit trail”, “worker asincroni”, “storage cifrato”, “OIDC e RBAC”. Inserisci “test automatici verdi” e “LLM locale 4/4 casi”. Footer: “Dataset ufficiali Roma, Bologna e Milano”. Non presentare Streamlit come l’intera architettura enterprise.
```

Note relatore, 30 s:

> La portabilità è già provata su tre schemi reali: eventi individuali a Roma, aggregati a Bologna e serie per zona a Milano. Per venderlo, Streamlit resta la console del pilot. Il prodotto aggiunge API, PostgreSQL per policy e audit trail, storage cifrato, job asincroni e accesso per ruolo. La suite automatica copre anche gli incroci ufficiali; il flusso locale ha superato quattro casi di accettazione.

## 6 · Business plan e committente

```text
Crea la slide 6 con palette esatta #F7F3E8, #17282B, #1F6B69, #D9EBE7, #A63F2E, #B3872C e layout a tre colonne. Titolo: “Il primo acquisto è un pilot su tre dataset comunali”. Colonna sinistra: “8–12 settimane” e “€12–25 mila” molto grandi, con oro per il prezzo. Colonna centrale: tre deliverable connessi, “audit”, “policy pack”, “integrazione”. Colonna destra: buyer map con “Comune / in-house / gestore” sopra e “DPO · Open Data Officer · RTD” sotto. Fascia finale #D9EBE7: “Cerchiamo [COMUNE_PILOTA_O_PARTNER_TECNOLOGICO]”. Sotto inserisci “KPI: tempo di revisione · falsi allarmi · correzioni accettate”. Footer: “Prezzo da validare · benchmark Cinastra e TrueVault · 7.894 Comuni, ISTAT”. Non mostrare ricavi futuri, TAM grafico o clienti inventati.
```

Note relatore, 25 s:

> Il committente è il Comune, una società in-house o il gestore del servizio; gli utenti sono DPO, open data officer e RTD. Il primo prodotto è un pilot di otto-dodici settimane su tre dataset, tra dodici e venticinquemila euro. Consegniamo audit, regole riutilizzabili e integrazione. Misuriamo tempo di revisione, falsi allarmi e correzioni accettate. Cerchiamo **[COMUNE PILOTA O PARTNER TECNOLOGICO]**.

## Asset da passare al compagno

- `[LOGO_WATERMARK]`: `assets/logo.svg`.
- `[LOGO_WATERMARK_PNG]`: `assets/logo-watermark.png`, versione trasparente pronta per PowerPoint.
- `[SCREENSHOT_VERIFICA_ROMA]`: vedere `docs/DEMO_SCREENSHOT_PLAN.md`.
- `[SCREENSHOT_ASSISTENTE_LOCALE]`: vedere `docs/DEMO_SCREENSHOT_PLAN.md`.
- `[SCREENSHOT_INCROCIO_MILANO]`: **[DA ACQUISIRE DOPO IL FREEZE DELLA DEMO]**.
- `[SCREENSHOT_VERIFICA_BOLOGNA]`: vedere `docs/DEMO_SCREENSHOT_PLAN.md`.
- `[FONTE_ROMA_WIFI]`: URL del catalogo già mostrato nell’app.
- `[SCREENSHOT_ARCHITETTURA_OPZIONALE]`: usare il diagramma nativo di PowerPoint se non disponibile.
- Dataset demo dell’incrocio: `data/milano_wifi_utenti_sample.csv` e `data/milano_wifi_login_sample.csv`.
