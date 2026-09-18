"""Scheda telemetria: dati personali nei flussi, rischio di re-identificazione,
anonimizzazione e collegamento con bollettini e provvedimenti."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from core.privacy import (
    DIRECT, QUASI, SENSITIVE, anonymize, classify_columns, inference_attack, profile_exposure,
    reidentification_risk,
)
from core.text_corpus import search
from views.corpus_loader import Corpus

NONE = "Nessuno"
CATEGORY_QUERIES = {
    DIRECT: "identificativi diretti dati personali email telefono indirizzo IP codice fiscale",
    QUASI: "pseudonimizzazione anonimizzazione re-identificazione dati di localizzazione",
    SENSITIVE: "categorie particolari di dati salute biometrici articolo 9",
}


def _risk_cards(before: dict, after: dict | None) -> None:
    labels = ["k minimo", "Righe uniche %", "Rischio massimo %", "l-diversità minima"]
    cards = st.columns(4)
    for card, label in zip(cards, labels):
        if label not in before:
            continue
        delta = None if after is None or label not in after else after[label] - before[label]
        value = before[label] if after is None else after[label]
        inverse = label in {"Righe uniche %", "Rischio massimo %"}
        card.metric(label, value, delta=None if delta is None else round(delta, 1),
                    delta_color="inverse" if inverse else "normal", border=True)


def _links(scan: pd.DataFrame, corpora: dict[str, Corpus | None]) -> None:
    found = [category for category in CATEGORY_QUERIES if (scan["categoria"] == category).any()]
    available = {name: corpus for name, corpus in corpora.items() if corpus is not None}
    if not found:
        return
    with st.container(border=True):
        st.subheader("Riferimenti per le colonne segnalate", icon=":material/link:")
        if not available:
            st.info("Carica bollettini CSIRT o provvedimenti del Garante per collegare le colonne segnalate a minacce e norme.", icon=":material/info:")
            return
        for category in found:
            columns = scan.loc[scan["categoria"] == category, "variabile"].tolist()
            query = f"{CATEGORY_QUERIES[category]} {' '.join(columns)}"
            st.markdown(f"**{category}** · {', '.join(columns)}")
            for name, corpus in available.items():
                hits = search(corpus.index, query, 3)
                for position, score in hits.items():
                    st.caption(f"{name} · {corpus.title.loc[position]} · similarità {score:.2f}")


def render(data: pd.DataFrame, signature: tuple, corpora: dict[str, Corpus | None]) -> None:
    st.caption("TELEMETRIA E DATI PERSONALI")
    scan = classify_columns(data)
    counts = scan["categoria"].value_counts()
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Identificativi diretti", int(counts.get(DIRECT, 0)), border=True)
    k2.metric("Quasi-identificativi", int(counts.get(QUASI, 0)), border=True)
    k3.metric("Attributi sensibili", int(counts.get(SENSITIVE, 0)), border=True)
    k4.metric("Colonne analizzate", len(scan), border=True)
    with st.container(border=True):
        st.subheader("Classificazione delle colonne", icon=":material/policy:")
        st.dataframe(scan, width="stretch", hide_index=True)
        st.caption("Regole esplicite su nome colonna e formato dei valori (email, codice fiscale, IBAN, telefono, IP). Verificare le colonne classificate come Altro.")

    _links(scan, corpora)

    columns = data.columns.tolist()
    with st.container(border=True):
        st.subheader("Rischio di re-identificazione", icon=":material/fingerprint:")
        quasi = st.multiselect(
            "Quasi-identificativi noti a un attaccante", columns,
            default=scan.loc[scan["categoria"] == QUASI, "variabile"].tolist(), key="privacy_quasi",
        )
        direct = scan.loc[scan["categoria"] == DIRECT, "variabile"].tolist()
        sensitive_default = scan.loc[scan["categoria"] == SENSITIVE, "variabile"].tolist()
        options = [NONE] + [column for column in columns if column not in quasi]
        sensitive = st.selectbox(
            "Attributo sensibile da proteggere", options,
            index=options.index(sensitive_default[0]) if sensitive_default and sensitive_default[0] in options else 0,
            key="privacy_sensitive",
        )
        k_target = st.slider("k richiesto", 2, 20, 5, key="privacy_k")
        run = st.button("Misura e anonimizza", type="primary", icon=":material/shield:", width="stretch")

    sensitive_column = None if sensitive == NONE else sensitive
    if run:
        if not quasi:
            st.error("Seleziona almeno un quasi-identificativo.", icon=":material/error:")
        else:
            with st.spinner("Calcolo del rischio…"):
                before = reidentification_risk(data, quasi, k_target, sensitive_column)
                anonymized = anonymize(data, direct, quasi, k_target)
                after = reidentification_risk(anonymized.data, quasi, k_target, sensitive_column)
                attacks = {}
                if sensitive_column:
                    try:
                        attacks = {
                            "Originale": inference_attack(data, quasi, sensitive_column),
                            "Anonimizzato": inference_attack(anonymized.data, quasi, sensitive_column),
                        }
                    except ValueError as exc:
                        st.warning(str(exc), icon=":material/warning:")
            st.session_state["privacy_run"] = {
                "signature": signature, "params": (tuple(quasi), sensitive_column, k_target),
                "before": before, "after": after, "anonymized": anonymized, "attacks": attacks,
            }

    state = st.session_state.get("privacy_run")
    if not state or state["signature"] != signature or state["params"] != (tuple(quasi), sensitive_column, k_target):
        return

    st.markdown("**Prima dell’anonimizzazione**")
    _risk_cards(state["before"].metrics, None)
    st.markdown("**Dopo l’anonimizzazione**")
    _risk_cards(state["before"].metrics, state["after"].metrics)
    anonymized = state["anonymized"]
    for line in anonymized.log:
        st.caption(line)
    st.caption(f"Righe conservate: {len(anonymized.data):,} su {len(data):,}. Rischio calcolato come 1 / dimensione della classe di equivalenza.")

    if state["attacks"]:
        with st.container(border=True):
            st.subheader(f"Attacco di inferenza su {sensitive_column}", icon=":material/psychology_alt:")
            table = pd.DataFrame({name: result.metrics for name, result in state["attacks"].items()})
            st.dataframe(table, width="stretch")
            st.caption(
                "Random Forest addestrata a dedurre l’attributo sensibile dai soli quasi-identificativi, "
                "misurata sul 30% delle righe escluso dall’addestramento. Un vantaggio alto dopo l’anonimizzazione "
                "indica che k-anonimato non basta: serve l-diversità o la rimozione della correlazione."
            )
            with st.form("profile_form"):
                st.markdown("**Simula un residente**: quanti record coincidono e cosa deduce l’attaccante")
                inputs = st.columns(min(len(quasi), 4))
                profile = {
                    column: inputs[i % len(inputs)].selectbox(column, sorted(data[column].dropna().unique().tolist(), key=str))
                    for i, column in enumerate(quasi)
                }
                submitted = st.form_submit_button("Valuta profilo", icon=":material/person_search:")
            if submitted:
                matches = profile_exposure(data, profile)
                model = state["attacks"]["Originale"].model
                probabilities = model.predict_proba(pd.DataFrame([profile]))[0]
                best = probabilities.argmax()
                p1, p2 = st.columns(2)
                p1.metric("Record con lo stesso profilo", matches, border=True)
                p2.metric(f"{sensitive_column} stimato", f"{model.classes_[best]} · {probabilities[best]:.0%}", border=True)

    st.download_button(
        "Scarica dataset anonimizzato", anonymized.data.to_csv(index=False).encode("utf-8"),
        "telemetria_anonimizzata.csv", "text/csv", icon=":material/download:",
    )
