$ErrorActionPreference = "Stop"

$projectRoot = $PSScriptRoot
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$appPath = Join-Path $projectRoot "app.py"

if (-not (Test-Path -LiteralPath $venvPython)) {
    throw "Ambiente virtuale assente. Esegui prima .\setup.ps1"
}

# L'avvio tramite percorso assoluto rende il comando indipendente dalla cartella
# corrente e impedisce di usare per errore uno Streamlit installato globalmente.
& $venvPython -m streamlit run $appPath
