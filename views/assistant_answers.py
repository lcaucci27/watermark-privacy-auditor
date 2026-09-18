"""Risposte dell'assistente: ogni intenzione esegue gli strumenti locali, mostra i passaggi
e restituisce un riassunto in parole semplici (riusabile dal percorso LLM opzionale)."""

from __future__ import annotations

import re
from collections.abc import Callable

import pandas as pd
import streamlit as st

from core.audit_agent import INFRASTRUCTURE_QUERY, RULE_QUERY, run_audit
from core.generic_privacy import (
    audit_generic, infer_granularity, protect_generic, report_markdown as generic_report, suggested_roles,
)
from core.linkability import scan_counters
from core.privacy import DIRECT, SENSITIVE, classify_columns
from core.privacy_optimizer import Variant, publish, recommend
from core.semantic import hybrid_search
from core.threat_model import bulletin_text, explain, predict_semantic
from core.wifi_dataset import PUBLISHED_KEYS, unique_share
from views.dataset import ActiveDataset
from views.shared import (
    csirt_corpus, csirt_hybrid, frontier_chart, garante_corpus, garante_passages, impact_model,
    semantic_impact_model, variants,
)

DEFAULT_RISK = 0.15


def _step(label: str, replay: bool):
    """Passaggio visibile dell'agente; nella rilettura della cronologia compare già completato."""
    return st.status(label, type="step", state="complete" if replay else "running")


@st.cache_data(show_spinner=False, max_entries=5)
def _scan(frame: pd.DataFrame) -> pd.DataFrame:
    return scan_counters(frame, frame["inizio"], ["sede", "DTLN"], location="sede")


def verifica(data: ActiveDataset, question: str, threshold: float | None, replay: bool, key: str = "") -> str:
    if not data.is_wifi:
        return _verifica_generica(data, replay)
    frame = data.frame
    with _step(f"Leggo {len(frame):,} sessioni da {frame['sede'].nunique()} sedi", replay):
        st.caption(f"Righe duplicate escluse: {data.removed:,}.")
    with _step("Misuro quante sessioni sono riconoscibili", replay):
        share = unique_share(frame, PUBLISHED_KEYS)
        st.caption("Chiave: giorno, orario al secondo, sede, lingua del telefono.")
    with _step("Cerco colonne che fanno da pseudonimo", replay):
        scan = _scan(frame)
        st.dataframe(scan, hide_index=True, width="stretch")
    flagged = scan[scan["esito"] == "Pseudonimo probabile"]

    st.markdown(":red-badge[:material/block: Non pubblicabile così com'è]" if share > DEFAULT_RISK or not flagged.empty
                else ":green-badge[:material/check: Pubblicabile]")
    c1, c2 = st.columns(2)
    c1.metric("Sessioni riconoscibili", f"{share:.1%}", border=True)
    c2.metric("Colonne-pseudonimo", len(flagged), border=True)
    summary = f"Il {share:.1%} delle sessioni è unico: chi sa giorno, ora, luogo e lingua di una persona trova la sua riga."
    if not flagged.empty:
        row = flagged.iloc[0]
        st.markdown(f"**{row['colonna']}**: tra due numeri vicini, quante volte il più alto arriva dopo?")
        st.progress(float(row["ordine nel tempo"]), text=f"Nei dati pubblicati: {row['ordine nel tempo']:.0%}")
        st.progress(float(row["ipotesi nulla"]), text=f"Con numeri mescolati a caso: {row['ipotesi nulla']:.0%}")
        summary += (
            f" In più, la colonna **{row['colonna']}** mostra memoria temporale compatibile con un contatore persistente: "
            "può creare correlabilità tra sessioni e richiede un chiarimento dell'ente."
        )
    st.markdown(summary + "\n\nPuoi chiedermi *correggilo* o *perché è un problema?*")
    return summary


def _verifica_generica(data: ActiveDataset, replay: bool) -> str:
    with _step("Classifico le colonne per tipo di dato personale", replay):
        scan = classify_columns(data.frame)
        st.dataframe(scan, hide_index=True, width="stretch")
    direct, quasi, sensitive = suggested_roles(data.frame)
    granularity = infer_granularity(data.frame)
    row_kind = data.row_kind_hint or granularity.kind
    measure = granularity.measures[0] if granularity.measures else None
    audit = audit_generic(
        data.frame, row_kind, direct, quasi, sensitive[0] if sensitive else None, 5, measure, "pubblicazione"
    )
    counts = scan["categoria"].value_counts()
    c1, c2, c3 = st.columns(3)
    c1.metric("Identificativi diretti", int(counts.get(DIRECT, 0)), border=True)
    c2.metric("Quasi-identificativi", len(quasi), border=True)
    c3.metric("Dati sensibili", int(counts.get(SENSITIVE, 0)), border=True)
    summary = f"Esito: **{audit.outcome}**. Ho trovato {len(direct)} identificativi diretti e {len(quasi)} quasi-identificativi."
    if row_kind == "aggregato":
        summary += (
            f" Il file descrive celle aggregate; controllo i conteggi piccoli, non l’unicità delle righe. "
            f"Celle sotto 5: {audit.metrics.get('Celle sotto soglia', 'da verificare')}."
        )
    elif quasi:
        summary += f" Righe uniche sui quasi-identificativi: {audit.metrics.get('Righe uniche %', 'da verificare')}%."
    st.markdown(f":{'green' if audit.outcome == 'Compatibile con pubblicazione' else 'red'}-badge[{audit.outcome}]")
    for reason in audit.reasons:
        st.caption(reason)
    st.markdown(summary)
    return summary


def correggi(data: ActiveDataset, question: str, threshold: float | None, replay: bool, key: str = "") -> str:
    max_risk = threshold or DEFAULT_RISK
    if not data.is_wifi:
        direct, quasi, _ = suggested_roles(data.frame)
        granularity = infer_granularity(data.frame)
        row_kind = data.row_kind_hint or granularity.kind
        measure = granularity.measures[0] if granularity.measures else None
        if row_kind == "individuale" and not quasi:
            st.markdown("Devi indicare almeno una colonna che un estraneo potrebbe già conoscere.")
            return "Manca la scelta dei quasi-identificativi."
        action = "Sopprimo i conteggi piccoli" if row_kind == "aggregato" else "Generalizzo fino a 5 righe per gruppo"
        with _step(action, replay):
            corrected, log = protect_generic(data.frame, row_kind, direct, quasi, 5, measure)
        st.download_button("Scarica il file corretto", corrected.to_csv(index=False).encode("utf-8"),
                           "dataset_corretto.csv", "text/csv", icon=":material/download:", key=f"dlg_{key}")
        summary = " ".join(log) or "Il file non richiede trasformazioni automatiche con le impostazioni rilevate."
        st.markdown(summary)
        return summary

    with _step("Genero 36 versioni del dataset (orario, luogo, contatore)", replay):
        st.caption("Orario al secondo, 15 minuti, 1 ora, 3 ore · civico, via, municipio · contatore pubblicato, in fasce, rimosso.")
    with _step("Per ognuna misuro rischio e utilità con un modello di gradient boosting", replay):
        table = variants(data.frame)
    with _step(f"Scelgo la più utile sotto il {max_risk:.0%} di rischio", replay):
        chosen = recommend(table, max_risk)
    if chosen is None:
        st.markdown(f"Nessuna versione scende sotto il {max_risk:.0%}. Prova con una soglia più alta, per esempio *correggi sotto il 20%*.")
        return "Nessuna versione sotto la soglia richiesta."
    before = unique_share(data.frame, PUBLISHED_KEYS)
    st.markdown(":green-badge[:material/verified: Versione pubblicabile trovata]")
    c1, c2, c3 = st.columns(3)
    c1.metric("Riconoscibili oggi", f"{before:.1%}", border=True)
    c2.metric("Dopo la correzione", f"{chosen['rischio']:.1%}", delta=f"{(chosen['rischio'] - before) * 100:.0f} punti",
              delta_color="inverse", border=True)
    c3.metric("Informazione conservata", f"{chosen['utilità relativa']:.0%}", border=True)
    st.plotly_chart(frontier_chart(table, max_risk, chosen), width="stretch", key=f"chart_{key}")
    corrected = publish(data.frame, Variant(chosen["orario"], chosen["luogo"], chosen["contatore"]))
    st.download_button("Scarica il dataset corretto", corrected.drop(columns=["minuto_del_giorno"]).to_csv(index=False).encode("utf-8"),
                       "dataset_corretto.csv", "text/csv", icon=":material/download:", key=f"dl_{key}")
    summary = (
        f"Ho scelto: **{chosen['variante']}**. Le sessioni riconoscibili scendono dal {before:.1%} al {chosen['rischio']:.1%} "
        f"e il dataset conserva il {chosen['utilità relativa']:.0%} dell'informazione utile a pianificare il servizio."
    )
    st.markdown(summary)
    return summary


def minacce(data: ActiveDataset, question: str, threshold: float | None, replay: bool, key: str = "") -> str:
    csirt, _ = csirt_corpus()
    if csirt is None:
        st.markdown("Non trovo i bollettini CSIRT in `data/`.")
        return "Bollettini non disponibili."
    index = csirt_hybrid(tuple(bulletin_text(csirt)))
    context = INFRASTRUCTURE_QUERY if data.is_wifi else " ".join(map(str, data.frame.columns)) + " sistemi comunali applicazione database"
    mode = "per significato e per parole" if index.semantic else "per parole"
    with _step(f"Cerco tra {len(csirt):,} bollettini CSIRT, {mode}", replay):
        hits = hybrid_search(index, f"{question} {context}", 8)
    table = csirt.loc[hits.index, ["codice", "titolo", "impatto_classe", "n_cve_sfruttate"]].rename(
        columns={"impatto_classe": "impatto ACN", "n_cve_sfruttate": "CVE sfruttate"})
    critical = int((table["impatto ACN"] == "Critico").sum())
    exploited = int((table["CVE sfruttate"].fillna(0) > 0).sum())
    st.markdown(f":orange-badge[:material/security: {len(table)} bollettini pertinenti]")
    st.dataframe(table, hide_index=True, width="stretch")
    domain = "access point, captive portal e accesso remoto" if data.is_wifi else "i sistemi associati alle colonne del file"
    summary = (f"Per {domain} ci sono {len(table)} "
               f"bollettini pertinenti: {critical} con impatto critico, {exploited} con vulnerabilità già sfruttate in rete.")
    st.markdown(summary)
    sources = "\n".join(f"[{i}] {row.codice} {row.titolo} (impatto {row._3})" for i, row in enumerate(table.itertuples(), 1))
    return f"{summary}\nBollettini:\n{sources}"


def norme(data: ActiveDataset, question: str, threshold: float | None, replay: bool, key: str = "") -> str:
    loaded = garante_passages()
    if loaded is None:
        st.markdown("Non trovo i provvedimenti del Garante in `data/`.")
        return "Provvedimenti non disponibili."
    passages, index = loaded
    mode = "per significato e per parole" if index.semantic else "per parole"
    query = f"{question} {RULE_QUERY}"
    with _step(f"Cerco in {len(passages):,} passaggi di {passages['titolo'].nunique()} documenti del Garante, {mode}", replay):
        hits = hybrid_search(index, query, 3)
    quotes = []
    for number, position in enumerate(hits.index, 1):
        title, passage = passages.loc[position, "titolo"], passages.loc[position, "passaggio"]
        st.caption(f"[{number}] {title}")
        st.markdown(f"> {passage}")
        quotes.append(f"[{number}] {title}: {passage}")
    return "Passaggi del Garante:\n" + "\n".join(quotes)


def spiega(data: ActiveDataset, question: str, threshold: float | None, replay: bool, key: str = "") -> str:
    if not data.is_wifi:
        text = "Una riga è riconoscibile quando nessun'altra ha gli stessi valori sulle colonne che un estraneo può conoscere."
        st.markdown(text)
        return text
    scan = _scan(data.frame)
    row = scan[scan["colonna"] == "LOGINCOUNT"].iloc[0]
    text = f"""Pensa alla tessera di una palestra: ogni volta che entri, **il tuo** contatore sale di 1.

**LOGINCOUNT** può essere tre cose: il contatore di una persona, il contatore dell'hotspot, oppure un numero a caso. Ho controllato:

1. **Il numero più alto arriva dopo?** Tra due sessioni nello stesso posto, stesso giorno, stessa lingua, con numeri vicini (es. 95 e 96): succede nel **{row['ordine nel tempo']:.0%}** dei casi. Con numeri mescolati a caso: {row['ipotesi nulla']:.0%}, come lanciare una moneta.
2. **È il contatore dell'hotspot?** Allora dentro lo stesso hotspot salirebbe sempre. Sale solo nel **{row['crescita nel luogo']:.0%}** dei passi: no.
3. Il campo conserva quindi **memoria temporale** ed è compatibile con un contatore persistente. Potrebbe rendere collegabili sessioni diverse, ma questi test non dimostrano che appartengano alla stessa persona.

Nessun documento ufficiale descrive questa colonna. Per stabilire se sia davvero riferita all'utente o al dispositivo serve una conferma di Roma Capitale."""
    st.markdown(text)
    return text


def rapporto(data: ActiveDataset, question: str, threshold: float | None, replay: bool, key: str = "") -> str:
    if not data.is_wifi:
        direct, quasi, sensitive = suggested_roles(data.frame)
        granularity = infer_granularity(data.frame)
        row_kind = data.row_kind_hint or granularity.kind
        measure = granularity.measures[0] if granularity.measures else None
        with _step("Preparo la valutazione portabile sullo schema del file", replay):
            audit = audit_generic(
                data.frame, row_kind, direct, quasi, sensitive[0] if sensitive else None, 5, measure, "pubblicazione"
            )
        markdown = generic_report(data.name, audit, 5)
        st.download_button(
            "Scarica il rapporto per il DPO", markdown.encode("utf-8"), "rapporto_watermark.md",
            "text/markdown", icon=":material/description:", type="primary", key=f"rep_{key}",
        )
        summary = f"Rapporto pronto. Esito: {audit.outcome}. " + " ".join(audit.reasons[:2])
        st.markdown(summary)
        return summary
    csirt, csirt_index = csirt_corpus()
    garante, garante_index = garante_corpus()
    max_risk = threshold or DEFAULT_RISK
    with _step("Eseguo i cinque controlli dell'agente", replay):
        # Il rapporto si calcola una volta per messaggio; la cronologia lo rilegge dalla sessione.
        cache_key = f"report_{key}"
        if cache_key not in st.session_state:
            st.session_state[cache_key] = run_audit(
                data.frame, variants(data.frame), max_risk, csirt, csirt_index,
                impact_model(csirt) if csirt is not None else None, garante, garante_index,
            )
        report = st.session_state[cache_key]
        for step in report.steps:
            st.caption(f"{'✓' if step.ok else '✗'} {step.title}: {step.outcome}")
    st.download_button("Scarica il rapporto per il DPO", report.markdown.encode("utf-8"), "rapporto_watermark.md",
                       "text/markdown", icon=":material/description:", type="primary", key=f"rep_{key}")
    summary = f"Rapporto pronto: {sum(not s.ok for s in report.steps)} controlli su {len(report.steps)} richiedono una correzione."
    st.markdown(summary)
    return summary


def allarme(data: ActiveDataset, question: str, threshold: float | None, replay: bool, key: str = "") -> str:
    csirt, _ = csirt_corpus()
    model = impact_model(csirt) if csirt is not None else None
    if model is None:
        st.markdown("Il modello di impatto richiede i bollettini CSIRT in `data/`.")
        return "Modello non disponibile."
    # Un allarme incollato non ha i campi strutturati del CSIRT: li deduce dal testo.
    alert = pd.DataFrame({
        "sintesi": [question],
        "n_cve_sfruttate": [int(bool(re.search(r"sfruttament|sfruttat|exploited", question, re.IGNORECASE)))],
        "n_cve_con_poc": [int(bool(re.search(r"\bpoc\b|proof of concept", question, re.IGNORECASE)))],
    })
    text = bulletin_text(alert).iloc[0]
    with _step("Stimo l'impatto con il modello validato sui bollettini successivi (TF-IDF)", replay):
        predicted, drivers = explain(model, text)
        st.dataframe(drivers, hide_index=True, width="stretch")
        st.caption("Parole dell'allarme che hanno spinto di più la stima.")
    semantic = semantic_impact_model(csirt)
    second = predict_semantic(semantic, text) if semantic is not None else None
    if second is not None:
        with _step("Cerco per significato i bollettini storici più simili (embedding bge-m3)", replay):
            st.dataframe(second[2], hide_index=True, width="stretch")
    colour = {"Critico": "red", "Alto": "orange", "Medio": "blue"}.get(predicted, "gray")
    st.markdown(f":{colour}-badge[Impatto stimato: {predicted}]")
    words = ", ".join(drivers["parola"].head(4))
    summary = f"Impatto stimato **{predicted}**. Parole decisive: {words}."
    if second is not None:
        opinion = "concorda" if second[0] == predicted else f"stima invece {second[0]}"
        summary += (f" Il modello semantico {opinion}. Bollettini più simili: "
                    + "; ".join(second[2]["titolo"].head(3)) + ".")
    st.markdown(summary)
    return summary


def aiuto(data: ActiveDataset, question: str, threshold: float | None, replay: bool, key: str = "") -> str:
    text = """Posso aiutarti a decidere se e come pubblicare un dataset:

- *Questo dataset è pubblicabile?*: verifico se le persone sono riconoscibili e se ci sono pseudonimi nascosti.
- *Correggilo*: per dati individuali generalizzo i quasi-identificativi; per aggregati sopprimo i conteggi piccoli.
- *Quali sistemi sono a rischio?*: cerco nei bollettini CSIRT.
- *Cosa dice il Garante?*: cito i provvedimenti parola per parola.
- *Incolla il testo di un allarme*: stimo l'impatto e spiego perché.
- *Fammi il rapporto*: preparo il documento per il DPO."""
    st.markdown(text)
    return text


def cerca(data: ActiveDataset, question: str, threshold: float | None, replay: bool, key: str = "") -> str:
    st.markdown("Non ho riconosciuto la richiesta. Ecco cosa trovo nelle fonti:")
    return norme(data, question, threshold, replay) + " " + minacce(data, question, threshold, replay)


def statistica(data: ActiveDataset, question: str, threshold: float | None, replay: bool, key: str = "") -> str:
    if not data.is_wifi:
        frame = data.frame
        missing = int(frame.isna().sum().sum())
        duplicates = int(frame.duplicated().sum())
        granularity = infer_granularity(frame)
        text = (
            f"Il file contiene **{len(frame):,} righe** e **{len(frame.columns)} colonne**; "
            f"valori mancanti: **{missing:,}**, duplicati: **{duplicates:,}**. "
            f"La struttura sembra **{'aggregata' if granularity.kind == 'aggregato' else 'a livello di evento o persona'}**."
        )
        st.markdown(text)
        st.caption("Per una decisione privacy conferma prima che cosa rappresenta una riga e quali colonne sono conoscibili dall’esterno.")
        return text
    st.markdown(
        "**Il segnale non sembra casuale.** Il numero più alto arriva dopo nel **93%** dei casi; "
        "mescolando i dati accade nel **50%**, come il lancio di una moneta. Tra due giorni consecutivi la continuità "
        "è **32%**, contro **9%** nei dati mescolati."
    )
    st.info(
        "In parole semplici: LOGINCOUNT conserva memoria nel tempo. Non sappiamo però se rappresenti una persona, "
        "un dispositivo o altro; serve il dizionario dati di Roma Capitale.",
        icon=":material/lightbulb:",
    )
    st.caption("Metodo e test completi: Verifica → Il caso LOGINCOUNT → Validazione statistica.")
    return (
        "LOGINCOUNT conserva memoria nel tempo: ordine 93% contro 50% casuale; continuità tra giorni 32% contro 9%. "
        "Il risultato non identifica persone e il significato del campo deve essere confermato da Roma Capitale."
    )


ANSWERS: dict[str, Callable[..., str]] = {
    "verifica": verifica, "correggi": correggi, "minacce": minacce, "norme": norme, "spiega": spiega,
    "rapporto": rapporto, "allarme": allarme, "aiuto": aiuto, "cerca": cerca, "statistica": statistica,
}
