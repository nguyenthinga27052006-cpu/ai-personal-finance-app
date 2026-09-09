# PHASE 17 FILE INVENTORY

Status describes implementation/document presence and local evidence only. It does not imply staging or production verification.

| Path | Category | Purpose | Status |
|---|---|---|---|
| `.github/workflows/ci.yml` | CI | Backend, worker, Flutter, container, and security jobs | LOCALLY VERIFIED |
| `infra/docker/docker-compose.staging.yml` | Infrastructure | Staging service composition template | LOCALLY VERIFIED |
| `infra/environments/local.env.example` | Infrastructure | Local environment template | LOCALLY VERIFIED |
| `infra/environments/staging.env.example` | Infrastructure | Staging environment template | LOCALLY VERIFIED |
| `infra/environments/production.env.example` | Infrastructure | Production environment template | LOCALLY VERIFIED |
| `apps/api/Dockerfile` | Docker | Hardened API image | LOCALLY VERIFIED |
| `apps/worker/Dockerfile` | Docker | Hardened worker image and shutdown handling | LOCALLY VERIFIED |
| `apps/api/app/observability.py` | Observability | JSON logging, correlation context, and metrics | LOCALLY VERIFIED |
| `apps/api/app/main.py` | Observability | Middleware and `/metrics` integration | LOCALLY VERIFIED |
| `apps/api/app/ai/usage.py` | AI | In-memory per-user/per-feature budget enforcement | LOCALLY VERIFIED |
| `apps/api/app/ai/routes.py` | AI | AI route budget and rate-limit integration | LOCALLY VERIFIED |
| `apps/api/core/config.py` | AI | Phase 17 configuration values | LOCALLY VERIFIED |
| `scripts/backup-restore-drill.ps1` | Backup | pg_dump/pg_restore procedure and validation hooks | DOCUMENTED / NOT VERIFIED |
| `apps/api/tests/test_phase17_operability.py` | Tests | Nine focused observability and AI budget tests | LOCALLY VERIFIED |
| `docs/phase17/CI_CD.md` | Documentation | CI/CD design and operating guidance | LOCALLY VERIFIED |
| `docs/phase17/OBSERVABILITY.md` | Documentation | Logging, correlation, and metrics guidance | LOCALLY VERIFIED |
| `docs/phase17/AI_COST_CONTROL.md` | Documentation | AI budgets and cost controls | LOCALLY VERIFIED |
| `docs/phase17/RATE_LIMITING.md` | Documentation | Rate-limit policy and limitations | LOCALLY VERIFIED |
| `docs/phase17/ALERTING.md` | Documentation | Alert definitions and response guidance | LOCALLY VERIFIED |
| `docs/phase17/BACKUP_DR.md` | Backup | Backup and disaster recovery policy | DOCUMENTED / NOT VERIFIED |
| `docs/phase17/RESTORE_DRILL.md` | Backup | Restore drill procedure | DOCUMENTED / NOT VERIFIED |
| `docs/phase17/RPO_RTO.md` | Backup | RPO/RTO targets and measurement guidance | DOCUMENTED / NOT VERIFIED |
| `docs/phase17/SECURITY_PIPELINE.md` | Security | Secret/dependency/container scan pipeline design | LOCALLY VERIFIED |
| `docs/phase17/ENVIRONMENTS.md` | Deployment | Environment separation guidance | LOCALLY VERIFIED |
| `docs/phase17/DEPLOYMENT.md` | Deployment | Deployment procedure and approval concept | LOCALLY VERIFIED |
| `docs/phase17/ROLLBACK.md` | Deployment | Rollback procedure | LOCALLY VERIFIED |
| `docs/phase17/COST_OBSERVABILITY.md` | Documentation | Cost observability guidance | LOCALLY VERIFIED |
| `docs/phase17/PRODUCTION_READINESS_MATRIX.md` | Documentation | Capability readiness matrix | LOCALLY VERIFIED |
| `docs/phase17/README.md` | Documentation | Phase 17 documentation index | LOCALLY VERIFIED |
| `docs/phase17/RUNBOOK_API_DOWN.md` | Runbooks | API incident response | LOCALLY VERIFIED |
| `docs/phase17/RUNBOOK_DATABASE.md` | Runbooks | Database incident response | LOCALLY VERIFIED |
| `docs/phase17/RUNBOOK_QUEUE.md` | Runbooks | Worker/queue incident response | LOCALLY VERIFIED |
| `docs/phase17/RUNBOOK_AI_PROVIDER.md` | Runbooks | AI provider incident response | LOCALLY VERIFIED |
| `docs/phase17/RUNBOOK_BACKUP.md` | Runbooks | Backup incident response | LOCALLY VERIFIED |
| `docs/phase17/RUNBOOK_ROLLBACK.md` | Runbooks | Rollback incident response | LOCALLY VERIFIED |
| `docs/phase17/RUNBOOK_SECRET_COMPROMISE.md` | Runbooks | Secret compromise response | LOCALLY VERIFIED |
| `docs/phase17/RUNBOOK_CONTAINER.md` | Runbooks | Container incident response | LOCALLY VERIFIED |
| `docs/phase17/RUNBOOK_COST_SPIKE.md` | Runbooks | AI/cost spike response | LOCALLY VERIFIED |
| `docs/phase17/PHASE17_REGRESSION.md` | Documentation | Phase 17 evidence report | LOCALLY VERIFIED |
| `docs/phase17/PHASE17_ACCEPTANCE_MATRIX.md` | Documentation | Acceptance criteria matrix | LOCALLY VERIFIED |
| `docs/phase17/PHASE17_FILE_INVENTORY.md` | Documentation | Maintainability inventory | LOCALLY VERIFIED |
