#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
venv_path="$project_root/.venv"
venv_python="$venv_path/bin/python"
requirements_path="$project_root/requirements.txt"

if ! command -v python3.12 >/dev/null 2>&1; then
    printf '%s\n' \
        "Python 3.12 non è disponibile." \
        "Su macOS con Homebrew esegui: brew install python@3.12"
    exit 1
fi

if [[ ! -x "$venv_python" ]]; then
    printf '%s\n' "Creo l'ambiente Python 3.12 in .venv..."
    python3.12 -m venv "$venv_path"
fi

# Usiamo sempre l'interprete della repo: un Python globale configurato diversamente
# potrebbe nascondere dipendenze mancanti fino al momento della demo.
"$venv_python" -m pip install --upgrade pip
"$venv_python" -m pip install -r "$requirements_path"
"$venv_python" -m pip check

printf '%s\n' "Ambiente pronto. Avvia l'app con: ./scripts/run.sh"
