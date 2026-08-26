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
- Host developer tools and Alembic: `localhost:5433` using `HOST_DATABASE_URL`.
- Redis remains `redis:6379` inside Docker and `localhost:6379` from the host.

The verified Compose mapping is `0.0.0.0:5433 -> postgres:5432`. It avoids the separately installed PostgreSQL 17 service on host port 5432. Never use `localhost` in Docker service connection strings. `DATABASE_URL` remains the Docker URL; `HOST_DATABASE_URL` is for Windows host-side migration tools.

## Current Audit Evidence

On 2026-08-27, Docker 29.7.2 and Compose v5.4.0 were available. Compose reported healthy PostgreSQL 18.6, Redis 8, API, and worker; `docker compose port postgres 5432` reported `0.0.0.0:5433`. Host Alembic commands use `HOST_DATABASE_URL`; Docker services use `DATABASE_URL`. The PostgreSQL integration suite passed against the host-published PostgreSQL 18.6 endpoint.
