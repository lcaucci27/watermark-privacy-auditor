"""Modello di valutazione delle minacce: stima l'impatto sistemico ACN di un bollettino CSIRT."""

from __future__ import annotations

import re

import pandas as pd

from core.text_corpus import TextClassifierResult, train_text_classifier

TEXT_FIELDS = ("titolo", "sintesi", "tipologia", "prodotti", "descrizione", "argomenti")
LABEL = "impatto_classe"
# La gravità dichiarata dal fornitore è quasi l'etichetta stessa: il modello principale non la vede.
SEVERITY_PATTERN = re.compile(
    r"(di cui \w+ )?(con )?gravit[àa]\s*[“”\"'«]?\s*(critica|alta|media|bassa)\s*[“”\"'»]?|CVSS[^.;]{0,40}?\d+[.,]\d",
    re.IGNORECASE,
)


def bulletin_text(df: pd.DataFrame, mask_severity: bool = True) -> pd.Series:
    """Testo del bollettino più segnali strutturati resi come parole (sfruttamento, PoC, tipo)."""
    text = df[[field for field in TEXT_FIELDS if field in df.columns]].fillna("").astype(str).agg(" ".join, axis=1)
    if mask_severity:
        text = text.str.replace(SEVERITY_PATTERN, " ", regex=True)
    signals = (
        " tipo_" + df.get("tipo", pd.Series("", index=df.index)).fillna("").astype(str).str.lower()
        + " sfruttata_" + (df.get("n_cve_sfruttate", 0) > 0).astype(str).str.lower()
        + " poc_" + (df.get("n_cve_con_poc", 0) > 0).astype(str).str.lower()
    )
    return text + signals


def train_threat_model(df: pd.DataFrame, mask_severity: bool = True) -> TextClassifierResult:
    if LABEL not in df.columns:
        raise ValueError("Il file CSIRT non contiene la colonna impatto_classe: rigenera con scripts/fetch_data.py.")
    frame = df.assign(_testo=bulletin_text(df, mask_severity)).dropna(subset=[LABEL])
    return train_text_classifier(frame, "_testo", LABEL)


def ablation(df: pd.DataFrame) -> pd.DataFrame:
    """Confronto onesto: stesso modello con e senza le frasi di gravità del fornitore."""
    rows = []
    for masked in (True, False):
        result = train_threat_model(df, masked)
        rows.append({
            "testo usato": "senza gravità dichiarata" if masked else "con gravità dichiarata",
            "accuratezza bilanciata": result.metrics["Balanced accuracy"],
            "F1 ponderato": result.metrics["Weighted F1"],
            "caso (1/classi)": 1 / result.metrics["Classi"],
            "bollettini di test": result.metrics["Test rows"],
        })
    return pd.DataFrame(rows)
