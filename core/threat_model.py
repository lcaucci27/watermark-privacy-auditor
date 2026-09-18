"""Modello di valutazione delle minacce: stima l'impatto sistemico ACN di un bollettino CSIRT."""

from __future__ import annotations

import re

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, f1_score
from sklearn.pipeline import Pipeline

from core.text_corpus import TextClassifierResult, _vectorizer, train_text_classifier

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


def _dates(df: pd.DataFrame) -> pd.Series:
    raw = df.get("data", pd.Series("", index=df.index)).astype(str).str.replace(" ore ", " ", regex=False)
    return pd.to_datetime(raw, format="%d/%m/%y %H:%M", errors="coerce")


def temporal_validation(df: pd.DataFrame, test_share: float = 0.25) -> dict[str, object]:
    """Addestra sui bollettini più vecchi e valuta sui più recenti, come accadrebbe in servizio."""
    frame = df.assign(_data=_dates(df), _testo=bulletin_text(df)).dropna(subset=["_data", LABEL])
    frame = frame.sort_values("_data")
    cut = int(len(frame) * (1 - test_share))
    train, test = frame.iloc[:cut], frame.iloc[cut:]
    test = test[test[LABEL].isin(train[LABEL].unique())]
    if len(train) < 30 or len(test) < 10:
        raise ValueError("Servono almeno 40 bollettini datati per la validazione temporale.")
    model = Pipeline([
        ("tfidf", _vectorizer()),
        ("model", LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42)),
    ])
    model.fit(train["_testo"], train[LABEL])
    predicted = model.predict(test["_testo"])
    majority = train[LABEL].value_counts().idxmax()
    return {
        "Addestramento fino al": f"{train['_data'].max():%d/%m/%Y}",
        "Test dal": f"{test['_data'].min():%d/%m/%Y}",
        "Bollettini di test": len(test),
        "Accuratezza bilanciata": balanced_accuracy_score(test[LABEL], predicted),
        "F1 ponderato": f1_score(test[LABEL], predicted, average="weighted", zero_division=0),
        "Classe più frequente": balanced_accuracy_score(test[LABEL], [majority] * len(test)),
    }


def explain(model: Pipeline, text: str, top_n: int = 8) -> tuple[str, pd.DataFrame]:
    """Classe stimata e parole del testo che l'hanno spinta di più (peso TF-IDF × coefficiente)."""
    vectorizer, classifier = model.named_steps["tfidf"], model.named_steps["model"]
    vector = vectorizer.transform([text])
    probabilities = classifier.predict_proba(vector)[0]
    best = int(np.argmax(probabilities))
    coefficients = classifier.coef_[0] if len(classifier.classes_) == 2 else classifier.coef_[best]
    if len(classifier.classes_) == 2 and best == 0:
        coefficients = -coefficients
    contribution = vector.multiply(coefficients).tocsr()
    terms = np.array(vectorizer.get_feature_names_out())
    order = np.argsort(contribution.data)[::-1][:top_n]
    drivers = pd.DataFrame({
        "parola": terms[contribution.indices[order]],
        "spinta verso la classe": contribution.data[order],
    })
    return str(classifier.classes_[best]), drivers[drivers["spinta verso la classe"] > 0]
