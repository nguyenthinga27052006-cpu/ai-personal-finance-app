# Phase 01 to Phase 03 Fix Register

**Audit date:** 2026-08-27  
**Scope:** Final gate for Phase 01-03 only. Phase 04 work is excluded.

## FIX-001 - Phase status claims exceed current evidence

TYPE: REQUIRED NOW  
SEVERITY: HIGH  
SOURCE PHASE: Phase 02 / Phase 03  
CATEGORY: Documentation

### A. ISSUE
`AGENT_PROGRESS.md` currently reports Phase 02 and Phase 03 as `PASS`, while the current environment cannot connect to the Docker daemon and the current pytest run skips all PostgreSQL integration tests. The same file also reports Flutter/Dart evidence as blocked even though both executables are available and `flutter test` passed.

### B. WHY IS THIS AN ISSUE?
The final gate requires evidence-based status and the canonical status vocabulary. A current `PASS` claim is misleading when the required Compose/PostgreSQL 18 verification cannot be reproduced in this run.

### C. ROOT CAUSE
Progress documentation was not synchronized with the latest environment and test evidence.

### D. IMPACT
This affects release-gate correctness, reproducibility, test evidence, and developer routing. It does not change financial data.

### E. DECISION
`REQUIRED NOW`: current status must reflect the strongest evidence available before Phase 04.

### F. FIX
Update progress to `BLOCKED` for Phase 02 and Phase 03, record Flutter/Dart as verified, and list the exact Docker daemon and PostgreSQL integration blockers.

### G. FILES CHANGED
- `AGENT_PROGRESS.md` -> synchronize current gate status and evidence.

### H. WHY THIS FIX?
Current evidence has priority over stale report claims. No implementation scope is expanded.

### I. BEFORE / AFTER
BEFORE: Phase 02/03 `PASS`; Flutter/Dart executable evidence `BLOCKED`.  
AFTER: Phase 02/03 `BLOCKED`; Flutter/Dart executable checks `PASS`; Docker/PG18 verification explicitly blocked.

### J. VERIFICATION
COMMAND: `scripts/check-env.ps1`, API pytest, Flutter test, Docker Compose status.  
RESULT: Git/Python/Docker/Flutter/Dart available; Docker daemon unavailable; API `7 passed, 12 skipped`; Flutter tests passed.  
TEST: Re-run API and mobile checks after documentation-only update.  
EXPECTED: Documentation matches evidence.  
ACTUAL: `AGENT_PROGRESS.md` now records Phase 02/03 `BLOCKED`, Flutter/Dart `PASS`, and the Docker/PG integration blockers.

### K. REGRESSION IMPACT
No API, DB, migration, seed, worker, or mobile code behavior changes.

### L. DATA SAFETY
No database or data changes.

### M. DOCUMENTATION IMPACT
`AGENT_PROGRESS.md` and final gate report require synchronization.

### N. FINAL STATUS
FIXED

## FIX-011 - Host versus Docker database URL

TYPE: REQUIRED NOW  
SEVERITY: HIGH  
SOURCE PHASE: Phase 03  
CATEGORY: Configuration / Migration

### A. ISSUE
Host-side Alembic inherited `DATABASE_URL=postgresql://...@postgres:5432/finance`, but `postgres` is only resolvable inside the Docker Compose network. Windows host migration commands therefore failed to resolve the database host.

### B. WHY IS THIS AN ISSUE?
The API and worker need the Docker service URL, while host-side migration tools need the published host endpoint. Reusing one URL across both network contexts makes migration execution non-reproducible.

### C. ROOT CAUSE
A single `DATABASE_URL` was used for both Docker and Windows host execution contexts.

### D. IMPACT
Host migration commands failed before database access. Docker API/worker connectivity must remain unchanged. No financial correctness or schema behavior is changed by this configuration fix.

### E. DECISION
`REQUIRED NOW`: Phase 03 migration reproducibility requires both execution contexts to be explicit.

### F. FIX
Add `HOST_DATABASE_URL` with the verified published endpoint `localhost:5433`, keep `DATABASE_URL` at `postgres:5432` for Compose, make Alembic use the host URL, and keep Redis host resolution unchanged because no host-side Redis tool requires it.

### G. FILES CHANGED
- `.env.example` -> document Docker and host URL contexts.
- `.env` -> add the local host migration URL.
- `apps/api/app/core/config.py` -> expose host database configuration and migration URL helper.
- `apps/api/migrations/env.py` -> use host URL for Alembic.
- `scripts/migrate.ps1` -> provide host URL fallback only when absent.
- `apps/api/tests/test_configuration.py` -> verify host/Docker URL separation and canonical `.env` loading.
- `docs/database/MIGRATION_GUIDE.md` -> document host migration commands and Docker runtime URL.
- `docs/operations/DEVELOPMENT_ENVIRONMENT.md` -> document explicit URL contexts and verified port.

### H. WHY THIS FIX?
It preserves Docker service DNS for containers, uses the actual Compose-published port for host tools, and avoids creating a second database or migration root.

### I. BEFORE / AFTER
BEFORE: Windows -> `postgres:5432` -> DNS failure.  
AFTER: Windows migration -> `localhost:5433`; Docker API/worker -> `postgres:5432`.

### J. VERIFICATION
COMMAND: `docker compose ... ps`; `docker compose ... port postgres 5432`; root Alembic `current`, `heads`, `history`; `scripts\migrate.ps1`; pytest; Ruff; `git diff --check`.  
EXPECTED: published port is verified, host migration reaches PostgreSQL, Docker URLs remain unchanged, and regression checks pass.  
ACTUAL: Compose reports healthy PostgreSQL 18.6, Redis 8, API, and worker; port is `0.0.0.0:5433`; Alembic commands and migration script exit 0; 21 tests pass, Ruff passes, and diff check passes.

### K. REGRESSION IMPACT
Alembic source chain and ORM are unchanged. Docker API/worker retain `DATABASE_URL` and `REDIS_URL`. Configuration tests, API tests, and lint verify the separation.

### L. DATA SAFETY
No migration history reset, database reset, seed mutation, or data deletion was performed. The migration operates only against the configured development database.

### M. DOCUMENTATION IMPACT
Migration and development-environment docs now distinguish host and Docker contexts.

### N. FINAL STATUS
FIXED

## FIX-002 - Repository test and lint scripts bypass project virtual environment

TYPE: REQUIRED NOW  
SEVERITY: HIGH  
SOURCE PHASE: Phase 02  
CATEGORY: Environment

### A. ISSUE
`scripts/test.ps1` and `scripts/lint.ps1` invoke `py -3.13` globally instead of the repository root `.venv`. The documented script test fails during collection with `ModuleNotFoundError: sqlalchemy`, while the root venv has the project dependencies and runs the suite.

### B. WHY IS THIS AN ISSUE?
The repository's documented checks are not reproducible from the configured project environment. This creates false failures and invalidates the test gate when users follow the setup instructions.

### C. ROOT CAUSE
The scripts hard-code a system interpreter rather than resolving the project-local interpreter.

### D. IMPACT
Reproducibility and CI/developer verification are affected. No financial runtime behavior changes.

### E. DECISION
`REQUIRED NOW`: the foundation scripts must use the dependency environment documented by the repository.

### F. FIX
Resolve `..\.venv\Scripts\python.exe` from the repository root and use it for both pytest and Ruff, failing clearly if it is absent.

### G. FILES CHANGED
- `scripts/test.ps1` -> use root project interpreter.
- `scripts/lint.ps1` -> use root project interpreter.

### H. WHY THIS FIX?
It is the smallest change that makes the existing checks use the same installed dependency set as the API commands.

### I. BEFORE / AFTER
BEFORE: `py -3.13 -m pytest` and `py -3.13 -m ruff`.  
AFTER: root `.venv\Scripts\python.exe -m pytest` and `root .venv\Scripts\python.exe -m ruff check`.

### J. VERIFICATION
COMMAND: `scripts/test.ps1`; `scripts/lint.ps1`.  
RESULT BEFORE: test exit 2 with missing SQLAlchemy; lint exit 0 under unrelated global environment.  
EXPECTED AFTER: same project-local result as direct venv commands.  
ACTUAL: `scripts/test.ps1` returned 7 passed, 12 skipped, 1 warning; `scripts/lint.ps1` passed.

### K. REGRESSION IMPACT
Only developer test/lint invocation changes. API, DB, migration, seed, worker, and mobile behavior are unchanged.

### L. DATA SAFETY
No data access or mutation.

### M. DOCUMENTATION IMPACT
Final report records the corrected script evidence.

### N. FINAL STATUS
FIXED

## FIX-003 - Current final audit report claims completed PG18 verification

TYPE: REQUIRED NOW  
SEVERITY: HIGH  
SOURCE PHASE: Phase 02 / Phase 03  
CATEGORY: Documentation

### A. ISSUE
`docs/architecture/PHASE_01_TO_03_FINAL_AUDIT.md` presents PostgreSQL 18.6 Compose, health, migration, seed, integration, and readiness evidence as current PASS evidence, but the current Docker daemon is unavailable and current integration tests skip.

### B. WHY IS THIS AN ISSUE?
The report is a current audit artifact and must not claim evidence that was not executed or re-established in the current gate.

### C. ROOT CAUSE
The report was written from a prior execution context and not refreshed for the current environment.

### D. IMPACT
High risk of incorrect release decision and misleading handoff.

### E. DECISION
`REQUIRED NOW`: replace current claims with the actual blocked evidence while preserving historical results as historical evidence.

### F. FIX
Rewrite the report as historical findings plus current-gate evidence, explicitly separating the two.

### G. FILES CHANGED
- `docs/architecture/PHASE_01_TO_03_FINAL_AUDIT.md` -> current evidence and status.

### H. WHY THIS FIX?
Evidence provenance is required by the gate; historical evidence is retained rather than deleted.

### I. BEFORE / AFTER
BEFORE: current final status PASS with current-sounding PG18 execution claims.  
AFTER: current status BLOCKED; prior PG18 claims labeled historical and not used as current proof.

### J. VERIFICATION
COMMAND: Docker Compose status/version, API integration test collection.  
RESULT: Docker daemon connection failed; 12 PostgreSQL tests skipped.  
EXPECTED: report agrees with command output.  
ACTUAL: Current report records Docker API failure and skipped PostgreSQL tests; prior PG18 claims are labeled historical.

### K. REGRESSION IMPACT
Documentation only.

### L. DATA SAFETY
No data changes.

### M. DOCUMENTATION IMPACT
Final report and progress file become canonical current status.

### N. FINAL STATUS
FIXED

## FIX-004 - Seed guide describes obsolete category names and algorithm

TYPE: SAFE IMPROVEMENT  
SEVERITY: MEDIUM  
SOURCE PHASE: Phase 03  
CATEGORY: Documentation

### A. ISSUE
`docs/database/seed.md` documents names such as `Food & Dining` and an early-return query that skips all insertion when any system category exists. The implementation uses the current 15 definitions (`Food`, `Housing`, etc.) and checks each `(name, type)` identity before inserting.

### B. WHY IS THIS AN ISSUE?
The guide is a current operational procedure and its examples do not describe the actual seed data or idempotency behavior.

### C. ROOT CAUSE
Documentation was not updated after the seed implementation was refined.

### D. IMPACT
Operational verification and maintenance can be misleading; no correctness or security issue is introduced by the docs alone.

### E. DECISION
`SAFE IMPROVEMENT`: small documentation correction within Phase 03.

### F. FIX
Update the documented category names and per-identity idempotency algorithm.

### G. FILES CHANGED
- `docs/database/seed.md` -> align examples and strategy with implementation.

### H. WHY THIS FIX?
The code is the actual source for runtime behavior; the guide should help reproduce it.

### I. BEFORE / AFTER
BEFORE: obsolete names and any-row early return.  
AFTER: current names and per-name/type checks protected by the PostgreSQL partial unique index.

### J. VERIFICATION
COMMAND: API unit seed test and source inspection.  
EXPECTED: 15 system categories remain idempotent.  
ACTUAL: SQLite seed test passed; live PostgreSQL seed remains blocked by Docker.

### K. REGRESSION IMPACT
No runtime behavior changes.

### L. DATA SAFETY
No data changes.

### M. DOCUMENTATION IMPACT
This file is the documentation update.

### N. FINAL STATUS
FIXED

## FIX-005 - Docker/PostgreSQL 18 evidence is unavailable in the current environment

TYPE: DEFERRED  
SEVERITY: HIGH  
SOURCE PHASE: Phase 02 / Phase 03  
CATEGORY: Environment

### A. ISSUE
The Docker CLI is installed, but Docker Desktop's Linux engine is unavailable. Compose status/version execution cannot connect to `dockerDesktopLinuxEngine`; localhost ports 5433 and 8000 are also closed. PostgreSQL integration tests therefore skip because `POSTGRES_TEST_DATABASE_URL` is not configured.

### B. WHY IS THIS AN ISSUE?
Phase 02 and Phase 03 gates explicitly require real Compose health, PostgreSQL 18 server verification, fresh migration, seed twice, readiness, and PostgreSQL integration tests.

### C. ROOT CAUSE
External runtime prerequisite: Docker daemon is not running in this environment; no project code failure was established.

### D. IMPACT
The release gate remains blocked for Docker, PostgreSQL 18, Redis, API container, worker, readiness, fresh migration, schema, seed, and PostgreSQL integration evidence.

### E. DECISION
`DEFERRED TO: Phase 03 re-verification` because the required action is to start Docker and rerun the gate, not to change code in this audit.

### F. FIX
No code fix. Start Docker externally, then rerun the exact documented verification sequence.

### G. FILES CHANGED
- None.

### H. WHY THIS FIX?
Changing application code cannot establish infrastructure evidence.

### I. BEFORE / AFTER
BEFORE: prior report says PG18 Compose PASS; current run cannot connect to daemon.  
AFTER: current gate records BLOCKED pending Docker daemon and full PG18 rerun.

### J. VERIFICATION
COMMAND: `docker compose ... ps`; `docker compose ... exec postgres postgres --version`; API pytest.  
RESULT: Docker API connection failure; 12 PostgreSQL tests skipped.  
EXPECTED: PG18, healthy services, fresh migration, seed, and 12 integration tests pass.  
ACTUAL: Not available.

### K. REGRESSION IMPACT
No code change.

### L. DATA SAFETY
No project-local database was reset or modified.

### M. DOCUMENTATION IMPACT
Progress and final report state the blocker and rerun procedure.

### N. FINAL STATUS
DEFERRED

## FIX-006 - Deferred domain and application financial rules are represented only structurally

TYPE: DEFERRED  
SEVERITY: HIGH  
SOURCE PHASE: Phase 03  
CATEGORY: Architecture

### A. ISSUE
Transfer ownership/distinctness/currency/balance rules, refund eligibility/capping, split equality enforcement, authorization, atomic orchestration, audit events, and reconciliation are not implemented as services or complete database invariants.

### B. WHY IS THIS AN ISSUE?
The Phase 01 contract requires these behaviors for the eventual financial API, but the Phase 03 scope explicitly excludes business APIs and Phase 04 authentication.

### C. ROOT CAUSE
The repository currently contains the database foundation only; no application/domain transaction service exists.

### D. IMPACT
These rules must not be claimed implemented. They remain risks for later financial feature phases, but do not by themselves fail a database-foundation gate when explicitly deferred.

### E. DECISION
`DEFERRED TO: Phase 04+` because implementing them would expand scope beyond this final gate.

### F. FIX
No code fix. Keep the boundary classification explicit.

### G. FILES CHANGED
- None.

### H. WHY THIS FIX?
The user explicitly prohibits transaction business logic, authentication, and later-phase features in this task.

### I. BEFORE / AFTER
BEFORE: schema fields and structural tests could be mistaken for complete behavior.  
AFTER: `FINANCIAL_INVARIANT_BOUNDARIES.md` and final report label domain/application rules deferred.

### J. VERIFICATION
COMMAND: source inspection and boundary-document review.  
RESULT: only models, migration, and structural tests exist; no business routes/services.  
EXPECTED: no deferred rule is claimed implemented.  
ACTUAL: Confirmed.

### K. REGRESSION IMPACT
None; no implementation change.

### L. DATA SAFETY
No data changes.

### M. DOCUMENTATION IMPACT
Boundary and final reports retain the deferral.

### N. FINAL STATUS
DEFERRED

## FIX-007 - Historical reports contain earlier contradictory findings

TYPE: DO NOT TOUCH  
SEVERITY: LOW  
SOURCE PHASE: Phase 01 / Phase 02 / Phase 03  
CATEGORY: Documentation

### A. ISSUE
`docs/PHASE_01_02_03_COMPARISON.md` and `docs/READINESS_REPORT.md` preserve earlier states such as no implementation, PG17-only evidence, or blocked Docker.

### B. WHY IS THIS AN ISSUE?
Those statements conflict with the current repository if read as current status, but they are explicitly dated historical evidence and preserve audit provenance.

### C. ROOT CAUSE
Reports document different checkpoints in repository history.

### D. IMPACT
Deleting or rewriting them would destroy evidence. The risk is limited to readers failing to distinguish historical from current status.

### E. DECISION
`DO NOT TOUCH`: preserve historical evidence; current reports must identify the canonical current status.

### F. FIX
No file change.

### G. FILES CHANGED
- None.

### H. WHY THIS FIX?
Historical evidence is required by the audit instructions and should not be rewritten as fake current evidence.

### I. BEFORE / AFTER
BEFORE: dated historical report remains unchanged.  
AFTER: unchanged; final report points to it as historical.

### J. VERIFICATION
COMMAND: document review.  
RESULT: reports contain dated checkpoint context.  
EXPECTED: no historical evidence is silently rewritten.  
ACTUAL: Confirmed.

### K. REGRESSION IMPACT
None.

### L. DATA SAFETY
None.

### M. DOCUMENTATION IMPACT
Current final report explains provenance.

### N. FINAL STATUS
DO NOT TOUCH

## FIX-008 - Money and migration baseline are consistent

TYPE: FALSE POSITIVE  
SEVERITY: LOW  
SOURCE PHASE: Phase 03  
CATEGORY: Database

### A. ISSUE
Earlier material suggested an `INTEGER` versus `BIGINT` mismatch and multiple Alembic roots.

### B. WHY IS THIS AN ISSUE?
The claim looked current because older comparison text still describes it.

### C. ROOT CAUSE
Historical report retained pre-reconciliation findings.

### D. IMPACT
No current implementation defect was found in ORM or migration source.

### E. DECISION
`FALSE POSITIVE`: current source uses `BigInteger`/`BIGINT` and Alembic reports one head.

### F. FIX
No code fix.

### G. FILES CHANGED
- None.

### H. WHY THIS FIX?
The current source and direct Alembic output disprove the current mismatch.

### I. BEFORE / AFTER
BEFORE: historical claim of `Integer`/multiple heads.  
AFTER: current ORM/migration use `BigInteger`; `03811dfc2d31` is the sole head.

### J. VERIFICATION
COMMAND: `alembic heads`; `alembic history`; source inspection.  
RESULT: one head and BIGINT declarations.  
EXPECTED: no current type or branch mismatch.  
ACTUAL: Confirmed; live PostgreSQL catalog remains unverified in this run.

### K. REGRESSION IMPACT
None.

### L. DATA SAFETY
No data changes.

### M. DOCUMENTATION IMPACT
Final report distinguishes current source from historical claims.

### N. FINAL STATUS
FALSE POSITIVE

## FIX-009 - README misstates migration and seed availability

TYPE: REQUIRED NOW  
SEVERITY: MEDIUM  
SOURCE PHASE: Phase 03  
CATEGORY: Documentation

### A. ISSUE
`README.md` says migration and seed are intentional guard commands whose schema and business data are reserved for a later phase, although Phase 03 contains a migration and system-category seed implementation.

### B. WHY IS THIS AN ISSUE?
The setup instructions must describe the actual Phase 03 foundation. The current wording can cause developers to skip the database baseline or believe it does not exist.

### C. ROOT CAUSE
README text was not updated after the Phase 03 database foundation was added.

### D. IMPACT
Documentation and reproducibility are affected; no runtime or data behavior is changed.

### E. DECISION
`REQUIRED NOW`: correct the current setup description.

### F. FIX
Describe migration and seed as available Phase 03 foundation commands and keep later business data explicitly deferred.

### G. FILES CHANGED
- `README.md` -> correct migration/seed status wording.

### H. WHY THIS FIX?
It aligns the primary setup document with the implementation and avoids a misleading phase boundary.

### I. BEFORE / AFTER
BEFORE: migration and seed are described as guard commands reserved for a later phase.  
AFTER: migration and idempotent system-category seed are documented as Phase 03 foundation commands.

### J. VERIFICATION
COMMAND: API tests, Alembic heads/history, and source inspection.  
EXPECTED: README describes commands that exist and are testable.  
ACTUAL: To be recorded in final report.

### K. REGRESSION IMPACT
Documentation only.

### L. DATA SAFETY
No database changes.

### M. DOCUMENTATION IMPACT
This README section is updated.

### N. FINAL STATUS
FIXED

## Summary

TOTAL ISSUES: 11  
REQUIRED NOW: 5  
SAFE IMPROVEMENT: 1  
DEFERRED: 2  
DO NOT TOUCH: 1  
FIXED: 7  
BLOCKED: 0  
FALSE POSITIVE: 1  
REMAINING: 2 (Docker/PG18 evidence; deferred financial behavior)

## FIX-010 - Alembic script_location fails from project root

TYPE: REQUIRED NOW  
SEVERITY: HIGH  
SOURCE PHASE: Phase 03  
CATEGORY: Migration / Configuration

### A. ISSUE
Alembic fails when invoked from the repository root with `-c .\apps\api\alembic.ini` because it cannot find the canonical `apps/api/migrations` directory.

### B. WHY IS THIS AN ISSUE?
Migration commands must be reproducible from both the repository root and `apps/api`. A path failure occurs before Alembic can inspect the database.

### C. ROOT CAUSE
`script_location = migrations` and `prepend_sys_path = .` resolve against the current working directory instead of the directory containing `alembic.ini`. Settings also loaded `.env` relative to CWD.

### D. IMPACT
Migration execution and source-chain inspection fail from the documented project-root command. No migration history or database data is changed by this configuration failure.

### E. DECISION
`REQUIRED NOW`: root execution is part of Phase 03 reproducibility.

### F. FIX
Use `%(here)s/migrations` and `%(here)s` in `apps/api/alembic.ini`, and resolve the canonical root `.env` from the repository path in `app/core/config.py`. Keep `apps/api/migrations` as the only migration root.

### G. FILES CHANGED
- `apps/api/alembic.ini` -> deterministic config-relative migration and import paths.
- `apps/api/app/core/config.py` -> deterministic repository-root `.env` resolution.
- `docs/architecture/PHASE_01_TO_03_FIX_REGISTER.md` -> this issue and evidence.

### H. WHY THIS FIX?
Alembic's config-file directory is stable regardless of CWD, and the repository root is stable relative to the source config module. This preserves one migration directory and one environment file.

### I. BEFORE / AFTER
BEFORE: `script_location = migrations`; root command failed with `Path doesn't exist: migrations`.  
AFTER: `script_location = %(here)s/migrations`; root and `apps/api` commands resolve `apps/api/migrations`.

### J. VERIFICATION
COMMAND: `\.venv\Scripts\python.exe -m alembic -c .\apps\api\alembic.ini current`; `... heads`; `... history`; `scripts\migrate.ps1`.  
EXPECTED: config path resolves from root; source-chain commands show one head. Live upgrade may remain blocked if PostgreSQL is unavailable.  
ACTUAL: Root `heads`, `history`, and `current` pass against the host-published PostgreSQL 18.6 endpoint; the migration script passes. `apps/api` `heads/history` pass and config resolves the repository root `.env`. Final Ruff and pytest regression pass.

### K. REGRESSION IMPACT
Alembic source chain remains unchanged. API tests, Ruff, seed, worker, and mobile behavior are not changed. Root and `apps/api` execution paths are both checked.

### L. DATA SAFETY
No migration history reset, migration-file duplication, database reset, or data mutation is performed. The migration script may fail safely if the local database is unavailable.

### M. DOCUMENTATION IMPACT
Final gate report should distinguish source-chain verification from live database verification.

### N. FINAL STATUS
FIXED
