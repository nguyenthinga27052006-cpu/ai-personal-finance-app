$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
docker compose --env-file .env -f infra/docker/docker-compose.dev.yml down
