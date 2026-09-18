"""Audit portabile per dataset comunali individuali o già aggregati."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from core.privacy import DIRECT, QUASI, SENSITIVE, anonymize, classify_columns, reidentification_risk

AGGREGATE_HINTS = (
    "conteggio", "count", "numero", "totale", "total", "media", "medio", "mean", "average",
    "mediana", "median", "percentuale", "percent", "quota", "tasso", "rate", "affollamento",
    "connessioni", "accessi", "utenti_unici", "unique_users", "valore",
)


@dataclass(frozen=True)
class GranularityAssessment:
    kind: str
    confidence: float
    reasons: tuple[str, ...]
    measures: tuple[str, ...]


@dataclass(frozen=True)
class GenericAudit:
    outcome: str
    reasons: tuple[str, ...]
    metrics: dict[str, float | int | str]
    scan: pd.DataFrame
    quasi: tuple[str, ...]
    direct: tuple[str, ...]
    sensitive: str | None
    row_kind: str
    purpose: str
    measure: str | None = None


def _normalised(name: str) -> str:
    return str(name).lower().replace(" ", "_").replace("-", "_")


def aggregate_measures(df: pd.DataFrame) -> list[str]:
    """Colonne numeriche il cui nome indica conteggi o statistiche aggregate."""
    return [
        str(column)
        for column in df.columns
        if pd.api.types.is_numeric_dtype(df[column])
        and any(hint in _normalised(column) for hint in AGGREGATE_HINTS)
    ]


def infer_granularity(df: pd.DataFrame) -> GranularityAssessment:
    """Suggerisce se ogni riga descrive un evento/persona o una cella statistica."""
    scan = classify_columns(df)
    direct = int((scan["categoria"] == DIRECT).sum())
    measures = aggregate_measures(df)
    reasons: list[str] = []
    score = 0.0
    if measures:
        score += 0.65
        reasons.append("Sono presenti misure aggregate: " + ", ".join(measures[:3]) + ".")
    if direct == 0:
        score += 0.15
        reasons.append("Non sono stati rilevati identificativi diretti.")
    if len(df) and any(df[column].duplicated().any() for column in measures):
        score += 0.10
    kind = "aggregato" if score >= 0.65 else "individuale"
    if kind == "individuale":
        reasons.append("Non emergono conteggi o statistiche che provino un’aggregazione per gruppo.")
    return GranularityAssessment(kind, min(score, 0.95), tuple(reasons), tuple(measures))


def suggested_roles(df: pd.DataFrame) -> tuple[list[str], list[str], list[str]]:
    scan = classify_columns(df)
    direct = scan.loc[scan["categoria"] == DIRECT, "variabile"].tolist()
    quasi = scan.loc[scan["categoria"] == QUASI, "variabile"].tolist()
    sensitive = scan.loc[scan["categoria"] == SENSITIVE, "variabile"].tolist()
    return direct, quasi, sensitive


def audit_generic(
    df: pd.DataFrame,
    row_kind: str,
    direct: list[str],
    quasi: list[str],
    sensitive: str | None,
    k: int = 5,
    measure: str | None = None,
    purpose: str = "pubblicazione",
) -> GenericAudit:
    """Valuta un file senza dipendere da nomi o schema di uno specifico Comune."""
    scan = classify_columns(df)
    metrics: dict[str, float | int | str] = {"Righe": len(df), "Colonne": len(df.columns)}
    reasons: list[str] = []
    outcome = "Da verificare"

    internal = purpose == "interno"
    if direct and not internal:
        reasons.append("Rimuovere gli identificativi diretti: " + ", ".join(direct) + ".")
        outcome = "Da correggere"
    elif direct:
        reasons.append(
            "Gli identificativi possono essere necessari all’operatività, ma richiedono base giuridica, accessi per ruolo e tempi di cancellazione."
        )
        outcome = "Uso interno da governare"

    if row_kind == "aggregato":
        candidates = aggregate_measures(df)
        selected = measure if measure in df.columns else (candidates[0] if candidates else None)
        if selected and pd.api.types.is_numeric_dtype(df[selected]):
            values = pd.to_numeric(df[selected], errors="coerce")
            small = values.gt(0) & values.lt(k)
            metrics["Celle sotto soglia %"] = round(float(small.mean() * 100), 1)
            metrics["Celle sotto soglia"] = int(small.sum())
            metrics["Misura controllata"] = selected
            if small.any() and not internal:
                reasons.append(f"Sopprimere o accorpare {int(small.sum())} celle con valori tra 1 e {k - 1}.")
                outcome = "Da correggere"
            elif not direct and not internal:
                outcome = "Compatibile con pubblicazione"
                reasons.append(f"Nessuna cella positiva di {selected} contiene meno di {k} unità.")
        else:
            reasons.append("Indicare la colonna che contiene il numero di persone o eventi per cella.")
        if not internal:
            reasons.append("Verificare anche attacchi per differenza tra pubblicazioni successive.")
    elif quasi:
        risk = reidentification_risk(df, quasi, k, sensitive).metrics
        metrics.update(risk)
        unique = float(risk["Righe uniche %"])
        if internal:
            outcome = "Uso interno da governare"
            reasons.append(
                f"Il {unique:.1f}% delle righe è unico: può essere necessario per il servizio, ma aumenta l’impatto di accessi impropri o violazioni."
            )
        elif unique > 0 or float(risk["Righe sotto k %"]) > 0:
            reasons.append(f"Il {unique:.1f}% delle righe è unico sui quasi-identificativi selezionati.")
            outcome = "Da correggere"
        elif not direct:
            outcome = "Compatibile con pubblicazione"
            reasons.append(f"Ogni combinazione selezionata compare almeno {k} volte.")
    else:
        reasons.append("Selezionare le colonne che un estraneo potrebbe già conoscere.")

    return GenericAudit(
        outcome, tuple(reasons), metrics, scan, tuple(quasi), tuple(direct), sensitive, row_kind, purpose, measure
    )


def protect_generic(
    df: pd.DataFrame,
    row_kind: str,
    direct: list[str],
    quasi: list[str],
    k: int,
    measure: str | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    """Produce una copia prudente per dati individuali o tabelle aggregate."""
    if row_kind == "individuale":
        result = anonymize(df, direct, quasi, k)
        return result.data, result.log

    protected = df.drop(columns=[column for column in direct if column in df.columns]).copy()
    log = [f"Colonne rimosse: {', '.join(direct)}"] if direct else []
    if measure and measure in protected.columns:
        values = pd.to_numeric(protected[measure], errors="coerce")
        small = values.gt(0) & values.lt(k)
        protected.loc[small, measure] = pd.NA
        log.append(f"Celle soppresse in {measure} perché comprese tra 1 e {k - 1}: {int(small.sum())}")
    return protected, log


def report_markdown(name: str, audit: GenericAudit, k: int) -> str:
    lines = [
        f"# Valutazione privacy · {name}", "", f"Esito: **{audit.outcome}**", "",
        f"Unità dichiarata: **{'cella aggregata' if audit.row_kind == 'aggregato' else 'persona o evento'}**.",
        f"Scopo dichiarato: **{'uso operativo interno' if audit.purpose == 'interno' else 'pubblicazione o condivisione'}**.",
        f"Soglia prudenziale: **{k}** unità per gruppo o cella.", "", "## Evidenze",
    ]
    lines += [f"- {key}: {value}" for key, value in audit.metrics.items()]
    lines += ["", "## Azioni"] + [f"- {reason}" for reason in audit.reasons]
    lines += [
        "", "## Limiti",
        "- La classificazione automatica delle colonne è un suggerimento e deve essere confermata dal titolare dei dati.",
        "- Il controllo non dimostra anonimato assoluto e non sostituisce la valutazione del DPO.",
    ]
    return "\n".join(lines)
