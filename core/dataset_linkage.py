"""Misura la collegabilità tra dataset senza materializzare profili personali."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class LinkageReport:
    primary_rows: int
    comparable_rows: int
    matched_rows: int
    unique_matches: int
    multiple_matches: int
    keys: tuple[str, ...]
    auxiliary_attributes: tuple[str, ...]
    assumption: str

    @property
    def matched_share(self) -> float:
        return self.matched_rows / self.primary_rows if self.primary_rows else 0.0

    @property
    def unique_share(self) -> float:
        return self.unique_matches / self.primary_rows if self.primary_rows else 0.0


def suggested_common_keys(primary: pd.DataFrame, auxiliary: pd.DataFrame) -> list[str]:
    """Ordina le colonne comuni privilegiando tempo e luogo, evitando misure e tipi di record."""
    common = [str(column) for column in primary.columns if column in auxiliary.columns]
    key_hints = ("data", "date", "giorno", "time", "ora", "zona", "luogo", "place", "area", "codice")
    excluded_hints = ("valore", "value", "conteggio", "count", "misura", "tipologia", "type")
    likely = [
        column for column in common
        if any(hint in column.casefold() for hint in key_hints)
        and not any(hint in column.casefold() for hint in excluded_hints)
    ]
    return likely or common[:2]


def exact_linkage(primary: pd.DataFrame, auxiliary: pd.DataFrame, keys: list[str]) -> LinkageReport:
    """Conta per ogni riga quante righe ausiliarie condividono tutte le chiavi indicate."""
    return mapped_exact_linkage(primary, auxiliary, [(key, key) for key in keys])


def mapped_exact_linkage(
    primary: pd.DataFrame, auxiliary: pd.DataFrame, key_pairs: list[tuple[str, str]]
) -> LinkageReport:
    """Collega chiavi equivalenti anche quando hanno nomi diversi nei due portali."""
    if not key_pairs:
        raise ValueError("Seleziona almeno una coppia di chiavi.")
    if any(left not in primary.columns or right not in auxiliary.columns for left, right in key_pairs):
        raise ValueError("Le chiavi selezionate devono esistere nei rispettivi dataset.")
    aliases = [f"_key_{index}" for index in range(len(key_pairs))]
    left = primary[[column for column, _ in key_pairs]].astype("string").fillna("<mancante>")
    right = auxiliary[[column for _, column in key_pairs]].astype("string").fillna("<mancante>")
    left.columns = aliases
    right.columns = aliases
    right_counts = right.value_counts(dropna=False).rename("_candidati")
    candidates = left.merge(right_counts.reset_index(), on=aliases, how="left")["_candidati"].fillna(0).astype(int)
    right_keys = {column for _, column in key_pairs}
    labels = tuple(left_key if left_key == right_key else f"{left_key} ↔ {right_key}" for left_key, right_key in key_pairs)
    return LinkageReport(
        len(primary), len(primary), int(candidates.gt(0).sum()), int(candidates.eq(1).sum()),
        int(candidates.gt(1).sum()), labels,
        tuple(column for column in auxiliary.columns if column not in right_keys),
        "Corrispondenza esatta sulle coppie di chiavi selezionate.",
    )


def suggested_mapped_keys(primary: pd.DataFrame, auxiliary: pd.DataFrame) -> list[tuple[str, str]]:
    """Propone la coppia di colonne con la maggiore sovrapposizione di valori."""
    candidates: list[tuple[float, str, str]] = []
    for left in primary.columns:
        left_values = set(primary[left].dropna().astype("string").str.strip().str.casefold().head(5000))
        if not left_values or len(left_values) > 2000:
            continue
        for right in auxiliary.columns:
            right_values = set(auxiliary[right].dropna().astype("string").str.strip().str.casefold().head(5000))
            if not right_values or len(right_values) > 2000:
                continue
            overlap = len(left_values & right_values) / min(len(left_values), len(right_values))
            if overlap:
                stable_id = (
                    any(hint in str(left).casefold() for hint in ("id", "codice", "code"))
                    and any(hint in str(right).casefold() for hint in ("id", "codice", "code"))
                )
                candidates.append((overlap + (0.25 if stable_id else 0.0), str(left), str(right)))
    candidates.sort(reverse=True)
    return [(left, right) for _, left, right in candidates[:1]]


def temporal_linkage(
    primary: pd.DataFrame,
    auxiliary: pd.DataFrame,
    primary_time: str,
    auxiliary_time: str,
    primary_location: str,
    auxiliary_location: str,
    tolerance_minutes: int,
) -> LinkageReport:
    """Conta candidati nello stesso luogo entro una finestra temporale simmetrica."""
    if tolerance_minutes < 0:
        raise ValueError("La tolleranza temporale non può essere negativa.")
    left = pd.DataFrame({
        "_time": pd.to_datetime(primary[primary_time], errors="coerce", utc=True),
        "_place": primary[primary_location].astype("string").str.strip().str.casefold(),
    })
    right = pd.DataFrame({
        "_time": pd.to_datetime(auxiliary[auxiliary_time], errors="coerce", utc=True),
        "_place": auxiliary[auxiliary_location].astype("string").str.strip().str.casefold(),
    }).dropna()
    counts = pd.Series(0, index=left.index, dtype=int)
    delta = np.int64(tolerance_minutes * 60 * 1_000_000_000)
    for place, indexes in left.dropna().groupby("_place").groups.items():
        candidates = (
            right.loc[right["_place"] == place, "_time"].sort_values()
            .dt.tz_convert(None).to_numpy(dtype="datetime64[ns]").astype("int64")
        )
        if not len(candidates):
            continue
        moments = (
            left.loc[indexes, "_time"].dt.tz_convert(None)
            .to_numpy(dtype="datetime64[ns]").astype("int64")
        )
        lower = np.searchsorted(candidates, moments - delta, side="left")
        upper = np.searchsorted(candidates, moments + delta, side="right")
        counts.loc[indexes] = upper - lower
    comparable = int(left["_time"].notna().sum())
    keys = (f"{primary_location} ↔ {auxiliary_location}", f"±{tolerance_minutes} minuti")
    excluded = {auxiliary_time, auxiliary_location}
    return LinkageReport(
        len(primary), comparable, int(counts.gt(0).sum()), int(counts.eq(1).sum()), int(counts.gt(1).sum()),
        keys, tuple(column for column in auxiliary.columns if column not in excluded),
        f"Stesso luogo e orario entro ±{tolerance_minutes} minuti.",
    )


def report_markdown(primary_name: str, auxiliary_name: str, report: LinkageReport, identity_present: bool) -> str:
    meaning = (
        "Una corrispondenza unica può trasferire gli attributi identificativi del secondo file."
        if identity_present else
        "Una corrispondenza unica collega due record, ma non identifica una persona senza ulteriori attributi."
    )
    return "\n".join([
        "# Valutazione di collegabilità tra dataset", "",
        f"Dataset principale: **{primary_name}**.", f"Dataset ausiliario: **{auxiliary_name}**.",
        f"Assunzione dell’attaccante: {report.assumption}", "",
        f"- Righe con almeno una corrispondenza: {report.matched_rows:,} ({report.matched_share:.1%})",
        f"- Righe con una sola corrispondenza: {report.unique_matches:,} ({report.unique_share:.1%})",
        f"- Righe con più candidati: {report.multiple_matches:,}", "", f"Interpretazione: {meaning}", "",
        "Limite: il test misura collegabilità sotto un’ipotesi esplicita; non dimostra che l’attaccante possieda davvero il secondo file o conosca la persona.",
    ])
