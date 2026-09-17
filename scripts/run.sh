#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
venv_python="$project_root/.venv/bin/python"
app_path="$project_root/streamlit_app.py"

if [[ ! -x "$venv_python" ]]; then
    printf '%s\n' "Ambiente virtuale assente. Esegui prima ./scripts/setup.sh" >&2
    exit 1
fi

# Streamlit cerca tema e configurazione dalla cartella corrente; entriamo nella
# root anche quando lo script viene richiamato da un'altra posizione.
cd "$project_root"
exec "$venv_python" -m streamlit run "$app_path"
