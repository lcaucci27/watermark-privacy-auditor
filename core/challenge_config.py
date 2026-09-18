"""Testi da adattare appena viene comunicata la traccia.

Modificare questo file prima di toccare layout o pipeline. Le etichette devono
descrivere l'utente, la decisione e il risultato misurato nel dominio scelto.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ChallengeConfig:
    product_name: str
    page_title: str
    event_line: str
    subtitle: str
    description: str
    status_badges: str
    sidebar_label: str
    upload_prompt: str
    privacy_note: str


CHALLENGE = ChallengeConfig(
    product_name="Watermark",
    page_title="Watermark · Auditor privacy e sicurezza",
    event_line="CAMPIONATO UNIVERSITARIO AI 2026  /  NAPOLI  /  18 SETTEMBRE  /  PRIVACY",
    subtitle="Quello che i dati anonimi lasciano vedere in controluce",
    description=(
        "Per il DPO di un Comune, prima di pubblicare open data: verifica se il dataset è davvero anonimo, "
        "collega i bollettini CSIRT sui sistemi che lo producono e i provvedimenti del Garante, "
        "sceglie la correzione che toglie il rischio conservando l’informazione utile."
    ),
    status_badges=":green-badge[Dati locali] :blue-badge[Seed 42] :orange-badge[Nessuna API] :red-badge[GDPR art. 5, 9, 25, 32]",
    sidebar_label="WATERMARK / AUDITOR",
    upload_prompt="Trascina qui un estratto di telemetria o un registro del servizio.",
    privacy_note="Elaborazione sul dispositivo. Nessun dato viene inviato fuori.",
)
