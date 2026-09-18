"""Dataset attivo, scelto una volta nella barra laterale e condiviso da tutte le pagine."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

import pandas as pd
import streamlit as st

from core.wifi_dataset import is_wifi_dataset, prepare
from views.shared import WIFI_FILE, load_wifi

EXAMPLE = "WiFi Roma Capitale · ultimi 14 giorni"
UPLOAD = "Carica un file CSV"


@dataclass
class ActiveDataset:
    name: str
    frame: pd.DataFrame
    is_wifi: bool
    removed: int


@st.cache_data(show_spinner="Lettura del file…", max_entries=5)
def _read_upload(raw: bytes) -> tuple[pd.DataFrame, bool, int]:
    table = pd.read_csv(BytesIO(raw), sep=None, engine="python")
    if is_wifi_dataset(table):
        frame = prepare(table)
        return frame, True, len(table) - len(frame)
    return table, False, 0


def sidebar_picker() -> ActiveDataset | None:
    with st.sidebar:
        st.subheader("Dataset da verificare", icon=":material/dataset:")
        source = st.segmented_control(
            "Origine", [EXAMPLE, UPLOAD], default=EXAMPLE, required=True, key="dataset_source",
            label_visibility="collapsed",
        )
        if source == UPLOAD:
            uploaded = st.file_uploader("File CSV", type=["csv"], key="dataset_upload")
            if uploaded is None:
                st.caption("Il file resta su questo computer.")
                return None
            frame, is_wifi, removed = _read_upload(uploaded.getvalue())
            name = uploaded.name
        else:
            if not WIFI_FILE.exists():
                st.warning("Esempio non scaricato: esegui `python scripts/fetch_data.py`.", icon=":material/download:")
                return None
            frame, removed = load_wifi(WIFI_FILE.read_bytes())
            is_wifi, name = True, EXAMPLE
        st.caption(f"{len(frame):,} righe · {len(frame.columns)} colonne")
    return ActiveDataset(name, frame, is_wifi, removed)
