$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker CLI is required for the development database reset."
}

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example"
}

$composeFile = "infra/docker/docker-compose.dev.yml"
$envFile = ".env"
$projectName = (Get-Content $envFile | Where-Object { $_ -match '^COMPOSE_PROJECT_NAME=' } | Select-Object -First 1) -replace '^COMPOSE_PROJECT_NAME=', ''
if ([string]::IsNullOrWhiteSpace($projectName)) {
    $projectName = "finance-assistant"
}

$postgresVolume = "${projectName}_postgres_data"
Write-Host "This will permanently delete local development volume: $postgresVolume"
Write-Host "Only the PostgreSQL volume declared by this Compose project is targeted. Production and staging are not referenced."
$confirmation = Read-Host "Type RESET-LOCAL-POSTGRES to continue"
if ($confirmation -cne "RESET-LOCAL-POSTGRES") {
    Write-Host "Reset cancelled."
    exit 0
}

docker compose --env-file $envFile -f $composeFile down
docker volume rm $postgresVolume
docker compose --env-file $envFile -f $composeFile up --build -d
Write-Host "Local PostgreSQL volume reset and development stack started."