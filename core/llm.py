"""Estensione opzionale con un LLM remoto (Claude). Spenta di default.

L'app funziona interamente in locale. Questo modulo si attiva solo se il pacchetto `anthropic`
è installato (`pip install -r requirements-llm.txt`) e la variabile ANTHROPIC_API_KEY è impostata.
Al modello arrivano solo la domanda e il riassunto aggregato calcolato in locale: mai righe del dataset.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

MODEL = os.environ.get("WATERMARK_LLM_MODEL", "claude-opus-5")
SYSTEM_PROMPT = (
    "Sei l'assistente di Watermark, uno strumento di audit privacy per il DPO di un Comune. "
    "Riscrivi i risultati che ricevi in italiano semplice per un dirigente non tecnico, in al massimo 120 parole. "
    "Usa solo i fatti e i numeri forniti: non aggiungere dati, norme o stime che non compaiono nei risultati. "
    "Se i risultati non rispondono alla domanda, dillo."
)


def available() -> bool:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    return True


def rewrite(question: str, local_summary: str) -> str | None:
    """Riformula il riassunto locale; restituisce None se la chiamata non va a buon fine."""
    if not available():
        return None
    import anthropic

    client = anthropic.Anthropic()
    try:
        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            # Se il modello principale rifiuta, la richiesta viene ripetuta sul modello di riserva.
            betas=["server-side-fallback-2026-06-01"],
            fallbacks=[{"model": "claude-opus-4-8"}],
            messages=[{
                "role": "user",
                "content": f"Domanda del DPO: {question}\n\nRisultati calcolati in locale:\n{local_summary}",
            }],
        )
    except anthropic.APIConnectionError:
        logger.warning("LLM non raggiungibile: resta la risposta locale")
        return None
    except anthropic.APIStatusError as exc:
        logger.warning("LLM ha risposto con errore %s: resta la risposta locale", exc.status_code)
        return None
    if response.stop_reason == "refusal":
        return None
    text = "".join(block.text for block in response.content if block.type == "text").strip()
    return text or None
