$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
Write-Host "No migrations exist yet; database schema is intentionally deferred to the next phase."
