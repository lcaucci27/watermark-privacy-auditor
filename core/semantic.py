"""Ricerca semantica ibrida: embedding locali (significato) + TF-IDF (parole esatte),
fusi con Reciprocal Rank Fusion. Se gli embedding non sono disponibili resta il solo TF-IDF."""

from __future__ import annotations

import hashlib
import os
import re
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from core import local_ai
from core.text_corpus import TextIndex, build_index, search

CACHE_DIR = Path(__file__).resolve().parent.parent / "data"
RRF_K = 60
CHECKPOINT_BATCH = 32


def _normalize(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / np.where(norms == 0, 1, norms)


_STORES: dict[str, dict[str, np.ndarray]] = {}


def _store_path(model: str) -> Path:
    return CACHE_DIR / f".emb_store_{re.sub(r'[^a-z0-9]+', '_', model.lower())}.npz"


def _read_store(path: Path) -> dict[str, np.ndarray]:
    if not path.exists():
        return {}
    with np.load(path) as saved:
        return {key: saved[key] for key in saved.files}


@contextmanager
def _store_lock(path: Path, timeout: float = 30.0):
    """Serializza gli aggiornamenti senza dipendenze e funziona su Windows e macOS."""
    lock = path.with_suffix(path.suffix + ".lock")
    deadline = time.monotonic() + timeout
    while True:
        try:
            lock.mkdir()
            break
        except FileExistsError:
            try:
                stale = time.time() - lock.stat().st_mtime > 120
            except FileNotFoundError:
                continue
            if stale:
                try:
                    lock.rmdir()
                except OSError:
                    pass
                continue
            if time.monotonic() >= deadline:
                raise TimeoutError(f"Cache embedding occupata: {lock}")
            time.sleep(0.1)
    try:
        yield
    finally:
        lock.rmdir()


def _save_store(path: Path, additions: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """Unisce gli aggiornamenti più recenti e sostituisce il file solo quando è completo."""
    with _store_lock(path):
        merged = _read_store(path)
        merged.update(additions)
        temporary = path.with_name(f"{path.name}.{os.getpid()}.tmp.npz")
        try:
            np.savez(temporary, **merged)
            os.replace(temporary, path)
        finally:
            if temporary.exists():
                temporary.unlink()
    return merged


def _store(model: str) -> dict[str, np.ndarray]:
    # Cache di processo sopra il file su disco: ogni testo si trasforma in vettore una sola volta.
    if model not in _STORES:
        path = _store_path(model)
        _STORES[model] = _read_store(path)
    return _STORES[model]


def _key(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def embed_cached(texts: list[str], model: str = local_ai.EMBED_MODEL) -> np.ndarray | None:
    """Embedding normalizzati per testo; calcola solo quelli mai visti e li salva su disco."""
    store = _store(model)
    missing = list(dict.fromkeys(text for text in texts if _key(text) not in store))
    for start in range(0, len(missing), CHECKPOINT_BATCH):
        chunk = missing[start:start + CHECKPOINT_BATCH]
        vectors = local_ai.embed(chunk, model, batch=CHECKPOINT_BATCH)
        if vectors is None:
            return None
        additions = {
            _key(text): vector
            for text, vector in zip(chunk, _normalize(np.asarray(vectors, dtype=np.float32)))
        }
        try:
            store.clear()
            store.update(_save_store(_store_path(model), additions))
        except (OSError, TimeoutError):
            # La risposta corrente resta utilizzabile anche se la cache su disco non è scrivibile.
            store.update(additions)
    return np.vstack([store[_key(text)] for text in texts])


@dataclass
class HybridIndex:
    texts: pd.Series
    lexical: TextIndex
    vectors: np.ndarray | None

    @property
    def semantic(self) -> bool:
        return self.vectors is not None


def build_hybrid(texts: pd.Series) -> HybridIndex:
    clean = texts.fillna("").astype(str)
    return HybridIndex(clean, build_index(clean), embed_cached(clean.tolist()))


def hybrid_search(index: HybridIndex, query: str, top_n: int = 10) -> pd.Series:
    """Punteggio RRF: somma di 1/(k + posizione) nelle due classifiche; premia chi è in alto in entrambe."""
    lexical = search(index.lexical, query, 200)
    scores = pd.Series(0.0, index=index.texts.index)
    scores.loc[lexical.index] += 1 / (RRF_K + np.arange(1, len(lexical) + 1))
    if index.vectors is not None:
        query_vector = embed_cached([query])
        if query_vector is not None:
            similarity = index.vectors @ query_vector[0]
            order = np.argsort(similarity)[::-1][:200]
            scores.iloc[order] += 1 / (RRF_K + np.arange(1, len(order) + 1))
    ranked = scores[scores > 0].sort_values(ascending=False)
    return ranked.head(top_n)


def split_passages(text: str, size: int = 700) -> list[str]:
    """Divide un documento lungo in passaggi di circa `size` caratteri, senza spezzare le frasi."""
    sentences = [s.strip() for s in re.split(r"(?<=[.;:!?])\s+|\n+", str(text)) if len(s.strip()) > 20]
    passages, current = [], ""
    for sentence in sentences:
        if current and len(current) + len(sentence) > size:
            passages.append(current)
            current = ""
        current = f"{current} {sentence}".strip()
    if current:
        passages.append(current)
    return passages
