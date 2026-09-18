"""Caricamenti e calcoli condivisi tra le schede, con cache di sessione del server Streamlit."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.privacy_optimizer import explore, pareto
from core.text_corpus import TextIndex, build_index
from core.threat_model import LABEL, bulletin_text, train_threat_model
from core.wifi_dataset import prepare

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
WIFI_FILE = DATA_DIR / "romawifi_sessioni.csv"
CSIRT_FILE = DATA_DIR / "csirt_bollettini.csv"
GARANTE_FILE = DATA_DIR / "garante_provvedimenti.csv"

AQUA, CORAL, GOLD, INK, MUTED = "#1F6B69", "#A63F2E", "#B3872C", "#17282B", "#8FB7B5"


@st.cache_data(show_spinner="Lettura delle sessioni…")
def load_wifi(raw: bytes) -> tuple[pd.DataFrame, int]:
    table = pd.read_csv(BytesIO(raw))
    frame = prepare(table)
    return frame, len(table) - len(frame)


@st.cache_data(show_spinner="L’ottimizzatore prova 36 versioni del dataset…")
def variants(frame: pd.DataFrame) -> pd.DataFrame:
    table = explore(frame)
    table["frontiera"] = pareto(table)
    return table


@st.cache_data(show_spinner=False)
def load_csv(path: str) -> pd.DataFrame | None:
    return pd.read_csv(path) if Path(path).exists() else None


@st.cache_resource(show_spinner="Indicizzazione dei testi…")
def text_index(texts: tuple[str, ...]) -> TextIndex:
    return build_index(pd.Series(texts))


@st.cache_resource(show_spinner="Addestramento del modello di impatto…")
def impact_model(csirt: pd.DataFrame):
    labelled = csirt.dropna(subset=[LABEL])
    return train_threat_model(labelled).model if len(labelled) >= 30 else None


def csirt_corpus() -> tuple[pd.DataFrame | None, TextIndex | None]:
    frame = load_csv(str(CSIRT_FILE))
    if frame is None:
        return None, None
    return frame, text_index(tuple(bulletin_text(frame)))


def garante_corpus() -> tuple[pd.DataFrame | None, TextIndex | None]:
    frame = load_csv(str(GARANTE_FILE))
    if frame is None:
        return None, None
    return frame, text_index(tuple(frame["testo"].fillna("").astype(str)))


def frontier_chart(table: pd.DataFrame, max_risk: float, chosen: pd.Series | None) -> go.Figure:
    """Rischio contro utilità per ogni versione del dataset; evidenzia frontiera, soglia e scelta."""
    figure = go.Figure()
    groups = (
        ("Contatore pubblicato: sessioni collegabili", table["collegabile"], CORAL, "x"),
        ("Altre versioni", ~table["collegabile"] & ~table["frontiera"], MUTED, "circle"),
        ("Frontiera: miglior compromesso", ~table["collegabile"] & table["frontiera"], AQUA, "circle"),
    )
    for name, mask, color, symbol in groups:
        subset = table[mask]
        figure.add_trace(go.Scatter(
            x=subset["rischio"], y=subset["utilità relativa"], mode="markers", name=name,
            marker=dict(color=color, size=11, symbol=symbol, line=dict(width=1, color=INK)),
            text=subset["variante"], hovertemplate="%{text}<br>rischio %{x:.1%}<br>utilità %{y:.0%}<extra></extra>",
        ))
    published = table[(table["orario"] == "secondo") & (table["luogo"] == "civico") & (table["contatore"] == "pubblicato")]
    if not published.empty:
        figure.add_annotation(x=published["rischio"].iloc[0], y=published["utilità relativa"].iloc[0],
                              text="come pubblicato oggi", showarrow=True, arrowhead=2, ax=-80, ay=30)
    if chosen is not None:
        figure.add_trace(go.Scatter(
            x=[chosen["rischio"]], y=[chosen["utilità relativa"]], mode="markers", name="Scelta dell’ottimizzatore",
            marker=dict(color=GOLD, size=22, symbol="star", line=dict(width=1.5, color=INK)),
            text=[chosen["variante"]], hovertemplate="%{text}<extra></extra>",
        ))
    figure.add_vline(x=max_risk, line_dash="dash", line_color=INK, annotation_text=f"soglia {max_risk:.0%}")
    figure.update_layout(
        title="Ogni punto è una versione pubblicabile del dataset",
        xaxis=dict(title="Rischio: sessioni uniche", tickformat=".0%", range=[-0.02, 1.02]),
        yaxis=dict(title="Utilità conservata", tickformat=".0%"),
        margin=dict(l=20, r=20, t=60, b=20), legend=dict(orientation="h", y=-0.25),
    )
    return figure
