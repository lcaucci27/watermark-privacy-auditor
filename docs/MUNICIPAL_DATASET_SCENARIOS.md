# Incroci tra dataset dello stesso Comune

Questi scenari separano tre concetti: una riga può essere rara, due righe possono essere collegabili e una persona può essere identificata. L’ultimo passaggio esiste solo quando il secondo dataset contiene un’identità, oppure quando l’attaccante possiede davvero quella conoscenza esterna.

## Milano · triple già pubblicate sullo stesso portale

Il portale Open Data Milano pubblica più serie OpenWifiMilano con la stessa struttura temporale e territoriale:

1. [utenti unici giornalieri per zona](https://dati.comune.milano.it/dataset/ds917-openwifimilano-uniqueuserzone);
2. [login giornalieri per zona](https://dati.comune.milano.it/dataset/ds918-openwifimilano-logincountzone);
3. tempo di navigazione e traffico di download/upload giornalieri per zona, elencati nella [raccolta CSV del Comune](https://dati.comune.milano.it/dataset?_dcat_subtheme_it_limit=0&_tags_limit=0&res_format=CSV).

Chiave verificata negli export utenti e login: `Data + Zona`; entrambi usano le colonne `Tipologia_API;Zona;Data;Valore`. L’incrocio permette di derivare sessioni per dispositivo, durata media per sessione e traffico medio per dispositivo. È una profilazione di aree e fasce temporali, non di persone. Il rischio cresce quando una cella contiene pochi utenti, quando le release consentono sottrazioni o quando un altro file aggiunge un identificativo stabile.

Uso nella demo: caricare due export, scegliere `Data` e `Zona` e mostrare quante righe trovano un solo candidato.

CSV inclusi: `data/milano_wifi_utenti_sample.csv` e `data/milano_wifi_login_sample.csv`. Fonti esplicite:

- https://dati.comune.milano.it/dataset/ds917-openwifimilano-uniqueuserzone
- https://dati.comune.milano.it/dataset/ds918-openwifimilano-logincountzone

## Bologna · coppia unibile e terzo dataset di contesto

Il portale del Comune pubblica:

1. [affollamento orario delle aree WiFi](https://opendata.comune.bologna.it/explore/dataset/iperbole-wifi-affollamento/);
2. [anagrafica e geometrie delle aree di segnale](https://opendata.comune.bologna.it/explore/dataset/bolognawifi-elenco-aree-segnale/export/?flg=it-it);
3. [connessioni giornaliere BolognaWifi](https://opendata.comune.bologna.it/explore/dataset/bolognawifi-connessioni-giornaliere/).

La prima coppia si collega tramite il codice dell’area e aggiunge geometria/indirizzo alla serie oraria. Il terzo dataset è un controllo di contesto sul volume complessivo giornaliero; non va presentato come join riga-per-riga finché non si conferma una chiave territoriale comune.

Questo caso è utile perché prova la portabilità su dati già aggregati: Watermark non grida al rischio solo perché vede luogo e ora, ma controlla celle piccole, differenze tra release e precisione geografica.

CSV inclusi: `data/bologna_wifi_affollamento_sample.csv` e `data/bologna_wifi_aree_sample.csv`. Fonti esplicite:

- https://opendata.comune.bologna.it/explore/dataset/iperbole-wifi-affollamento/
- https://opendata.comune.bologna.it/explore/dataset/bolognawifi-elenco-aree-segnale/

## Roma · composizione tra pubblicazioni successive

Il catalogo di Roma Capitale espone un pacchetto WiFi composto da file giornalieri. Anche senza un secondo catalogo, due release successive sono due dataset osservabili dall’attaccante. Confrontarle può rivelare incrementi, persistenza di contatori o record aggiunti e rimossi.

Uso nella demo: trattare due giornate come dataset distinti e testare `luogo + finestra temporale`, oppure confrontare release successive. Non affermare che `LOGINCOUNT` sia un identificativo personale: la sua semantica resta **[DA CONFERMARE CON ROMA CAPITALE]**.

## Cosa dimostra davvero l’incrocio

- Se il secondo file non contiene identità, una corrispondenza unica dimostra collegabilità tra record, non re-identificazione personale.
- Se contiene un account, una prenotazione nominativa o un identificativo stabile, gli attributi possono trasferirsi al primo file.
- Se entrambi sono aggregati, il rischio principale è la composizione: celle piccole, differenze tra release e attributi derivati.
- Il test deve sempre mostrare quali chiavi e quale finestra temporale sono state assunte.
