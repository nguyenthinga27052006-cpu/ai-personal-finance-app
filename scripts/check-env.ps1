$ErrorActionPreference = "Continue"

function Write-Check([string]$Name, [string]$Status, [string]$Detail) {
    Write-Output ("{0}: {1} - {2}" -f $Status, $Name, $Detail)
}

$git = Get-Command git -ErrorAction SilentlyContinue
if ($git) { Write-Check "Git" "PASS" $git.Source } else { Write-Check "Git" "FAIL" "git is not available on PATH" }

$python = Get-Command python -ErrorAction SilentlyContinue
if ($python) { Write-Check "Python" "PASS" (& python --version 2>&1) } else { Write-Check "Python" "FAIL" "python is not available on PATH" }

$docker = Get-Command docker -ErrorAction SilentlyContinue
if ($docker) {
    Write-Check "Docker" "PASS" (& docker --version 2>&1)
    Write-Check "Docker Compose" "PASS" (& docker compose version 2>&1)
    $composeFile = Join-Path $PSScriptRoot "..\infra\docker\docker-compose.dev.yml"
    if (Test-Path (Join-Path $PSScriptRoot "..\.env")) {
        $services = & docker compose --env-file (Join-Path $PSScriptRoot "..\.env") -f $composeFile ps --format json 2>$null | ConvertFrom-Json
        foreach ($service in @($services)) {
            $status = if ($service.Health -eq "healthy" -or $service.State -eq "running") { "PASS" } else { "BLOCKED" }
            Write-Check $service.Service $status ("state={0}; health={1}" -f $service.State, $service.Health)
        }
    } else {
        Write-Check "PostgreSQL container" "BLOCKED" ".env is missing"
        Write-Check "Redis container" "BLOCKED" ".env is missing"
    }
} else {
    Write-Check "Docker" "BLOCKED" "docker is not available on PATH"
    Write-Check "Docker Compose" "BLOCKED" "docker is not available on PATH"
    Write-Check "PostgreSQL container" "BLOCKED" "Docker is unavailable"
    Write-Check "Redis container" "BLOCKED" "Docker is unavailable"
}

$flutter = Get-Command flutter -ErrorAction SilentlyContinue
if ($flutter) { Write-Check "Flutter" "PASS" (& flutter --version 2>&1 | Select-Object -First 1) } else { Write-Check "Flutter" "BLOCKED" "Flutter is not available on PATH; mobile scaffold is not executable" }
$dart = Get-Command dart -ErrorAction SilentlyContinue
if ($dart) { Write-Check "Dart" "PASS" (& dart --version 2>&1) } else { Write-Check "Dart" "BLOCKED" "Dart is not available on PATH" }

$pg = Get-Command psql -ErrorAction SilentlyContinue
if ($pg) { Write-Check "PostgreSQL client" "PASS" $pg.Source } else { Write-Check "PostgreSQL client" "BLOCKED" "psql is not available on PATH" }
