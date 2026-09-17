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
    page_title="Segnale · Data lab",
    event_line="CAMPIONATO UNIVERSITARIO AI 2026  /  NAPOLI  /  18 SETTEMBRE",
    subtitle="Analisi locale di dati tabellari",
    description="Carica un file, seleziona il target, misura il modello su dati esclusi dall’addestramento.",
    status_badges=":green-badge[Dati locali] :blue-badge[Seed 42] :orange-badge[Nessuna API]",
    sidebar_label="SEGNALE / DATA LAB",
    upload_prompt="Trascina qui il file della traccia.",
    privacy_note="Elaborazione sul dispositivo. Nessun dato viene inviato fuori.",
)
