# Phase 01 -> Phase 02 -> Phase 03 Comparison

**Review date:** 2026-08-26  
**Purpose:** Compare the original contract, Phase 02 foundation, and Phase 03 implementation to identify mismatches and stale claims.  
**Scope boundary:** This review stops at Phase 03. It does not implement Phase 04 or Authentication.

## Executive Result

| Phase | Intended result | Actual state | Verdict |
|---|---|---|---|
| Phase 01 | Freeze product, architecture, financial rules, and implementation contract | Contract and blueprint documents exist | PASS as documentation baseline |
| Phase 02 | Build repository/runtime foundation without financial business behavior | FastAPI foundation, configuration, Compose files, scripts, and health endpoints exist | BLOCKED: current-source rebuild/runtime evidence incomplete |
| Phase 03 | Build and verify database foundation | ORM, Alembic, seed, tests, and local PostgreSQL verification exist | BLOCKED: host endpoint resolved PG17; PG18 container evidence incomplete |

**Current safe status:** Phase 03 is `BLOCKED`. It must not be called `PASS` until PostgreSQL 18 Docker verification is completed against the correct endpoint.

## 1. Phase 01 Baseline

Primary source: [IMPLEMENTATION_CONTRACT.md](IMPLEMENTATION_CONTRACT.md).

### What Phase 01 defined

- FastAPI backend and Flutter mobile client.
- PostgreSQL as the financial source of truth.
- Redis only for cache, rate limit, transient state, queue, and locks.
- SQLAlchemy and Alembic for persistence and migration.
- Modular-monolith boundary: API -> Application -> Domain -> Repository -> Database.
- Integer minor units for money; no binary floating point.
- Ledger entries as the balance source of truth; cached account balance must be reconcilable.
- Server-side ownership checks; client-supplied `user_id` must not control ownership.
- Atomic financial writes, idempotency where applicable, auditability, timezone-aware reporting.
- Transfer is neither expense nor income.
- Refund is linked to an eligible original transaction and is not normal income.
- Split item amounts must equal the transaction amount.
- MVP API inventory includes Auth, accounts, categories, transactions, transfers, dashboard, budgets, analytics, and notifications.

### Phase 01 expectations that are intentionally not Phase 03 deliverables

These are business/API/runtime requirements, not database-foundation completion criteria:

- Authentication and authorization workflows.
- Financial transaction application services and API endpoints.
- Atomic balance updates and reconciliation jobs.
- Refund eligibility and partial-refund policy.
- Posted-record edit/void state transitions.
- Currency matching and timezone period resolution.
- Dashboard, analytics, budgets, notifications, and AI gateway behavior.

They remain deferred and must not be claimed as implemented by Phase 03.

## 2. Phase 02 Comparison

Primary source: [READINESS_REPORT.md](READINESS_REPORT.md) and the Phase 02 section of [AGENT_PROGRESS.md](../AGENT_PROGRESS.md).

### Phase 02 before implementation

The readiness report recorded:

- No source code.
- No package manifests.
- No Docker/Compose.
- No migrations.
- No tests.
- No CI/CD workflows.
- Documentation-only repository.

### Phase 02 after implementation

The repository now contains:

- `apps/api` FastAPI project and Python manifest.
- Configuration using `.env`, PostgreSQL URL, and Redis URL.
- `/health` and `/ready` endpoints.
- Docker Compose definition under `infra/docker/`.
- Root development scripts for startup, migration, seeding, testing, and linting.
- SQLAlchemy/Alembic database foundation added during Phase 03.

### Phase 02 gaps or stale statements

| Finding | Evidence | Impact | Correct interpretation |
|---|---|---|---|
| Docker Compose health was not proven in this session | `docker compose --version` returned command not found | Cannot claim PostgreSQL 18/Redis container health | Phase 02 runtime smoke test remains blocked in this environment |
| Phase 02 expected foundation only | Contract section 10 | Phase 03 database work must not be described as Phase 02 work | Keep phase ownership separate |
| Phase 02 documentation originally said migrations/seed were next | Previous progress text | That statement became stale after Phase 03 | Current progress file now records the Phase 03 result |

## 3. Phase 03 Added and Changed

### Added implementation

- SQLAlchemy base and timestamp/ID mixins in `apps/api/app/db/base.py`.
- Engine, session factory, and FastAPI database dependency in `apps/api/app/db/session.py`.
- 14 ORM models in `apps/api/app/db/models/finance.py`.
- Enum classes for user, account, category, budget, goal, transaction, source, and ledger entry states.
- Relationships and foreign keys between users, accounts, transactions, entries, items, budgets, goals, merchants, and settings.
- Check constraints for non-negative balances, positive amounts, non-zero ledger entries, valid budget dates, and system-category ownership.
- Idempotent system-category seed: 15 rows, 10 expense and 5 income.
- Alembic environment and configuration.
- Alembic migration generated from current ORM metadata: revision `03811dfc2d31`.
- Direct PostgreSQL verification helper in `apps/api/verify_postgres.py`.
- Six focused database tests plus the existing health test.

### Changed implementation

- `apps/api/app/core/config.py`: centralized SQLAlchemy `postgresql+psycopg://` URL normalization.
- `scripts/migrate.ps1`: corrected path construction and failure propagation.
- `scripts/seed.ps1`: corrected path construction and failure propagation.
- Alembic model registration fixed so autogeneration sees all ORM tables.
- Duplicate and stale migration roots removed after the real migration exposed multiple heads and schema drift.
- Ruff formatting and import issues fixed.

### Added documentation

- [database/schema.md](database/schema.md)
- [database/MIGRATION_GUIDE.md](database/MIGRATION_GUIDE.md)
- [database/seed.md](database/seed.md)
- [database/FINANCIAL_DATA_RULES.md](database/FINANCIAL_DATA_RULES.md)
- [database/PHASE_03_ACCEPTANCE_REPORT.md](database/PHASE_03_ACCEPTANCE_REPORT.md)

## 4. What Is Correct

The following Phase 03 claims are supported by code or executed evidence:

- 14 tables are present in the local PostgreSQL database.
- Alembic upgrade completed and current revision is `03811dfc2d31 (head)`.
- Direct PostgreSQL catalog check found expected primary/foreign/check/unique constraints and indexes.
- Seed completed twice on PostgreSQL without duplicate system categories.
- Direct PostgreSQL check found 15 system categories: 10 `EXPENSE`, 5 `INCOME`.
- Full pytest result: `7 passed, 1 warning, 0 failed, 0 skipped`.
- Full Ruff result: `All checks passed!`.
- `/health`: HTTP 200 with `{"status":"ok"}`.
- `/ready`: HTTP 200 with `{"status":"ready"}` against the local PostgreSQL and Redis endpoints.
- `git diff --check`: passed.

## 5. What Is Wrong or Misleading

### 5.1 BIGINT claim does not match the implementation

**Resolved mismatch:** The ORM and initial migration now declare monetary columns as `BigInteger`/`BIGINT`; the superseded conversion revision was removed.

**Why it matters:** This contradicts the stated 64-bit money policy and can create a range mismatch for high-value balances.

**Required decision:** Either:

1. Change all monetary ORM columns to `BigInteger` and regenerate/test the migration, or
2. Change the contract and documentation to explicitly accept PostgreSQL `integer` and document its range.

For financial data, option 1 is the safer alignment with the existing documented policy, but this review does not implement that change.

### 5.2 PostgreSQL version gate remains blocked

**Problem:** The executed real database was PostgreSQL `17.10` installed as a Windows service. The required Docker command could not run because Docker CLI was unavailable.

**Result:** Local PostgreSQL verification is useful evidence, but it is not evidence for PostgreSQL 18 Docker health.

**Required decision:** Keep Phase 03 `BLOCKED` until the fresh database, schema, seed, and integration sequence is rerun against the PostgreSQL 18 container endpoint.

### 5.3 Container health cannot be inferred from localhost readiness

`/ready` passed against local PostgreSQL and Redis endpoints. This proves application connectivity for those endpoints, not that the requested Compose PostgreSQL 18 and Redis containers are healthy.

### 5.4 Documentation has stale or contradictory claims

Historical acceptance sections are retained as evidence notes; the canonical current status is `BLOCKED` in `AGENT_PROGRESS.md` and the final audit report.

### 5.5 Phase 01 business invariants are only partially database-represented

The schema stores fields for transfer/refund/split behavior, but several invariants are not database constraints:

- Transfer source/destination accounts must belong to the same authenticated user.
- A transfer must have distinct accounts and balanced debit/credit entries.
- A refund must reference an eligible original and obey amount/partial-refund policy.
- Split item sum must equal transaction amount.
- Transaction currency must match account currency.
- Posted-record edit/void policy must preserve auditability.
- Cached account balance must be reconciled with ledger entries.

This is acceptable for a database foundation only if these are explicitly deferred; it is not evidence that the complete MVP financial behavior exists.

### 5.6 Missing Phase 01 contract tables/features

The contract mentions entities/features that are not in the Phase 03 14-table foundation, including:

- `device_sessions` for authentication/session management.
- `notifications` and optional `notification_events`.
- Recurring transactions and related P1 features.
- API/application/domain/repository layers for financial behavior.

These are not necessarily Phase 03 defects, but they must not be counted as Phase 03 implemented functionality.

## 6. Exact Comparison Matrix

| Requirement | Phase 01 contract | Phase 02 | Phase 03 | Difference |
|---|---|---|---|---|
| PostgreSQL source of truth | Required | Compose planned | Local PG17 verified; PG18 Docker blocked | Version/environment gate remains open |
| Redis non-financial infrastructure | Required | Compose planned | Local `/ready` passed; container health blocked | Container evidence missing |
| SQLAlchemy | Required | Dependency direction | Implemented | Correct |
| Alembic | Required | Planned foundation | Implemented and migrated locally | Real PG17 passed; PG18 blocked |
| Integer money | Required | No implementation | Implemented as SQLAlchemy `Integer` | Documentation says BIGINT, code says integer |
| Ownership | Server-side required | Not implemented | FK columns/cascades partly implemented | Cross-owner semantic validation still application-level |
| Ledger source of truth | Required | Not implemented | `transaction_entries` table and relationship | Reconciliation logic not implemented |
| Transfer | Required | Not implemented | Fields and ledger relationships | Balanced/distinct/same-owner rules not enforced |
| Refund | Required | Not implemented | Parent transaction field | Eligibility/amount policy not enforced |
| Split | Required | Not implemented | `transaction_items` table | Sum equality not DB-enforced |
| Authentication | MVP P0 | Explicitly deferred from this task | Not implemented | Correctly not implemented per user instruction |
| Tests | Invariant tests required before feature completion | Health test | 7 tests pass; mostly SQLite, plus helper for PG17 | PG18 integration evidence absent |
| Documentation | Canonical docs required | Foundation docs | Database docs added | Acceptance report needed ongoing status consistency |

## 7. Recommended Corrections Before Any PASS Decision

1. Make Docker CLI available and run the exact Compose health command.
2. Confirm PostgreSQL container version is 18.x and Redis container is healthy.
3. Reset only the project-local development database/volume.
4. Run migration script and verify one Alembic head on PostgreSQL 18.
5. Run seed twice and query counts on PostgreSQL 18.
6. Resolve the `Integer` versus documented `BIGINT` decision before calling financial storage complete.
7. Rerun direct schema/invariant verification and record outputs.
8. Keep `AGENT_PROGRESS.md` and the acceptance report aligned with the evidence.

## Final Boundary

This comparison is the Phase 03 review artifact. **Stop here. Do not proceed to Phase 04. Do not implement Authentication.**
