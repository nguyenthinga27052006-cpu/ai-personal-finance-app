# FULL REGRESSION - PHASE 00 -> PHASE 16

## Regression Date

2026-09-09

## Repository Commit

Branch: `main`
Implementation commit: `b3c07aa` (`chore: commit verified phase 04-16 implementation`)
Regression execution commit: `b3c07aa`
Final repository HEAD after status-only commits: final documentation consistency commit; exact value is recorded in the final report.
Working tree at final baseline: **CLEAN**
The regression evidence is pinned to the implementation commit; it was not rerun on the final documentation commits.

## Environment

- OS: Windows
- Python: 3.14.7
- Flutter: 3.47.1 stable
- Dart: 3.13.1
- Docker: 29.7.2
- Docker Compose: v5.4.0
- Backend: FastAPI application at `http://localhost:8000`
- Database/runtime readiness: `/ready` returned HTTP 200
- Redis/runtime readiness: included by `/ready`
- Emulator/device: `emulator-5554`, Android 16, `sdk_gphone64_x86_64`
- Browser: Flutter web build only; no browser E2E claimed

## Summary

| Phase | Verification | Status | Evidence |
|---|---|---|---|
| 00 | Repository governance and documentation audit | PASS WITH DOCUMENTED LIMITATIONS | Rules, progress, README, docs and Git identity reviewed |
| 01 | Contract and architecture documents | PASS WITH DOCUMENTED LIMITATIONS | Implementation contract and ADRs reviewed |
| 02 | Environment/config/build/runtime | PASS WITH DOCUMENTED LIMITATIONS | Gate, tool versions, `/health`, `/ready` |
| 03 | Migrations/schema/PostgreSQL tests | PASS | Full pytest and PostgreSQL integration tests |
| 04 | Auth/session/security tests | PASS | Auth lifecycle, rotation, revocation and ownership tests |
| 05 | Accounts/catalog/merchant tests | PASS | `test_phase05.py` and full suite |
| 06 | Financial core/invariants | PASS | Transfer/refund/split/idempotency/rollback/ownership tests |
| 07 | Budgets/goals | PASS | `test_phase07.py`, Journey B and C |
| 08 | Flutter core and critical Android flow | PASS WITH DOCUMENTED LIMITATIONS | Flutter gate and Journey A; non-fatal hit-test warning |
| 09 | Analytics/dashboard | PASS | Analytics/dashboard tests and Journey A dashboard assertions |
| 10 | Insights | PASS WITH DOCUMENTED LIMITATIONS | Insight provenance/expiry/ownership tests |
| 11 | Notifications | PASS WITH DOCUMENTED LIMITATIONS | Notification tests and Journey B |
| 12 | Recommendations | PASS WITH DOCUMENTED LIMITATIONS | Recommendation lifecycle/provenance tests |
| 13 | AI gateway/tools/guardrails | PASS WITH DOCUMENTED LIMITATIONS | AI platform tests; FakeProvider only |
| 14 | User-facing AI features | PASS WITH DOCUMENTED LIMITATIONS | AI feature tests and Journey D |
| 15 | Security/privacy hardening | PASS WITH DOCUMENTED LIMITATIONS | Security regression and threat/data docs |
| 16 | Full regression and current A-D closure | PASS WITH DOCUMENTED LIMITATIONS | Local gate plus current A/B/C/D |

## Detailed Results

### PHASE 00

Objective: Establish repository governance and a truthful status baseline.
Method: DOCUMENT VERIFICATION and STATIC VERIFICATION.
Command: `git status --short; git branch --show-current; git log -n 10 --oneline; git diff --check`.
Result: `main`, regression execution commit `b3c07aa`; final HEAD the final documentation consistency commit; final worktree clean; diff check passes.
Evidence: Rules/progress/README/docs inventory completed.
Status: PASS WITH DOCUMENTED LIMITATIONS.
Limitation: No executable phase-specific gate.

### PHASE 01

Objective: Freeze product/architecture/financial contract.
Method: DOCUMENT VERIFICATION.
Command: Documentation inventory and source/test cross-check.
Result: Contract and ADRs are present and reflected by implementation.
Evidence: `docs/IMPLEMENTATION_CONTRACT.md`, `docs/architecture/adr/`.
Status: PASS WITH DOCUMENTED LIMITATIONS.
Limitation: Documentary phase.

### PHASE 02

Objective: Verify runnable development foundation.
Method: BUILD and RUNTIME VERIFICATION.
Command: `scripts\\phase16-gate.ps1`; `Invoke-WebRequest http://localhost:8000/health`; `Invoke-WebRequest http://localhost:8000/ready`.
Result: Gate passes; both endpoints return HTTP 200.
Evidence: Python 3.14.7, Flutter 3.47.1, Dart 3.13.1, Docker 29.7.2, Compose v5.4.0.
Status: PASS WITH DOCUMENTED LIMITATIONS.
Limitation: Local environment; status documentation was committed separately after the implementation baseline.

### PHASE 03

Objective: Verify database foundation.
Method: EXECUTABLE TEST.
Command: `scripts\\phase16-gate.ps1`.
Result: PostgreSQL integration/schema/seed tests are included in `110 passed`.
Evidence: BIGINT, foreign keys, ownership, migration and seed idempotency tests.
Status: PASS.

### PHASE 04

Objective: Verify authentication and sessions.
Method: EXECUTABLE TEST.
Command: `scripts\\phase16-gate.ps1`.
Result: Auth tests pass.
Evidence: Register/login, refresh rotation, old-token rejection, logout revocation, invalid/expired token and disabled-user tests.
Status: PASS.

### PHASE 05

Objective: Verify accounts, categories and merchants.
Method: EXECUTABLE TEST.
Command: `scripts\\phase16-gate.ps1`.
Result: Phase 05 tests pass within 110 backend tests.
Evidence: Account lifecycle/ownership, category visibility and merchant normalization tests.
Status: PASS.

### PHASE 06

Objective: Verify financial invariants and atomic writes.
Method: EXECUTABLE TEST.
Command: `scripts\\phase16-gate.ps1`.
Result: Full backend suite passes.
Evidence: Transfer neutrality, refund bounds, split equality, ownership, idempotency and rollback tests.
Status: PASS.

### PHASE 07

Objective: Verify budget and goal calculations.
Method: EXECUTABLE TEST and CURRENT E2E.
Command: `scripts\\phase16-gate.ps1`; current Journey B/C commands.
Result: Backend tests and Journeys B/C pass.
Evidence: Budget ignores transfers/income, refunds apply; Journey C renders 4000 current, 6000 remaining, 40%.
Status: PASS.

### PHASE 08

Objective: Verify Flutter core and dashboard journey.
Method: BUILD VERIFICATION and CURRENT ANDROID E2E.
Command: `flutter analyze`; `flutter test`; `flutter build apk --debug`; `flutter build web`; Journey A command.
Result: Analyze no errors, Flutter 11 passed, APK/web pass, Journey A `+1: All tests passed!`.
Evidence: Register -> login -> account -> income -> expense -> dashboard.
Status: PASS WITH DOCUMENTED LIMITATIONS.
Limitation: Non-fatal Amount-field hit-test warning.

### PHASE 09

Objective: Verify canonical analytics.
Method: EXECUTABLE TEST.
Command: `scripts\\phase16-gate.ps1`.
Result: Analytics/dashboard tests pass.
Evidence: Canonical facts, period validation, timezone boundaries, currency and ownership tests.
Status: PASS.

### PHASE 10

Objective: Verify deterministic insights.
Method: EXECUTABLE TEST.
Command: `scripts\\phase16-gate.ps1`.
Result: Insight tests pass.
Evidence: Traceability, ranking, expiry, no-evidence fail-closed and ownership tests.
Status: PASS WITH DOCUMENTED LIMITATIONS.
Limitation: Deterministic/historical report limitations.

### PHASE 11

Objective: Verify notifications.
Method: EXECUTABLE TEST and CURRENT ANDROID E2E.
Command: `scripts\\phase16-gate.ps1`; Journey B command with worker token.
Result: Notification tests and Journey B pass.
Evidence: Live worker evaluation creates 80%/90% alerts; app displays the title after tab refresh.
Status: PASS WITH DOCUMENTED LIMITATIONS.
Limitation: Push delivery is not in scope.

### PHASE 12

Objective: Verify recommendation lifecycle.
Method: EXECUTABLE TEST and STATIC VERIFICATION.
Command: `scripts\\phase16-gate.ps1`.
Result: Recommendation tests pass.
Evidence: Candidate provenance, lifecycle events, feedback and cross-user isolation.
Status: PASS WITH DOCUMENTED LIMITATIONS.
Limitation: Recurring/push delivery deferred.

### PHASE 13

Objective: Verify AI gateway/tool security.
Method: EXECUTABLE TEST and STATIC VERIFICATION.
Command: `scripts\\phase16-gate.ps1`; `test_ai_platform.py` within full suite.
Result: AI platform tests pass.
Evidence: Tool allowlists, injected ownership, raw SQL/write rejection, prompt/secret redaction and provenance.
Status: PASS WITH DOCUMENTED LIMITATIONS.
Limitation: FakeProvider only.

### PHASE 14

Objective: Verify user-facing AI features.
Method: EXECUTABLE TEST and CURRENT ANDROID E2E.
Command: `scripts\\phase16-gate.ps1`; Journey D command.
Result: AI feature tests and Journey D pass.
Evidence: Grounded `monthly_expense` -> `get_monthly_expense` -> `analytics.service`, unsupported request and UI answer.
Status: PASS WITH DOCUMENTED LIMITATIONS.
Limitation: Temporary chat and OCR abstraction.

### PHASE 15

Objective: Verify security/privacy hardening.
Method: EXECUTABLE TEST and DOCUMENT VERIFICATION.
Command: `scripts\\phase16-gate.ps1`; security-related tests included in full suite.
Result: Pass.
Evidence: Auth/BOLA, request-size 413, headers, AI error mapping, rate limiting, token storage and threat/data docs.
Status: PASS WITH DOCUMENTED LIMITATIONS.
Limitation: Production deployment controls and dependency scan not verified.

### PHASE 16

Objective: Full repository regression and current E2E closure.
Method: COMBINATION: EXECUTABLE TEST, BUILD, RUNTIME and DOCUMENT VERIFICATION.
Commands: `scripts\\phase16-gate.ps1`; current A/B/C/D Flutter commands; health/readiness; `git diff --check`.
Result: 110 backend tests, 11 Flutter tests, APK/web builds, health/readiness, and Journeys A-D pass.
Evidence: A/B/C/D current Android results each ended with `+1: All tests passed!`; A logs one non-fatal hit-test warning.
Status: PASS WITH DOCUMENTED LIMITATIONS.
Limitations: Real-model evaluation, coverage, production performance thresholds, hosted CI.

## Financial Invariants

Current tests verify:

1. Transfers are excluded from expense and preserve total wealth.
2. Refunds reverse eligible expense only and reject over-refund/duplicate cases.
3. Split item amounts equal the transaction amount.
4. Account, transaction, category, budget, goal and AI ownership are server-derived and tested.
5. Financial amounts use integer/BIGINT representations.
6. Financial writes and ledger/balance updates roll back atomically.
7. Idempotency protects repeated and conflicting requests.

## Authorization Regression

Cross-user account, transaction, budget, goal, notification, recommendation and AI-tool access tests pass. AI ownership injection and arbitrary `user_id` attempts are rejected.

## AI Verification

Deterministic golden evaluation passes 7/7 cases with `FakeProvider`. Real-model evaluation is **not completed** and is not claimed as PASS.

## Failure Evidence and Fixes

- Journey B initially reproduced stale notification UI: API contained `Budget alert: Phase 16 Budget`, app initially rendered zero matching widgets. Root cause: ViewModel loaded only at app startup. Fix: refresh on Notifications tab selection; retest passed.
- Journey B then exposed two valid same-title threshold rows (80% and 90%). Fix: test assertion changed from exactly one to at least one.
- Journey D initially had no expense, so API returned intentional insufficient-data with `source: null`. Fix: test fixture creates a canonical expense; retest passed.
- Journey A initially had persisted auth and selector/cardinality assumptions. Fixes were scoped to test setup/selectors/assertions; clean retest passed.

## Final Regression Verdict

**PASS WITH DOCUMENTED LIMITATIONS**

No current critical blocker remains for Phase 00-16. The historical Phase 16 gate predates Phase 17; current Phase 17 and Phase 18 status are recorded in the separate Phase 17 documents.

## Phase 17 Preservation Note

Phase 17 changes were validated against the existing Phase 00-16 regression baseline. This historical report remains a Phase 00-16 report; Phase 17 evidence is recorded separately in `docs/phase17/PHASE17_REGRESSION.md`.
