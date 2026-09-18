"""Risposte dell'assistente: ogni intenzione esegue gli strumenti locali, mostra i passaggi
e restituisce un riassunto in parole semplici (riusabile dal percorso LLM opzionale)."""

from __future__ import annotations

import re
from collections.abc import Callable

import pandas as pd
import streamlit as st

from core.audit_agent import INFRASTRUCTURE_QUERY, RULE_QUERY, run_audit
from core.linkability import scan_counters
from core.privacy import DIRECT, QUASI, SENSITIVE, anonymize, classify_columns, reidentification_risk
from core.privacy_optimizer import Variant, publish, recommend
from core.text_corpus import best_passages, search
from core.threat_model import bulletin_text, explain
from core.wifi_dataset import PUBLISHED_KEYS, unique_share
from views.dataset import ActiveDataset
from views.shared import csirt_corpus, frontier_chart, garante_corpus, impact_model, variants

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
            f" In più, la colonna **{row['colonna']}** si comporta come un contatore personale di accessi: "
            "collega tra loro le sessioni della stessa persona, giorno dopo giorno."
        )
    st.markdown(summary + "\n\nPuoi chiedermi *correggilo* o *perché è un problema?*")
    return summary


def _verifica_generica(data: ActiveDataset, replay: bool) -> str:
    with _step("Classifico le colonne per tipo di dato personale", replay):
        scan = classify_columns(data.frame)
        st.dataframe(scan, hide_index=True, width="stretch")
    quasi = scan.loc[scan["categoria"] == QUASI, "variabile"].tolist()
    counts = scan["categoria"].value_counts()
    c1, c2, c3 = st.columns(3)
    c1.metric("Identificativi diretti", int(counts.get(DIRECT, 0)), border=True)
    c2.metric("Quasi-identificativi", len(quasi), border=True)
    c3.metric("Dati sensibili", int(counts.get(SENSITIVE, 0)), border=True)
    summary = f"Ho trovato {int(counts.get(DIRECT, 0))} identificativi diretti e {len(quasi)} quasi-identificativi."
    if quasi:
        with _step("Misuro quante righe sono uniche sui quasi-identificativi", replay):
            risk = reidentification_risk(data.frame, quasi, 5).metrics
        summary += f" Il {risk['Righe uniche %']}% delle righe è unico su {', '.join(quasi)}."
    st.markdown(summary)
    return summary


def correggi(data: ActiveDataset, question: str, threshold: float | None, replay: bool, key: str = "") -> str:
    max_risk = threshold or DEFAULT_RISK
    if not data.is_wifi:
        quasi = classify_columns(data.frame).query("categoria == @QUASI")["variabile"].tolist()
        direct = classify_columns(data.frame).query("categoria == @DIRECT")["variabile"].tolist()
        if not quasi:
            st.markdown("Non ho trovato quasi-identificativi da generalizzare.")
            return "Nessuna correzione necessaria sui quasi-identificativi."
        with _step("Generalizzo i quasi-identificativi fino a 5 righe per gruppo", replay):
            result = anonymize(data.frame, direct, quasi, 5)
        st.download_button("Scarica il file corretto", result.data.to_csv(index=False).encode("utf-8"),
                           "dataset_corretto.csv", "text/csv", icon=":material/download:", key=f"dlg_{key}")
        return " ".join(result.log)

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
    csirt, index = csirt_corpus()
    if csirt is None:
        st.markdown("Non trovo i bollettini CSIRT in `data/`.")
        return "Bollettini non disponibili."
    with _step(f"Cerco tra {len(csirt):,} bollettini CSIRT quelli sui sistemi WiFi", replay):
        hits = search(index, f"{question} {INFRASTRUCTURE_QUERY}", 8)
    table = csirt.loc[hits.index, ["codice", "titolo", "impatto_classe", "n_cve_sfruttate"]].rename(
        columns={"impatto_classe": "impatto ACN", "n_cve_sfruttate": "CVE sfruttate"})
    critical = int((table["impatto ACN"] == "Critico").sum())
    exploited = int((table["CVE sfruttate"].fillna(0) > 0).sum())
    st.markdown(f":orange-badge[:material/security: {len(table)} bollettini pertinenti]")
    st.dataframe(table, hide_index=True, width="stretch")
    summary = (f"Sui sistemi che producono questi dati (access point, captive portal, accesso remoto) ci sono {len(table)} "
               f"bollettini pertinenti: {critical} con impatto critico, {exploited} con vulnerabilità già sfruttate in rete.")
    st.markdown(summary)
    return summary


def norme(data: ActiveDataset, question: str, threshold: float | None, replay: bool, key: str = "") -> str:
    garante, index = garante_corpus()
    if garante is None:
        st.markdown("Non trovo i provvedimenti del Garante in `data/`.")
        return "Provvedimenti non disponibili."
    query = f"{question} {RULE_QUERY}"
    with _step(f"Cerco nei {len(garante)} documenti del Garante", replay):
        hits = search(index, query, 3)
    quotes = []
    for position in hits.index:
        passage = best_passages(index, str(garante.loc[position, "testo"]), query, 1)[0]
        st.caption(str(garante.loc[position, "titolo"]))
        st.markdown(f"> {passage}")
        quotes.append(passage)
    return "Il Garante: " + " … ".join(quotes[:2])


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
3. Resta una sola spiegazione: **è il contatore personale**. Chi lo vede collega le sessioni della stessa persona tra giorni e luoghi.

Nessun documento ufficiale descrive questa colonna: è una deduzione dai dati, per questo diciamo *si comporta come*."""
    st.markdown(text)
    return text


def rapporto(data: ActiveDataset, question: str, threshold: float | None, replay: bool, key: str = "") -> str:
    if not data.is_wifi:
        st.markdown("Il rapporto completo è disponibile per il dataset WiFi di esempio.")
        return "Rapporto non disponibile per questo file."
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
    csirt, index = csirt_corpus()
    model = impact_model(csirt) if csirt is not None else None
    if model is None:
        st.markdown("Il modello di impatto richiede i bollettini CSIRT in `data/`.")
        return "Modello non disponibile."
    with _step("Stimo l'impatto sistemico con il modello addestrato sui bollettini CSIRT", replay):
        # Un allarme incollato non ha i campi strutturati del CSIRT: li deduce dal testo.
        alert = pd.DataFrame({
            "sintesi": [question],
            "n_cve_sfruttate": [int(bool(re.search(r"sfruttament|sfruttat|exploited", question, re.IGNORECASE)))],
            "n_cve_con_poc": [int(bool(re.search(r"\bpoc\b|proof of concept", question, re.IGNORECASE)))],
        })
        predicted, drivers = explain(model, bulletin_text(alert).iloc[0])
        st.dataframe(drivers, hide_index=True, width="stretch")
    with _step("Cerco bollettini simili già pubblicati", replay):
        similar = csirt.loc[search(index, question, 3).index, ["codice", "titolo", "impatto_classe"]]
    colour = {"Critico": "red", "Alto": "orange", "Medio": "blue"}.get(predicted, "gray")
    st.markdown(f":{colour}-badge[Impatto stimato: {predicted}]")
    st.dataframe(similar, hide_index=True, width="stretch")
    words = ", ".join(drivers["parola"].head(4))
    summary = f"Impatto stimato **{predicted}**. Le parole che hanno pesato di più: {words}."
    st.markdown(summary)
    return summary


def aiuto(data: ActiveDataset, question: str, threshold: float | None, replay: bool, key: str = "") -> str:
    text = """Posso aiutarti a decidere se e come pubblicare un dataset:

- *Questo dataset è pubblicabile?*: verifico se le persone sono riconoscibili e se ci sono pseudonimi nascosti.
- *Correggilo sotto il 10%*: provo 36 versioni e scelgo quella che conserva più informazione.
- *Quali sistemi sono a rischio?*: cerco nei bollettini CSIRT.
- *Cosa dice il Garante?*: cito i provvedimenti parola per parola.
- *Incolla il testo di un allarme*: stimo l'impatto e spiego perché.
- *Fammi il rapporto*: preparo il documento per il DPO."""
    st.markdown(text)
    return text


def cerca(data: ActiveDataset, question: str, threshold: float | None, replay: bool, key: str = "") -> str:
    st.markdown("Non ho riconosciuto la richiesta. Ecco cosa trovo nelle fonti:")
    return norme(data, question, threshold, replay) + " " + minacce(data, question, threshold, replay)


ANSWERS: dict[str, Callable[..., str]] = {
    "verifica": verifica, "correggi": correggi, "minacce": minacce, "norme": norme, "spiega": spiega,
    "rapporto": rapporto, "allarme": allarme, "aiuto": aiuto, "cerca": cerca,
}
