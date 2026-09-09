$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
$python = Join-Path $PWD ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $python = (Get-Command python -ErrorAction Stop).Source
}

Push-Location "apps/api"
try {
    & $python -m pytest
    & $python -m ruff check app tests
    & $python -m compileall -q app ..\worker\app
} finally {
    Pop-Location
}

Push-Location "apps/mobile"
try {
    flutter analyze
    flutter test
    flutter build apk --debug
    flutter build web
} finally {
    Pop-Location
}
