# Development Environment

**Scope:** Phase 01-03 verification only

Run `./scripts/check-env.ps1` from the repository root. The doctor reports `PASS`, `FAIL`, or `BLOCKED`; it does not install software or modify `PATH`.

## Required Evidence

- Git and Python are available.
- Docker and Docker Compose are available for the Phase 02 runtime gate.
- PostgreSQL and Redis Compose services report healthy.
- The PostgreSQL server used for the Phase 03 gate reports PostgreSQL 18.x.
- Flutter and Dart are available before claiming the mobile scaffold is executable.

## Endpoint Contract

- Docker API and worker: `postgres:5432` using `DATABASE_URL=postgresql://...@postgres:5432/finance`.
- Host developer tools: `localhost:5433` using `POSTGRES_PORT=5433`.
- Redis remains `redis:6379` inside Docker and `localhost:6379` from the host.

The `5433:5432` mapping avoids the separately installed PostgreSQL 17 service on host port 5432. Never use `localhost` in Docker service connection strings.

## Current Audit Evidence

On 2026-08-26, Docker 29.7.2 and Compose v5.4.0 were available. PostgreSQL host mapping `localhost:5433 -> postgres:5432` was verified; the existing PostgreSQL 17.10 service remains untouched on port 5432. Clean no-cache API/worker builds passed, PostgreSQL 18.6 integration passed, and API health/readiness returned HTTP 200. Flutter and Dart are unavailable, so executable mobile evidence remains BLOCKED.
