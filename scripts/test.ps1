$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
Push-Location "apps/api"
try {
    py -3.13 -m pytest
} finally {
    Pop-Location
}
