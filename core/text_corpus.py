"""Motore testuale locale per bollettini di sicurezza e provvedimenti: ricerca TF-IDF,
classificazione, temi latenti ed estrazione di entità, senza modelli remoti."""

from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

# scikit-learn fornisce solo stopword inglesi; i corpora CSIRT e Garante sono in italiano.
ITALIAN_STOPWORDS = frozenset("""
a ad al alla alle allo agli ai anche che chi ci con cui da dal dalla dalle dagli dai degli dei del della
delle dello di e ed era essere gli ha hanno il in la le lo loro ma mi ne nei nel nella nelle nello noi non
o per più piu può puo quale quali quando quella quelle quello questa queste questo se si sia sono su sua sue
suo sul sulla sulle tra un una uno the of and to in for on is are be by with this that from as an or at it
via come dove essere stato stata stati state viene vengono tale tali ogni altri altre altro nonché nonche
presente presenti relativo relativa relativi relative ai sensi art articolo
""".split())

CVE_PATTERN = re.compile(r"CVE-\d{4}-\d{4,7}", re.IGNORECASE)
# Il gruppo opzionale consuma la versione ("v3.1") così il punteggio catturato è quello decimale.
CVSS_PATTERN = re.compile(r"CVSS(?:\s*v?\d(?:\.\d)?)?[^0-9]{0,20}(\d{1,2}[.,]\d)", re.IGNORECASE)
SENTENCE_SPLIT = re.compile(r"(?<=[.;:!?])\s+|\n+")

# Tassonomia degli asset urbani: collega un testo a una famiglia di infrastruttura.
ASSET_TAXONOMY: dict[str, tuple[str, ...]] = {
    "Videosorveglianza": ("videosorveglianza", "telecamer", "camera", "cctv", "nvr", "dvr", "hikvision", "dahua", "axis", "ip camera"),
    "Contatori intelligenti ed energia": ("smart meter", "contator", "energia", "elettric", "gas", "fotovoltaic", "inverter", "grid"),
    "Controllo industriale (ICS/SCADA)": ("scada", "ics", "plc", "hmi", "modbus", "siemens", "schneider", "rockwell", "industrial", "ot "),
    "Rete e accesso remoto": ("vpn", "firewall", "router", "fortinet", "fortigate", "cisco", "palo alto", "ivanti", "citrix", "gateway"),
    "Dispositivi IoT": ("iot", "firmware", "sensor", "embedded", "mqtt", "zigbee", "lorawan", "bluetooth"),
    "Dati biometrici e identità": ("biometric", "biometri", "riconoscimento facciale", "facial", "impronta", "spid", "identità digitale", "identita digitale", "autenticazione"),
    "Servizi web e cloud della PA": ("wordpress", "apache", "microsoft", "exchange", "sharepoint", "cloud", "portale", "web server", "php"),
    "Mobilità e trasporti": ("traffico", "semafor", "veicol", "trasport", "parcheggi", "targa", "ztl"),
}


def extract_entities(texts: pd.Series) -> pd.DataFrame:
    """CVE citate e punteggio CVSS massimo trovato nel testo."""
    text = texts.fillna("").astype(str)
    cves = text.apply(lambda value: sorted(set(match.upper() for match in CVE_PATTERN.findall(value))))
    cvss = text.apply(
        lambda value: max((float(score.replace(",", ".")) for score in CVSS_PATTERN.findall(value)
                           if float(score.replace(",", ".")) <= 10), default=np.nan)
    )
    return pd.DataFrame({"cve": cves.apply(", ".join), "n_cve": cves.apply(len), "cvss_max": cvss}, index=texts.index)


def tag_assets(texts: pd.Series) -> pd.DataFrame:
    """Matrice booleana testo × famiglia di asset, basata su parole chiave esplicite."""
    lowered = texts.fillna("").astype(str).str.lower()
    return pd.DataFrame(
        {family: lowered.apply(lambda value, keys=keys: any(key in value for key in keys))
         for family, keys in ASSET_TAXONOMY.items()},
        index=texts.index,
    )


@dataclass
class TextIndex:
    vectorizer: TfidfVectorizer
    matrix: object
    index: pd.Index


def _vectorizer(**kwargs) -> TfidfVectorizer:
    return TfidfVectorizer(
        strip_accents="unicode",
        lowercase=True,
        stop_words=list(ITALIAN_STOPWORDS),
        ngram_range=(1, 2),
        sublinear_tf=True,
        min_df=1,
        max_features=60000,
        **kwargs,
    )


def build_index(texts: pd.Series) -> TextIndex:
    clean = texts.fillna("").astype(str)
    if (clean.str.strip() == "").all():
        raise ValueError("La colonna di testo selezionata è vuota.")
    vectorizer = _vectorizer()
    return TextIndex(vectorizer=vectorizer, matrix=vectorizer.fit_transform(clean), index=clean.index)


def search(text_index: TextIndex, query: str, top_n: int = 10) -> pd.Series:
    """Similarità coseno tra la richiesta e ogni documento; restituisce solo punteggi positivi."""
    if not query.strip():
        return pd.Series(dtype=float)
    scores = (text_index.matrix @ text_index.vectorizer.transform([query]).T).toarray().ravel()
    ranked = pd.Series(scores, index=text_index.index).sort_values(ascending=False)
    return ranked[ranked > 0].head(top_n)


def best_passages(text_index: TextIndex, text: str, query: str, top_n: int = 2) -> list[str]:
    """Frasi del documento più vicine alla richiesta: citazione estrattiva, nessun testo generato."""
    sentences = [part.strip() for part in SENTENCE_SPLIT.split(str(text)) if len(part.strip()) > 30]
    if not sentences:
        return [str(text)[:300]]
    vectorizer = text_index.vectorizer
    scores = (vectorizer.transform(sentences) @ vectorizer.transform([query]).T).toarray().ravel()
    order = np.argsort(scores)[::-1][:top_n]
    return [sentences[i][:400] for i in sorted(order) if scores[i] > 0] or [sentences[0][:400]]


@dataclass
class TextClassifierResult:
    model: Pipeline
    metrics: dict[str, float | int]
    top_terms: pd.DataFrame
    predictions: pd.DataFrame


def train_text_classifier(df: pd.DataFrame, text_column: str, label_column: str) -> TextClassifierResult:
    """TF-IDF + regressione logistica: stima l'etichetta (es. gravità o tipologia) dal testo."""
    clean = df.dropna(subset=[text_column, label_column])
    labels = clean[label_column].astype(str)
    counts = labels.value_counts()
    # Classi con un solo esempio impediscono uno split stratificato e una misura onesta.
    keep = counts[counts >= 5].index
    clean, labels = clean[labels.isin(keep)], labels[labels.isin(keep)]
    if len(keep) < 2 or len(clean) < 30:
        raise ValueError("Servono almeno 30 testi e due etichette con almeno 5 esempi ciascuna.")
    X_train, X_test, y_train, y_test = train_test_split(
        clean[text_column].astype(str), labels, test_size=0.25, random_state=42, stratify=labels
    )
    model = Pipeline([
        ("tfidf", _vectorizer()),
        ("model", LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42)),
    ])
    model.fit(X_train, y_train)
    predicted = model.predict(X_test)
    confidence = model.predict_proba(X_test).max(axis=1)

    vocabulary = np.array(model.named_steps["tfidf"].get_feature_names_out())
    coefficients = model.named_steps["model"].coef_
    classes = model.named_steps["model"].classes_
    if len(classes) == 2:
        coefficients = np.vstack([-coefficients[0], coefficients[0]])
    top_terms = pd.DataFrame({
        "etichetta": classes,
        "termini più indicativi": [", ".join(vocabulary[np.argsort(row)[::-1][:8]]) for row in coefficients],
    })
    return TextClassifierResult(
        model=model,
        metrics={
            "Balanced accuracy": balanced_accuracy_score(y_test, predicted),
            "Weighted F1": f1_score(y_test, predicted, average="weighted", zero_division=0),
            "Test rows": len(y_test),
            "Classi": len(classes),
        },
        top_terms=top_terms,
        predictions=pd.DataFrame(
            {"testo": X_test.str.slice(0, 200), "reale": y_test, "stimato": predicted, "confidenza": confidence}
        ),
    )


def discover_topics(texts: pd.Series, n_topics: int = 6) -> tuple[pd.DataFrame, pd.Series]:
    """Temi latenti con NMF: utili per una tassonomia quando il dataset non ha etichette."""
    clean = texts.fillna("").astype(str)
    if len(clean) < n_topics * 3:
        raise ValueError("Servono almeno tre documenti per tema richiesto.")
    vectorizer = _vectorizer(max_df=0.8)
    matrix = vectorizer.fit_transform(clean)
    model = NMF(n_components=n_topics, random_state=42, init="nndsvda", max_iter=400)
    weights = model.fit_transform(matrix)
    vocabulary = np.array(vectorizer.get_feature_names_out())
    assignment = pd.Series(weights.argmax(axis=1), index=clean.index)
    topics = pd.DataFrame({
        "tema": range(n_topics),
        "termini": [", ".join(vocabulary[np.argsort(row)[::-1][:8]]) for row in model.components_],
        "documenti": [int((assignment == topic).sum()) for topic in range(n_topics)],
    })
    return topics, assignment
