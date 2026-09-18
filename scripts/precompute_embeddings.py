"""Pre-calcola gli embedding locali usati nella demo e verifica la cache risultante."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.assistant import INTENT_EXAMPLES
from core.semantic import embed_cached, split_passages
from core.threat_model import bulletin_text

DATA_DIR = ROOT / "data"


def _embed(label: str, texts: list[str]) -> None:
    unique = list(dict.fromkeys(texts))
    print(f"{label}: {len(unique)} testi", flush=True)
    vectors = embed_cached(unique)
    if vectors is None or len(vectors) != len(unique):
        raise RuntimeError(f"Embedding non disponibili per {label}")
    print(f"{label}: completato", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--only",
        choices=("all", "csirt", "garante", "intents"),
        default="all",
        help="Gruppo da pre-calcolare (predefinito: tutti)",
    )
    args = parser.parse_args()

    if args.only in {"all", "csirt"}:
        csirt = pd.read_csv(DATA_DIR / "csirt_bollettini.csv")
        _embed("Bollettini CSIRT", bulletin_text(csirt).tolist())

    if args.only in {"all", "garante"}:
        garante = pd.read_csv(DATA_DIR / "garante_provvedimenti.csv")
        passages = [
            passage
            for text in garante["testo"].fillna("").astype(str)
            for passage in split_passages(text)
        ]
        _embed("Passaggi del Garante", passages)

    if args.only in {"all", "intents"}:
        examples = [example for group in INTENT_EXAMPLES.values() for example in group]
        _embed("Frasi di intenzione", examples)


if __name__ == "__main__":
    main()
