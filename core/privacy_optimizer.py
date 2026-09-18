"""Ottimizzatore privacy-utilità: prova varie versioni pubblicabili di un dataset di sessioni,
misura per ciascuna rischio di individuazione e utilità analitica residua, sceglie la migliore."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import cross_val_score

TIME_LEVELS = {"secondo": None, "15 minuti": "15min", "1 ora": "1h", "3 ore": "3h"}
PLACE_LEVELS = ("civico", "via", "municipio")
COUNTER_LEVELS = ("pubblicato", "in fasce", "rimosso")
COUNTER_BINS = [0, 1, 10, 100, 1000, np.inf]


@dataclass(frozen=True)
class Variant:
    time: str
    place: str
    counter: str

    @property
    def label(self) -> str:
        return f"orario al {self.time} · {self.place} · contatore {self.counter}"


def publish(frame: pd.DataFrame, variant: Variant) -> pd.DataFrame:
    """Versione del dataset come verrebbe pubblicata con la variante indicata."""
    out = pd.DataFrame({"giorno": frame["giorno"], "lingua": frame["DTLN"].astype(str)})
    freq = TIME_LEVELS[variant.time]
    start = frame["inizio"] if freq is None else frame["inizio"].dt.floor(freq)
    out["orario"] = start.dt.strftime("%H:%M:%S")
    out["minuto_del_giorno"] = start.dt.hour * 60 + start.dt.minute + start.dt.second / 60
    out["luogo"] = {
        "civico": frame["sede"],
        "via": frame["DUG"].astype(str) + " " + frame["DUF"].astype(str),
        "municipio": frame["MUNICIPIO"].astype(str),
    }[variant.place]
    if variant.counter == "pubblicato":
        out["contatore"] = frame["LOGINCOUNT"].astype(float)
    elif variant.counter == "in fasce":
        out["contatore"] = pd.cut(frame["LOGINCOUNT"], COUNTER_BINS, labels=False, include_lowest=True).astype(float)
    return out


def risk(published: pd.DataFrame) -> float:
    """Quota di sessioni uniche sulle colonne pubblicate (individuazione, WP29 05/2014)."""
    keys = ["giorno", "orario", "luogo", "lingua"] + (["contatore"] if "contatore" in published else [])
    sizes = published.groupby(keys, dropna=False)["giorno"].transform("size")
    return float((sizes == 1).mean())


def utility(published: pd.DataFrame, target: pd.Series, seed: int = 42) -> float:
    """R² in validazione incrociata di un modello che stima il traffico della sessione
    dalle sole colonne pubblicate: misura quanto il dataset resta utile per pianificare il servizio."""
    features = pd.DataFrame({
        "minuto_del_giorno": published["minuto_del_giorno"],
        "giorno_settimana": pd.to_datetime(published["giorno"]).dt.dayofweek,
        "luogo": published["luogo"].astype("category").cat.codes,
        "lingua": published["lingua"].astype("category").cat.codes,
    })
    if "contatore" in published:
        features["contatore"] = published["contatore"]
    model = HistGradientBoostingRegressor(
        max_iter=60, learning_rate=0.15, random_state=seed,
        categorical_features=[features.columns.get_loc(c) for c in ("luogo", "lingua")],
    )
    return float(cross_val_score(model, features, target, cv=3, scoring="r2").mean())


def explore(frame: pd.DataFrame, sample: int = 4000, seed: int = 42) -> pd.DataFrame:
    """Valuta tutte le combinazioni di generalizzazione.

    Il rischio si misura su tutte le sessioni: su un campione le righe sembrerebbero più uniche.
    L'utilità si misura su un campione fisso per contenere i tempi di addestramento.
    """
    rows = frame.sample(min(sample, len(frame)), random_state=seed)
    target = np.log1p(rows["DOWNLOAD"] + rows["UPLOAD"])
    results = []
    for time, place, counter in product(TIME_LEVELS, PLACE_LEVELS, COUNTER_LEVELS):
        variant = Variant(time, place, counter)
        results.append({
            "variante": variant.label, "orario": time, "luogo": place, "contatore": counter,
            "rischio": risk(publish(frame, variant)), "utilità": utility(publish(rows, variant), target, seed),
            # Un contatore potenzialmente persistente resta rischioso anche se nessuna riga è unica.
            "collegabile": counter == "pubblicato",
        })
    table = pd.DataFrame(results)
    table["utilità relativa"] = table["utilità"] / table["utilità"].max()
    return table


def pareto(table: pd.DataFrame) -> pd.Series:
    """True per le varianti non dominate: nessun'altra ha rischio minore e utilità maggiore insieme."""
    flags = []
    for _, row in table.iterrows():
        dominated = (
            (table["rischio"] <= row["rischio"]) & (table["utilità"] >= row["utilità"])
            & ((table["rischio"] < row["rischio"]) | (table["utilità"] > row["utilità"]))
        ).any()
        flags.append(not dominated)
    return pd.Series(flags, index=table.index)


def recommend(table: pd.DataFrame, max_risk: float) -> pd.Series | None:
    """Variante più utile tra quelle sotto la soglia di rischio e non collegabili."""
    allowed = table[(table["rischio"] <= max_risk) & ~table["collegabile"]]
    if allowed.empty:
        return None
    return allowed.sort_values(["utilità", "rischio"], ascending=[False, True]).iloc[0]
