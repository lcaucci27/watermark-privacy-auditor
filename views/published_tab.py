"""Scheda dati pubblicati: verifica di un open data dichiarato anonimo (WiFi di Roma Capitale)."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from core.linkability import scan_counters
from core.wifi_dataset import CORRECTED_KEYS, PUBLISHED_KEYS, correct, is_wifi_dataset, prepare, unique_share

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "romawifi_sessioni.csv"
SOURCE_URL = "https://dati.comune.roma.it/catalog/dataset/wifi2026"
MARGIN = dict(l=20, r=20, t=60, b=20)


@st.cache_data(show_spinner="Lettura delle sessioni…")
def _load(raw: bytes) -> tuple[pd.DataFrame, int]:
    table = pd.read_csv(BytesIO(raw))
    frame = prepare(table)
    return frame, len(table) - len(frame)


@st.cache_data(show_spinner="Ricerca di contatori nascosti…")
def _scan(frame: pd.DataFrame) -> pd.DataFrame:
    return scan_counters(frame, frame["inizio"], ["sede", "DTLN"], location="sede")


def _source() -> bytes | None:
    uploaded = st.file_uploader("Sessioni WiFi (CSV del portale open data)", type=["csv"], key="wifi_upload")
    if uploaded is not None:
        return uploaded.getvalue()
    if DATA_FILE.exists():
        return DATA_FILE.read_bytes()
    st.info("Esegui `python scripts/fetch_data.py --only wifi` oppure carica un CSV del portale.", icon=":material/upload_file:")
    return None


def render() -> None:
    st.caption("OPEN DATA DICHIARATI ANONIMI · WIFI DI ROMA CAPITALE")
    with st.container(border=True):
        st.subheader("Dataset sotto verifica", icon=":material/dataset:")
        st.markdown(
            "“Sessioni anonimizzate di navigazione web riscontrate nel sistema WiFi di Roma Capitale”, "
            f"licenza CC-BY, un file al giorno. [Scheda sul portale]({SOURCE_URL})"
        )
        raw = _source()
    if raw is None:
        return
    frame, removed = _load(raw)
    if not is_wifi_dataset(frame):
        st.error("Il CSV non ha le colonne del dataset WiFi di Roma Capitale (STARTDATE, STARTTIME, CIVICO, DTLN, LOGINCOUNT…).", icon=":material/error:")
        return

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Sessioni", f"{len(frame):,}", border=True)
    k2.metric("Giorni", frame["giorno"].nunique(), border=True)
    k3.metric("Sedi", frame["sede"].nunique(), border=True)
    k4.metric("Sessioni uniche", f"{unique_share(frame, PUBLISHED_KEYS):.1%}", border=True)
    st.caption(
        "Sessione unica: nessun'altra sessione ha stesso giorno, orario al secondo, sede e lingua. "
        "Chi conosce questi quattro dati di una persona trova la sua riga (individuazione, WP29 parere 05/2014)."
        + (f" Righe duplicate o senza orario escluse: {removed:,}." if removed else "")
    )

    with st.container(border=True):
        st.subheader("Pseudonimi nascosti", icon=":material/fingerprint:")
        st.caption(
            "Per ogni colonna numerica: dentro stesso giorno, sede e lingua, tra valori che differiscono di 1-3, "
            "quante volte il più alto arriva dopo? Un contatore personale supera l'80%; valori casuali restano intorno al 50%."
        )
        scan = _scan(frame)
        st.dataframe(
            scan, width="stretch", hide_index=True,
            column_config={
                "ordine nel tempo": st.column_config.ProgressColumn("Ordine nel tempo", min_value=0, max_value=1, format="percent"),
                "ipotesi nulla": st.column_config.NumberColumn("Valori mescolati", format="percent"),
                "crescita nel luogo": st.column_config.NumberColumn("Crescita dentro la sede", format="percent"),
            },
        )
        flagged = scan[scan["esito"] == "Pseudonimo probabile"]
        if not flagged.empty:
            row = flagged.iloc[0]
            chart = px.bar(
                pd.DataFrame({
                    "serie": ["Dati pubblicati", "Valori mescolati a caso"],
                    "quota": [row["ordine nel tempo"], row["ipotesi nulla"]],
                }),
                x="quota", y="serie", orientation="h", range_x=[0, 1], text_auto=".1%",
                title=f"{row['colonna']}: il valore più alto arriva dopo",
            )
            chart.update_layout(margin=MARGIN, yaxis_title="", xaxis_title="")
            st.plotly_chart(chart, width="stretch")
            st.error(
                f"**{row['colonna']}** si comporta come un contatore di accessi personale: cresce nel tempo per la stessa "
                "persona e non per la sede. Rende collegabili le sessioni della stessa persona tra ore e giorni "
                "(correlabilità). La documentazione del dataset non descrive questa colonna.",
                icon=":material/link:",
            )

    with st.container(border=True):
        st.subheader("Correzione proposta", icon=":material/build:")
        st.markdown(
            "- rimuovere il contatore\n"
            "- orario in fasce di un'ora\n"
            "- municipio al posto del numero civico"
        )
        corrected = correct(frame)
        before, after = unique_share(frame, PUBLISHED_KEYS), unique_share(corrected, CORRECTED_KEYS)
        c1, c2 = st.columns(2)
        c1.metric("Sessioni uniche, come pubblicato", f"{before:.1%}", border=True)
        c2.metric("Sessioni uniche, dopo la correzione", f"{after:.1%}", delta=f"{(after - before) * 100:.1f} punti",
                  delta_color="inverse", border=True)
        st.caption("Le misure restano utili per il servizio: traffico, durata e lingua per municipio e fascia oraria.")
        st.download_button(
            "Scarica il dataset corretto",
            corrected.drop(columns=["inizio"]).to_csv(index=False).encode("utf-8"),
            "romawifi_corretto.csv", "text/csv", icon=":material/download:",
        )

    st.caption(
        "Limiti: il significato di LOGINCOUNT è dedotto dai dati, non confermato dall'ente. "
        "Nessuna persona è stata identificata; la scheda mostra solo misure aggregate."
    )
