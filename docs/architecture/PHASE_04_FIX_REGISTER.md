# Phase 04 Fix Register

**Scope:** Authentication, user identity, and session security only.

## FIX-001 - Missing refresh-session persistence

TYPE: REQUIRED NOW  
SEVERITY: CRITICAL  
SOURCE PHASE: Phase 04  
CATEGORY: Database / Migration / Security

### ISSUE
The Phase 01 contract references `device_sessions`, but the Phase 03 schema has no session table. Refresh rotation and server-side logout cannot be implemented safely without persisted revocable session state.

### WHY
Refresh sessions must expire independently, rotate, detect reuse, and be revoked server-side. A client-only refresh token would violate ADR-009 and the Phase 04 security boundary.

### ROOT CAUSE
The database foundation stopped at user/profile tables and intentionally deferred authentication persistence.

### IMPACT
Without this fix, refresh replay and logout revocation cannot be enforced; refresh credentials would have no server-controlled lifecycle.

### DECISION
REQUIRED NOW.

### BEFORE / AFTER
BEFORE: no `device_sessions` table.  
AFTER: one versioned `device_sessions` table stores user binding, refresh hash, expiry, revocation, last use, and minimal device/IP metadata.

### FIX
Add one Alembic revision and ORM model. Store only a hash of the opaque refresh credential.

### FILES CHANGED
`apps/api/app/db/models/finance.py`, `apps/api/migrations/versions/7f4a9b2c1d0e_add_device_sessions.py`, `apps/api/tests/test_auth.py`, and `docs/security/SESSION_SECURITY.md`.

### TEST
PostgreSQL migration/schema/session rotation tests.

### REGRESSION
Existing Phase 01-03 migration chain must retain one head and all foundation tests must pass.

### SECURITY IMPACT
Enables revocation, rotation, reuse detection, and prevents a database leak from yielding a usable refresh secret.

### DATA SAFETY
Additive migration only; no existing rows are deleted or rewritten.

### DOCUMENTATION IMPACT
Session security, API auth, privacy, and acceptance reports.

### FINAL STATUS
FIXED

## FIX-002 - Authentication dependencies and configuration are undeclared

TYPE: REQUIRED NOW  
SEVERITY: HIGH  
SOURCE PHASE: Phase 04  
CATEGORY: Configuration / Security

### ISSUE
The API has no declared password-hashing or JWT dependency and no documented auth secret/TTL configuration.

### WHY
Security behavior must use reviewed libraries and explicit, reproducible configuration rather than ambient packages or undocumented defaults.

### ROOT CAUSE
Phase 03 foundation intentionally had no authentication implementation.

### IMPACT
Auth code would be non-reproducible and token lifetime/security assumptions would be ambiguous.

### DECISION
REQUIRED NOW.

### BEFORE / AFTER
BEFORE: no auth dependencies or auth settings.  
AFTER: declared `pwdlib[argon2]` and `PyJWT`, explicit JWT secret/issuer/audience and access/session TTL settings.

### FIX
Declare dependencies, load settings from the canonical environment file, and document safe development defaults without storing production secrets.

### FILES CHANGED
`apps/api/app/core/config.py`, `apps/api/pyproject.toml`, `.env.example`, and `docs/security/AUTHENTICATION.md`.

### TEST
Password, token, configuration, and API auth tests.

### REGRESSION
Existing API tests and Ruff must pass.

### SECURITY IMPACT
Provides battle-tested hashing/signing primitives and avoids plaintext credentials.

### DATA SAFETY
No existing data changed.

### DOCUMENTATION IMPACT
Security and environment documentation.

### FINAL STATUS
FIXED

## FIX-003 - No authenticated identity boundary or auth API

TYPE: REQUIRED NOW  
SEVERITY: HIGH  
SOURCE PHASE: Phase 04  
CATEGORY: API / Security

### ISSUE
No register/login/refresh/logout/me endpoints or `current_user` dependency exists.

### WHY
Later financial APIs need a server-derived authenticated identity and a consistent unauthorized/error contract.

### ROOT CAUSE
Only Phase 02 health/readiness routes exist.

### IMPACT
There is no protected request boundary, credential lifecycle, or user enumeration-safe auth response.

### DECISION
REQUIRED NOW.

### BEFORE / AFTER
BEFORE: no auth routes/dependency.  
AFTER: versioned auth routes, current-user dependency, protected test endpoint, and consistent safe errors.

### FIX
Implement only Phase 04 identity/session behavior; no financial business routes.

### FILES CHANGED
`apps/api/app/auth/`, `apps/api/app/main.py`, and `apps/api/tests/test_auth.py`.

### TEST
Backend API/security test matrix.

### REGRESSION
Health/readiness and Phase 01-03 tests remain unchanged and passing.

### SECURITY IMPACT
Defines authentication and authorization foundation.

### DATA SAFETY
No financial data access is added.

### DOCUMENTATION IMPACT
Auth API and security docs.

### FINAL STATUS
FIXED

## Historical / Superseded Checkpoint Summary

This checkpoint predates FIX-004 through FIX-009 and is retained for audit history. The final current summary appears at the end of this document.

TOTAL ISSUES: 9  
REQUIRED NOW: 8  
SAFE IMPROVEMENT: 0  
DEFERRED: 1  
DO NOT TOUCH: 0  
FIXED: 8  
BLOCKED: 0  
REMAINING: 0

## FIX-004 - Mobile scaffold lacks auth state and secure storage

TYPE: REQUIRED NOW  
SEVERITY: HIGH  
SOURCE PHASE: Phase 04  
CATEGORY: Mobile / Security

### ISSUE
The Flutter scaffold has only the template counter screen and no auth state machine, API client, secure token storage, or protected routing.

### WHY
The Phase 04 contract requires mobile auth lifecycle handling and prohibits ordinary local storage for refresh credentials.

### ROOT CAUSE
Mobile foundation was intentionally empty in Phase 03.

### IMPACT
Mobile cannot register/login, refresh, revoke, or protect authenticated app routes.

### DECISION
REQUIRED NOW.

### BEFORE / AFTER
BEFORE: template app only.  
AFTER: auth state, centralized client, secure storage, auth screens, and protected route behavior.

### FIX
Add the smallest feature-first auth foundation without financial screens or business APIs.

### FILES CHANGED
`apps/mobile/lib/auth/`, `apps/mobile/lib/main.dart`, `apps/mobile/test/auth_controller_test.dart`, and `apps/mobile/pubspec.yaml`.

### TEST
Flutter unit/widget auth state and route tests.

### REGRESSION
Existing Flutter tests must pass.

### SECURITY IMPACT
Refresh credential is stored only through platform secure storage.

### DATA SAFETY
No backend data mutation outside auth endpoints.

### DOCUMENTATION IMPACT
Mobile auth/security docs.

### FINAL STATUS
FIXED

## FIX-005 - Financial business authorization remains deferred

TYPE: DEFERRED  
SEVERITY: HIGH  
SOURCE PHASE: Phase 05+  
CATEGORY: Security / Architecture

### ISSUE
Resource-specific ownership checks for accounts, categories, transactions, transfers, refunds, budgets, and other financial features do not exist.

### WHY
Those features are outside Phase 04 and no financial business API may be added here.

### ROOT CAUSE
Financial application services are intentionally deferred.

### IMPACT
Future financial endpoints must use `current_user`; this phase only provides identity/authorization primitives.

### DECISION
DEFERRED TO: Phase 05+  
REASON: outside Phase 04 scope.

### FIX
No financial resource implementation.

### FILES CHANGED
None.

### TEST
Current-user identity and protected dummy endpoint only.

### REGRESSION
No financial behavior added.

### SECURITY IMPACT
The foundation rejects unauthenticated access but cannot authorize resources that do not exist yet.

### DATA SAFETY
No financial rows are modified by this deferred item.

### DOCUMENTATION IMPACT
Keep this boundary explicit in Phase 04 report.

### FINAL STATUS
DEFERRED

## Historical / Superseded Summary

This summary predates FIX-006, FIX-007, and FIX-008 and is retained for audit history. The final current summary appears at the end of this document.

TOTAL ISSUES: 8  
REQUIRED NOW: 7  
SAFE IMPROVEMENT: 0  
DEFERRED: 1  
DO NOT TOUCH: 0  
FIXED: 7  
BLOCKED: 0
REMAINING: 0

## FIX-006 - Repository root resolver crashes inside the API image

TYPE: REQUIRED NOW  
SEVERITY: HIGH  
SOURCE PHASE: Phase 04  
CATEGORY: Configuration / Deployment

### ISSUE
The rebuilt Docker API exits during import because `Path(__file__).resolve().parents[4]` is out of range for the image path `/app/app/core/config.py`.

### WHY
Phase 04 auth configuration must work in the same Docker runtime as Phase 01-03. A startup crash prevents every auth endpoint and health/readiness check from running.

### ROOT CAUSE
The repository-root resolver assumed the host source path depth and did not account for the shorter packaged image path.

### IMPACT
API startup and Docker regression fail. No database or financial behavior is affected.

### DECISION
REQUIRED NOW.

### BEFORE / AFTER
BEFORE: fixed `parents[4]` indexing, Docker import raises `IndexError`.  
AFTER: resolver finds the repository root through `.git` and falls back safely when environment variables are supplied by Docker.

### FIX
Make root discovery path-depth safe while retaining canonical host `.env` resolution.

### FILES CHANGED
- `apps/api/app/core/config.py` -> path-depth-safe environment-file discovery.

### TEST
Docker rebuild/start, `/health`, `/ready`, auth smoke test, full pytest, Ruff.

### REGRESSION
Host config tests must continue to resolve the root `.env`; Docker API must start with Compose environment variables.

### SECURITY IMPACT
Prevents auth configuration crash without weakening secret handling.

### DATA SAFETY
No data or migration changes.

### DOCUMENTATION IMPACT
Final Phase 04 report records container portability.

### FINAL STATUS
FIXED

## Historical / Superseded Checkpoint Summary

This checkpoint predates FIX-007 and FIX-008 and is retained for audit history. The final current summary appears at the end of this document.

TOTAL ISSUES: 8  
REQUIRED NOW: 7  
SAFE IMPROVEMENT: 0  
DEFERRED: 1  
DO NOT TOUCH: 0  
FIXED: 7  
BLOCKED: 0  
REMAINING: 0

## FIX-007 - Local .env database contract mismatch

TYPE: REQUIRED NOW  
SEVERITY: HIGH  
CATEGORY: Configuration

### ISSUE
`apps/api/.env` was an older local configuration and was selected before the repository-root `.env`, causing configuration tests and container readiness to use `localhost:5433` inside Docker.

### ROOT CAUSE
The settings root resolver selected the nearest `.env` instead of the repository root. The canonical root `.env` and `.env.example` define `postgres:5432/finance` for Docker and `localhost:5433/finance` for host tools.

### BEFORE / AFTER
BEFORE: nested `.env` could override the documented root database contract.  
AFTER: settings identify the repository root through `.git`; the root `.env` is canonical and the nested local file is not used.

### FILES CHANGED
`apps/api/app/core/config.py` and `.env.example`.

### WHY THIS FIX
Smallest change preserving the existing Docker/host split without creating another database or changing auth architecture.

### TESTS
Configuration tests pass; Compose API readiness and PostgreSQL integration pass.

### SECURITY IMPACT
No credential or auth behavior changed. The fix prevents services from connecting to an unintended local database.

### DATA SAFETY
No database was reset or deleted. The project-local PostgreSQL database remained isolated.

### FINAL STATUS
FIXED

## FIX-008 - Missing current PostgreSQL Phase 04 evidence

TYPE: REQUIRED NOW  
SEVERITY: HIGH  
CATEGORY: Testing / Integration

### ISSUE
Phase 04 had not executed auth integration coverage against the project-local PostgreSQL 18 service.

### ROOT CAUSE
`POSTGRES_TEST_DATABASE_URL` was not configured for the test process, so PostgreSQL tests were skipped.

### BEFORE / AFTER
BEFORE: PostgreSQL integration tests skipped.  
AFTER: repeatable Phase 04 PostgreSQL auth integration covers persistence, rotation, replay rejection, revocation, expiry, current-user resolution, and protected access.

### FILES CHANGED
`apps/api/tests/integration/test_postgres_auth.py` and `docs/security/PHASE_04_ACCEPTANCE_REPORT.md`.

### WHY THIS FIX
The test uses the documented project-local PostgreSQL 18 instance, does not use production/staging data, and uses unique test identities for repeatable runs.

### TESTS
`scripts/test.ps1`: 30 passed, 0 skipped. PostgreSQL auth integration passed. Flutter tests, Ruff, health, and readiness passed.

### SECURITY IMPACT
Provides current evidence for refresh rotation, old-token rejection, session revocation, expiry, and authenticated identity boundaries on the real database engine.

### DATA SAFETY
Only synthetic UUID-based test users were created in the project-local database. No production/staging data was used.

### FINAL STATUS
FIXED

## Historical / Superseded Summary

This summary predates FIX-009 and is retained for audit history. The final current summary appears at the end of this document.

TOTAL ISSUES: 8  
REQUIRED NOW: 7  
SAFE IMPROVEMENT: 0  
DEFERRED: 1  
DO NOT TOUCH: 0  
FIXED: 7  
BLOCKED: 0

## FIX-009 - Pytest integration collection fails because API package `app` is not importable from repository root

TYPE: REQUIRED NOW  
SEVERITY: HIGH  
SOURCE PHASE: Phase 04  
CATEGORY: Testing / Environment / Packaging

### ISSUE
Running pytest from the repository root against either PostgreSQL integration file failed during collection with `ModuleNotFoundError: No module named 'app'`.

### ROOT CAUSE
The API package root was available implicitly only when pytest was launched from `apps/api`. The API pytest configuration did not declare its package directory as an import path.

### IMPACT
Root-level integration commands could not collect or execute Phase 04 PostgreSQL tests reliably, weakening reproducibility evidence.

### DECISION
REQUIRED NOW.

### EXACT FIX
Declare `pythonpath = ["."]` in the existing `[tool.pytest.ini_options]` section of `apps/api/pyproject.toml`. The canonical `app` package and all test imports remain unchanged.

### FILES CHANGED
`apps/api/pyproject.toml` and this Fix Register entry.

### BEFORE / AFTER
BEFORE: root-level pytest collection failed with `ModuleNotFoundError: No module named 'app'`.  
AFTER: root-level and API-directory pytest invocations collect and execute the same canonical API package.

### VERIFICATION
- Root direct auth integration: PASS.
- Root direct foundation integration: PASS.
- API-directory auth integration: 1 passed.
- API-directory foundation integration: 12 passed.
- `scripts/test.ps1`: 30 passed, 0 skipped.
- `scripts/lint.ps1`: PASS.
- `flutter test`: PASS.
- `git diff --check`: PASS.

### REGRESSION
No authentication business logic, JWT logic, password hashing, database schema, migration, Flutter code, or test logic was modified.

### DATA SAFETY
No database reset or migration change was performed. Existing project-local PostgreSQL data was preserved.

### FINAL STATUS
FIXED

## Historical / Superseded Summary

This summary predates FIX-010 and is retained for audit history. The final current summary appears at the end of this document.

TOTAL ISSUES: 9  
REQUIRED NOW: 8  
SAFE IMPROVEMENT: 0  
DEFERRED: 1  
DO NOT TOUCH: 0  
FIXED: 8  
BLOCKED: 0  
REMAINING: 0

## FIX-010 - PostgreSQL integration tests lacked reproducible isolated database configuration

TYPE: REQUIRED NOW  
SEVERITY: HIGH  
SOURCE PHASE: Phase 04  
CATEGORY: Testing / Environment / Configuration

### ISSUE
Integration fixtures read `POSTGRES_TEST_DATABASE_URL` with `os.getenv()`, but the canonical local environment did not define it. Tests therefore skipped even though PostgreSQL 18 was running.

### ROOT CAUSE
Application settings load `.env` through Pydantic, but raw `os.getenv()` does not load `.env`. The integration suite also had no dedicated `finance_test` database configuration.

### IMPACT
PostgreSQL integration evidence was not reproducible and required a manual per-terminal export.

### DECISION
REQUIRED NOW.

### EXACT FIX
Create the project-local PostgreSQL 18 database `finance_test`, migrate it to Alembic head, define `POSTGRES_TEST_DATABASE_URL` only in the ignored local `.env`, document a password placeholder in `.env.example`, and add `apps/api/tests/conftest.py` to load the repository-root `.env` for pytest. The loader normalizes the test URL to the installed psycopg v3 dialect without exposing credentials.

### FILES CHANGED
`.env` (ignored local configuration), `.env.example`, `apps/api/tests/conftest.py`, and `docs/testing/DATABASE_TESTING.md`.

### BEFORE / AFTER
BEFORE: missing variable caused PostgreSQL tests to skip; manual environment export was required.  
AFTER: pytest automatically loads the canonical local configuration and targets `localhost:5433/finance_test`, separate from the application database `finance`.

### VERIFICATION
- Dedicated database confirmed: `finance_test`.
- Test schema migrated to `7f4a9b2c1d0e (head)`.
- Root auth integration: 1 passed.
- Root foundation integration: 12 passed.
- API-directory integration: 13 passed.
- `scripts/test.ps1`: 30 passed, 0 skipped.
- `scripts/lint.ps1`: PASS.
- `flutter test`: PASS.
- `git diff --check`: PASS.
- Docker PostgreSQL 18 and Redis: healthy.

### REGRESSION
The development database `finance` was not reset or used for integration tests. No authentication, JWT, password hashing, schema, migration, or financial business logic was modified.

### DATA SAFETY
Integration tests use only the isolated project-local `finance_test` database and synthetic test identities. Production and staging data are not used.

### DOCUMENTATION IMPACT
Database testing documentation now distinguishes Docker application DB, host application DB, and host integration test DB.

### FINAL STATUS
FIXED

## Final Current Summary

TOTAL ISSUES: 10  
REQUIRED NOW: 9  
SAFE IMPROVEMENT: 0  
DEFERRED: 1  
DO NOT TOUCH: 0  
FIXED: 9  
BLOCKED: 0  
REMAINING: 0
