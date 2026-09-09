# Deployment Runbook

## Prerequisites

Pin Git SHA, image tags/digests, migration head, environment template and approved secrets. Never copy secret values into logs or documents.

## Local

Use `scripts/dev-up.ps1`, migrate/seed scripts, then check `/health`, `/ready`, `/metrics` and the smoke checklist. Local evidence is LOCALLY VERIFIED from prior phases.

## Staging

Provision isolated PostgreSQL, Redis, secrets and network. Deploy exact image digests, run migrations, health/readiness, smoke and rollback checks. Status: NOT VERIFIED.

## Production

Require approved staging evidence, backup freshness, migration compatibility, immutable image digests, operator approval and monitored rollout. Status: NOT VERIFIED.

## Order

1. Validate secrets/configuration.
2. Validate database and Redis connectivity.
3. Run migration job.
4. Start API and worker.
5. Check health/readiness and smoke flows.
6. Monitor errors, latency, worker age and financial writes.
7. Accept or invoke rollback decision.

Failure handling: stop promotion on failed health, smoke, migration, dependency, authorization or financial checks. Application rollback does not undo database migrations.
