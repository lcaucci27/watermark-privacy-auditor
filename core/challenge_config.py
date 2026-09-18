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
    product_name="Segnale",
    page_title="Segnale · Auditor privacy e sicurezza",
    event_line="CAMPIONATO UNIVERSITARIO AI 2026  /  NAPOLI  /  18 SETTEMBRE  /  PRIVACY",
    subtitle="Auditor di privacy e sicurezza per l’infrastruttura urbana",
    description=(
        "Collega bollettini CSIRT, provvedimenti del Garante e telemetria dei servizi: "
        "individua asset esposti, dati personali nei flussi e rischio di re-identificazione."
    ),
    status_badges=":green-badge[Dati locali] :blue-badge[Seed 42] :orange-badge[Nessuna API] :red-badge[GDPR art. 5, 9, 25, 32]",
    sidebar_label="SEGNALE / AUDITOR",
    upload_prompt="Trascina qui un estratto di telemetria o un registro del servizio.",
    privacy_note="Elaborazione sul dispositivo. Nessun dato viene inviato fuori.",
)
