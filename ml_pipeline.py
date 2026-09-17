"""Reusable, fully local ML engine for tabular hackathon datasets."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Any, Literal

import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import IsolationForest, RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    silhouette_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

Task = Literal["classification", "regression", "clustering"]


@dataclass
class MLResult:
    task: Task
    model: BaseEstimator
    metrics: dict[str, float | int | str]
    predictions: pd.DataFrame
    feature_importance: pd.DataFrame
    confusion: pd.DataFrame | None = None
    notes: tuple[str, ...] = ()


def infer_task(target: pd.Series) -> Literal["classification", "regression"]:
    """Conservative task inference; users can always override it in the UI."""
    unique = target.nunique(dropna=True)
    if not pd.api.types.is_numeric_dtype(target):
        return "classification"
    if unique <= max(12, int(len(target) * 0.05)):
        return "classification"
    return "regression"


def _clean_features(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    X = df.copy()
    notes: list[str] = []
    unusable = [column for column in X.columns if X[column].isna().all() or X[column].nunique(dropna=True) <= 1]
    if unusable:
        X = X.drop(columns=unusable)
        notes.append(f"Colonne vuote o costanti escluse: {', '.join(map(str, unusable))}")

    # Identifier-like columns usually memorize rows and hurt generalization.
    identifiers = [
        column for column in X.columns
        if (str(column).lower() in {"id", "uuid", "index"} or str(column).lower().endswith("_id"))
        and X[column].nunique(dropna=True) >= 0.9 * len(X)
    ]
    if identifiers and len(identifiers) < len(X.columns):
        X = X.drop(columns=identifiers)
        notes.append(f"Identificatori probabili esclusi: {', '.join(map(str, identifiers))}")

    high_cardinality = [
        column for column in X.select_dtypes(exclude=np.number).columns
        if X[column].nunique(dropna=True) > min(100, max(20, int(len(X) * 0.5)))
    ]
    if high_cardinality and len(high_cardinality) < len(X.columns):
        X = X.drop(columns=high_cardinality)
        notes.append(f"Testo ad alta cardinalità escluso: {', '.join(map(str, high_cardinality))}")

    if X.empty:
        raise ValueError("Dopo i controlli non restano variabili utilizzabili.")
    return X, notes


def _preprocessor(X: pd.DataFrame, *, scale_numeric: bool = False) -> ColumnTransformer:
    numeric = X.select_dtypes(include=np.number).columns.tolist()
    categorical = [column for column in X.columns if column not in numeric]
    number_steps: list[tuple[str, Any]] = [("imputer", SimpleImputer(strategy="median"))]
    if scale_numeric:
        number_steps.append(("scaler", StandardScaler()))
    return ColumnTransformer(
        transformers=[
            ("number", Pipeline(number_steps), numeric),
            (
                "category",
                Pipeline([
                    ("imputer", SimpleImputer(strategy="most_frequent")),
                    ("encoder", OneHotEncoder(handle_unknown="ignore", min_frequency=2, sparse_output=False)),
                ]),
                categorical,
            ),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def _importance(model: Pipeline, X: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
    try:
        result = permutation_importance(model, X, y, n_repeats=3, random_state=42, n_jobs=-1)
        return pd.DataFrame({"feature": X.columns, "importance": result.importances_mean}).sort_values(
            "importance", ascending=False
        )
    except Exception:
        return pd.DataFrame(columns=["feature", "importance"])


def train_supervised(
    df: pd.DataFrame,
    target: str,
    task: Literal["classification", "regression"],
    test_size: float = 0.2,
) -> MLResult:
    if target not in df.columns:
        raise ValueError(f"La colonna target '{target}' non esiste.")
    clean = df.dropna(subset=[target]).copy()
    if len(clean) < 20:
        raise ValueError("Servono almeno 20 righe con target noto.")
    X, notes = _clean_features(clean.drop(columns=[target]))
    y = clean[target]
    if y.nunique(dropna=True) < 2:
        raise ValueError("Il target deve contenere almeno due valori distinti.")

    stratify = y if task == "classification" and y.value_counts().min() >= 2 else None
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=stratify
    )
    if task == "classification":
        estimator = RandomForestClassifier(
            n_estimators=160, min_samples_leaf=2, class_weight="balanced", random_state=42, n_jobs=-1
        )
    else:
        estimator = RandomForestRegressor(
            n_estimators=160, min_samples_leaf=2, random_state=42, n_jobs=-1
        )
    model = Pipeline([("preprocess", _preprocessor(X)), ("model", estimator)])
    model.fit(X_train, y_train)
    predicted = model.predict(X_test)

    output = X_test.copy()
    output[f"actual_{target}"] = y_test
    output[f"predicted_{target}"] = predicted
    confusion = None
    if task == "classification":
        metrics = {
            "Accuracy": accuracy_score(y_test, predicted),
            "Balanced accuracy": balanced_accuracy_score(y_test, predicted),
            "Weighted F1": f1_score(y_test, predicted, average="weighted", zero_division=0),
            "Test rows": len(y_test),
        }
        labels = list(model.named_steps["model"].classes_)
        confusion = pd.DataFrame(confusion_matrix(y_test, predicted, labels=labels), index=labels, columns=labels)
        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(X_test)
            output["confidence"] = probabilities.max(axis=1)
    else:
        metrics = {
            "R²": r2_score(y_test, predicted),
            "MAE": mean_absolute_error(y_test, predicted),
            "RMSE": mean_squared_error(y_test, predicted) ** 0.5,
            "Test rows": len(y_test),
        }
        output["absolute_error"] = np.abs(y_test.to_numpy() - predicted)

    return MLResult(
        task=task,
        model=model,
        metrics=metrics,
        predictions=output.sort_index(),
        feature_importance=_importance(model, X_test, y_test),
        confusion=confusion,
        notes=tuple(notes),
    )


def train_clustering(df: pd.DataFrame, clusters: int = 3) -> MLResult:
    X, notes = _clean_features(df)
    if len(X) < clusters + 2:
        raise ValueError("Il dataset è troppo piccolo per il numero di segmenti selezionato.")
    preprocess = _preprocessor(X, scale_numeric=True)
    matrix = preprocess.fit_transform(X)
    model = KMeans(n_clusters=clusters, n_init=10, random_state=42)
    labels = model.fit_predict(matrix)
    predictions = df.copy()
    predictions["cluster"] = labels
    counts = pd.Series(labels).value_counts().sort_index()
    metrics: dict[str, float | int | str] = {
        "Clusters": clusters,
        "Silhouette score": silhouette_score(matrix, labels) if clusters < len(X) else float("nan"),
        "Largest cluster": int(counts.max()),
        "Smallest cluster": int(counts.min()),
    }
    pipeline = Pipeline([("preprocess", preprocess), ("model", model)])
    return MLResult(
        task="clustering",
        model=pipeline,
        metrics=metrics,
        predictions=predictions,
        feature_importance=pd.DataFrame(columns=["feature", "importance"]),
        notes=tuple(notes),
    )


def detect_anomalies(df: pd.DataFrame, contamination: float = 0.05) -> pd.DataFrame:
    numeric = df.select_dtypes(include=np.number)
    if numeric.empty:
        raise ValueError("La rilevazione delle anomalie richiede almeno una variabile numerica.")
    prepared = SimpleImputer(strategy="median").fit_transform(numeric)
    model = IsolationForest(contamination=contamination, random_state=42, n_jobs=-1)
    labels = model.fit_predict(prepared)
    result = df.copy()
    result["anomaly_score"] = -model.score_samples(prepared)
    result["is_anomaly"] = labels == -1
    return result.sort_values("anomaly_score", ascending=False)


def serialize_model(model: BaseEstimator) -> bytes:
    buffer = BytesIO()
    joblib.dump(model, buffer)
    return buffer.getvalue()
