# Architettura verso un prodotto vendibile

## Stato del prototipo

La separazione attuale è adatta a una demo estendibile: `core/` contiene le regole, `views/` e `app_pages/` la presentazione, `scripts/` acquisizione e setup, `tests/` le regressioni. L’audit generico non dipende dallo schema Roma e distingue righe individuali da celle aggregate. L’assistente riceve risultati già calcolati, non righe grezze, e la risposta locale viene accettata solo se rispetta schema e numeri disponibili.

Streamlit è adeguato per pilot locale e console amministrativa. Non dovrebbe essere l’unico strato di un servizio multi-ente.

## Architettura target

```text
CSV / API / catalogo
        |
ingestione isolata e scansione schema
        |
motore di policy e collegabilità
        |
job asincroni + archivio oggetti cifrato
        |
API applicativa + PostgreSQL metadati
        |
console DPO / workflow approvazione / report firmato
```

- **PostgreSQL:** utenti, enti, ruoli, policy versionate, esiti, approvazioni e audit trail. Non è necessario per la demo monoutente, ma lo è per un prodotto persistente e multi-tenant.
- **Object storage cifrato:** opzionale e preferibilmente nel tenant del cliente. I file grezzi devono essere effimeri per default, con cancellazione verificabile.
- **Worker/queue:** profilazioni pesanti, embedding e confronti tra release non devono bloccare la UI.
- **API:** separa motore e interfaccia, consente CI/CD, cataloghi CKAN/Opendatasoft e sistemi documentali.
- **OIDC, RBAC e tenant isolation:** DPO, data owner, revisore e amministratore hanno permessi diversi.
- **Osservabilità:** log senza dati personali, metriche, tracing, allarmi, backup e prove di ripristino.
- **Sicurezza:** gestione segreti, cifratura, SBOM, scansioni dipendenze, firma degli artefatti e test di isolamento.

## IA locale: cosa è e cosa non è

`watermark-dpo:latest` è una configurazione specializzata di Qwen 2.5 3B con istruzioni di dominio; non è un fine-tuning dei pesi. L’output è JSON vincolato a quattro campi, a temperatura zero, con massimo 90 parole, controllo dei numeri, conservazione delle fonti, un retry correttivo e fallback deterministico. Nel test semantico finale tutti i modelli hanno ottenuto 4/4 con gli stessi guardrail: il 3B base e la variante Watermark hanno richiesto circa 52 secondi complessivi, il 7B circa 187.

La UI espone una sola opzione conversazionale, **Watermark · chatbot locale**. Qwen 3B base e Qwen 7B restano benchmark da riga di comando; BGE-M3 indicizza testi per somiglianza e TF-IDF stima l'impatto degli allarmi. Questa separazione evita di presentare all'utente strumenti tecnici come chatbot alternativi.

Il pacchetto Ollama del 3B riporta Qwen Research License; il 7B riporta Apache 2.0. La demo privilegia il 3B per latenza, ma una distribuzione commerciale deve completare la verifica legale o scegliere un modello piccolo con licenza compatibile. Il motore di regole e i guardrail non dipendono dal modello scelto.

Per una vera specializzazione servono **[SET DI CASI ANNOTATI DA DPO]**, split di valutazione congelato, metriche su fedeltà/azione/citazione e solo dopo un eventuale LoRA. Finché non esistono questi dati, prompt vincolato più validazione deterministica è più verificabile di un claim di fine-tuning.

## Gate prima della vendita

1. threat model e DPIA del prodotto;
2. test multi-tenant e cancellazione end-to-end;
3. 100–300 casi annotati da almeno due revisori;
4. connettori a due famiglie di portali e mapping guidato degli schemi;
5. export firmato con versione di dati, regole e software;
6. accessibilità, localizzazione, SLA, backup e runbook incidenti;
7. chiarimento contrattuale: Watermark supporta la decisione, non certifica da solo l’anonimato.
