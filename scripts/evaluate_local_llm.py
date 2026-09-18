"""Valuta fedeltà e formato dei modelli locali su casi DPO rappresentativi."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.local_ai import SPECIALIZED_MODEL, chat_answer

CASES = (
    (
        "Posso pubblicare questo dataset?",
        "Esito: non pubblicare nella forma attuale. Il 99,5% delle sessioni è individuabile. "
        "Azione: aggregare in gruppi di almeno 5 sessioni. Limite: nessuna persona è stata identificata.",
        ("non pubblicare", "99,5", "almeno 5", "nessuna persona"),
        ("persona identificata con certezza",),
    ),
    (
        "Il sistema interno deve riconoscere gli utenti: è un errore?",
        "Esito: l'identificazione interna non è automaticamente un errore. È necessaria per assistenza e sicurezza. "
        "Azione: documentare base giuridica, accessi per ruolo e cancellazione. Limite: non è autorizzata la pubblicazione open data.",
        ("non è automaticamente", "base giuridica", "accessi", "cancellazione"),
        ("pubblicabile senza condizioni",),
    ),
    (
        "Cosa dice la fonte?",
        "[1] Il Garante richiede dati necessari e proporzionati. Azione: rimuovere i dettagli non necessari. "
        "Limite: il passaggio non valuta questo specifico dataset.",
        ("[1]", "necessari e proporzionati", "rimuovere"),
        ("conforme per legge",),
    ),
    (
        "Il file aggregato di Bologna è pubblicabile?",
        "Esito: compatibile con pubblicazione. 2.000 righe aggregate; 0 celle positive sotto 5 unità. "
        "Azione: verificare attacchi per differenza tra release. Limite: il DPO deve confermare l'unità della riga.",
        ("compatibile", "2.000", "0 celle", "differenza"),
        ("anonimato garantito",),
    ),
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("models", nargs="*", default=[SPECIALIZED_MODEL])
    args = parser.parse_args()
    for model in args.models:
        passed = 0
        elapsed = 0.0
        print(f"\n{model}")
        for number, (question, facts, required, forbidden) in enumerate(CASES, 1):
            start = time.perf_counter()
            answer, issues = chat_answer(question, facts, model)
            duration = time.perf_counter() - start
            elapsed += duration
            rendered = answer.text().casefold() if answer else ""
            missing = [phrase for phrase in required if phrase.casefold() not in rendered]
            present_forbidden = [phrase for phrase in forbidden if phrase.casefold() in rendered]
            semantic_issues = (["manca: " + ", ".join(missing)] if missing else []) + (
                ["presente ma vietato: " + ", ".join(present_forbidden)] if present_forbidden else []
            )
            issues += semantic_issues
            ok = answer is not None and not issues
            passed += int(ok)
            print(f"  caso {number}: {'OK' if ok else 'ERRORE'} · {duration:.1f}s" + (f" · {issues}" if issues else ""))
            if answer:
                print("   ", answer.markdown().replace("\n", " "))
        print(f"  risultato: {passed}/{len(CASES)} · {elapsed:.1f}s totali")


if __name__ == "__main__":
    main()
