$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
Push-Location "apps/api"
try {
    py -3.13 -m ruff check app tests
} finally {
    Pop-Location
}
