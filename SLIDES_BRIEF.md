# Brief per le slide

Usare questo documento dopo aver compilato `PRESENTATION_SHEET.md` e completato la demo. Non generare slide finché target, metrica e output atteso contengono valori reali.

## Materiale da raccogliere

- `PRESENTATION_SHEET.md` compilato;
- nome e descrizione finali da `challenge_config.py`;
- una schermata del dataset o della qualità dei dati;
- una schermata del risultato principale;
- metrica calcolata sul test set;
- grafico di feature importance, cluster o anomalie usato nella demo;
- limite principale del prototipo;
- azione operativa che segue l’output.

Non inserire numeri ricavati dai dataset di esempio nelle slide della gara.

## Formato

- Rapporto 16:9.
- Sei slide al massimo.
- Tre minuti complessivi.
- Una tesi per slide.
- Titolo dichiarativo, non etichetta generica.
- Massimo 35 parole visibili per slide, esclusi grafici e fonti.
- Un solo grafico o screenshot dominante per slide.
- Font e palette coerenti con l’app: acquamarina, avorio, corallo, oro e antracite.
- Nessuna animazione necessaria al significato.

## Regole anti-slop

- Non usare “rivoluzionario”, “innovativo”, “smart”, “potente”, “trasformativo” o “actionable”.
- Non scrivere “sfrutta l’intelligenza artificiale” senza nominare algoritmo, input e output.
- Non dichiarare efficienza senza confronto temporale o quantitativo.
- Non descrivere feature importance o correlazioni come cause.
- Non inventare utenti, metriche, risparmi, percentuali o risultati.
- Ogni claim deve avere una prova nella demo, nel dataset o nella valutazione.
- Preferire una limitazione precisa a una promessa generica.

## Struttura delle slide

### Slide 1 · Il problema osservabile

Titolo da completare:

> **[utente] perde o rischia [quantità] quando deve [decisione]**

Contenuto:

- utente;
- momento della decisione;
- costo, rischio o ritardo osservabile;
- fonte del dato che dimostra il problema.

Visuale: un numero, una riga del dataset o uno schema del processo attuale.

Frase del relatore:

> **[utente]** deve decidere **[decisione]** usando **[informazione disponibile]**. Il problema misurato è **[dato]**.

### Slide 2 · Il dataset determina cosa possiamo prevedere

Titolo da completare:

> **[numero] righe e [numero] variabili descrivono [unità di analisi]**

Contenuto:

- origine e periodo del dataset;
- unità di analisi;
- target;
- principali controlli di qualità;
- colonne escluse e motivo.

Visuale: profilo del dataset o tre campi annotati. Non mostrare una tabella illeggibile.

Frase del relatore:

> Usiamo **[dataset]**. Ogni riga rappresenta **[unità]**; il target è **[target]**. Abbiamo escluso **[colonne]** perché **[motivo]**.

### Slide 3 · Dal dato all’output

Titolo da completare:

> **Il modello trasforma [input] in [output] prima di [decisione]**

Contenuto:

```text
File → validazione → preprocessing → modello → metrica → output operativo
```

Specificare algoritmo e motivo della scelta in una frase. Indicare che l’esecuzione è locale se questo incide su privacy, affidabilità o latenza.

Visuale: architettura lineare con cinque o sei blocchi.

Frase del relatore:

> Il preprocessing gestisce **[problema dati]**. **[Algoritmo]** produce **[output]**; il calcolo resta sul dispositivo.

### Slide 4 · La prova quantitativa

Titolo da completare:

> **Sul test set, [metrica] vale [valore]**

Contenuto:

- dimensione o quota del test set;
- metrica principale;
- baseline o confronto, se disponibile;
- grafico che spiega errori, variabili importanti o segmenti.

Visuale: metrica grande e un grafico. Riportare unità e direzione desiderabile.

Frase del relatore:

> La metrica è calcolata su dati esclusi dall’addestramento. Otteniamo **[valore]** rispetto a **[baseline]**. L’errore principale riguarda **[caso]**.

### Slide 5 · L’utente trasforma l’output in un’azione

Titolo da completare:

> **Quando [condizione], [utente] esegue [azione]**

Contenuto:

- output mostrato nell’app;
- regola decisionale;
- responsabile dell’azione;
- KPI del pilot.

Visuale: screenshot ritagliato della demo con massimo tre annotazioni.

Frase del relatore:

> Il sistema non decide al posto di **[utente]**. Segnala **[output]**; l’utente verifica **[informazione]** e avvia **[azione]**.

### Slide 6 · Limite e prossimo test

Titolo da completare:

> **Il prossimo test verifica [limite] su [perimetro]**

Contenuto:

- limite principale;
- dato o esperimento necessario;
- perimetro e durata del pilot;
- criterio di successo.

Visuale: sequenza “oggi → pilot → criterio”.

Frase del relatore:

> Il limite principale è **[limite]**. Proponiamo un pilot su **[perimetro]** per **[durata]**; proseguiamo se **[soglia]**.

## Prompt di produzione

Copiare questo blocco nello strumento scelto per generare la presentazione:

```text
Leggi PRESENTATION_SHEET.md, SLIDES_BRIEF.md e challenge_config.py. Crea una presentazione 16:9 di massimo sei slide per un pitch di tre minuti. Usa esclusivamente fatti, metriche e limiti presenti nei file forniti. Se un campo è vuoto, mantieni un segnaposto esplicito invece di inventare il contenuto.

Per ogni slide restituisci: titolo dichiarativo, testo visibile, visuale consigliata, dati necessari e note del relatore. Mantieni massimo 35 parole visibili per slide. Usa la palette acquamarina, avorio, corallo, oro e antracite dell’app. Evita claim promozionali, metafore generiche e ripetizioni. Distingui risultati sul test set, deduzioni e ipotesi operative.
```

## Controllo finale

- [ ] Ogni numero è presente nel dataset, nell’app o nella valutazione.
- [ ] La prima slide identifica utente e decisione.
- [ ] La seconda prova l’uso effettivo dei dati.
- [ ] La quarta mostra una metrica su dati non usati nel training.
- [ ] La quinta collega output e azione umana.
- [ ] La sesta dichiara un limite verificabile.
- [ ] Il discorso completo dura meno di 2:45.
- [ ] Le slide restano comprensibili se la demo live non parte.
