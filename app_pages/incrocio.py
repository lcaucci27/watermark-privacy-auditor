"""Valuta quanto un secondo dataset pubblico restringa i candidati del primo."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

from core.dataset_linkage import (
    exact_linkage, mapped_exact_linkage, report_markdown, suggested_common_keys,
    suggested_mapped_keys, temporal_linkage,
)
from views.dataset import sidebar_picker

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
BUILT_INS = {
    "Milano": {
        "label": "Milano · login giornalieri per zona (ufficiale)",
        "path": DATA_DIR / "milano_wifi_login_sample.csv",
        "url": "https://dati.comune.milano.it/dataset/ds918-openwifimilano-logincountzone",
    },
    "Bologna": {
        "label": "Bologna · elenco aree WiFi (ufficiale)",
        "path": DATA_DIR / "bologna_wifi_aree_sample.csv",
        "url": "https://opendata.comune.bologna.it/explore/dataset/bolognawifi-elenco-aree-segnale/",
    },
}

data = sidebar_picker()
st.title("Incrocia due dataset", icon=":material/join:")
st.markdown(
    "Una riga unica non identifica da sola una persona. Qui rendiamo esplicita l’informazione ausiliaria: "
    "misuriamo quante righe del primo file trovano **un solo candidato** nel secondo."
)

if data is None:
    st.info("Scegli il dataset principale nella barra laterale.", icon=":material/arrow_back:")
    st.stop()

if data.municipality not in BUILT_INS:
    st.info(
        "Per l’incrocio dimostrativo scegli **Milano** o **Bologna** nella barra laterale. "
        "Roma resta nel percorso di verifica singolo: non associamo un secondo dataset non documentato.",
        icon=":material/dataset:",
    )
    st.stop()

built_in = BUILT_INS[data.municipality]
source_choice = st.selectbox(
    "Secondo dataset", [built_in["label"], "Carica un altro CSV"],
    help="L’esempio ufficiale è già incluso; l’upload resta disponibile per altri casi.",
)
if source_choice == built_in["label"]:
    if not built_in["path"].exists():
        st.warning("Esempio non disponibile: esegui `python scripts/fetch_municipal_examples.py`.")
        st.stop()
    auxiliary = pd.read_csv(built_in["path"])
    auxiliary_name = built_in["label"]
    auxiliary_url = built_in["url"]
else:
    uploaded = st.file_uploader(
        "Secondo dataset pubblico", type=["csv"],
        help="Il file resta su questo computer; Watermark non materializza né mostra profili personali.",
    )
    if uploaded is None:
        st.stop()
    auxiliary = pd.read_csv(BytesIO(uploaded.getvalue()), sep=None, engine="python")
    auxiliary_name = uploaded.name
    auxiliary_url = None

default_mode = "Colonne equivalenti" if data.municipality == "Bologna" else "Chiavi uguali"
mode = st.segmented_control(
    "Tipo di collegamento", ["Chiavi uguali", "Colonne equivalenti", "Luogo e finestra temporale"],
    default=default_mode, required=True,
)
identity_present = st.checkbox(
    "Il secondo file contiene un nome, account o altro identificativo",
    help="Questa informazione cambia l’interpretazione: collegare due righe non significa sempre identificare una persona.",
)

try:
    if mode == "Chiavi uguali":
        common = [column for column in data.frame.columns if column in auxiliary.columns]
        keys = st.multiselect(
            "Colonne comuni usate dall’attaccante", common,
            default=suggested_common_keys(data.frame, auxiliary),
        )
        report = exact_linkage(data.frame, auxiliary, keys)
    elif mode == "Colonne equivalenti":
        suggestion = suggested_mapped_keys(data.frame, auxiliary)
        default_left, default_right = suggestion[0] if suggestion else (data.frame.columns[0], auxiliary.columns[0])
        left_key = st.selectbox(
            "Chiave nel dataset principale", list(data.frame.columns),
            index=list(data.frame.columns).index(default_left),
        )
        right_key = st.selectbox(
            "Chiave equivalente nel secondo dataset", list(auxiliary.columns),
            index=list(auxiliary.columns).index(default_right),
        )
        report = mapped_exact_linkage(data.frame, auxiliary, [(left_key, right_key)])
    else:
        left_time = st.selectbox("Tempo nel dataset principale", list(data.frame.columns))
        right_time = st.selectbox("Tempo nel secondo dataset", list(auxiliary.columns))
        left_place = st.selectbox("Luogo nel dataset principale", list(data.frame.columns))
        right_place = st.selectbox("Luogo nel secondo dataset", list(auxiliary.columns))
        tolerance = st.slider("Finestra conosciuta dall’attaccante", 0, 180, 15, 5, format="±%d minuti")
        report = temporal_linkage(
            data.frame, auxiliary, left_time, right_time, left_place, right_place, tolerance
        )
except (KeyError, TypeError, ValueError) as exc:
    st.info(str(exc), icon=":material/info:")
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Righe con un candidato", f"{report.unique_share:.1%}", border=True)
c2.metric("Righe con almeno un match", f"{report.matched_share:.1%}", border=True)
c3.metric("Nuovi attributi collegabili", len(report.auxiliary_attributes), border=True)

if identity_present and report.unique_matches:
    st.error(
        f"Il secondo file assegna un solo candidato a {report.unique_matches:,} righe. "
        "Gli identificativi ausiliari potrebbero quindi essere trasferiti al primo dataset.",
        icon=":material/link:",
    )
elif report.unique_matches and data.row_kind_hint == "aggregato":
    st.info(
        f"{report.unique_matches:,} celle aggregate ricevono un solo record ausiliario. "
        "Questo arricchisce zona o periodo, ma non attribuisce una persona.",
        icon=":material/map:",
    )
elif report.unique_matches:
    st.warning(
        f"{report.unique_matches:,} righe sono collegabili in modo univoco, ma il test non attribuisce ancora un’identità.",
        icon=":material/warning:",
    )
else:
    st.success("Con questa conoscenza ausiliaria non emerge alcun collegamento univoco.", icon=":material/check:")

st.caption(
    "Assunzione verificata: " + report.assumption + " Il risultato vale soltanto se il secondo dataset è realmente disponibile all’attaccante."
)
with st.expander("Dataset e fonti", icon=":material/source:"):
    st.markdown(f"- Dataset principale: [{data.name}]({data.source_url})")
    if auxiliary_url:
        st.markdown(f"- Dataset ausiliario: [{auxiliary_name}]({auxiliary_url})")
    else:
        st.markdown(f"- Dataset ausiliario caricato: `{auxiliary_name}`")
st.download_button(
    "Scarica la valutazione di collegabilità",
    report_markdown(data.name, auxiliary_name, report, identity_present).encode("utf-8"),
    "valutazione_collegabilita.md",
    "text/markdown",
    icon=":material/description:",
)
