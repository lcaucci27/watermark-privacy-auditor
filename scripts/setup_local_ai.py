"""Crea in Ollama il modello Watermark specializzato sul caso d'uso DPO."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODELFILE = ROOT / "ollama" / "Modelfile.watermark"


def main() -> None:
    executable = shutil.which("ollama")
    if not executable:
        raise SystemExit("Ollama non è installato o non è presente nel PATH.")
    subprocess.run([executable, "pull", "qwen2.5:3b"], check=True)
    subprocess.run([executable, "create", "watermark-dpo:latest", "-f", str(MODELFILE)], check=True)
    print("Modello creato: watermark-dpo:latest")


if __name__ == "__main__":
    main()
