"""Scheda minacce: bollettini CSIRT, asset urbani esposti e modello di valutazione."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from core.text_corpus import discover_topics, extract_entities, search, tag_assets, train_text_classifier
from views.corpus_loader import Corpus, corpus_picker

DEFAULT_ASSET = "telecamere IP per videosorveglianza urbana, NVR, VPN per accesso remoto dei manutentori"
MARGIN = dict(l=20, r=20, t=60, b=20)


def _enrich(corpus: Corpus) -> tuple[pd.DataFrame, pd.DataFrame]:
    entities = extract_entities(corpus.text)
    assets = tag_assets(corpus.text)
    table = pd.DataFrame({"titolo": corpus.title}).join(entities)
    table["asset"] = assets.apply(lambda row: ", ".join(row.index[row]), axis=1)
    if corpus.date is not None:
        table.insert(0, "data", corpus.date)
    if corpus.label:
        table["etichetta"] = corpus.frame[corpus.label]
    return table, assets


def render() -> Corpus | None:
    st.caption("BOLLETTINI DI SICUREZZA · CSIRT ITALIA")
    corpus = corpus_picker("csirt", "csirt", "Bollettini e allarmi")
    if corpus is None:
        return None
    table, assets = _enrich(corpus)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Bollettini", f"{len(table):,}", border=True)
    cves = {cve for value in table["cve"] if value for cve in value.split(", ")}
    k2.metric("CVE distinte", f"{len(cves):,}", border=True)
    k3.metric("CVSS medio", f"{table['cvss_max'].mean():.1f}" if table["cvss_max"].notna().any() else "n/d", border=True)
    k4.metric("Su asset urbani", f"{assets.any(axis=1).mean() * 100:.0f}%", border=True)

    left, right = st.columns(2)
    with left.container(border=True, height="stretch"):
        counts = assets.sum().sort_values().rename("bollettini").reset_index().rename(columns={"index": "famiglia"})
        figure = px.bar(counts, x="bollettini", y="famiglia", orientation="h", title="Bollettini per famiglia di asset")
        figure.update_layout(margin=MARGIN, yaxis_title="")
        st.plotly_chart(figure, width="stretch")
    with right.container(border=True, height="stretch"):
        if corpus.date is not None and corpus.date.notna().any():
            monthly = (
                assets.assign(mese=corpus.date.dt.to_period("M").dt.to_timestamp())
                .dropna(subset=["mese"]).groupby("mese").sum().reset_index()
                .melt(id_vars="mese", var_name="famiglia", value_name="bollettini")
            )
            trend = px.line(monthly, x="mese", y="bollettini", color="famiglia", title="Andamento mensile per famiglia")
            trend.update_layout(margin=MARGIN, legend_title_text="")
            st.plotly_chart(trend, width="stretch")
        else:
            st.info("Seleziona la colonna data per vedere l’andamento nel tempo.", icon=":material/calendar_month:")
    st.caption("Le famiglie di asset derivano da parole chiave esplicite nel testo (`ASSET_TAXONOMY`); un bollettino può appartenere a più famiglie.")

    with st.container(border=True):
        st.subheader("Esposizione di un’infrastruttura", icon=":material/radar:")
        query = st.text_area("Descrivi asset, fornitori e tecnologie in uso", DEFAULT_ASSET, key="asset_query")
        top_n = st.slider("Bollettini da mostrare", 5, 30, 10, key="asset_top")
        hits = search(corpus.index, query, top_n)
        if hits.empty:
            st.warning("Nessun bollettino condivide termini con la descrizione. Aggiungi fornitori o prodotti.", icon=":material/search_off:")
        else:
            matched = table.loc[hits.index].assign(similarità=hits.round(3))
            e1, e2, e3 = st.columns(3)
            e1.metric("Bollettini pertinenti", len(matched), border=True)
            e2.metric("CVSS massimo", f"{matched['cvss_max'].max():.1f}" if matched["cvss_max"].notna().any() else "n/d", border=True)
            e3.metric("CVE citate", int(matched["n_cve"].sum()), border=True)
            st.dataframe(
                matched, width="stretch", hide_index=True,
                column_config={"similarità": st.column_config.ProgressColumn("Similarità", min_value=0, max_value=1, format="%.2f")},
            )
            st.caption("Similarità coseno TF-IDF tra descrizione e testo del bollettino: misura termini condivisi, non conferma che la versione in uso sia vulnerabile.")
            st.download_button(
                "Scarica bollettini pertinenti", matched.to_csv(index=False).encode("utf-8"),
                "esposizione_asset.csv", "text/csv", icon=":material/download:",
            )

    with st.container(border=True):
        st.subheader("Modello di valutazione delle minacce", icon=":material/model_training:")
        if corpus.label:
            run = st.button("Addestra sul testo dei bollettini", type="primary", icon=":material/play_arrow:", key="train_threat")
            if run:
                try:
                    with st.spinner("Addestramento…"):
                        st.session_state["threat_model"] = train_text_classifier(
                            corpus.frame.assign(_testo=corpus.text), "_testo", corpus.label
                        )
                    st.session_state["threat_model_key"] = (len(corpus.frame), corpus.label)
                except ValueError as exc:
                    st.error(str(exc), icon=":material/error:")
            model = st.session_state.get("threat_model")
            if model is not None and st.session_state.get("threat_model_key") == (len(corpus.frame), corpus.label):
                cards = st.columns(4)
                labels = {"Balanced accuracy": "Accuratezza bilanciata", "Weighted F1": "F1 ponderato", "Test rows": "Testi di test"}
                for card, (name, value) in zip(cards, model.metrics.items()):
                    card.metric(labels.get(name, name), f"{value:.3f}" if isinstance(value, float) else value, border=True)
                st.caption("TF-IDF + regressione logistica. Metriche sul 25% dei bollettini escluso dall’addestramento, seed 42.")
                st.dataframe(model.top_terms, width="stretch", hide_index=True)
                new_text = st.text_area("Testo di un nuovo allarme da valutare", key="new_alert")
                if new_text.strip():
                    probabilities = pd.DataFrame({
                        "etichetta": model.model.classes_,
                        "probabilità": model.model.predict_proba([new_text])[0],
                    }).sort_values("probabilità", ascending=False)
                    st.dataframe(
                        probabilities, width="stretch", hide_index=True,
                        column_config={"probabilità": st.column_config.ProgressColumn("Probabilità", min_value=0, max_value=1, format="%.2f")},
                    )
        else:
            n_topics = st.slider("Temi da individuare", 3, 12, 6, key="topics_n")
            try:
                topics, _ = discover_topics(corpus.text, n_topics)
                st.dataframe(topics, width="stretch", hide_index=True)
                st.caption("NMF su TF-IDF: raggruppa bollettini con lessico simile. Seleziona una colonna etichetta per addestrare un classificatore supervisionato.")
            except ValueError as exc:
                st.info(str(exc), icon=":material/info:")
    return corpus
