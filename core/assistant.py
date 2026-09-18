"""Comprensione delle richieste dell'assistente: classifica una frase in italiano in un'intenzione
con TF-IDF a n-grammi di caratteri e ricerca del vicino più simile, interamente in locale."""

from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

INTENT_EXAMPLES: dict[str, tuple[str, ...]] = {
    "verifica": (
        "questo dataset è pubblicabile?", "è davvero anonimo?", "posso pubblicare questi dati",
        "ci sono dati personali", "le persone sono riconoscibili?", "verifica il dataset",
        "c'è un rischio privacy", "analizza il file", "si può risalire alle persone?",
    ),
    "correggi": (
        "correggilo", "correggi il dataset", "rendilo pubblicabile", "anonimizza i dati",
        "trova la correzione migliore", "come lo sistemo", "abbassa il rischio sotto il 10%",
        "sistemalo senza perdere informazioni", "genera la versione da pubblicare",
    ),
    "minacce": (
        "quali sistemi sono a rischio", "ci sono vulnerabilità sui sistemi wifi", "minacce informatiche",
        "bollettini csirt collegati", "i nostri hotspot sono esposti?", "attacchi agli access point",
        "sicurezza dell'infrastruttura", "cve sfruttate",
    ),
    "norme": (
        "cosa dice il garante", "quali norme si applicano", "è conforme al gdpr?", "riferimenti normativi",
        "cosa prevede la legge", "provvedimenti sul wifi pubblico", "regole sull'anonimizzazione",
    ),
    "spiega": (
        "perché logincount è un problema", "spiegami la colonna", "come fai a saperlo",
        "come funziona il test", "cosa significa pseudonimo", "spiega in parole semplici", "perché?",
    ),
    "rapporto": (
        "fammi il rapporto", "report per il dpo", "riassunto completo", "esegui l'audit completo",
        "scarica il documento", "prepara la relazione",
    ),
    "statistica": (
        "mostrami l'analisi statistica", "è statisticamente significativo?", "qual è il p-value",
        "intervallo di confidenza", "anova", "quale fattore conta di più", "dimostralo con i test",
    ),
    "aiuto": ("cosa sai fare", "aiuto", "come ti uso", "quali domande posso fare", "ciao"),
}
ALERT_HINT = re.compile(r"CVE-\d{4}-\d+|vulnerabilit|sfruttament|exploit|patch|aggiornamento di sicurezza", re.IGNORECASE)
THRESHOLD = re.compile(r"(\d{1,2})\s*%")
SEMANTIC_MIN = 0.55
LEXICAL_STRONG = 0.50


@dataclass(frozen=True)
class Intent:
    name: str
    confidence: float
    threshold: float | None
    method: str = "parole"


class IntentRouter:
    def __init__(self) -> None:
        self.labels = [name for name, examples in INTENT_EXAMPLES.items() for _ in examples]
        phrases = [phrase for examples in INTENT_EXAMPLES.values() for phrase in examples]
        self.phrases = phrases
        self.example_vectors = None
        # N-grammi di caratteri: tollerano refusi e flessioni ("correggi", "correggilo", "correzione").
        self.vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), strip_accents="unicode", lowercase=True)
        self.matrix = self.vectorizer.fit_transform(phrases)

    def route(self, text: str) -> Intent:
        match = THRESHOLD.search(text)
        threshold = int(match.group(1)) / 100 if match else None
        # Un allarme incollato è lungo e tecnico: va al modello di impatto, non al classificatore di intenzioni.
        if len(text) > 160 and ALERT_HINT.search(text):
            return Intent("allarme", 1.0, threshold)
        scores = (self.matrix @ self.vectorizer.transform([text]).T).toarray().ravel()
        best = int(np.argmax(scores))
        # Parole inequivocabili come "Garante" o "correggilo" non vanno scavalcate da una vicinanza semantica.
        if scores[best] >= LEXICAL_STRONG:
            return Intent(self.labels[best], float(scores[best]), threshold, "parole")
        semantic = self._semantic(text)
        if semantic is not None:
            return Intent(semantic[0], semantic[1], threshold, "significato")
        if scores[best] < 0.18:
            return Intent("cerca", float(scores[best]), threshold, "parole")
        return Intent(self.labels[best], float(scores[best]), threshold, "parole")

    def _semantic(self, text: str) -> tuple[str, float] | None:
        """Vicino più simile per significato (embedding locali); None se Ollama non è disponibile."""
        from core.semantic import embed_cached

        if self.example_vectors is None:
            self.example_vectors = embed_cached(self.phrases)
        query = embed_cached([text]) if self.example_vectors is not None else None
        if query is None:
            return None
        similarity = self.example_vectors @ query[0]
        best = int(np.argmax(similarity))
        if similarity[best] < SEMANTIC_MIN:
            return "cerca", float(similarity[best])
        return self.labels[best], float(similarity[best])
