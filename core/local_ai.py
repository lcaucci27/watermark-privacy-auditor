"""Modelli di IA eseguiti in locale tramite Ollama (http://localhost:11434).

Nessuna chiamata esce dal computer: Ollama gira sulla stessa macchina. Se il server o il modello
non sono disponibili, le funzioni restituiscono None e l'app usa i metodi classici.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from collections.abc import Iterator

logger = logging.getLogger(__name__)

HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
EMBED_MODEL = os.environ.get("WATERMARK_EMBED_MODEL", "bge-m3")
CHAT_MODELS = ("qwen2.5:3b", "qwen2.5:7b")
SYSTEM_PROMPT = (
    "Sei Watermark, assistente del DPO di un Comune. Scrivi in italiano semplice per un dirigente non tecnico.\n"
    "Regole:\n"
    "- Usa solo i fatti e i numeri presenti nei RISULTATI; non aggiungere dati, norme, date o nomi.\n"
    "- Riporta i numeri esattamente come scritti. Non dedurre conseguenze che i RISULTATI non dicono.\n"
    "- Se i RISULTATI contengono fonti numerate [1], [2], citale con lo stesso numero.\n"
    "- Massimo 90 parole, in tre parti: esito in una frase; motivo con i numeri; prossimo passo consigliato.\n"
    "- Se i RISULTATI non bastano a rispondere, dillo."
)


def _post(path: str, payload: dict, timeout: float) -> urllib.request.addinfourl:
    request = urllib.request.Request(
        f"{HOST}{path}", data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}
    )
    return urllib.request.urlopen(request, timeout=timeout)


def installed_models() -> set[str]:
    try:
        with urllib.request.urlopen(f"{HOST}/api/tags", timeout=1.5) as response:
            return {model["name"] for model in json.load(response).get("models", [])}
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        return set()


def has_model(name: str) -> bool:
    models = installed_models()
    return name in models or f"{name}:latest" in models


def embed(texts: list[str], model: str = EMBED_MODEL, batch: int = 32) -> list[list[float]] | None:
    """Vettori semantici per una lista di testi; None se Ollama o il modello non rispondono."""
    vectors: list[list[float]] = []
    try:
        for start in range(0, len(texts), batch):
            chunk = [text[:2000] or " " for text in texts[start:start + batch]]
            with _post("/api/embed", {"model": model, "input": chunk}, timeout=300) as response:
                vectors.extend(json.load(response)["embeddings"])
    except (urllib.error.URLError, TimeoutError, KeyError, ValueError, OSError) as exc:
        logger.warning("Embedding locale non disponibile: %s", exc)
        return None
    return vectors


def chat_stream(question: str, facts: str, model: str) -> Iterator[str]:
    """Risposta in streaming del modello locale, vincolata ai risultati calcolati dall'app."""
    payload = {
        "model": model,
        "stream": True,
        "options": {"temperature": 0, "num_ctx": 4096, "num_predict": 180},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"DOMANDA: {question}\n\nRISULTATI:\n{facts}"},
        ],
    }
    try:
        with _post("/api/chat", payload, timeout=180) as response:
            for line in response:
                if not line.strip():
                    continue
                part = json.loads(line)
                if part.get("message", {}).get("content"):
                    yield part["message"]["content"]
                if part.get("done"):
                    break
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
        logger.warning("LLM locale non disponibile: %s", exc)
        yield "\n\n_(Il modello locale non ha risposto: resta valida la risposta calcolata sopra.)_"
