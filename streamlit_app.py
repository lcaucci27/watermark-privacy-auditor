"""Segnale: laboratorio dati locale per il Campionato Universitario AI."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn.datasets import load_breast_cancer, load_diabetes, load_iris

from core.challenge_config import CHALLENGE
from core.ml_pipeline import detect_anomalies, infer_task, serialize_model, train_clustering, train_supervised
from core.privacy import synthetic_residents
from views import published_tab, rules_tab, telemetry_tab, threats_tab

ASSETS = Path(__file__).resolve().parent / "assets"

st.set_page_config(page_title=CHALLENGE.page_title, page_icon=str(ASSETS / "favicon.png"), layout="wide")
st.logo(str(ASSETS / "logo.svg"), icon_image=str(ASSETS / "logo_mark.svg"), size="large")

SAMPLE_RESIDENTS = "Residenti · telemetria sintetica"
SAMPLE_IRIS = "Iris · classificazione o segmentazione"
SAMPLE_CANCER = "Tumori mammari · classificazione"
SAMPLE_DIABETES = "Diabete · regressione"
SAMPLE_OPERATIONS = "Operazioni · anomalie"
NO_FILTER = "Nessun filtro"
NO_GROUP = "Nessun gruppo"
NO_TARGET = "Nessun target · segmentazione"

METRIC_LABELS = {
    "Accuracy": "Accuratezza",
    "Balanced accuracy": "Accuratezza bilanciata",
    "Weighted F1": "F1 ponderato",
    "Test rows": "Casi di test",
    "R²": "R²",
    "MAE": "Errore medio",
    "RMSE": "RMSE",
    "Clusters": "Segmenti",
    "Silhouette score": "Indice silhouette",
    "Largest cluster": "Segmento maggiore",
    "Smallest cluster": "Segmento minore",
}


@st.cache_data(show_spinner=False)
def sample_data(name: str) -> tuple[pd.DataFrame, str | None]:
    if name == SAMPLE_RESIDENTS:
        return synthetic_residents(), "patologia_cronica"
    if name == SAMPLE_IRIS:
        bundle = load_iris(as_frame=True)
    elif name == SAMPLE_CANCER:
        bundle = load_breast_cancer(as_frame=True)
    elif name == SAMPLE_DIABETES:
        bundle = load_diabetes(as_frame=True)
    else:
        index = pd.Series(range(240), name="event_id")
        frame = pd.DataFrame(
            {
                "event_id": index,
                "carico": 50 + (index % 24) * 1.5,
                "temperatura": 12 + (index % 30) * 0.7,
                "area": ["Nord", "Centro", "Sud"] * 80,
            }
        )
        frame.loc[[18, 91, 177], "carico"] *= 2.8
        return frame, None
    return bundle.frame.copy(), "target"


@st.cache_data(show_spinner=False)
def read_upload(file_bytes: bytes, filename: str) -> pd.DataFrame:
    stream = BytesIO(file_bytes)
    if filename.lower().endswith(".csv"):
        return pd.read_csv(stream)
    return pd.read_excel(stream)


def metric_value(value) -> str:
    return f"{value:.3f}" if isinstance(value, float) else str(value)


def dataset_signature(frame: pd.DataFrame) -> tuple[int, tuple[str, ...]]:
    return len(frame), tuple(map(str, frame.columns))


st.html(
    """
    <style>
    .st-key-hero {
        background: linear-gradient(120deg, #B9DDDC 0%, #DCECEA 58%, #F7F3E8 100%);
        border: 1px solid #6E9E9C;
        border-left: 10px solid #A63F2E;
        box-shadow: 7px 7px 0 #D5B15F;
        padding: 1.35rem 1.6rem 1rem;
        margin: 0.35rem 0.5rem 1.7rem 0;
    }
    .st-key-hero h1 {
        letter-spacing: -0.035em;
    }
    .st-key-hero h3 {
        color: #1F6B69;
    }
    </style>
    """
)

with st.container(key="hero"):
    st.caption(CHALLENGE.event_line)
    st.title(CHALLENGE.product_name)
    st.subheader(CHALLENGE.subtitle)
    st.caption(CHALLENGE.description)
    st.markdown(CHALLENGE.status_badges)

with st.sidebar:
    st.caption(CHALLENGE.sidebar_label)
    st.header("Telemetria", icon=":material/database:")
    source = st.segmented_control(
        "Sorgente",
        ["Esempio", "File"],
        default="Esempio",
        required=True,
        width="stretch",
    )
    suggested_target = None
    if source == "Esempio":
        choice = st.selectbox(
            "Caso di prova",
            [SAMPLE_RESIDENTS, SAMPLE_IRIS, SAMPLE_CANCER, SAMPLE_DIABETES, SAMPLE_OPERATIONS],
        )
        data, suggested_target = sample_data(choice)
    else:
        uploaded = st.file_uploader("CSV o XLSX", type=["csv", "xlsx"])
        if uploaded is None:
            st.info(CHALLENGE.upload_prompt, icon=":material/upload_file:")
            st.stop()
        try:
            data = read_upload(uploaded.getvalue(), uploaded.name)
        except Exception as exc:
            st.error(f"File non leggibile: {exc}", icon=":material/error:")
            st.stop()

    st.header("Filtro", icon=":material/filter_alt:")
    categorical = [column for column in data.columns if 1 < data[column].nunique(dropna=True) <= 20]
    filter_column = st.selectbox("Variabile", [NO_FILTER] + categorical)
    if filter_column != NO_FILTER:
        options = data[filter_column].dropna().unique().tolist()
        selected = st.multiselect("Valori", options, default=options)
        data = data[data[filter_column].isin(selected)]

    st.caption("TF-IDF · Random Forest · K-Means · Isolation Forest")
    st.caption(CHALLENGE.privacy_note)

if data.empty:
    st.warning("Il filtro non restituisce righe.", icon=":material/filter_alt_off:")
    st.stop()

signature = dataset_signature(data)
published, threats, rules, telemetry, overview, explore, model_tab, anomaly_tab = st.tabs(
    [
        ":material/dataset: Dati pubblicati",
        ":material/security: Minacce",
        ":material/gavel: Norme",
        ":material/sensors: Telemetria",
        ":material/dashboard: Quadro",
        ":material/query_stats: Relazioni",
        ":material/model_training: Modello",
        ":material/warning: Anomalie",
    ]
)

with published:
    published_tab.render()

with threats:
    csirt_corpus = threats_tab.render()

with rules:
    garante_corpus = rules_tab.render()

with telemetry:
    telemetry_tab.render(data, signature, {"CSIRT": csirt_corpus, "Garante": garante_corpus})

with overview:
    st.caption("STRUTTURA DEL DATASET")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Righe", f"{len(data):,}", border=True)
    k2.metric("Variabili", len(data.columns), border=True)
    k3.metric("Valori mancanti", f"{data.isna().sum().sum():,}", border=True)
    k4.metric("Duplicati", f"{data.duplicated().sum():,}", border=True)

    with st.container(border=True):
        st.subheader("Campione", icon=":material/table_view:")
        st.dataframe(data.head(100), width="stretch", hide_index=True)

    profile = pd.DataFrame(
        {
            "variabile": data.columns,
            "tipo": data.dtypes.astype(str).values,
            "mancanti_%": (data.isna().mean() * 100).round(1).values,
            "valori_distinti": [data[column].nunique(dropna=True) for column in data.columns],
        }
    )
    with st.expander("Controllo qualità", icon=":material/fact_check:"):
        st.dataframe(
            profile,
            width="stretch",
            hide_index=True,
            column_config={
                "mancanti_%": st.column_config.ProgressColumn(
                    "Mancanti", format="%.1f%%", min_value=0, max_value=100
                )
            },
        )

with explore:
    st.caption("DISTRIBUZIONI E CORRELAZIONI")
    numeric = data.select_dtypes("number").columns.tolist()
    if not numeric:
        st.info("Servono variabili numeriche per costruire i grafici.", icon=":material/info:")
    else:
        with st.container(border=True):
            left, right, color_box = st.columns(3)
            x_axis = left.selectbox("Asse X", numeric, index=0)
            y_default = 2 if len(numeric) >= 2 else 1
            y_axis = right.selectbox("Asse Y", ["Solo distribuzione"] + numeric, index=y_default)
            color = color_box.selectbox("Colore", [NO_GROUP] + categorical)

            if y_axis == "Solo distribuzione":
                figure = px.histogram(
                    data,
                    x=x_axis,
                    color=None if color == NO_GROUP else color,
                    marginal="box",
                    title=f"Distribuzione · {x_axis}",
                )
            else:
                figure = px.scatter(
                    data,
                    x=x_axis,
                    y=y_axis,
                    color=None if color == NO_GROUP else color,
                    hover_data=data.columns[: min(5, len(data.columns))],
                    title=f"{x_axis} × {y_axis}",
                )
            figure.update_layout(margin=dict(l=20, r=20, t=60, b=20), legend_title_text="")
            st.plotly_chart(figure, width="stretch")

        if len(numeric) > 1:
            with st.container(border=True):
                correlations = data[numeric].corr(numeric_only=True)
                heatmap = px.imshow(
                    correlations,
                    text_auto=".2f",
                    aspect="auto",
                    color_continuous_scale="Tealgrn",
                    title="Mappa delle correlazioni",
                )
                heatmap.update_layout(margin=dict(l=20, r=20, t=60, b=20))
                st.plotly_chart(heatmap, width="stretch")

with model_tab:
    st.caption("ADDESTRAMENTO E VALUTAZIONE")
    with st.container(border=True):
        st.subheader("Definisci il target", icon=":material/tune:")
        target_options = [NO_TARGET] + data.columns.tolist()
        default_index = target_options.index(suggested_target) if suggested_target in target_options else 0
        target = st.selectbox("Variabile da stimare", target_options, index=default_index)

        if target == NO_TARGET:
            task = "clustering"
            cluster_count = st.slider("Numero di segmenti", 2, min(10, max(2, len(data) - 1)), 3)
            st.caption("K-Means raggruppa le righe in base alla distanza tra le variabili preprocessate.")
        else:
            inferred = infer_task(data[target])
            task = st.segmented_control(
                "Tipo di problema",
                ["classification", "regression"],
                default=inferred,
                required=True,
                format_func=lambda value: "Classificazione" if value == "classification" else "Regressione",
            )
            st.caption(f"Tipo suggerito dai valori del target: **{'classificazione' if inferred == 'classification' else 'regressione'}**.")

        run_model = st.button(
            "Esegui analisi",
            type="primary",
            icon=":material/play_arrow:",
            width="stretch",
        )

    if run_model:
        try:
            with st.spinner("Calcolo in corso…"):
                result = (
                    train_clustering(data, cluster_count)
                    if task == "clustering"
                    else train_supervised(data, target, task)
                )
            st.session_state["ml_result"] = result
            st.session_state["ml_signature"] = signature
            st.toast("Analisi completata", icon=":material/check_circle:")
        except Exception as exc:
            st.error(f"Analisi interrotta: {exc}", icon=":material/error:")

    result = st.session_state.get("ml_result")
    if result is not None and st.session_state.get("ml_signature") == signature:
        st.subheader("Metriche sul campione di test", icon=":material/analytics:")
        cards = st.columns(len(result.metrics))
        for card, (label, value) in zip(cards, result.metrics.items()):
            card.metric(METRIC_LABELS.get(label, label), metric_value(value), border=True)
        for note in result.notes:
            st.info(note, icon=":material/info:")

        if result.task == "clustering":
            st.caption("L’indice silhouette misura la separazione interna dei gruppi; non dimostra che i segmenti siano utili nel dominio.")
        else:
            st.caption("Metriche calcolate sul 20% delle righe, escluso dall’addestramento. Seed fisso: 42. Non è una validazione esterna.")

        left_result, right_result = st.columns(2)
        if result.confusion is not None:
            with left_result.container(border=True, height="stretch"):
                matrix = px.imshow(
                    result.confusion,
                    text_auto=True,
                    aspect="auto",
                    color_continuous_scale="Tealgrn",
                    title="Matrice degli errori",
                )
                matrix.update_layout(margin=dict(l=20, r=20, t=60, b=20))
                st.plotly_chart(matrix, width="stretch")
        if not result.feature_importance.empty:
            with right_result.container(border=True, height="stretch"):
                top = result.feature_importance.head(15).sort_values("importance")
                importance = px.bar(
                    top,
                    x="importance",
                    y="feature",
                    orientation="h",
                    title="Importanza delle variabili",
                    labels={"importance": "peso", "feature": "variabile"},
                )
                importance.update_layout(margin=dict(l=20, r=20, t=60, b=20))
                st.plotly_chart(importance, width="stretch")

        if result.task == "clustering":
            numeric_result = result.predictions.select_dtypes("number").columns.tolist()
            if len(numeric_result) >= 2:
                with st.container(border=True):
                    segments = px.scatter(
                        result.predictions,
                        x=numeric_result[0],
                        y=numeric_result[1],
                        color=result.predictions["cluster"].astype(str),
                        title="Segmenti rilevati",
                    )
                    segments.update_layout(margin=dict(l=20, r=20, t=60, b=20), legend_title_text="Segmento")
                    st.plotly_chart(segments, width="stretch")
            st.dataframe(
                result.predictions.groupby("cluster").mean(numeric_only=True).round(2),
                width="stretch",
            )

        with st.container(border=True):
            st.subheader("Output", icon=":material/download:")
            st.dataframe(result.predictions.head(200), width="stretch", hide_index=True)
            with st.container(horizontal=True):
                st.download_button(
                    "Scarica risultati",
                    result.predictions.to_csv(index=False).encode("utf-8"),
                    "risultati.csv",
                    "text/csv",
                    icon=":material/download:",
                )
                st.download_button(
                    "Scarica modello",
                    serialize_model(result.model),
                    "modello_locale.joblib",
                    "application/octet-stream",
                    icon=":material/save:",
                )

with anomaly_tab:
    st.caption("RILEVAZIONE NON SUPERVISIONATA")
    with st.container(border=True):
        st.subheader("Quota attesa", icon=":material/tune:")
        contamination = st.slider("Quota attesa di casi insoliti", 0.01, 0.20, 0.05, 0.01)
        run_anomaly = st.button(
            "Individua casi",
            icon=":material/search:",
            width="stretch",
        )

    if run_anomaly:
        try:
            st.session_state["anomalies"] = detect_anomalies(data, contamination)
            st.session_state["anomaly_signature"] = signature
            st.toast("Scansione completata", icon=":material/check_circle:")
        except Exception as exc:
            st.error(f"Scansione interrotta: {exc}", icon=":material/error:")

    anomalies = st.session_state.get("anomalies")
    if anomalies is not None and st.session_state.get("anomaly_signature") == signature:
        st.metric("Righe segnalate", int(anomalies["is_anomaly"].sum()), border=True)
        st.caption("Isolation Forest assegna un punteggio relativo. Una riga segnalata richiede verifica nel contesto applicativo.")
        with st.container(border=True):
            st.dataframe(anomalies.head(100), width="stretch", hide_index=True)
        st.download_button(
            "Scarica elenco",
            anomalies.to_csv(index=False).encode("utf-8"),
            "casi_insoliti.csv",
            "text/csv",
            icon=":material/download:",
        )

st.caption("TF-IDF / Random Forest / K-Means / Isolation Forest  ·  seed 42  ·  esecuzione locale")
