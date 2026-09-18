"""Percorso guidato per dataset comunali con schema non preconfigurato."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from core.generic_privacy import (
    aggregate_measures,
    audit_generic,
    infer_granularity,
    protect_generic,
    report_markdown,
    suggested_roles,
)
from views.dataset import ActiveDataset


def _key(frame: pd.DataFrame) -> str:
    sample = pd.util.hash_pandas_object(frame.head(200), index=True).sum()
    return f"generic_{len(frame)}_{int(sample) & 0xFFFFFFFF:08x}"


def render(data: ActiveDataset) -> None:
    frame = data.frame
    fingerprint = _key(frame)
    inferred = infer_granularity(frame)
    default_direct, default_quasi, default_sensitive = suggested_roles(frame)

    if data.source_url:
        st.info(
            f"Secondo caso reale: **{data.municipality}** pubblica dati già aggregati per zona e ora. "
            "Watermark applica lo stesso motore, ma cambia il test in base all’unità della riga.",
            icon=":material/location_city:",
        )

    with st.container(border=True):
        st.subheader("Che cosa rappresenta una riga?", icon=":material/table_rows:")
        purpose_label = st.segmented_control(
            "Destinazione del file",
            ["Uso interno autorizzato", "Pubblicazione open data"],
            default="Pubblicazione open data",
            required=True,
            key=f"{fingerprint}_purpose",
        )
        purpose = "interno" if purpose_label == "Uso interno autorizzato" else "pubblicazione"
        row_label = st.segmented_control(
            "Unità della riga",
            ["Persona o evento", "Cella aggregata"],
            default="Cella aggregata" if data.row_kind_hint == "aggregato" or inferred.kind == "aggregato" else "Persona o evento",
            required=True,
            key=f"{fingerprint}_kind",
        )
        row_kind = "aggregato" if row_label == "Cella aggregata" else "individuale"
        st.caption("Suggerimento automatico: " + " ".join(inferred.reasons))

    with st.expander("Conferma il significato delle colonne", icon=":material/tune:"):
        st.caption("Il nome di una colonna è solo un indizio: il DPO o il responsabile del dato conferma i ruoli.")
        direct = st.multiselect(
            "Identificativi diretti da rimuovere",
            list(frame.columns),
            default=default_direct,
            key=f"{fingerprint}_direct",
        )
        quasi = st.multiselect(
            "Informazioni che un estraneo potrebbe già conoscere",
            [column for column in frame.columns if column not in direct],
            default=[column for column in default_quasi if column not in direct],
            key=f"{fingerprint}_quasi",
        )
        sensitive_options = ["Nessuno"] + [column for column in frame.columns if column not in direct]
        sensitive = st.selectbox(
            "Dato da proteggere",
            sensitive_options,
            index=sensitive_options.index(default_sensitive[0]) if default_sensitive else 0,
            key=f"{fingerprint}_sensitive",
        )
        candidates = aggregate_measures(frame)
        measure = None
        if row_kind == "aggregato":
            measure = st.selectbox(
                "Numero di persone o eventi nella cella",
                ["Da indicare"] + candidates,
                index=1 if candidates else 0,
                key=f"{fingerprint}_measure",
            )
            measure = None if measure == "Da indicare" else measure
        k = st.slider("Numero minimo per gruppo o cella", 3, 20, 5, key=f"{fingerprint}_k")

    audit = audit_generic(
        frame, row_kind, direct, quasi, None if sensitive == "Nessuno" else sensitive, k, measure, purpose
    )
    colour = "green" if audit.outcome == "Compatibile con pubblicazione" else "red" if audit.outcome == "Da correggere" else "orange"
    st.markdown(f":{colour}-badge[{audit.outcome}]")

    metrics = list(audit.metrics.items())[:4]
    cards = st.columns(len(metrics))
    for card, (label, value) in zip(cards, metrics):
        suffix = "%" if label.endswith("%") else ""
        card.metric(label, f"{value}{suffix}", border=True)

    with st.container(border=True):
        st.subheader("Decisione proposta", icon=":material/rule:")
        for reason in audit.reasons:
            st.markdown(f"- {reason}")
        st.caption("La decisione finale resta al titolare del trattamento e al DPO, sulla base di scopo e base giuridica.")

    protected, log = protect_generic(frame, row_kind, direct, quasi, k, measure)
    with st.container(horizontal=True):
        st.download_button(
            "Scarica la versione protetta",
            protected.to_csv(index=False).encode("utf-8"),
            "dataset_protetto.csv",
            "text/csv",
            icon=":material/download:",
            type="primary",
        )
        st.download_button(
            "Scarica la valutazione",
            report_markdown(data.name, audit, k).encode("utf-8"),
            "valutazione_privacy.md",
            "text/markdown",
            icon=":material/description:",
        )
    if log:
        st.caption("Interventi applicati: " + " · ".join(log))

    with st.expander("Come sono state classificate le colonne", icon=":material/schema:"):
        st.dataframe(audit.scan, hide_index=True, width="stretch")
    if data.source_url:
        st.markdown(f"[Apri il dataset ufficiale del Comune di {data.municipality}]({data.source_url})")
    with st.expander("Perché il controllo è portabile", icon=":material/account_tree:"):
        st.markdown(
            "La logica non cerca nomi fissati per Roma, Bologna o Milano. Prima inferisce se ogni riga descrive "
            "un evento o una cella aggregata; poi il responsabile conferma identificativi, informazioni conoscibili, "
            "dato da proteggere e soglia. I connettori caricano i file, mentre regole, incrocio e protezione restano "
            "nello stesso motore `core/`. Un nuovo Comune richiede quindi una mappatura dello schema, non una "
            "riscrittura dell’audit."
        )
