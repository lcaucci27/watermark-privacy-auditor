$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$appPath = Join-Path $projectRoot "streamlit_app.py"

if (-not (Test-Path -LiteralPath $venvPython)) {
    throw "Ambiente virtuale assente. Esegui prima .\scripts\setup.ps1"
}

# Streamlit cerca tema e configurazione dalla cartella corrente; entriamo nella
# root anche quando lo script viene richiamato da un'altra posizione.
Push-Location $projectRoot
try {
    & $venvPython -m streamlit run $appPath
}
finally {
    Pop-Location
}
