$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
$python = Join-Path $PWD ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Project virtual environment not found at $python"
}
Push-Location "apps/api"
try {
    & $python -m pytest
} finally {
    Pop-Location
}
