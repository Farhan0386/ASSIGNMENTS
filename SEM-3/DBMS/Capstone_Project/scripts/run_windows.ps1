# Run from the project root in PowerShell after database setup.
$ErrorActionPreference = "Stop"

$venvPython = Join-Path $PWD ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    throw "Virtual environment not found. Run: py -m venv .venv, then .\.venv\Scripts\python.exe -m pip install -r requirements.txt"
}
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Warning "Created .env. Edit FLASK_SECRET_KEY and DATABASE_URL before running the app."
    notepad .env
    exit 1
}

& $venvPython run.py
