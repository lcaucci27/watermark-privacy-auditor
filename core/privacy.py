"""Audit di privacy locale: classificazione delle colonne, rischio di re-identificazione,
anonimizzazione con k-anonimato e attacco di inferenza sugli attributi sensibili."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from core.ml_pipeline import _preprocessor

DIRECT = "Identificativo diretto"
QUASI = "Quasi-identificativo"
SENSITIVE = "Attributo sensibile"
OTHER = "Altro"

DIRECT_KEYS = (
    "nome", "cognome", "name", "surname", "email", "mail", "telefono", "phone", "cellulare",
    "mobile", "codice_fiscale", "codicefiscale", "fiscal", "iban", "indirizzo", "address",
    "ssn", "passaporto", "passport", "targa", "plate", "documento", "username", "ip", "mac_address",
    "macaddress", "device_id", "deviceid", "id_utente", "userid", "user_id", "session_id", "cookie",
)
QUASI_KEYS = (
    "eta", "age", "sesso", "genere", "gender", "sex", "cap", "zip", "postal", "comune", "city",
    "citta", "provincia", "province", "municipalita", "quartiere", "nascita", "birth", "nazionalita",
    "nationality", "cittadinanza", "professione", "occupation", "lavoro", "job", "titolo_studio",
    "istruzione", "education", "stato_civile", "marital", "residenza", "zona", "municipio", "data",
    "date", "giorno", "day", "ora", "time", "timestamp", "latitudine", "latitude", "longitudine",
    "longitude", "coordinate", "geopoint", "geo_point", "sede", "luogo", "location",
)
SENSITIVE_KEYS = (
    "salute", "health", "diagnosi", "diagnosis", "malattia", "disease", "patologia", "religione",
    "religion", "etnia", "ethnic", "orientamento", "politic", "sindacato", "union", "reddito",
    "income", "salary", "stipendio", "disabilita", "disability", "farmaco", "terapia", "condanna",
    "servizi_sociali", "assistenza", "fragilita", "vulnerabilita", "minore", "penale", "biometr",
)

# Pattern sui valori: una colonna con nome neutro può comunque contenere dati personali.
VALUE_PATTERNS = {
    "email": re.compile(r"^[\w.+-]+@[\w-]+\.[\w.-]+$"),
    "codice fiscale": re.compile(r"^[A-Z]{6}\d{2}[A-EHLMPRST]\d{2}[A-Z]\d{3}[A-Z]$", re.IGNORECASE),
    "IBAN": re.compile(r"^[A-Z]{2}\d{2}[A-Z0-9]{11,30}$", re.IGNORECASE),
    "telefono": re.compile(r"^(\+?39)?[\s-]?(3\d{2}|0\d{1,4})[\s-]?\d{5,8}$"),
    "indirizzo IP": re.compile(r"^(\d{1,3}\.){3}\d{1,3}$"),
}


def _tokens(name: str) -> tuple[str, list[str]]:
    plain = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode().lower()
    return plain, [token for token in re.split(r"[^a-z0-9]+", plain) if token]


def _matches(name: str, keys: tuple[str, ...]) -> str | None:
    plain, tokens = _tokens(name)
    joined = "_".join(tokens)
    for key in keys:
        if key in {"nome", "name"} and set(tokens) & {
            "zona", "sede", "luogo", "area", "quartiere", "municipio", "comune", "city", "location"
        }:
            continue
        # Le chiavi corte ("ip", "cap", "eta") producono falsi positivi come sottostringhe.
        if (len(key) <= 3 and key in tokens) or (len(key) > 3 and key in joined):
            return key
    return None


def _value_pattern(series: pd.Series) -> str | None:
    values = series.dropna().astype(str).str.strip()
    values = values[values != ""].head(500)
    if values.empty:
        return None
    for label, pattern in VALUE_PATTERNS.items():
        if values.str.match(pattern).mean() >= 0.5:
            return label
    return None


def classify_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Assegna a ogni colonna una categoria di privacy con il motivo della scelta."""
    rows = []
    n = max(len(df), 1)
    for column in df.columns:
        distinct = df[column].nunique(dropna=True)
        pattern = _value_pattern(df[column])
        if pattern:
            category, reason = DIRECT, f"valori in formato {pattern}"
        elif key := _matches(column, DIRECT_KEYS):
            category, reason = DIRECT, f"nome colonna: '{key}'"
        elif key := _matches(column, SENSITIVE_KEYS):
            category, reason = SENSITIVE, f"nome colonna: '{key}'"
        elif key := _matches(column, QUASI_KEYS):
            category, reason = QUASI, f"nome colonna: '{key}'"
        elif not pd.api.types.is_numeric_dtype(df[column]) and distinct >= 0.9 * n and n >= 20:
            category, reason = DIRECT, "testo quasi univoco per riga"
        else:
            category, reason = OTHER, ""
        rows.append({
            "variabile": str(column),
            "categoria": category,
            "motivo": reason,
            "valori_distinti": distinct,
            "unicità_%": round(distinct / n * 100, 1),
        })
    return pd.DataFrame(rows)


@dataclass
class RiskReport:
    metrics: dict[str, float | int]
    class_sizes: pd.Series


def reidentification_risk(
    df: pd.DataFrame, quasi: list[str], k_target: int, sensitive: str | None = None
) -> RiskReport:
    """Rischio del modello 'prosecutor': chi conosce i quasi-identificativi di una persona
    la individua con probabilità 1/dimensione della sua classe di equivalenza."""
    if not quasi:
        raise ValueError("Seleziona almeno un quasi-identificativo.")
    keys = df[quasi].astype(str)
    sizes = keys.groupby(quasi, dropna=False)[quasi[0]].transform("size")
    metrics: dict[str, float | int] = {
        "k minimo": int(sizes.min()),
        "Righe uniche %": round(float((sizes == 1).mean() * 100), 1),
        "Rischio massimo %": round(float(100 / sizes.min()), 1),
        "Righe sotto k %": round(float((sizes < k_target).mean() * 100), 1),
    }
    if sensitive and sensitive in df.columns:
        # k-anonimato non basta se tutta la classe condivide lo stesso valore sensibile.
        diversity = df.assign(_key=keys.agg("|".join, axis=1)).groupby("_key")[sensitive].nunique(dropna=False)
        metrics["l-diversità minima"] = int(diversity.min())
    return RiskReport(metrics=metrics, class_sizes=sizes)


@dataclass
class AnonymizationResult:
    data: pd.DataFrame
    level: int
    suppressed: int
    log: list[str] = field(default_factory=list)


NUMERIC_BINS = (None, 10, 5, 3, 2)
CATEGORY_TOP = (None, 25, 10, 5, 3)


def _generalize(series: pd.Series, level: int, k: int) -> pd.Series:
    if level == 0:
        return series
    if pd.api.types.is_numeric_dtype(series) and series.nunique(dropna=True) > NUMERIC_BINS[level]:
        binned = pd.qcut(series, q=NUMERIC_BINS[level], duplicates="drop")
        return binned.astype(str).replace("nan", "mancante")
    values = series.astype(str)
    counts = values.value_counts()
    keep = set(counts.head(CATEGORY_TOP[level]).index) & set(counts[counts >= k].index)
    return values.where(values.isin(keep), "Altro")


def anonymize(df: pd.DataFrame, direct: list[str], quasi: list[str], k: int) -> AnonymizationResult:
    """Rimuove gli identificativi diretti, generalizza i quasi-identificativi al livello
    minimo che raggiunge k e sopprime le righe che restano in classi più piccole."""
    base = df.drop(columns=[column for column in direct if column in df.columns and column not in quasi])
    log = [f"Colonne rimosse: {', '.join(direct)}"] if direct else []
    candidate = base
    level = 0
    for level in range(len(NUMERIC_BINS)):
        candidate = base.copy()
        for column in quasi:
            candidate[column] = _generalize(base[column], level, k)
        if reidentification_risk(candidate, quasi, k).metrics["k minimo"] >= k:
            break
    if level:
        log.append(
            f"Generalizzazione livello {level}: numeri in {NUMERIC_BINS[level]} fasce, "
            f"categorie ridotte alle {CATEGORY_TOP[level]} più frequenti con almeno {k} casi"
        )
    sizes = reidentification_risk(candidate, quasi, k).class_sizes
    suppressed = int((sizes < k).sum())
    if suppressed:
        candidate = candidate[sizes >= k]
        log.append(f"Righe soppresse perché ancora in classi con meno di {k} casi: {suppressed}")
    return AnonymizationResult(data=candidate.reset_index(drop=True), level=level, suppressed=suppressed, log=log)


@dataclass
class AttackResult:
    model: Pipeline | None
    metrics: dict[str, float | int]
    target: pd.Series


def _attack_target(series: pd.Series) -> pd.Series:
    # Un valore sensibile continuo (es. reddito) diventa fasce, come farebbe un attaccante.
    if pd.api.types.is_numeric_dtype(series) and series.nunique(dropna=True) > 12:
        return pd.qcut(series, q=4, duplicates="drop").astype(str)
    return series.astype(str)


def inference_attack(df: pd.DataFrame, quasi: list[str], sensitive: str) -> AttackResult:
    """Addestra un attaccante che deduce l'attributo sensibile dai soli quasi-identificativi
    e misura il guadagno rispetto a una scelta casuale su righe escluse dall'addestramento."""
    clean = df.dropna(subset=[sensitive])
    y = _attack_target(clean[sensitive])
    X = clean[quasi]
    classes = y.nunique()
    if len(clean) < 30 or classes < 2:
        raise ValueError("L'attacco richiede almeno 30 righe e due valori sensibili distinti.")
    stratify = y if y.value_counts().min() >= 2 else None
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=stratify)
    model = Pipeline([
        ("preprocess", _preprocessor(X)),
        ("model", RandomForestClassifier(
            n_estimators=150, min_samples_leaf=3, class_weight="balanced", random_state=42, n_jobs=-1
        )),
    ])
    model.fit(X_train, y_train)
    score = balanced_accuracy_score(y_test, model.predict(X_test))
    chance = 1 / classes
    return AttackResult(
        model=model,
        metrics={
            "Accuratezza attacco": round(float(score), 3),
            "Base casuale": round(chance, 3),
            "Vantaggio attacco": round(float(max(score - chance, 0) / (1 - chance)), 3),
        },
        target=y,
    )


def profile_exposure(df: pd.DataFrame, profile: dict[str, object]) -> int:
    """Numero di righe identiche al profilo sui quasi-identificativi indicati."""
    mask = pd.Series(True, index=df.index)
    for column, value in profile.items():
        mask &= df[column].astype(str) == str(value)
    return int(mask.sum())


def synthetic_residents(rows: int = 1200) -> pd.DataFrame:
    """Dataset sintetico di prova con identificativi, quasi-identificativi e un attributo sensibile.
    Nessuna persona reale: i valori sono generati con seed 42."""
    rng = np.random.default_rng(42)
    age = rng.integers(18, 90, rows)
    sex = rng.choice(["F", "M"], rows)
    municipality = rng.choice([f"Municipalità {i}" for i in range(1, 11)], rows)
    cap = rng.choice([f"801{i:02d}" for i in range(21, 48)], rows)
    education = rng.choice(["Licenza media", "Diploma", "Laurea", "Dottorato"], rows, p=[0.3, 0.4, 0.25, 0.05])
    income = np.round(rng.lognormal(10, 0.45, rows) * (1 + (education == "Laurea") * 0.3), -2)
    chronic_p = 1 / (1 + np.exp(-(age - 62) / 9))
    chronic = np.where(rng.random(rows) < chronic_p, "Sì", "No")
    letters = np.array(list("ABCDEFGHILMNOPRSTUVZ"))
    fiscal = [
        "".join(rng.choice(letters, 6)) + f"{rng.integers(0, 99):02d}" + rng.choice(list("ABCDEHLMPRST"))
        + f"{rng.integers(1, 71):02d}" + "F839" + rng.choice(letters)
        for _ in range(rows)
    ]
    return pd.DataFrame({
        "codice_fiscale": fiscal,
        "email": [f"residente{i:04d}@esempio.it" for i in range(rows)],
        "eta": age,
        "sesso": sex,
        "cap": cap,
        "municipalita": municipality,
        "titolo_studio": education,
        "reddito": income,
        "patologia_cronica": chronic,
        "accessi_servizi_anno": rng.poisson(2 + (chronic == "Sì") * 3, rows),
    })
