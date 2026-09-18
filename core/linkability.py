"""Ricerca di pseudonimi nascosti: colonne numeriche che, in dati dichiarati anonimi,
si comportano come contatori legati alla stessa persona e rendono le righe collegabili."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

MIN_PAIRS = 100
MIN_ORDERED_SHARE = 0.80
MIN_GAP_FROM_NULL = 0.25


def _ordered_pairs(values: np.ndarray, max_step: int) -> tuple[int, int]:
    """Coppie di valori vicini (differenza 1..max_step) e quante rispettano l'ordine temporale."""
    pairs = ordered = 0
    for i in range(len(values) - 1):
        diff = values[i + 1:] - values[i]
        near = (np.abs(diff) >= 1) & (np.abs(diff) <= max_step)
        pairs += int(near.sum())
        ordered += int((diff[near] > 0).sum())
    return pairs, ordered


@dataclass(frozen=True)
class CounterEvidence:
    column: str
    pairs: int
    ordered_share: float
    null_share: float
    location_growth: float | None
    verdict: str


def test_counter(
    df: pd.DataFrame,
    column: str,
    timestamps: pd.Series,
    context: list[str],
    location: str | None = None,
    max_step: int = 3,
    seed: int = 42,
) -> CounterEvidence:
    """Verifica se `column` cresce nel tempo come un contatore personale.

    Dentro ogni gruppo (giorno + colonne di contesto) ordina le righe per orario e conta
    le coppie di valori vicini. Se il valore più alto arriva quasi sempre dopo, la colonna
    segue la stessa entità nel tempo. L'ipotesi nulla mescola i valori dentro il gruppo.
    """
    rng = np.random.default_rng(seed)
    frame = df.assign(_ts=timestamps, _day=timestamps.dt.date).dropna(subset=["_ts", column])
    pairs = ordered = null_pairs = null_ordered = 0
    for _, group in frame.groupby(["_day", *context], sort=False):
        if len(group) < 2:
            continue
        values = group.sort_values("_ts")[column].to_numpy(dtype=float)
        p, o = _ordered_pairs(values, max_step)
        pairs, ordered = pairs + p, ordered + o
        p, o = _ordered_pairs(rng.permutation(values), max_step)
        null_pairs, null_ordered = null_pairs + p, null_ordered + o

    growth = None
    if location:
        # Se fosse un contatore del luogo, dentro il luogo crescerebbe a ogni passo.
        steps = [
            g.sort_values("_ts")[column].diff().dropna().gt(0).mean()
            for _, g in frame.groupby(location) if len(g) > 30
        ]
        growth = float(np.mean(steps)) if steps else None

    share = ordered / pairs if pairs else float("nan")
    null_share = null_ordered / null_pairs if null_pairs else float("nan")
    if pairs < MIN_PAIRS:
        verdict = "Dati insufficienti"
    elif share >= MIN_ORDERED_SHARE and share - null_share >= MIN_GAP_FROM_NULL and (growth is None or growth < 0.8):
        verdict = "Pseudonimo probabile"
    else:
        verdict = "Nessun segnale"
    return CounterEvidence(column, pairs, share, null_share, growth, verdict)


def scan_counters(
    df: pd.DataFrame,
    timestamps: pd.Series,
    context: list[str],
    location: str | None = None,
    min_distinct: int = 50,
) -> pd.DataFrame:
    """Esegue `test_counter` su ogni colonna intera con molti valori distinti."""
    candidates = [
        column for column in df.select_dtypes(include="integer").columns
        if column not in context and df[column].nunique() >= min_distinct
    ]
    rows = []
    for column in candidates:
        evidence = test_counter(df, column, timestamps, context, location)
        rows.append({
            "colonna": column,
            "coppie vicine": evidence.pairs,
            "ordine nel tempo": evidence.ordered_share,
            "ipotesi nulla": evidence.null_share,
            "crescita nel luogo": evidence.location_growth,
            "esito": evidence.verdict,
        })
    return pd.DataFrame(rows).sort_values("ordine nel tempo", ascending=False, na_position="last")
