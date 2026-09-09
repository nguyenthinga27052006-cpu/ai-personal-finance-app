# MASTER PROJECT STATUS

## 1. Project Information

Project: AI Personal Finance Assistant
Current Phase: Phase 16 complete; Phase 17 not started
Overall Status: **PASS WITH DOCUMENTED LIMITATIONS**
Last Verified: 2026-09-09
Current Branch: `main`
Current Commit: `b3c07aa` (`chore: commit verified phase 04-16 implementation`)
Status Commit: the documentation commit created after this implementation commit is recorded in [CHANGELOG.md](CHANGELOG.md).
Working Tree: **DIRTY during status authoring**; final cleanup requires the status/docs commit and excludes editor-local `.vscode/settings.json`.

Canonical evidence is recorded in [FULL_REGRESSION_PHASE_00_16.md](FULL_REGRESSION_PHASE_00_16.md). Historical reports remain historical and are not treated as current execution proof unless this baseline records a current command.

## 2. Phase Overview

| Phase | Status | Last Verified | Evidence | Commit | Blocker |
|---|---|---|---|---|---|
| 00 | PASS WITH DOCUMENTED LIMITATIONS | 2026-09-09 | Repository governance, rules, docs, and status audit | commit not identified; working tree dirty | No executable phase-specific gate |
| 01 | PASS WITH DOCUMENTED LIMITATIONS | 2026-09-09 | Implementation contract and architecture documentation reviewed | commit not identified | Requirements are documentary |
| 02 | PASS WITH DOCUMENTED LIMITATIONS | 2026-09-09 | Current Docker/Compose/scripts/manifests plus runtime readiness | commit not identified | Environment evidence is local and not commit-pinned |
| 03 | PASS | 2026-09-09 | Migration chain, PostgreSQL integration tests, BIGINT/schema checks, runtime readiness | commit not identified | None in current gate |
| 04 | PASS | 2026-09-09 | Auth lifecycle, refresh rotation, revocation, ownership, secure storage tests | commit not identified | None in current gate |
| 05 | PASS | 2026-09-09 | Account/catalog/merchant tests and ownership checks | commit not identified | None in current gate |
| 06 | PASS | 2026-09-09 | Financial core/invariant/PostgreSQL tests: transfer, refund, split, idempotency, rollback | commit not identified | Posted edit/void audit policy remains deferred |
| 07 | PASS | 2026-09-09 | Budget/goal calculations, timezone boundaries, refund/transfer semantics | commit not identified | None in current gate |
| 08 | PASS WITH DOCUMENTED LIMITATIONS | 2026-09-09 | Flutter gate and current Android Journey A | commit not identified | Non-fatal Amount-field hit-test warning |
| 09 | PASS | 2026-09-09 | Analytics canonical facts, dashboard, timezone and period tests | commit not identified | None in current gate |
| 10 | PASS WITH DOCUMENTED LIMITATIONS | 2026-09-09 | Deterministic insight, provenance, expiry and ownership tests | commit not identified | Deterministic engine; historical timestamp/report limitations |
| 11 | PASS WITH DOCUMENTED LIMITATIONS | 2026-09-09 | Notification rules/API/dedupe/quiet-hours/scheduler-lock tests and Journey B | commit not identified | Worker delivery is not independently end-to-end tested |
| 12 | PASS WITH DOCUMENTED LIMITATIONS | 2026-09-09 | Recommendation persistence, lifecycle, provenance and Journey coverage | commit not identified | Recurring/push delivery deferred; worker validation indirect |
| 13 | PASS WITH DOCUMENTED LIMITATIONS | 2026-09-09 | AI gateway, read-only tools, provenance, guardrails and golden tests | commit not identified | Fake provider only; no real-model evaluation |
| 14 | PASS WITH DOCUMENTED LIMITATIONS | 2026-09-09 | AI query/categorization/OCR abstraction/chat/mobile AI tests and Journey D | commit not identified | No durable chat or production OCR/object storage |
| 15 | PASS WITH DOCUMENTED LIMITATIONS | 2026-09-09 | Security regression, auth/BOLA, request limits, rate limits, threat model | commit not identified | Distributed limits, production network controls, vault rotation, dependency scan and retention workflows deferred |
| 16 | PASS WITH DOCUMENTED LIMITATIONS | 2026-09-09 | Full local gate plus current Android Journeys A, B, C, D | commit not identified | Real-model AI, coverage, performance threshold, hosted CI limitations |

Allowed status vocabulary above is limited to `PASS`, `FAIL`, `BLOCKED`, `PASS WITH DOCUMENTED LIMITATIONS`, and `NOT APPLICABLE`.

## 3. Current Blockers

No critical Phase 00-16 blocker was found in the current regression. Phase 17 and Phase 18 are not started.

## 4. Non-blocking Limitations

- Real-model semantic evaluation was not completed; current AI evaluation uses the deterministic `FakeProvider`.
- Coverage tooling is not installed, so no percentage is claimed.
- Performance measurements are a local baseline, not a production SLA or enforced threshold.
- No hosted `.github` CI workflow was found; `scripts/phase16-gate.ps1` is a local gate.
- Production distributed rate limiting, TLS/HSTS/CORS/WAF, secret vault rotation, dependency scanning, retention/export/deletion, and upload/object-storage hardening remain deployment or product work.
- Worker-specific delivery is indirectly covered; notification generation/API and scheduler locking are tested.
- Journey A passes but emits a non-fatal hit-test warning when the Amount field is outside the visible viewport.
- The implementation evidence is pinned to `b3c07aa`; status artifacts are committed separately.

## 5. Latest Full Regression

Date: 2026-09-09
Result: **PASS WITH DOCUMENTED LIMITATIONS**
Command: `scripts\\phase16-gate.ps1`
Report: [FULL_REGRESSION_PHASE_00_16.md](FULL_REGRESSION_PHASE_00_16.md)

Current results:

- Backend: `110 passed, 10 warnings`.
- Ruff and compileall: pass.
- Flutter analyze: no errors; existing `avoid_print` infos in integration/state-trace tests.
- Flutter unit/widget tests: `11 passed`.
- Debug APK build: pass.
- Web build: pass.
- Runtime `/health`: HTTP 200, `{"status":"ok"}`.
- Runtime `/ready`: HTTP 200, `{"status":"ready"}`.
- Android emulator `emulator-5554`: online, Android 16, `sdk_gphone64_x86_64`.
- Current Journey A, B, C, D: all passed sequentially.

## 6. Known Issues

- Journey A logs a non-fatal Flutter hit-test warning while entering the Amount field; the test still completes with `+1: All tests passed!`.
- Existing deprecation warnings include Starlette/httpx and Python 3.14 `datetime.utcnow()` usage.
- Historical documents contain superseded blocked claims; this directory is the canonical current baseline.

## 7. Last Fixes

- Added notification refresh when opening the Notifications tab after backend evaluation.
- Corrected Journey B threshold-title cardinality assertion for valid 80% and 90% alerts.
- Added canonical expense data to Journey D so the AI response has grounded `analytics.service` provenance.
- Stabilized Journey A auth reset, navigation, transaction dropdown interaction, and duplicate financial display assertions.
- Created this Phase 00-16 master status system.

Implementation commit: `b3c07aa`. Status/documentation commit: recorded in [CHANGELOG.md](CHANGELOG.md) after commit.

## 8. Next Phase

Phase 17 is **NOT STARTED**. Do not begin it as part of this baseline task. The next action is to preserve this evidence and separately decide whether to remediate the non-blocking limitations.

## 9. Verification Evidence

- Backend tests: `python -m pytest` through `scripts\\phase16-gate.ps1`.
- Quality: `python -m ruff check app tests`, `python -m compileall -q app ..\\worker\\app`.
- Mobile: `flutter analyze`, `flutter test`, `flutter build apk --debug`, `flutter build web`.
- Runtime: PowerShell `Invoke-WebRequest` against `/health` and `/ready`.
- Journey A: `flutter test integration_test/critical_journey_test.dart -d emulator-5554 --dart-define=API_BASE_URL=http://10.0.2.2:8000 --timeout 2m`.
- Journey B/C/D: `flutter test integration_test/phase16_journeys_test.dart -d emulator-5554 --dart-define=API_BASE_URL=http://10.0.2.2:8000 --dart-define=NOTIFICATION_WORKER_TOKEN=development-worker-token --name "Phase 16 Journey {B|C|D}: ..." --timeout 2m`.
- Final `git diff --check`: pass.
