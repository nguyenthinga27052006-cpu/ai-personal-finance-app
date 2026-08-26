$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..\apps\api")
if (-not $env:DATABASE_URL) {
	$env:DATABASE_URL = "postgresql://finance_dev:finance_dev_local_only@localhost:5433/finance"
}
Write-Host "Running database migrations..." -ForegroundColor Green
& ..\..\\.venv\Scripts\python.exe -m alembic upgrade head
if ($LASTEXITCODE -ne 0) {
	throw "Database migration failed with exit code $LASTEXITCODE"
}
Write-Host "Migrations completed successfully!" -ForegroundColor Green
