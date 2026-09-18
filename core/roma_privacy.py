"""Prove leggibili e pubblicazione prudente per il caso WiFi di Roma Capitale."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Finding:
    title: str
    severity: str
    evidence: str
    consequence: str
    remedy: str


def unique_share(frame: pd.DataFrame, keys: list[str]) -> float:
    """Quota di righe isolate dalla combinazione di chiavi indicata."""
    sizes = frame.groupby(keys, dropna=False)[keys[0]].transform("size")
    return float((sizes == 1).mean())


def knowledge_ladder(frame: pd.DataFrame) -> pd.DataFrame:
    """Quanto cresce l'individuabilità aggiungendo informazioni realistiche."""
    work = frame.copy()
    work["ora"] = work["inizio"].dt.floor("h")
    levels = (
        ("Solo giorno", ["giorno"]),
        ("Giorno e ora", ["giorno", "ora"]),
        ("Orario al secondo", ["giorno", "STARTTIME"]),
        ("Più sede al civico", ["giorno", "STARTTIME", "sede"]),
        ("Più lingua", ["giorno", "STARTTIME", "sede", "DTLN"]),
        ("Più durata", ["giorno", "STARTTIME", "sede", "DTLN", "DURATION"]),
    )
    return pd.DataFrame(
        {
            "informazioni conosciute": [label for label, _ in levels],
            "sessioni individuabili": [unique_share(work, keys) for _, keys in levels],
        }
    )


def findings(frame: pd.DataFrame) -> list[Finding]:
    exact = unique_share(frame, ["giorno", "STARTTIME", "sede", "DTLN"])
    with_duration = unique_share(frame, ["giorno", "STARTTIME", "sede", "DTLN", "DURATION"])
    return [
        Finding(
            "Orari al secondo",
            "Critica",
            f"Giorno e STARTTIME isolano già il {unique_share(frame, ['giorno', 'STARTTIME']):.1%} delle sessioni.",
            "Chi conosce l'orario di una connessione può trovare una singola riga.",
            "Pubblicare fasce orarie, non secondi esatti.",
        ),
        Finding(
            "Sede fino al numero civico",
            "Critica",
            f"Aggiungendo la sede, la quota individuabile sale al {unique_share(frame, ['giorno', 'STARTTIME', 'sede']):.1%}.",
            "Il luogo preciso rende più facile collegare conoscenza esterna e sessione.",
            "Usare il municipio o una zona sufficientemente ampia.",
        ),
        Finding(
            "Combinazione di quasi-identificativi",
            "Critica",
            f"Giorno, ora, sede e lingua rendono unica una sessione nel {exact:.1%} dei casi.",
            "La rimozione di nome ed e-mail non produce anonimato se la combinazione resta unica.",
            "Applicare una soglia k minima prima della pubblicazione.",
        ),
        Finding(
            "Misure comportamentali esatte",
            "Alta",
            f"Con la durata esatta, le sessioni individuabili raggiungono il {with_duration:.1%}; download e upload sono anch'essi molto granulari.",
            "Durata e volumi possono diventare un'impronta aggiuntiva della sessione.",
            "Pubblicare somme o mediane solo su gruppi sufficientemente numerosi.",
        ),
        Finding(
            "LOGINCOUNT non documentato",
            "Alta",
            f"La colonna ha {frame['LOGINCOUNT'].nunique():,} valori distinti, ma non è spiegata nella scheda ufficiale.",
            "Un contatore persistente potrebbe rendere collegabili sessioni diverse; la semantica va confermata dall'ente.",
            "Sospendere la colonna dalla pubblicazione finché significato e rischio non sono chiariti.",
        ),
        Finding(
            "Accumulo di file giornalieri",
            "Alta",
            f"Il campione unisce {frame['giorno'].nunique()} giornate scaricabili separatamente.",
            "Ogni nuova pubblicazione amplia la finestra osservabile e facilita attacchi di composizione nel tempo.",
            "Valutare il rischio sull'intera serie storica, non su un solo file giornaliero.",
        ),
        Finding(
            "Assenza di una soglia minima pubblicata",
            "Alta",
            "Il file contiene una riga per singola sessione, anche quando la combinazione descrive un solo evento.",
            "Non c'è protezione esplicita contro classi di equivalenza con una sola riga.",
            "Sopprimere o accorpare ogni gruppo con meno di cinque sessioni.",
        ),
        Finding(
            "Etichetta di anonimizzazione troppo forte",
            "Media",
            "Il catalogo definisce le sessioni “anonimizzate”, ma pubblica quasi-identificativi ad alta precisione.",
            "L'etichetta può far sottovalutare il rischio residuo e favorire riusi incompatibili.",
            "Descrivere tecnica applicata, rischio residuo, campi rimossi e limiti di riutilizzo.",
        ),
    ]


def aggregate_for_publication(frame: pd.DataFrame, k: int = 5) -> tuple[pd.DataFrame, int]:
    """Crea aggregati a tre ore e municipio; elimina i gruppi con meno di k sessioni."""
    work = frame.copy()
    work["fascia_3_ore"] = work["inizio"].dt.floor("3h").dt.strftime("%H:00")
    language = work["DTLN"].fillna("non indicata").astype(str)
    common = set(language.value_counts().head(4).index)
    work["lingua"] = language.where(language.isin(common), "altre")
    work["download_MB"] = work["DOWNLOAD"].clip(lower=0) / 1_000_000
    work["upload_MB"] = work["UPLOAD"].clip(lower=0) / 1_000_000
    work["durata_min"] = work["DURATION"].clip(lower=0) / 60
    keys = ["giorno", "fascia_3_ore", "MUNICIPIO", "lingua"]
    grouped = work.groupby(keys, dropna=False).agg(
        numero_sessioni=("giorno", "size"),
        durata_totale_min=("durata_min", "sum"),
        download_totale_MB=("download_MB", "sum"),
        upload_totale_MB=("upload_MB", "sum"),
    ).reset_index()
    suppressed = int(grouped.loc[grouped["numero_sessioni"] < k, "numero_sessioni"].sum())
    safe = grouped[grouped["numero_sessioni"] >= k].copy()
    for column in ("durata_totale_min", "download_totale_MB", "upload_totale_MB"):
        safe[column] = safe[column].round(1)
    return safe.reset_index(drop=True), suppressed


def report_markdown(frame: pd.DataFrame) -> str:
    lines = [
        "# Valutazione dell'anonimizzazione · WiFi Roma Capitale",
        "",
        f"Campione analizzato: {len(frame):,} sessioni, {frame['giorno'].nunique()} giornate, {frame['sede'].nunique()} sedi.",
        "",
        "## Esito",
        "",
        "Il dataset non dovrebbe essere pubblicato nella forma corrente senza una nuova valutazione del rischio.",
        "Nessuna persona è stata identificata: le prove misurano solo individuabilità, correlabilità potenziale e granularità.",
        "",
        "## Criticità",
    ]
    for item in findings(frame):
        lines += [
            "",
            f"### {item.title} · {item.severity}",
            f"- Evidenza: {item.evidence}",
            f"- Conseguenza: {item.consequence}",
            f"- Intervento: {item.remedy}",
        ]
    lines += [
        "",
        "## Limite su LOGINCOUNT",
        "",
        "LOGINCOUNT è presente nei CSV ufficiali ma non è definito nei metadati. Il suo comportamento può essere compatibile con un contatore persistente, ma non prova da solo che due righe appartengano alla stessa persona.",
        "",
        "## Pubblicazione raccomandata",
        "",
        "Aggregare per giorno, fascia di tre ore, municipio e lingua raggruppata; pubblicare solo gruppi con almeno cinque sessioni; rimuovere LOGINCOUNT e ogni orario, civico, durata o volume riferito alla singola sessione.",
    ]
    return "\n".join(lines)
