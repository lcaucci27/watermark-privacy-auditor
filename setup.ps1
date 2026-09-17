$ErrorActionPreference = "Stop"

$projectRoot = $PSScriptRoot
$venvPath = Join-Path $projectRoot ".venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"
$requirementsPath = Join-Path $projectRoot "requirements.txt"

if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Host "Creo l'ambiente Python 3.12 in .venv..."
    py -3.12 -m venv $venvPath
}

# Usiamo sempre l'interprete della repo: un Python globale configurato diversamente
# potrebbe nascondere dipendenze mancanti fino al momento della demo.
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r $requirementsPath
& $venvPython -m pip check

Write-Host "Ambiente pronto. Avvia l'app con: .\run.ps1"
