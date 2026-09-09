param(
    [Parameter(Mandatory = $true)]
    [string]$SourceDatabaseUrl,
    [Parameter(Mandatory = $true)]
    [string]$RestoreDatabaseUrl,
    [string]$BackupFile = (Join-Path $PWD "tmp\finance-backup.sql")
)

$ErrorActionPreference = "Stop"
$pgDump = Get-Command pg_dump -ErrorAction Stop
$psql = Get-Command psql -ErrorAction Stop
$backupDirectory = Split-Path -Parent $BackupFile
New-Item -ItemType Directory -Force -Path $backupDirectory | Out-Null

Write-Host "[$(Get-Date -Format o)] backup_started"
& $pgDump.Source --format=custom --file=$BackupFile $SourceDatabaseUrl
if ($LASTEXITCODE -ne 0) { throw "pg_dump failed with exit code $LASTEXITCODE" }

Write-Host "[$(Get-Date -Format o)] restore_started"
& $psql.Source $RestoreDatabaseUrl --command="DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
if ($LASTEXITCODE -ne 0) { throw "restore target reset failed with exit code $LASTEXITCODE" }
& pg_restore --exit-on-error --clean --if-exists --dbname=$RestoreDatabaseUrl $BackupFile
if ($LASTEXITCODE -ne 0) { throw "pg_restore failed with exit code $LASTEXITCODE" }

Write-Host "[$(Get-Date -Format o)] restore_completed"
Write-Host "Next: run migrations, health/readiness checks, and financial invariant tests against the isolated target."
