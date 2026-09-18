"""Caricamento dei corpora testuali (bollettini CSIRT, provvedimenti Garante) da file locali."""

from __future__ import annotations

import json
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

from core.text_corpus import TextIndex, build_index

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TABLE_SUFFIXES = (".csv", ".xlsx", ".json", ".jsonl")
TEXT_SUFFIXES = (".txt", ".md")
NONE = "Nessuna"


@dataclass
class Corpus:
    frame: pd.DataFrame
    text: pd.Series
    title: pd.Series
    date: pd.Series | None
    label: str | None
    index: TextIndex


def _read_table(raw: bytes, name: str) -> pd.DataFrame:
    lower = name.lower()
    if lower.endswith(".csv"):
        # Gli open data italiani usano spesso ';' come separatore.
        return pd.read_csv(BytesIO(raw), sep=None, engine="python")
    if lower.endswith(".xlsx"):
        return pd.read_excel(BytesIO(raw))
    if lower.endswith(".jsonl"):
        return pd.read_json(BytesIO(raw), lines=True)
    payload = json.loads(raw.decode("utf-8"))
    if isinstance(payload, dict):
        # Molte API restituiscono {"items": [...]}: prende la prima lista di record.
        payload = next((value for value in payload.values() if isinstance(value, list)), [payload])
    return pd.json_normalize(payload)


@st.cache_data(show_spinner=False)
def read_files(files: tuple[tuple[str, bytes], ...]) -> pd.DataFrame:
    tables, documents = [], []
    for name, raw in files:
        if name.lower().endswith(TEXT_SUFFIXES):
            documents.append({"titolo": Path(name).stem, "testo": raw.decode("utf-8", errors="ignore")})
        else:
            tables.append(_read_table(raw, name).assign(file_origine=name))
    if documents:
        tables.append(pd.DataFrame(documents))
    if not tables:
        return pd.DataFrame()
    return pd.concat(tables, ignore_index=True)


@st.cache_resource(show_spinner="Indicizzazione dei testi…")
def cached_index(texts: tuple[str, ...]) -> TextIndex:
    return build_index(pd.Series(texts))


def _local_files(prefix: str) -> list[Path]:
    if not DATA_DIR.exists():
        return []
    return sorted(
        path for path in DATA_DIR.iterdir()
        if path.name.lower().startswith(prefix) and path.suffix.lower() in TABLE_SUFFIXES + TEXT_SUFFIXES
    )


TITLE_NAMES = ("titolo", "title", "oggetto", "subject", "nome", "name")


def _guess_text_columns(frame: pd.DataFrame) -> list[str]:
    text_like = frame.select_dtypes(include="object").drop(columns=["file_origine"], errors="ignore")
    if text_like.empty:
        return []
    lengths = text_like.apply(lambda column: column.dropna().astype(str).str.len().mean()).fillna(0)
    return lengths.sort_values(ascending=False).head(1).index.tolist()


def _guess_title(columns: list[str]) -> int:
    """Indice nel selectbox (0 = Nessuna) della prima colonna con nome da titolo."""
    for position, column in enumerate(columns):
        if str(column).lower() in TITLE_NAMES:
            return position + 1
    return 0


def corpus_picker(key: str, prefix: str, label: str) -> Corpus | None:
    """Mostra sorgente e mappatura delle colonne; restituisce il corpus indicizzato."""
    local = _local_files(prefix)
    with st.container(border=True):
        st.subheader(label, icon=":material/folder_open:")
        uploaded = st.file_uploader(
            "CSV, XLSX, JSON o TXT",
            type=[suffix.strip(".") for suffix in TABLE_SUFFIXES + TEXT_SUFFIXES],
            accept_multiple_files=True,
            key=f"{key}_upload",
        )
        if uploaded:
            files = tuple((item.name, item.getvalue()) for item in uploaded)
        elif local:
            files = tuple((path.name, path.read_bytes()) for path in local)
            st.caption(f"File locali in `data/`: {', '.join(path.name for path in local)}")
        else:
            st.info(f"Carica i file oppure copiali in `data/` con nome che inizia per `{prefix}`.", icon=":material/upload_file:")
            return None

        try:
            frame = read_files(files)
        except Exception as exc:
            st.error(f"File non leggibile: {exc}", icon=":material/error:")
            return None
        if frame.empty:
            st.warning("I file non contengono righe.", icon=":material/warning:")
            return None

        columns = frame.columns.tolist()
        guessed = _guess_text_columns(frame)
        left, right = st.columns(2)
        text_columns = left.multiselect("Colonne di testo", columns, default=guessed, key=f"{key}_text")
        title_column = right.selectbox(
            "Titolo", [NONE] + columns, index=_guess_title(columns), key=f"{key}_title"
        )
        left, right = st.columns(2)
        date_column = left.selectbox("Data", [NONE] + columns, key=f"{key}_date")
        label_column = right.selectbox("Etichetta (gravità, tipologia…)", [NONE] + columns, key=f"{key}_label")

    if not text_columns:
        st.warning("Seleziona almeno una colonna di testo.", icon=":material/warning:")
        return None
    text = frame[text_columns].fillna("").astype(str).agg(" ".join, axis=1)
    try:
        index = cached_index(tuple(text))
    except ValueError as exc:
        st.error(str(exc), icon=":material/error:")
        return None
    title = frame[title_column].astype(str) if title_column != NONE else text.str.slice(0, 90)
    date = None
    if date_column != NONE:
        # utc=True evita l'errore su date con fusi orari misti, frequenti nei feed RSS.
        date = pd.to_datetime(frame[date_column], errors="coerce", dayfirst=True, utc=True).dt.tz_localize(None)
    return Corpus(
        frame=frame, text=text, title=title, date=date,
        label=None if label_column == NONE else label_column, index=index,
    )
