# Dati locali

File generati da `scripts/fetch_data.py` e `scripts/fetch_municipal_examples.py`. L'app li legge offline.

| File | Fonte | Licenza / note |
|---|---|---|
| `romawifi_sessioni.csv` | Roma Capitale, "Sessioni anonimizzate di navigazione web riscontrate nel sistema WiFi di Roma Capitale", dati.comune.roma.it (dataset `wifi2026`), ultimi 14 file giornalieri | CC-BY 4.0, attribuzione a Roma Capitale |
| `csirt_bollettini.csv` | CSIRT Italia, Agenzia per la cybersicurezza nazionale, acn.gov.it "Alert e bollettini" | Contenuti pubblici dell'ACN, citati con link al bollettino (colonna `slug`) |
| `garante_provvedimenti.csv` | Garante per la protezione dei dati personali, garanteprivacy.it (docweb) | Atti pubblici dell'Autorità, citati con URL |
| `bologna_wifi_affollamento_sample.csv` | Comune di Bologna, affollamento orario delle aree Iperbole WiFi | Campione di 5.000 osservazioni per una demo rapida |
| `bologna_wifi_aree_sample.csv` | Comune di Bologna, elenco aree BolognaWiFi | Anagrafica completa usata nell'incrocio ufficiale |
| `milano_wifi_utenti_sample.csv` | Comune di Milano, OpenWifiMilano utenti unici per zona | Export completo disponibile al download |
| `milano_wifi_login_sample.csv` | Comune di Milano, OpenWifiMilano login per zona | Export completo disponibile al download |

Nessun dato di persone identificate. Le sessioni WiFi sono pubblicate dall'ente come anonimizzate; l'app ne misura il rischio residuo in forma aggregata.

I link ai cataloghi e ai CSV sono documentati in `docs/MUNICIPAL_DATASET_SCENARIOS.md`. I nomi datati degli export Milano non sono fissati nello script: vengono risolti tramite l'API CKAN.
