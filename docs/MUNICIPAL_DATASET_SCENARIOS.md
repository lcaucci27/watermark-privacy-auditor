# Incroci tra dataset dello stesso Comune

Questi scenari separano tre concetti: una riga può essere rara, due righe possono essere collegabili e una persona può essere identificata. L’ultimo passaggio esiste solo quando il secondo dataset contiene un’identità, oppure quando l’attaccante possiede davvero quella conoscenza esterna.

## Milano · triple già pubblicate sullo stesso portale

Il portale Open Data Milano pubblica più serie OpenWifiMilano con la stessa struttura temporale e territoriale:

1. [utenti unici giornalieri per zona](https://dati.comune.milano.it/dataset/ds917-openwifimilano-uniqueuserzone);
2. [login giornalieri per zona](https://dati.comune.milano.it/dataset/ds918-openwifimilano-logincountzone);
3. tempo di navigazione e traffico di download/upload giornalieri per zona, elencati nella [raccolta CSV del Comune](https://dati.comune.milano.it/dataset?_dcat_subtheme_it_limit=0&_tags_limit=0&res_format=CSV).

Chiave usata nell’app: `Giorno + Zona`. `Giorno` deriva dal campo `Data` perché gli export storici conservano anche orari tecnici diversi. L’incrocio permette di derivare sessioni per dispositivo, durata media per sessione e traffico medio per dispositivo. È una profilazione di aree e periodi, non di persone. Il rischio cresce con celle piccole, differenze tra release o un altro file che aggiunge un identificativo stabile.

Uso nella demo: scegliere Milano e aprire `Incrocia`; il secondo export e le chiavi sono già configurati.

CSV inclusi: `data/milano_wifi_utenti_sample.csv` (13.793 righe) e `data/milano_wifi_login_sample.csv` (13.930 righe). Fonti esplicite:

- https://dati.comune.milano.it/dataset/ds917-openwifimilano-uniqueuserzone
- https://dati.comune.milano.it/dataset/ds918-openwifimilano-logincountzone
- CSV utenti risolto il 18 settembre 2026: https://dati.comune.milano.it/dataset/6c8bc9a9-2e37-4d63-b7a7-a24d34949617/resource/f766671a-07ff-49a3-a5f6-9d4568c60e50/download/20260917-230128_uniqueuserzone.csv
- CSV login risolto il 18 settembre 2026: https://dati.comune.milano.it/dataset/8b2529f7-5f8d-4b5b-92a5-6f1fe4476cb3/resource/7508cb64-6f83-4399-b47b-271479d59f18/download/20260917-230128_logincountzone.csv

Lo script non dipende dai due nomi datati: interroga CKAN e risolve ogni volta la risorsa CSV corrente.

## Bologna · coppia unibile e terzo dataset di contesto

Il portale del Comune pubblica:

1. [affollamento orario delle aree WiFi](https://opendata.comune.bologna.it/explore/dataset/iperbole-wifi-affollamento/);
2. [anagrafica e geometrie delle aree di segnale](https://opendata.comune.bologna.it/explore/dataset/bolognawifi-elenco-aree-segnale/export/?flg=it-it);
3. [connessioni giornaliere BolognaWifi](https://opendata.comune.bologna.it/explore/dataset/bolognawifi-connessioni-giornaliere/).

La prima coppia si collega tramite il codice dell’area e aggiunge geometria/indirizzo alla serie oraria. Il terzo dataset è un controllo di contesto sul volume complessivo giornaliero; non va presentato come join riga-per-riga finché non si conferma una chiave territoriale comune.

Questo caso è utile perché prova la portabilità su dati già aggregati: Watermark non grida al rischio solo perché vede luogo e ora, ma controlla celle piccole, differenze tra release e precisione geografica.

CSV inclusi: `data/bologna_wifi_affollamento_sample.csv` (5.000 osservazioni) e `data/bologna_wifi_aree_sample.csv` (76 aree). Fonti esplicite:

- https://opendata.comune.bologna.it/explore/dataset/iperbole-wifi-affollamento/
- https://opendata.comune.bologna.it/explore/dataset/bolognawifi-elenco-aree-segnale/
- CSV affollamento: https://opendata.comune.bologna.it/api/explore/v2.1/catalog/datasets/iperbole-wifi-affollamento/exports/csv?lang=it&timezone=Europe%2FRome&use_labels=true&delimiter=%3B
- CSV aree: https://opendata.comune.bologna.it/api/explore/v2.1/catalog/datasets/bolognawifi-elenco-aree-segnale/exports/csv?lang=it&timezone=Europe%2FRome&use_labels=true&delimiter=%3B

## Roma · composizione tra pubblicazioni successive

Il catalogo di Roma Capitale espone un pacchetto WiFi composto da file giornalieri. Anche senza un secondo catalogo, due release successive sono due dataset osservabili dall’attaccante. Confrontarle può rivelare incrementi, persistenza di contatori o record aggiunti e rimossi.

Uso nella demo: trattare due giornate come dataset distinti e testare `luogo + finestra temporale`, oppure confrontare release successive. Non affermare che `LOGINCOUNT` sia un identificativo personale: la sua semantica resta **[DA CONFERMARE CON ROMA CAPITALE]**.

## Cosa dimostra davvero l’incrocio

- Se il secondo file non contiene identità, una corrispondenza unica dimostra collegabilità tra record, non re-identificazione personale.
- Se contiene un account, una prenotazione nominativa o un identificativo stabile, gli attributi possono trasferirsi al primo file.
- Se entrambi sono aggregati, il rischio principale è la composizione: celle piccole, differenze tra release e attributi derivati.
- Il test deve sempre mostrare quali chiavi e quale finestra temporale sono state assunte.
