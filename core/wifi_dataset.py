"""Adattatore per il dataset open data "Sessioni anonimizzate" del WiFi di Roma Capitale."""

from __future__ import annotations

import pandas as pd

REQUIRED = ("STARTDATE", "STARTTIME", "DUG", "DUF", "CIVICO", "MUNICIPIO", "DTLN", "LOGINCOUNT")
# Quasi-identificativi così come pubblicati: giorno, orario al secondo, sede al civico, lingua.
PUBLISHED_KEYS = ["giorno", "STARTTIME", "sede", "DTLN"]
CORRECTED_KEYS = ["giorno", "fascia_oraria", "MUNICIPIO", "DTLN"]


def is_wifi_dataset(df: pd.DataFrame) -> bool:
    return all(column in df.columns for column in REQUIRED)


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    """Rimuove le righe duplicate e aggiunge orario completo, giorno e sede come colonne derivate."""
    # Il portale pubblica a volte due file per lo stesso giorno: le copie gonfierebbero le classi.
    frame = df.drop_duplicates().copy()
    frame["sede"] = (
        frame["DUG"].astype(str).str.strip() + " " + frame["DUF"].astype(str).str.strip()
        + " " + frame["CIVICO"].astype(str).str.strip()
    )
    frame["inizio"] = pd.to_datetime(
        frame["STARTDATE"].astype(str) + " " + frame["STARTTIME"].astype(str), dayfirst=True, errors="coerce"
    )
    frame["giorno"] = frame["inizio"].dt.date.astype(str)
    return frame.dropna(subset=["inizio"])


def correct(frame: pd.DataFrame) -> pd.DataFrame:
    """Correzione proposta: niente contatore, orario in fasce di un'ora, municipio al posto del civico."""
    corrected = frame.drop(columns=["LOGINCOUNT", "CIVICO", "DUF", "DUG", "sede", "STARTTIME", "ENDTIME"], errors="ignore")
    corrected["fascia_oraria"] = frame["inizio"].dt.strftime("%H:00")
    return corrected


def unique_share(frame: pd.DataFrame, keys: list[str]) -> float:
    """Quota di sessioni che nessun'altra sessione condivide sulle chiavi indicate."""
    sizes = frame.groupby(keys, dropna=False)[keys[0]].transform("size")
    return float((sizes == 1).mean())
