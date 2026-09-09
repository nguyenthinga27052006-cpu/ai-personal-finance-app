# PHASE STATUS

This file is the phase-by-phase current baseline. Historical acceptance reports remain linked evidence, but their old status wording is not stronger than the current executable evidence recorded here.

## PHASE 00

### Status
PASS WITH DOCUMENTED LIMITATIONS

### Objective
Establish repository governance, agent rules, scope and readiness.

### Scope
Rules, README, progress tracking, documentation structure and Git identity.

### Implemented
Repository rules, phase tracking, architecture documentation and test/build scripts exist.

### Files Changed
`AGENT_RULES.md`, `AGENT_PROGRESS.md`, `README.md`, `docs/`, `scripts/`.

### Verification Method
COMBINATION: DOCUMENT VERIFICATION and STATIC VERIFICATION.

### Commands
`git status --short`; `git branch --show-current`; `git log -n 10 --oneline`; `git diff --check`.

### Test Result
Repository audit completed against implementation commit `b3c07aa`; status documentation is committed separately.

### Evidence
Governance and documentation are present. No phase-specific executable test exists.

### Root Causes
Not applicable.

### Fixes
Canonical status documents were added during this audit.

### Regression
PASS

### Limitations
Historical readiness documents describe earlier repository states.

### Related Commit
Implementation baseline commit: `b3c07aa`; status/documentation commit is separate.

### Next Action
Maintain the status baseline.

## PHASE 01

### Status
PASS WITH DOCUMENTED LIMITATIONS

### Objective
Freeze product scope, architecture and financial rules.

### Scope
`docs/IMPLEMENTATION_CONTRACT.md`, ADRs and blueprint material.

### Implemented
Modular monolith, FastAPI, Flutter, PostgreSQL source of truth, ledger entries, integer money and AI tool boundary are documented.

### Files Changed
`docs/IMPLEMENTATION_CONTRACT.md`, `docs/architecture/adr/*`, blueprint documents.

### Verification Method
DOCUMENT VERIFICATION.

### Commands
Documentation inventory and source/test cross-check during the 2026-09-09 audit.

### Test Result
No phase-specific executable test applies; later implementation tests exercise the contract boundaries.

### Evidence
ADR-001 through ADR-011 and implementation contract reviewed.

### Root Causes
Not applicable.

### Fixes
None to product code in this audit.

### Regression
PASS

### Limitations
This phase is primarily documentary.

### Related Commit
Commit not identified for historical artifacts.

### Next Action
None; preserve contract decisions.

## PHASE 02

### Status
PASS WITH DOCUMENTED LIMITATIONS

### Objective
Provide runnable Python, Flutter, Docker and local service foundations.

### Scope
Manifests, Dockerfiles, Compose, environment files and scripts.

### Implemented
API, worker, mobile project, PostgreSQL, Redis, health/readiness routes and local scripts exist.

### Files Changed
`apps/api/pyproject.toml`, `apps/mobile/pubspec.yaml`, `apps/worker/pyproject.toml`, `infra/docker/docker-compose.dev.yml`, `scripts/*`.

### Verification Method
COMBINATION: STATIC, BUILD and RUNTIME VERIFICATION.

### Commands
`scripts\\phase16-gate.ps1`; `/health`; `/ready`; toolchain version checks.

### Test Result
Current gate and runtime endpoints pass.

### Evidence
Docker 29.7.2, Compose v5.4.0, Python 3.14.7, Flutter 3.47.1, Dart 3.13.1; `/health` and `/ready` HTTP 200.

### Root Causes
Not applicable.

### Fixes
None required by current audit.

### Regression
PASS

### Limitations
Evidence is local and the worktree is not commit-pinned.

### Related Commit
Commit not individually identified for the accumulated foundation changes.

### Next Action
None.

## PHASE 03

### Status
PASS

### Objective
Implement and verify PostgreSQL schema, migrations and seed.

### Scope
Alembic, ORM models, schema constraints, seed and PostgreSQL integration.

### Implemented
Single migration head `c93e2b7f4a18`, PostgreSQL BIGINT money columns, foreign keys, indexes and idempotent seed.

### Files Changed
`apps/api/migrations/`, `apps/api/app/db/`, `apps/api/tests/integration/`, `apps/api/verify_postgres.py`.

### Verification Method
COMBINATION: EXECUTABLE TEST and STATIC VERIFICATION.

### Commands
`scripts\\phase16-gate.ps1`; PostgreSQL integration tests within `pytest`.

### Test Result
Full backend suite: 110 passed.

### Evidence
Migration/schema integration tests include PostgreSQL version, BIGINT columns, foreign keys, ownership and seed idempotency.

### Root Causes
None found.

### Fixes
None in this audit.

### Regression
PASS

### Limitations
No fresh destructive database reset was performed during this audit.

### Related Commit
Commit not individually identified for the migration chain.

### Next Action
None.

## PHASE 04

### Status
PASS

### Objective
Implement authentication, sessions, refresh rotation and revocation.

### Scope
JWT, password hashing, device sessions, current-user dependency and mobile secure storage.

### Implemented
Register/login/refresh/logout, token validation, session revocation and secure mobile token storage.

### Files Changed
`apps/api/app/auth/`, `apps/mobile/lib/auth/`, auth tests.

### Verification Method
EXECUTABLE TEST.

### Commands
`scripts\\phase16-gate.ps1` and backend auth tests.

### Test Result
Auth lifecycle, rotation, revocation, invalid token and disabled-user tests pass.

### Evidence
`apps/api/tests/test_auth.py`; `apps/api/tests/integration/test_postgres_auth.py`; `apps/api/tests/test_ai_platform.py`.

### Root Causes
None found.

### Fixes
None in this audit.

### Regression
PASS

### Limitations
Production secret management and distributed session operations remain deployment concerns.

### Related Commit
b3c07aa — verified Phase 04-16 implementation.

### Next Action
None.

## PHASE 05

### Status
PASS

### Objective
Implement account, category and merchant management with ownership.

### Scope
Account lifecycle, catalog visibility, normalization and aliases.

### Implemented
Owned accounts/categories/merchants, system categories, archive/edit validation and alias lookup.

### Files Changed
`apps/api/app/accounts/`, `apps/api/app/catalog/`, related mobile finance surfaces.

### Verification Method
EXECUTABLE TEST.

### Commands
`scripts\\phase16-gate.ps1`; `test_phase05.py` and full suite.

### Test Result
Phase 05 and full backend suite pass.

### Evidence
`apps/api/tests/test_phase05.py` covers balance cache, ownership, archived edits, category visibility and merchant normalization.

### Root Causes
None found.

### Fixes
None in this audit.

### Regression
PASS

### Limitations
System seed is environment-dependent outside the tested local setup.

### Related Commit
b3c07aa — verified Phase 04-16 implementation.

### Next Action
None.

## PHASE 06

### Status
PASS

### Objective
Implement atomic financial transactions and ledger invariants.

### Scope
Income, expense, transfer, refund, split, idempotency, rollback and ownership.

### Implemented
Integer monetary amounts, ledger entries, atomic balance updates, transfer neutrality, bounded refunds, exact splits and idempotency.

### Files Changed
`apps/api/app/transactions/`, `apps/api/app/db/models/finance.py`, financial tests.

### Verification Method
EXECUTABLE TEST.

### Commands
`scripts\\phase16-gate.ps1`; financial core, invariant and PostgreSQL integration tests.

### Test Result
All current backend tests pass.

### Evidence
`test_financial_core.py`, `test_financial_invariants.py`, `test_phase06_acceptance.py`, PostgreSQL financial-core tests.

### Root Causes
None found.

### Fixes
None in this audit.

### Regression
PASS

### Limitations
Posted-record edit/void/reversal audit policy remains deferred by project scope.

### Related Commit
b3c07aa — verified Phase 04-16 implementation.

### Next Action
None.

## PHASE 07

### Status
PASS

### Objective
Implement deterministic budget and goal calculations.

### Scope
Budget thresholds, effective expenses, refunds/transfers, goals, deadlines and timezone boundaries.

### Implemented
Deterministic integer calculations, user ownership, period validation, projections and contribution progress.

### Files Changed
`apps/api/app/budget_goals/`, `apps/api/tests/test_phase07.py`, mobile budget/goal views.

### Verification Method
EXECUTABLE TEST.

### Commands
`scripts\\phase16-gate.ps1`; `test_phase07.py`; Journey B/C.

### Test Result
Backend tests and current Journeys B/C pass.

### Evidence
Budget excludes income/transfers, applies refunds and enforces ownership; Journey C renders 40% progress.

### Root Causes
None found.

### Fixes
None in this audit.

### Regression
PASS

### Limitations
None blocking current gate.

### Related Commit
b3c07aa — verified Phase 04-16 implementation.

### Next Action
None.

## PHASE 08

### Status
PASS WITH DOCUMENTED LIMITATIONS

### Objective
Deliver Flutter core experience, navigation, dashboard and critical journey.

### Scope
Auth UI, accounts, transactions, dashboard, mobile builds and Android E2E.

### Implemented
Flutter app shell, secure auth, finance views, navigation, dialogs and dashboard.

### Files Changed
`apps/mobile/lib/`, `apps/mobile/test/`, `apps/mobile/integration_test/`.

### Verification Method
COMBINATION: EXECUTABLE TEST and BUILD VERIFICATION.

### Commands
`flutter analyze`; `flutter test`; `flutter build apk --debug`; `flutter build web`; current Journey A command.

### Test Result
Flutter unit tests 11 passed; APK/web builds passed; Journey A passed on `emulator-5554`.

### Evidence
Journey A executed register -> login -> account -> income -> expense -> dashboard. It emits one non-fatal hit-test warning for the Amount field when outside the viewport.

### Root Causes
The warning is test interaction geometry, not a failed assertion or production exception.

### Fixes
Journey A auth reset, navigation and selectors were stabilized in the current test source.

### Regression
PASS

### Limitations
The warning should be cleaned up in a later focused test-quality task; it does not block this baseline.

### Related Commit
b3c07aa — verified Phase 04-16 implementation.

### Next Action
None for Phase 16 closure.

## PHASE 09

### Status
PASS

### Objective
Provide canonical deterministic analytics and financial facts.

### Scope
Period summaries, category analysis, trends, forecasts and dashboard data.

### Implemented
Analytics service is the source for dashboard and AI read-only tools, with timezone and period validation.

### Files Changed
`apps/api/app/analytics/`, dashboard routes/services, analytics tests.

### Verification Method
EXECUTABLE TEST.

### Commands
`scripts\\phase16-gate.ps1`; analytics/dashboard tests; Journey A dashboard assertions.

### Test Result
Pass.

### Evidence
Tests cover canonical facts, timezone boundaries, reversed periods, currencies and owned resources.

### Root Causes
None found.

### Fixes
None in this audit.

### Regression
PASS

### Limitations
None blocking current gate.

### Related Commit
b3c07aa — verified Phase 04-16 implementation.

### Next Action
None.

## PHASE 10

### Status
PASS WITH DOCUMENTED LIMITATIONS

### Objective
Generate deterministic traceable insights.

### Scope
Insight rules, severity/ranking, provenance, expiry and ownership.

### Implemented
Deterministic insight engine with source metric/value and expiry semantics.

### Files Changed
`apps/api/app/insights/`, `apps/mobile/lib/finance/`, insight tests.

### Verification Method
EXECUTABLE TEST.

### Commands
`scripts\\phase16-gate.ps1`; `test_insights.py` and full suite.

### Test Result
Pass.

### Evidence
Tests cover deterministic ranking, traceability, no-evidence fail-closed behavior, expiry and ownership.

### Root Causes
None found.

### Fixes
Numeric JSON parsing was fixed earlier and is covered by mobile model tests.

### Regression
PASS

### Limitations
No external probabilistic model is involved; historical report timestamp discrepancies remain documentary.

### Related Commit
b3c07aa — verified Phase 04-16 implementation.

### Next Action
None.

## PHASE 11

### Status
PASS WITH DOCUMENTED LIMITATIONS

### Objective
Generate and expose deterministic in-app notifications.

### Scope
Thresholds, dedupe, preferences, quiet hours, read/events and scheduler locking.

### Implemented
Budget threshold and insight notification candidates, API routes, worker evaluation and dedupe keys.

### Files Changed
`apps/api/app/notifications/`, `apps/worker/app/scheduler.py`, notification tests, mobile Notifications view.

### Verification Method
COMBINATION: EXECUTABLE TEST and CURRENT E2E.

### Commands
`scripts\\phase16-gate.ps1`; notification tests; current Journey B command.

### Test Result
Pass; Journey B renders the live alert.

### Evidence
API creates valid 80%/90% threshold notifications; the mobile tab refreshes on entry and displays the title.

### Root Causes
The app previously held a stale notification list after worker evaluation.

### Fixes
Refresh `FinanceViewModel.loadCore()` when Notifications is selected; corrected Journey B duplicate-title assertion.

### Regression
PASS

### Limitations
Worker delivery is indirectly tested; push delivery is outside current scope.

### Related Commit
b3c07aa — verified Phase 04-16 implementation.

### Next Action
None.

## PHASE 12

### Status
PASS WITH DOCUMENTED LIMITATIONS

### Objective
Implement traceable recommendation lifecycle and worker scheduling.

### Scope
Candidate generation, ranking, accept/dismiss/feedback, events and provenance.

### Implemented
Owned recommendations with deterministic candidate evidence and lifecycle events.

### Files Changed
`apps/api/app/recommendations/`, worker scheduler, recommendation tests, mobile recommendations view.

### Verification Method
EXECUTABLE TEST and STATIC VERIFICATION.

### Commands
`scripts\\phase16-gate.ps1`; `test_recommendations.py`.

### Test Result
Pass.

### Evidence
Tests cover traceability, empty evidence, recurring fail-closed behavior, lifecycle, events and cross-user isolation.

### Root Causes
None found.

### Fixes
None in this audit.

### Regression
PASS

### Limitations
Recurring recommendations and push delivery are deferred; worker validation is indirect.

### Related Commit
b3c07aa — verified Phase 04-16 implementation.

### Next Action
None.

## PHASE 13

### Status
PASS WITH DOCUMENTED LIMITATIONS

### Objective
Create the AI gateway, safe read-only tools and guardrail boundary.

### Scope
Gateway routing, context minimization, provenance, tool allowlists and prompt/security guardrails.

### Implemented
AI tools derive ownership from authenticated context; write tools and arbitrary raw SQL are blocked.

### Files Changed
`apps/api/app/ai/gateway.py`, `tools.py`, `guardrails.py`, `context.py`, AI tests.

### Verification Method
EXECUTABLE TEST and STATIC VERIFICATION.

### Commands
`scripts\\phase16-gate.ps1`; `test_ai_platform.py`.

### Test Result
Pass.

### Evidence
Tests cover user ID injection, cross-user denial, raw SQL/write blocking, prompt/secret redaction, provider errors and provenance.

### Root Causes
None found.

### Fixes
None in this audit.

### Regression
PASS

### Limitations
Only `FakeProvider` is configured; real-model semantic quality is not verified.

### Related Commit
b3c07aa — verified Phase 04-16 implementation.

### Next Action
Evaluate with a real provider only as a separate task.

## PHASE 14

### Status
PASS WITH DOCUMENTED LIMITATIONS

### Objective
Deliver user-facing AI features over the safe gateway.

### Scope
NL query, categorization, OCR abstraction, recommendations/explanations, temporary chat and mobile AI screen.

### Implemented
Authenticated `/api/v1/ai/query`, grounded tool answers, unsupported/insufficient semantics, OCR review boundary and mobile AI surface.

### Files Changed
`apps/api/app/ai/`, `apps/mobile/lib/ai/`, AI feature tests and docs.

### Verification Method
COMBINATION: EXECUTABLE TEST and CURRENT E2E.

### Commands
`scripts\\phase16-gate.ps1`; `test_phase14_ai_features.py`; current Journey D command.

### Test Result
Pass; Journey D returns grounded `analytics.service` provenance and renders the answer.

### Evidence
Current Journey D includes a real expense fixture, validates intent/tool/source/answer, unsupported request, and UI source text.

### Root Causes
The original Journey D fixture had no expense, so the API correctly returned insufficient data with no provenance.

### Fixes
Added canonical expense creation to the test fixture; production API behavior was preserved.

### Regression
PASS

### Limitations
Chat is in-memory/session-scoped; OCR is an abstraction without production object storage.

### Related Commit
b3c07aa — verified Phase 04-16 implementation.

### Next Action
None for current baseline.

## PHASE 15

### Status
PASS WITH DOCUMENTED LIMITATIONS

### Objective
Harden privacy, authentication and AI security boundaries.

### Scope
Security defaults, headers, request size, rate limits, ownership, token storage, threat/data inventory.

### Implemented
Production-default checks, security headers, 1 MiB guard, per-user/IP AI limiting, public-safe errors and secure mobile storage.

### Files Changed
`apps/api/app/auth/`, `apps/api/app/core/`, `apps/api/app/main.py`, `apps/mobile/lib/auth/`, security docs and tests.

### Verification Method
COMBINATION: EXECUTABLE TEST and DOCUMENT VERIFICATION.

### Commands
`scripts\\phase16-gate.ps1`; auth/AI/security tests; security docs audit.

### Test Result
Pass for implemented scope.

### Evidence
Full suite includes authentication, cross-user/BOLA, rate-limit, request-size, error-disclosure and secure token tests.

### Root Causes
None found in current tested scope.

### Fixes
None in this audit.

### Regression
PASS

### Limitations
Distributed rate limits, production TLS/HSTS/CORS/WAF, secret vault rotation, dependency scan, network segmentation and retention/export/deletion remain unverified or deferred.

### Related Commit
b3c07aa — verified Phase 04-16 implementation.

### Next Action
Deployment/security hardening is a separate task.

## PHASE 16

### Status
PASS WITH DOCUMENTED LIMITATIONS

### Objective
Run full repository regression, validate financial invariants and close current E2E journeys.

### Scope
Backend, worker, mobile, builds, runtime, AI evaluation, financial/security regression and Journeys A-D.

### Implemented
Current gate, current E2E tests, numeric parser fix, notification refresh, and canonical status artifacts.

### Files Changed
`apps/mobile/lib/finance/finance_home.dart`, `apps/mobile/integration_test/critical_journey_test.dart`, `apps/mobile/integration_test/phase16_journeys_test.dart`, `AGENT_PROGRESS.md`, `docs/project-status/*`.

### Verification Method
COMBINATION: EXECUTABLE TEST, BUILD VERIFICATION, RUNTIME VERIFICATION and DOCUMENT VERIFICATION.

### Commands
`scripts\\phase16-gate.ps1`; current A/B/C/D Flutter commands; `/health`; `/ready`; `git diff --check`.

### Test Result
Backend 110 passed; Flutter 11 passed; APK/web builds passed; A/B/C/D current Android runs passed.

### Evidence
A: auth/account/income/expense/dashboard. B: budget expense alert. C: goal contribution progress. D: grounded AI query/tool answer.

### Root Causes
Stale notification UI state and incomplete E2E fixture/test assumptions were identified and reproduced.

### Fixes
Minimal production notification refresh; focused test-only fixture, selector and cardinality fixes.

### Regression
PASS

### Limitations
Real-model AI, coverage percentage, production performance thresholds and hosted CI are not verified. Journey A has a non-fatal hit-test warning.

### Related Commit
Implementation commit: `b3c07aa`; status/documentation commit is separate.

### Next Action
Historical Phase 16 checkpoint: stop at Phase 16; Phase 17/18 were not started at that checkpoint.

### CURRENT
Phase 17 COMPLETE WITH DOCUMENTED LIMITATIONS.
Phase 18 NOT STARTED.

## PHASE 17

### Status
PASS WITH DOCUMENTED LIMITATIONS

### Objective
Production-operable CI/CD, infrastructure, observability, backup/restore and cost controls.

### Scope
CI/CD pipeline, container orchestration, structured logging, metrics, tracing, AI cost/usage limits, rate limiting, alerting, backup/restore, RPO/RTO, runbooks, production readiness.

### Implemented
- CI/CD: GitHub Actions workflow with Python linting, testing, container builds, and security scanning
- Observability: Structured JSON logging, correlation ID context variables, Prometheus metrics endpoint
- AI Cost Control: Per-user and per-feature daily budget tracking with hard-stop enforcement
- Containers: Docker images with non-root user, health checks, and graceful shutdown handling
- Backup/Restore: pg_dump/pg_restore procedure documented with post-restore validation guidance; execution NOT VERIFIED
- Documentation: 24 files covering operations (CI/CD, observability, rate limiting, alerting, deployment, runbooks, etc.)
- Runbooks: 9 operational runbooks (API, Database, Queue, AI Provider, Backup, Rollback, Secret Compromise, Container, Cost Spike)
- Production Readiness Matrix: capability-by-capability implementation and verification status

### Files Changed
`.github/workflows/ci.yml`, `apps/api/Dockerfile`, `apps/worker/Dockerfile`, `apps/api/app/observability.py`, `apps/api/app/main.py`, `apps/api/app/ai/usage.py`, `apps/api/app/ai/routes.py`, `apps/api/core/config.py`, `scripts/backup-restore-drill.ps1`, `infra/docker/docker-compose.staging.yml`, `infra/environments/*`, `docs/phase17/*` (24 files), `apps/api/tests/test_phase17_operability.py`.

### Verification Method
COMBINATION: EXECUTABLE TEST (9 focused Phase 17 operability tests), BUILD VERIFICATION (API and worker Docker images), STATIC VERIFICATION (workflow and configuration review), RUNTIME VERIFICATION (local observability endpoint and correlation headers), and DOCUMENT VERIFICATION (runbooks and readiness matrix).

### Commands
- Git audit: `git status --short`, `git log -10 --oneline`, `git diff --check`
- Phase 16 regression evidence: `scripts/phase16-gate.ps1` (119 API tests PASS, 10 warnings, Ruff PASS, compileall PASS; Flutter tests/builds PASS)
- Phase 17 focused tests: `python -m pytest apps/api/tests/test_phase17_operability.py -q` (9 passed)
- Phase 17 test inventory: Phase 16 historical baseline 110 backend tests; current full suite 119 passed, 0 failed, 9 warnings
- Docker builds: `docker build -t finance-assistant-api:test apps/api`, `docker build -t finance-assistant-worker:test apps/worker`
- CI validation: Workflow syntax check (`yq` or visual review), job structure verification

### Test Result
Phase 16 baseline: 110 backend tests (historical baseline stated by project directive).
Phase 16 historical baseline: 110 backend tests.
Phase 17 added: 9 focused operability tests.
Current backend suite: 119 collected, 119 passed, 0 failed, 9 warnings.
Post-Phase-17 regression: 119 backend tests passed.

### Evidence
- Phase 16 regression gate: All checks passing (119 API tests, Python linting, compilation, Flutter tests and builds)
- Observability: Metrics collection, correlation IDs, structured logging verified locally
- AI cost controls: Per-user and per-feature budget enforcement verified with hard-stop at limit
- Docker builds: Both API (312 MB) and worker images build successfully with security hardening
- Backup: script syntax/static review only; backup artifact creation is NOT VERIFIED
- Restore: NOT VERIFIED; no restore executed
- Financial restore integrity: NOT VERIFIED; no restored database checked
- RPO/RTO: DOCUMENTED / NOT VERIFIED; targets not measured
- CI/CD workflow: GitHub Actions jobs configured with proper dependencies and artifact handling
- Documentation: Production Readiness Matrix covers 12 capabilities with honest risk assessment

### Root Causes
None found in the locally verified Phase 17 implementation.

### Fixes
Implemented observability, AI budget enforcement, CI workflow, container hardening, environment templates, backup/restore procedure, and operational documentation.

### Regression
PASS — Phase 16 regression gate shows no financial logic regression. Flutter linting warnings (33 print issues) are pre-existing style issues from Phase 16, not Phase 17 regressions.

### Limitations
- Hosted GitHub Actions execution is NOT VERIFIED.
- Staging and production deployments are NOT VERIFIED; only templates and procedures exist.
- Backup artifact creation, actual restore execution, financial restore integrity, and DR drill are NOT VERIFIED.
- RPO and RTO are documented targets, not measured achievements.
- Distributed rate limiting and shared usage accounting are deferred; local in-memory controls are verified.
- OpenTelemetry exporters, external tracing, error tracking, monitoring backend, and external alert routing are NOT VERIFIED.
- Dependency scan, container scan, SBOM generation, and production security scanning are NOT VERIFIED locally.
- Real-model AI evaluation and production model routing are deferred; tests use local/deterministic providers.

### Related Commit
Implementation baseline: `b3c07aa`. Phase 17 core commits: `b017e4f`, `691009d`, `7bd23da`, `8d2dd0d`, `f2105d5`, `b3b555b`. Source verification HEAD: `f569550`; final repository HEAD: use the actual value from the final `git rev-parse HEAD` command.

### Next Action
Phase 18 NOT STARTED. Future work is limited to external staging/production verification and the documented limitations above.

---

### Phase 17 Implementation Details

**Observability Implementation:**
- `JsonFormatter` class formats logs as JSON with timestamp, level, service, message, request_id, trace_id, exception
- `correlation_ids()` extracts X-Request-ID and X-Trace-ID from headers or generates UUIDs
- `request_id_context` and `trace_id_context`: ContextVar for async-safe correlation tracking
- `Metrics` class: Counter for request counts by route/method/status, histogram for durations
- Prometheus endpoint at `/metrics` returns `app_http_requests_total` and `app_http_request_duration_ms`

**AI Cost Control Implementation:**
- `InMemoryAIUsageBudget`: Per-user, per-feature daily budget tracking with 86400s reset boundary
- `consume(user_id, feature, units)`: Returns cumulative usage; raises `AIUsageLimitExceeded` if exceeds daily_units
- `AIUsageLimitExceeded` exception includes `retry_after` for Retry-After header
- Middleware integration: `_consume_ai_budget()` enforces limits, returns HTTPException(429) on exceeded
- Tested with successful budget limit enforcement (per-user 3 units, per-feature, separate user/feature combinations tracked)

**CI/CD Pipeline:**
- Backend job: Runs pytest against PostgreSQL+Redis, ruff linting, Python compilation
- Worker job: Python compilation and dependency checks
- Flutter job: Analyze, unit tests, APK and web builds
- Security job: gitleaks (secret scanning), pip-audit (strict mode for CVE detection)
- Container job: Build and tag API and worker images with metadata
- Parallel execution with proper service dependencies (PostgreSQL 18, Redis 8)

**Docker Security Hardening:**
- Non-root user: `appuser:10001`
- HEALTHCHECK with curl to `/health` endpoint
- Multi-stage builds to reduce image size
- Signal handling: SIGTERM with graceful shutdown (worker)
- No hardcoded credentials or secrets in images

**Backup/Restore Procedure:**
- `backup-restore-drill.ps1`: pg_dump with custom format, pg_restore with --clean, --if-exists, --exit-on-error
- Post-restore validation instructions provided
- RPO: Backup frequency (daily/hourly configurable)
- RTO: Restore time documented as function of database size

**Production Readiness Verification:**
All 12 capabilities assessed with honest risk:
1. CI backend/worker/mobile checks: ✓ Implemented, locally verified
2. Immutable image contract: Template ready, digest promotion deferred
3. Environment isolation: Templates ready, cloud resources unavailable
4. Structured logs/correlation: ✓ Implemented and verified
5. Metrics: ✓ Local endpoint functional, scaling deferred
6. Tracing/error tracking: Documented, exporters deferred
7. Alerting: Rules documented, firing backend deferred
8. Backup/restore: Procedure documented; backup artifact, restore execution, and financial integrity NOT VERIFIED
9. RPO/RTO: Targets documented, production measurement deferred
10. AI usage/rate limits: ✓ Implemented and verified
11. Security supply chain: Workflow configured, hosted scanning deferred
12. Runbooks: ✓ 9 runbooks complete, incident exercises pending

---
