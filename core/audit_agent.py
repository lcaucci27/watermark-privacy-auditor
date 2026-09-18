"""Agente di audit: esegue in sequenza i controlli di Watermark su un dataset da pubblicare
e produce un rapporto per il DPO con prove, minacce collegate, norme e correzione scelta."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from core.linkability import scan_counters
from core.privacy_optimizer import recommend
from core.text_corpus import TextIndex, best_passages, search
from core.threat_model import bulletin_text
from core.wifi_dataset import PUBLISHED_KEYS, unique_share

INFRASTRUCTURE_QUERY = (
    "rete WiFi pubblica access point controller wireless captive portal autenticazione web "
    "hotspot router gateway VPN accesso remoto portale web"
)
RULE_QUERY = "pubblicazione open data anonimizzazione dati personali identificabili Wi-Fi pubblico dati di navigazione"


@dataclass
class AuditStep:
    title: str
    outcome: str
    ok: bool


@dataclass
class AuditReport:
    steps: list[AuditStep] = field(default_factory=list)
    flagged: pd.DataFrame | None = None
    bulletins: pd.DataFrame | None = None
    passages: list[tuple[str, str]] = field(default_factory=list)
    recommendation: pd.Series | None = None
    published_risk: float = 0.0
    markdown: str = ""


def run_audit(
    wifi: pd.DataFrame,
    variants: pd.DataFrame,
    max_risk: float,
    csirt: pd.DataFrame | None,
    csirt_index: TextIndex | None,
    threat_model,
    garante: pd.DataFrame | None,
    garante_index: TextIndex | None,
) -> AuditReport:
    report = AuditReport()

    report.published_risk = unique_share(wifi, PUBLISHED_KEYS)
    report.steps.append(AuditStep(
        "Individuazione",
        f"{report.published_risk:.1%} delle sessioni è unica su giorno, orario al secondo, sede e lingua.",
        report.published_risk < 0.2,
    ))

    scan = scan_counters(wifi, wifi["inizio"], ["sede", "DTLN"], location="sede")
    report.flagged = scan[scan["esito"] == "Pseudonimo probabile"]
    if report.flagged.empty:
        report.steps.append(AuditStep("Pseudonimi nascosti", "Nessuna colonna si comporta come contatore personale.", True))
    else:
        row = report.flagged.iloc[0]
        report.steps.append(AuditStep(
            "Pseudonimi nascosti",
            f"{row['colonna']}: tra valori vicini il più alto arriva dopo nel {row['ordine nel tempo']:.1%} dei casi "
            f"(valori mescolati: {row['ipotesi nulla']:.1%}). Le sessioni della stessa persona sono collegabili.",
            False,
        ))

    if csirt is not None and csirt_index is not None:
        hits = search(csirt_index, INFRASTRUCTURE_QUERY, 10)
        table = csirt.loc[hits.index, ["codice", "titolo", "impatto_classe", "impatto_punteggio", "n_cve_sfruttate"]].copy()
        table["pertinenza"] = hits.round(3).to_numpy()
        if threat_model is not None:
            # Dove ACN non ha ancora assegnato l'impatto, lo stima il modello addestrato sugli altri bollettini.
            missing = table["impatto_classe"].isna() | (table["impatto_classe"].astype(str).str.strip() == "")
            if missing.any():
                texts = bulletin_text(csirt.loc[table.index[missing]])
                table.loc[missing, "impatto_classe"] = pd.Series(threat_model.predict(texts), index=texts.index) + " (stimato)"
        report.bulletins = table
        exploited = int((table["n_cve_sfruttate"].fillna(0) > 0).sum())
        critical = int(table["impatto_classe"].astype(str).str.startswith("Critico").sum())
        report.steps.append(AuditStep(
            "Minacce sui sistemi che producono i dati",
            f"{len(table)} bollettini CSIRT su WiFi, captive portal e accesso remoto; {critical} con impatto critico, "
            f"{exploited} con CVE già sfruttate in rete.",
            critical == 0 and exploited == 0,
        ))

    if garante is not None and garante_index is not None:
        for position in search(garante_index, RULE_QUERY, 2).index:
            title = str(garante.loc[position, "titolo"])
            for passage in best_passages(garante_index, str(garante.loc[position, "testo"]), RULE_QUERY, 1):
                report.passages.append((title, passage))
        report.steps.append(AuditStep("Norme applicabili", f"{len(report.passages)} passaggi del Garante pertinenti.", True))

    report.recommendation = recommend(variants, max_risk)
    if report.recommendation is None:
        report.steps.append(AuditStep("Correzione", f"Nessuna variante resta sotto il {max_risk:.0%} di rischio.", False))
    else:
        rec = report.recommendation
        report.steps.append(AuditStep(
            "Correzione scelta",
            f"{rec['variante']}: rischio {rec['rischio']:.1%}, utilità conservata {rec['utilità relativa']:.0%}.",
            True,
        ))
    report.markdown = _markdown(report, max_risk)
    return report


def _markdown(report: AuditReport, max_risk: float) -> str:
    lines = [
        "# Rapporto di audit Watermark",
        "",
        "Committente: Comune titolare del trattamento (caso: Roma Capitale, WiFi DigitRoma). Destinatario: DPO.",
        "Dataset: \"Sessioni anonimizzate di navigazione web riscontrate nel sistema WiFi di Roma Capitale\", CC-BY.",
        "",
        "## Esito dei controlli",
    ]
    lines += [f"- **{step.title}** ({'conforme' if step.ok else 'da correggere'}): {step.outcome}" for step in report.steps]
    if report.bulletins is not None and not report.bulletins.empty:
        lines += ["", "## Bollettini CSIRT collegati"]
        lines += [
            f"- {row.codice} · {row.titolo} · impatto {row.impatto_classe}"
            for row in report.bulletins.head(5).itertuples()
        ]
    if report.passages:
        lines += ["", "## Riferimenti del Garante (citazione testuale)"]
        lines += [f"- {title}: \"{passage}\"" for title, passage in report.passages]
    if report.recommendation is not None:
        rec = report.recommendation
        lines += [
            "", "## Correzione raccomandata",
            f"Variante: {rec['variante']}. Rischio di individuazione {rec['rischio']:.1%} "
            f"(soglia scelta {max_risk:.0%}); utilità analitica conservata {rec['utilità relativa']:.0%}.",
        ]
    lines += [
        "", "## Limiti",
        "- Il significato delle colonne segnalate è dedotto dai dati, non confermato dall'ente.",
        "- Nessuna persona è stata identificata: tutte le misure sono aggregate.",
        "- La pertinenza dei bollettini misura termini condivisi, non conferma che le versioni in uso siano vulnerabili.",
        "",
        "Strumento: Watermark, esecuzione locale (Python, scikit-learn), nessun dato inviato fuori dal dispositivo.",
    ]
    return "\n".join(lines)
