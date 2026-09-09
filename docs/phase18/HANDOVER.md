# Release Candidate Handover

## System

Flutter client, FastAPI API, PostgreSQL source of truth, Redis support, worker scheduling, guarded AI gateway and local observability.

## Deploy/migrate

Use `DEPLOYMENT_RUNBOOK.md` and `MIGRATION_RELEASE_PLAN.md`. Pin Git SHA and image tags, configure environment-specific secrets, migrate before dependent code, then health/readiness/smoke.

## Monitor/rollback

Use `MONITORING_RELEASE_CHECK.md`, Phase 17 observability docs and `ROLLBACK_RUNBOOK.md`. External monitoring is NOT VERIFIED.

## Incidents

Use `INCIDENT_RESPONSE_RUNBOOK.md` and `RUNBOOK_INDEX.md`. Preserve request IDs, trace IDs, logs and financial evidence without logging secrets.

## Secrets/backups

Secrets belong in the environment secret manager. Backups must be isolated and validated; backup/restore is NOT VERIFIED.

## Before production

Close RELEASE GATES RC-001 through RC-005 in `RELEASE_DECISION.md`, obtain release signing, run staging/production deployment checks, execute smoke/E2E, produce security scan/SBOM evidence and establish monitoring/alert routing.

Owners: Platform/SRE, DBA, Security, Mobile/Release, API/Finance, AI/Product. Exact personnel and contacts are NOT VERIFIED.
