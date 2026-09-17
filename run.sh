#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
venv_python="$project_root/.venv/bin/python"
app_path="$project_root/app.py"

if [[ ! -x "$venv_python" ]]; then
    printf '%s\n' "Ambiente virtuale assente. Esegui prima ./setup.sh" >&2
    exit 1
fi

# Il percorso assoluto rende l'avvio indipendente dalla cartella corrente e
# impedisce di usare per errore uno Streamlit installato globalmente.
exec "$venv_python" -m streamlit run "$app_path"
