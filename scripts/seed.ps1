$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..\apps\api")
if (-not $env:DATABASE_URL) {
    $env:DATABASE_URL = "postgresql://finance_dev:finance_dev_local_only@localhost:5433/finance"
}
Write-Host "Seeding system categories..." -ForegroundColor Green
& ..\..\\.venv\Scripts\python.exe -c "
from app.db.session import SessionLocal
from app.db.seed import seed_system_categories

session = SessionLocal()
try:
    seed_system_categories(session)
    print('Seed completed successfully!')
finally:
    session.close()
"
if ($LASTEXITCODE -ne 0) {
    throw "Database seed failed with exit code $LASTEXITCODE"
}
Write-Host "Seed completed!" -ForegroundColor Green
