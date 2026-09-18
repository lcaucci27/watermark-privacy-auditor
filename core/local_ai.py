"""Modelli di IA eseguiti in locale tramite Ollama (http://localhost:11434).

Nessuna chiamata esce dal computer: Ollama gira sulla stessa macchina. Se il server o il modello
non sono disponibili, le funzioni restituiscono None e l'app usa i metodi classici.
"""

from __future__ import annotations

import json
import logging
import os
import re
import urllib.error
import urllib.request
from collections.abc import Iterator
from dataclasses import dataclass

logger = logging.getLogger(__name__)

HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
EMBED_MODEL = os.environ.get("WATERMARK_EMBED_MODEL", "bge-m3")
SPECIALIZED_MODEL = "watermark-dpo:latest"
CHAT_MODELS = (SPECIALIZED_MODEL, "qwen2.5:3b", "qwen2.5:7b")
SYSTEM_PROMPT = (
    "Sei Watermark, assistente del DPO di un Comune. Trasformi risultati già calcolati in una risposta fedele e semplice.\n"
    "Regole:\n"
    "- Usa solo i fatti e i numeri presenti nei RISULTATI; non aggiungere dati, norme, date o nomi.\n"
    "- Riporta i numeri esattamente come scritti. Non dedurre conseguenze che i RISULTATI non dicono.\n"
    "- Se i RISULTATI contengono fonti numerate [1], [2], inserisci lo stesso riferimento nel campo motivo.\n"
    "- Distingui uso operativo interno da pubblicazione open data: l'identificazione interna non è automaticamente un errore.\n"
    "- Estrai senza perdere contenuto: esito copia l'esito; motivo conserva tutte le spiegazioni e la fonte; azione copia l'azione; limite copia il limite.\n"
    "- Non numerare frasi o elenchi e non introdurre cifre che non compaiono nei RISULTATI.\n"
    "- Massimo 90 parole complessive. Se i RISULTATI non bastano, dichiaralo nel limite.\n"
    "- Compila soltanto i quattro campi richiesti dallo schema JSON."
)
ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "esito": {"type": "string", "description": "Copia l'esito indicato nei risultati."},
        "motivo": {"type": "string", "description": "Conserva tutte le spiegazioni fattuali e le fonti [n]."},
        "azione": {"type": "string", "description": "Copia soltanto l'azione indicata nei risultati."},
        "limite": {"type": "string", "description": "Copia il limite indicato nei risultati."},
    },
    "required": ["esito", "motivo", "azione", "limite"],
    "additionalProperties": False,
}
NUMBER = re.compile(r"(?<![\w-])\d+(?:[.,]\d+)?%?")
CITATION = re.compile(r"\[(\d+)\]")


@dataclass(frozen=True)
class LocalAnswer:
    outcome: str
    reason: str
    action: str
    limitation: str

    def markdown(self) -> str:
        return (
            f"**Esito:** {self.outcome}\n\n"
            f"**Perché:** {self.reason}\n\n"
            f"**Azione:** {self.action}\n\n"
            f"*Limite: {self.limitation}*"
        )

    def text(self) -> str:
        return " ".join((self.outcome, self.reason, self.action, self.limitation))


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


def _normalise_number(value: str) -> str:
    return value.replace(",", ".").rstrip("%")


def validate_answer(answer: LocalAnswer, facts: str, max_words: int = 90) -> list[str]:
    """Rifiuta risposte fuori formato o con numeri assenti dai risultati calcolati."""
    issues = []
    fields = (answer.outcome, answer.reason, answer.action, answer.limitation)
    if any(not field.strip() for field in fields):
        issues.append("campo vuoto")
    if len(answer.text().split()) > max_words:
        issues.append(f"oltre {max_words} parole")
    if len(re.findall(r"[A-Za-zÀ-ÿ]{3,}", answer.reason)) < 3:
        issues.append("motivo troppo breve: deve contenere l'affermazione, non soltanto la fonte")
    supported = {_normalise_number(value) for value in NUMBER.findall(facts)}
    invented = {
        value for value in NUMBER.findall(answer.text())
        if _normalise_number(value) not in supported
    }
    if invented:
        issues.append("numeri non presenti nei risultati: " + ", ".join(sorted(invented)))
    missing_citations = set(CITATION.findall(facts)) - set(CITATION.findall(answer.text()))
    if missing_citations:
        issues.append("fonti mancanti: " + ", ".join(f"[{value}]" for value in sorted(missing_citations)))
    return issues


def _remove_unsupported_citations(answer: LocalAnswer, facts: str) -> LocalAnswer:
    supported = set(CITATION.findall(facts))

    def clean(value: str) -> str:
        cleaned = CITATION.sub(lambda match: match.group(0) if match.group(1) in supported else "", value)
        cleaned = re.sub(r"\b[Ff]onte\s*:\s*(?=$|[.;])", "", cleaned)
        return re.sub(r"\s+", " ", cleaned).strip(" .;")

    return LocalAnswer(*(clean(value) for value in (
        answer.outcome, answer.reason, answer.action, answer.limitation
    )))


def _restore_supported_citations(answer: LocalAnswer, facts: str) -> LocalAnswer:
    """Riporta nel motivo le fonti presenti nei fatti che il modello ha omesso."""
    missing = set(CITATION.findall(facts)) - set(CITATION.findall(answer.text()))
    if not missing:
        return answer
    references = " ".join(f"[{value}]" for value in sorted(missing))
    return LocalAnswer(answer.outcome, f"{references} {answer.reason}".strip(), answer.action, answer.limitation)


def chat_answer(question: str, facts: str, model: str) -> tuple[LocalAnswer | None, list[str]]:
    """Genera una risposta strutturata e la accetta solo se resta ancorata ai risultati."""
    payload = {
        "model": model,
        "stream": False,
        "format": ANSWER_SCHEMA,
        "options": {"temperature": 0, "num_ctx": 4096, "num_predict": 160},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"DOMANDA: {question}\n\nRISULTATI:\n{facts}\n\n"
                    f"SCHEMA OBBLIGATORIO:\n{json.dumps(ANSWER_SCHEMA, ensure_ascii=False)}"
                ),
            },
        ],
    }
    try:
        for attempt in range(2):
            with _post("/api/chat", payload, timeout=180) as response:
                content = json.load(response)["message"]["content"]
            parsed = json.loads(content)
            answer = _restore_supported_citations(
                _remove_unsupported_citations(
                    LocalAnswer(parsed["esito"], parsed["motivo"], parsed["azione"], parsed["limite"]), facts
                ),
                facts,
            )
            issues = validate_answer(answer, facts)
            if not issues:
                return answer, []
            if attempt == 0:
                payload["messages"].extend([
                    {"role": "assistant", "content": content},
                    {
                        "role": "user",
                        "content": (
                            "CORREGGI LA RISPOSTA. Problemi: " + "; ".join(issues) + ". "
                            "Il motivo deve contenere l'affermazione fattuale completa, mai soltanto [n]. "
                            "Non aggiungere numeri, fonti o contenuti assenti dai RISULTATI."
                        ),
                    },
                ])
        return None, issues
    except (urllib.error.URLError, TimeoutError, KeyError, TypeError, ValueError, OSError) as exc:
        logger.warning("LLM locale non disponibile: %s", exc)
        return None, ["modello non disponibile o JSON non valido"]


def chat_stream(question: str, facts: str, model: str) -> Iterator[str]:
    """Mantiene l'interfaccia streaming, ma mostra solo una risposta già validata."""
    answer, issues = chat_answer(question, facts, model)
    if answer is None:
        logger.warning("Risposta locale scartata: %s", "; ".join(issues))
        yield "_(Riscrittura locale scartata dai controlli: resta valida la risposta calcolata sopra.)_"
        return
    yield answer.markdown()
