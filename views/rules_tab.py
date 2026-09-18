"""Scheda norme: ricerca nei provvedimenti del Garante con citazione estrattiva."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from core.text_corpus import best_passages, search
from views.corpus_loader import Corpus, corpus_picker

PRESET_QUERIES = {
    "Contatori intelligenti": "contatori intelligenti smart meter consumi energetici dati personali profilazione",
    "Videosorveglianza urbana": "videosorveglianza comune telecamere spazi pubblici conservazione immagini",
    "Biometria nella PA": "dati biometrici riconoscimento facciale rilevazione presenze pubblica amministrazione",
    "Telemetria e IoT": "dispositivi connessi telemetria geolocalizzazione indirizzo IP identificativi",
    "Open data e anonimizzazione": "pubblicazione open data anonimizzazione dati personali identificabili trasparenza",
    "WiFi pubblico": "servizio pubblico Wi-Fi gratuito autenticazione utenti dati di navigazione conservazione",
}


def show_matches(corpus: Corpus, query: str, top_n: int) -> pd.DataFrame:
    """Elenca i documenti pertinenti con i passaggi testuali che li rendono tali."""
    hits = search(corpus.index, query, top_n)
    if hits.empty:
        st.warning("Nessun documento condivide termini con la richiesta.", icon=":material/search_off:")
        return pd.DataFrame()
    rows = []
    for position, score in hits.items():
        passages = best_passages(corpus.index, corpus.text.loc[position], query)
        with st.container(border=True):
            st.markdown(f"**{corpus.title.loc[position]}**")
            meta = f"Similarità {score:.2f}"
            if corpus.date is not None and pd.notna(corpus.date.loc[position]):
                meta += f" · {corpus.date.loc[position]:%d/%m/%Y}"
            st.caption(meta)
            for passage in passages:
                st.markdown(f"> {passage}")
        rows.append({"titolo": corpus.title.loc[position], "similarità": round(score, 3), "passaggi": " … ".join(passages)})
    return pd.DataFrame(rows)


def render() -> Corpus | None:
    st.caption("PROVVEDIMENTI E LINEE GUIDA · GARANTE PRIVACY")
    corpus = corpus_picker(
        "garante", "garante", "Archivio provvedimenti", {"text": ("testo",), "title": ("titolo",)}
    )
    if corpus is None:
        return None
    st.metric("Documenti indicizzati", f"{len(corpus.frame):,}", border=True)

    preset = st.pills("Casi d’uso", list(PRESET_QUERIES), key="rules_preset")
    query = st.text_input(
        "Trattamento da verificare",
        PRESET_QUERIES.get(preset, PRESET_QUERIES["Open data e anonimizzazione"]),
        key=f"rules_query_{preset}",
    )
    top_n = st.slider("Documenti da mostrare", 3, 15, 5, key="rules_top")
    matches = show_matches(corpus, query, top_n)
    st.caption("Passaggi estratti dal testo originale, senza riscrittura. La pertinenza misura termini condivisi e non sostituisce una valutazione legale.")
    if not matches.empty:
        st.download_button(
            "Scarica riferimenti", matches.to_csv(index=False).encode("utf-8"),
            "riferimenti_garante.csv", "text/csv", icon=":material/download:",
        )
    return corpus
