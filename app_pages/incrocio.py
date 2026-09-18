"""Mostra quanto un secondo dataset pubblico arricchisce il primo."""

from __future__ import annotations

from io import BytesIO

import pandas as pd
import streamlit as st

from core.dataset_linkage import (
    exact_linkage,
    mapped_exact_linkage,
    report_markdown,
    suggested_common_keys,
    suggested_mapped_keys,
    temporal_linkage,
)
from core.municipal_catalog import LINKAGE_BY_PRIMARY
from views.dataset import sidebar_picker

data = sidebar_picker()
st.title("Incrocio tra dataset", icon=":material/join:")
st.caption("Verifichiamo se un secondo file aggiunge informazioni a ogni riga, senza cercare persone reali.")

if data is None:
    st.info("Scegli il dataset principale nella barra laterale.", icon=":material/arrow_back:")
    st.stop()

example = LINKAGE_BY_PRIMARY.get(data.source_key)
if example is None:
    st.info(
        "Questa demo usa gli abbinamenti ufficiali di Milano e Bologna. "
        "Scegline uno nella barra laterale; Roma resta nella verifica del singolo dataset.",
        icon=":material/dataset:",
    )
    st.stop()

auxiliary_source = example.auxiliary
auxiliary = pd.read_csv(auxiliary_source.path)
auxiliary_name = auxiliary_source.name
auxiliary_url = auxiliary_source.url
mode = "Esempio ufficiale"

with st.expander("Cambia confronto", icon=":material/tune:"):
    source_choice = st.selectbox(
        "Secondo dataset", [auxiliary_source.name, "Carica un altro CSV"],
        help="L’esempio ufficiale è già pronto. L’upload serve per provare altri enti.",
    )
    if source_choice != auxiliary_source.name:
        uploaded = st.file_uploader("File CSV", type=["csv"])
        if uploaded is None:
            st.info("Carica il secondo CSV per continuare.")
            st.stop()
        auxiliary = pd.read_csv(BytesIO(uploaded.getvalue()), sep=None, engine="python")
        auxiliary_name, auxiliary_url = uploaded.name, None
        mode = st.selectbox(
            "Come si collegano le righe",
            ["Chiavi con lo stesso nome", "Colonne equivalenti", "Luogo e finestra temporale"],
        )

identity_present = st.toggle(
    "Il secondo file contiene nomi o account",
    help="Attivalo solo se il secondo file può trasferire una vera identità al primo.",
)

try:
    if mode == "Esempio ufficiale":
        report = mapped_exact_linkage(data.frame, auxiliary, list(example.key_pairs))
    elif mode == "Chiavi con lo stesso nome":
        common = [column for column in data.frame.columns if column in auxiliary.columns]
        keys = st.multiselect(
            "Colonne comuni", common, default=suggested_common_keys(data.frame, auxiliary),
        )
        report = exact_linkage(data.frame, auxiliary, keys)
    elif mode == "Colonne equivalenti":
        suggestion = suggested_mapped_keys(data.frame, auxiliary)
        default_left, default_right = suggestion[0] if suggestion else (data.frame.columns[0], auxiliary.columns[0])
        left_key = st.selectbox(
            "Colonna nel primo dataset", list(data.frame.columns),
            index=list(data.frame.columns).index(default_left),
        )
        right_key = st.selectbox(
            "Colonna equivalente nel secondo", list(auxiliary.columns),
            index=list(auxiliary.columns).index(default_right),
        )
        report = mapped_exact_linkage(data.frame, auxiliary, [(left_key, right_key)])
    else:
        left_time = st.selectbox("Tempo nel primo dataset", list(data.frame.columns))
        right_time = st.selectbox("Tempo nel secondo dataset", list(auxiliary.columns))
        left_place = st.selectbox("Luogo nel primo dataset", list(data.frame.columns))
        right_place = st.selectbox("Luogo nel secondo dataset", list(auxiliary.columns))
        tolerance = st.slider("Finestra temporale", 0, 180, 15, 5, format="±%d minuti")
        report = temporal_linkage(
            data.frame, auxiliary, left_time, right_time, left_place, right_place, tolerance
        )
except (KeyError, TypeError, ValueError) as exc:
    st.info(str(exc), icon=":material/info:")
    st.stop()

with st.container(border=True):
    st.caption("CONFRONTO PRONTO")
    st.subheader(f"{data.municipality}: due fonti, una lettura più ricca")
    st.markdown(f"**Primo file:** {data.name}  \n**Secondo file:** {auxiliary_name}")
    st.caption("Collegamento usato: " + " + ".join(report.keys))

c1, c2, c3 = st.columns(3)
c1.metric("Collegate una a una", f"{report.unique_share:.1%}", border=True)
c2.metric("Con almeno un collegamento", f"{report.matched_share:.1%}", border=True)
c3.metric("Nuove colonne disponibili", len(report.auxiliary_attributes), border=True)

if identity_present and report.unique_matches:
    st.error(
        f"Il secondo file può trasferire un’identità a {report.unique_matches:,} righe. "
        "Il DPO deve fermare o ridurre la diffusione.",
        icon=":material/link:",
    )
elif report.unique_matches:
    st.info(
        f"{report.unique_matches:,} righe ricevono un solo record ausiliario. "
        "Il risultato arricchisce il dato, ma non identifica una persona.",
        icon=":material/hub:",
    )
else:
    st.success("Con queste chiavi non emerge alcun collegamento uno a uno.", icon=":material/check:")

st.caption(
    "Il risultato vale solo per le chiavi mostrate e per un secondo file realmente disponibile. "
    "Collegare due record non equivale a identificare una persona."
)
with st.container(horizontal=True):
    st.download_button(
        "Scarica la valutazione", report_markdown(data.name, auxiliary_name, report, identity_present).encode("utf-8"),
        "valutazione_collegabilita.md", "text/markdown", icon=":material/download:", type="primary",
    )
    st.link_button("Fonte principale", data.source_url, icon=":material/open_in_new:")
    if auxiliary_url:
        st.link_button("Seconda fonte", auxiliary_url, icon=":material/open_in_new:")
