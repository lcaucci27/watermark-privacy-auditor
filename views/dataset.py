"""Dataset attivo, scelto una volta nella barra laterale e condiviso da tutte le pagine."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

import pandas as pd
import streamlit as st

from core.wifi_dataset import is_wifi_dataset, prepare
from views.shared import WIFI_FILE, load_wifi

EXAMPLE = "Roma · sessioni WiFi"
BOLOGNA = "Bologna · affollamento"
MILANO = "Milano · utenti WiFi"
UPLOAD = "Carica CSV"
ROMA_NAME = "WiFi Roma Capitale · ultimi 14 giorni"
BOLOGNA_NAME = "WiFi Bologna · affollamento aggregato"
MILANO_NAME = "WiFi Milano · utenti unici per zona"
BOLOGNA_FILE = WIFI_FILE.parent / "bologna_wifi_affollamento_sample.csv"
MILANO_FILE = WIFI_FILE.parent / "milano_wifi_utenti_sample.csv"
ROMA_URL = "https://dati.comune.roma.it/catalog/dataset/wifi2026"
BOLOGNA_URL = "https://opendata.comune.bologna.it/explore/dataset/iperbole-wifi-affollamento/"
MILANO_URL = "https://dati.comune.milano.it/dataset/ds917-openwifimilano-uniqueuserzone"


@dataclass
class ActiveDataset:
    name: str
    frame: pd.DataFrame
    is_wifi: bool
    removed: int
    row_kind_hint: str | None = None
    municipality: str | None = None
    source_url: str | None = None


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
            "Origine", [EXAMPLE, BOLOGNA, MILANO, UPLOAD], default=EXAMPLE, required=True, key="dataset_source",
            label_visibility="collapsed",
        )
        if source == UPLOAD:
            uploaded = st.file_uploader("File CSV", type=["csv"], key="dataset_upload")
            if uploaded is None:
                st.caption("Il file resta su questo computer.")
                return None
            frame, is_wifi, removed = _read_upload(uploaded.getvalue())
            name = uploaded.name
            return ActiveDataset(name, frame, is_wifi, removed)
        if source == BOLOGNA:
            if not BOLOGNA_FILE.exists():
                st.warning(
                    "Esempio non scaricato: esegui `python scripts/fetch_municipal_examples.py`.",
                    icon=":material/download:",
                )
                return None
            frame = pd.read_csv(BOLOGNA_FILE)
            st.caption(f"{len(frame):,} righe · {len(frame.columns)} colonne")
            return ActiveDataset(BOLOGNA_NAME, frame, False, 0, "aggregato", "Bologna", BOLOGNA_URL)
        if source == MILANO:
            if not MILANO_FILE.exists():
                st.warning(
                    "Esempio non scaricato: esegui `python scripts/fetch_municipal_examples.py`.",
                    icon=":material/download:",
                )
                return None
            frame = pd.read_csv(MILANO_FILE)
            st.caption(f"{len(frame):,} righe · {len(frame.columns)} colonne")
            return ActiveDataset(MILANO_NAME, frame, False, 0, "aggregato", "Milano", MILANO_URL)
        else:
            if not WIFI_FILE.exists():
                st.warning("Esempio non scaricato: esegui `python scripts/fetch_data.py`.", icon=":material/download:")
                return None
            frame, removed = load_wifi(WIFI_FILE.read_bytes())
            is_wifi, name = True, ROMA_NAME
        st.caption(f"{len(frame):,} righe · {len(frame.columns)} colonne")
    return ActiveDataset(name, frame, is_wifi, removed, "individuale", "Roma", ROMA_URL)
