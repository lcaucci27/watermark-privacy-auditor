"""Scheda dati pubblicati: verifica di un open data dichiarato anonimo (WiFi di Roma Capitale)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from core.linkability import scan_counters
from core.privacy_optimizer import Variant, publish, recommend
from core.wifi_dataset import PUBLISHED_KEYS, is_wifi_dataset, unique_share
from views.shared import frontier_chart, load_wifi, variants

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "romawifi_sessioni.csv"
SOURCE_URL = "https://dati.comune.roma.it/catalog/dataset/wifi2026"
MARGIN = dict(l=20, r=20, t=60, b=20)


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
    frame, removed = load_wifi(raw)
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
            "quante volte il più alto arriva dopo? Un contatore persistente supera l'80%; valori casuali restano intorno al 50%."
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
                f"**{row['colonna']}** mostra memoria temporale compatibile con un contatore persistente e non con un "
                "semplice contatore della sede. Può creare correlabilità tra sessioni, ma il test non dimostra che "
                "appartengano alla stessa persona. La documentazione del dataset non descrive questa colonna.",
                icon=":material/link:",
            )

    with st.container(border=True):
        st.subheader("Correzione scelta dall'ottimizzatore", icon=":material/tune:")
        st.caption(
            "L'ottimizzatore genera 36 versioni del dataset (orario al secondo, 15 minuti, 1 ora, 3 ore; civico, via, municipio; "
            "contatore pubblicato, in fasce, rimosso), misura rischio e utilità di ciascuna e sceglie la più utile sotto la soglia."
        )
        max_risk = st.slider("Rischio massimo accettabile", 0.02, 0.50, 0.15, 0.01, format="%.2f", key="published_risk")
        if st.button("Trova la correzione migliore", icon=":material/auto_fix_high:", key="optimize"):
            st.session_state["variants_ready"] = True
        if st.session_state.get("variants_ready"):
            table = variants(frame)
            chosen = recommend(table, max_risk)
            st.plotly_chart(frontier_chart(table, max_risk, chosen), width="stretch")
            if chosen is None:
                st.warning("Nessuna versione resta sotto la soglia: alza il rischio accettabile.", icon=":material/warning:")
            else:
                c1, c2, c3 = st.columns(3)
                c1.metric("Come pubblicato", f"{unique_share(frame, PUBLISHED_KEYS):.1%}", border=True)
                c2.metric("Con la correzione", f"{chosen['rischio']:.1%}", border=True)
                c3.metric("Utilità conservata", f"{chosen['utilità relativa']:.0%}", border=True)
                st.success(f"Versione scelta: **{chosen['variante']}**", icon=":material/verified:")
                corrected = publish(frame, Variant(chosen["orario"], chosen["luogo"], chosen["contatore"]))
                st.download_button(
                    "Scarica il dataset corretto",
                    corrected.drop(columns=["minuto_del_giorno"]).to_csv(index=False).encode("utf-8"),
                    "romawifi_corretto.csv", "text/csv", icon=":material/download:",
                )

    st.caption(
        "Limiti: il significato di LOGINCOUNT è dedotto dai dati, non confermato dall'ente. "
        "Nessuna persona è stata identificata; la scheda mostra solo misure aggregate."
    )
