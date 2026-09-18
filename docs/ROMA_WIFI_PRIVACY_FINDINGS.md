# WiFi Roma Capitale: falle di anonimizzazione documentate

## Scopo e confine etico

Questa valutazione dimostra il rischio di individuazione e di correlabilità senza tentare di identificare persone reali. Le prove sono aggregate e servono al titolare e al DPO per decidere se e come pubblicare il dataset.

Fonte: “Sessioni anonimizzate di navigazione web riscontrate nel sistema WiFi di Roma Capitale: traffico e opzione linguistica”, catalogo open data di Roma Capitale.

## Esito sintetico

Il dataset non dovrebbe essere pubblicato nella forma corrente senza una nuova valutazione del rischio. La rimozione di nome, e-mail e identificativi dichiarati non è sufficiente: la combinazione di timestamp al secondo, sede al civico, lingua e misure della sessione rende quasi tutte le righe singolari.

## 1. Timestamp al secondo

Il file pubblica inizio e fine della sessione al secondo. Sul campione locale, giorno e ora di inizio isolano già circa il 96% delle sessioni.

Scenario di rischio: chi conosce l'orario di collegamento di una persona, per osservazione diretta o altra fonte, può cercare una sola riga.

Correzione: sostituire gli orari esatti con fasce sufficientemente ampie e verificare nuovamente il k-anonimato.

## 2. Localizzazione fino al numero civico

Le colonne DUG, DUF e CIVICO ricostruiscono la sede esatta. La combinazione giorno, ora al secondo e sede isola circa il 99,5% delle sessioni.

Scenario di rischio: conoscenza esterna di luogo e orario può essere collegata a durata e volumi di traffico della sessione.

Correzione: pubblicare il municipio o una zona più ampia; non il civico riferito alla singola sessione.

## 3. Combinazione di quasi-identificativi

Giorno, STARTTIME, sede e DTLN rendono unica quasi ogni riga. Il problema nasce dalla combinazione, anche se ciascun campo preso da solo sembra innocuo.

Correzione: definire formalmente i quasi-identificativi e imporre una soglia minima, per esempio k ≥ 5, prima della diffusione.

## 4. Durata, download e upload esatti

DURATION, DOWNLOAD e UPLOAD sono misure molto granulari. La durata aumenta ulteriormente la quota di sessioni uniche; i volumi possono agire come impronte comportamentali o aiutare a confermare un collegamento già ipotizzato.

Correzione: pubblicare somme, mediane o fasce esclusivamente su gruppi sufficientemente numerosi.

## 5. LOGINCOUNT presente ma non documentato

LOGINCOUNT è presente nei CSV ufficiali, ma la scheda del catalogo non ne definisce la semantica. Nel campione assume migliaia di valori distinti e mostra un forte ordinamento temporale tra valori vicini rispetto a un controllo casuale.

Questo è compatibile con un contatore persistente, ma non prova che due righe appartengano alla stessa persona. Non deve essere chiamato “ID utente” senza una conferma dell'ente.

Correzione: sospendere la pubblicazione del campo, ottenere il data dictionary dal gestore e ripetere la valutazione con la semantica confermata.

## 6. Accumulo longitudinale

Il catalogo pubblica file giornalieri. Una valutazione condotta su un solo giorno ignora l'effetto composizione: ogni nuova risorsa estende la finestra di osservazione e può rendere riconoscibili pattern prima poco evidenti.

Correzione: misurare il rischio sull'intera serie storica e considerare attacchi per differenza tra release successive.

## 7. Nessuna soglia minima esplicita

La struttura resta “una riga per sessione”. Non risulta applicata una regola pubblica che sopprima o accorpi combinazioni rappresentate da una sola sessione.

Correzione: impedire la pubblicazione di gruppi con numerosità inferiore alla soglia stabilita e documentare la regola.

## 8. Etichetta “anonimizzate” senza metodo verificabile

La scheda definisce i dati anonimizzati, ma non descrive metodo, quasi-identificativi considerati, soglia di rischio, test di singling-out o valutazione dell'effetto cumulativo.

Correzione: pubblicare una nota metodologica con trasformazioni applicate, rischio residuo, campi esclusi e limiti di riutilizzo.

## Dimostrazione consentita

È sufficiente mostrare:

- la quota di classi unitarie;
- la crescita dell'individuabilità aggiungendo giorno, ora, sede e lingua;
- il confronto statistico tra LOGINCOUNT osservato e valori mescolati;
- il miglioramento ottenuto con aggregazione e soglia minima.

Non è necessario né opportuno cercare nomi, abitazioni, account social o altre identità reali.

## Versione consigliata

Aggregare per giorno, fascia di tre ore, municipio e lingua raggruppata; pubblicare soltanto gruppi con almeno cinque sessioni; rimuovere LOGINCOUNT, timestamp al secondo, civico e misure riferite alla singola sessione. Prima della pubblicazione ricontrollare anche la possibilità di inferire gruppi piccoli confrontando release successive.
