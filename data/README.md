# Dati locali

File generati da `scripts/fetch_data.py`. L'app li legge offline.

| File | Fonte | Licenza / note |
|---|---|---|
| `romawifi_sessioni.csv` | Roma Capitale, "Sessioni anonimizzate di navigazione web riscontrate nel sistema WiFi di Roma Capitale", dati.comune.roma.it (dataset `wifi2026`), ultimi 14 file giornalieri | CC-BY 4.0, attribuzione a Roma Capitale |
| `csirt_bollettini.csv` | CSIRT Italia, Agenzia per la cybersicurezza nazionale, acn.gov.it "Alert e bollettini" | Contenuti pubblici dell'ACN, citati con link al bollettino (colonna `slug`) |
| `garante_provvedimenti.csv` | Garante per la protezione dei dati personali, garanteprivacy.it (docweb) | Atti pubblici dell'Autorità, citati con URL |

Nessun dato di persone identificate. Le sessioni WiFi sono pubblicate dall'ente come anonimizzate; l'app ne misura il rischio residuo in forma aggregata.
