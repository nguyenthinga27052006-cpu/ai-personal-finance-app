# Phase 16 Limitations Register

## Purpose

This is the official register for Phase 16 limitations and items that remain unverified. Current critical E2E items are no longer unpassed; the canonical overall status is in [docs/project-status/MASTER_STATUS.md](../project-status/MASTER_STATUS.md).

## Current Phase Status

**Phase 16: PASS WITH DOCUMENTED LIMITATIONS**

No critical E2E blockers remain. Current Android execution completed Journeys A, B, C, and D successfully on `emulator-5554`.

## Limitations and Evidence Items

| ID | Requirement | Current status | Blocking? | Evidence / reason | Required next action |
|---|---|---|---|---|---|
| P16-E2E-A | Register -> Login -> Account -> Income -> Expense -> Dashboard | PASS | No | Current `critical_journey_test.dart` run passed on `emulator-5554`. | None. |
| P16-E2E-B | Budget -> Expense -> Alert | PASS | No | Current `phase16_journeys_test.dart` Journey B run passed on `emulator-5554`, including live worker evaluation and notification UI. | None. |
| P16-E2E-C | Goal -> Contribution -> Progress | PASS | No | Current `phase16_journeys_test.dart` Journey C run passed on `emulator-5554`. | None. |
| P16-E2E-D | AI Query -> Tool -> Answer | PASS | No | Current `phase16_journeys_test.dart` Journey D run passed on `emulator-5554` with canonical expense grounding. | None. |
| P16-AI-EVAL | Golden dataset field-level evaluation | RESOLVED — deterministic contract PASS | No | `test_phase16_quality.py -q -s` evaluated 7/7 cases with per-case report: intent, tool, args, status, grounding, provenance, numeric facts, forbidden claims, safety, insufficient data, unsupported request, ownership injection, and malformed output. | Keep real-model evaluation separate and NOT VERIFIED. |
| P16-AI-REAL | Real-model semantic evaluation | NOT VERIFIED | No | Current provider is `FakeProvider`; production-model semantic accuracy cannot be concluded. | Evaluate only when a real provider/model is actually configured and executed. |
| P16-COVERAGE | Coverage measurement | NOT AVAILABLE | No* | Coverage tooling is unavailable; `python -m coverage --version` reports no module named `coverage`. | Report coverage when tooling exists; do not fabricate a percentage. |
| P16-PERF | Performance regression threshold | BASELINE ONLY | No* | p50/p95/p99 measurements exist, but no threshold is enforced as a regression gate. | Keep baseline-only or define a justified local threshold, explicitly not a production SLA. |
| P16-CI | Actual CI workflow / gate | LOCAL GATE ONLY / ACTUAL CI NOT IMPLEMENTED | No* | `scripts/phase16-gate.ps1` exists and passes executable checks; no `.github` workflow was found. | Keep local gate and document actual hosted CI as not implemented. |

`*` These items are not blockers under the Phase 16 acceptance policy.

## Journey Coverage Audit

| Journey | Current file/test | Executable in current environment | Status |
|---|---|---|---|
| A: Register -> Login -> Account -> Income -> Expense -> Dashboard | `apps/mobile/integration_test/critical_journey_test.dart`, `critical Phase 08 user journey` | Yes; `emulator-5554` | PASS |
| B: Budget -> Expense -> Alert | `phase16_journeys_test.dart` / `Phase 16 Journey B: budget expense alert` | Yes; `emulator-5554` | PASS |
| C: Goal -> Contribution -> Progress | `phase16_journeys_test.dart` / `Phase 16 Journey C: goal contribution progress` | Yes; `emulator-5554` | PASS |
| D: AI Query -> Tool -> Answer | `phase16_journeys_test.dart` / `Phase 16 Journey D: AI query tool answer` | Yes; `emulator-5554` | PASS |

Historical Phase 08 Android PASS is not counted as current Phase 16 evidence.

## Already Passing

- Backend full suite: `110 passed` in the required final command.
- Financial invariant coverage: PASS for executed evidence.
- API and security regression coverage: PASS for executed evidence.
- Ruff and compileall: PASS.
- Flutter analyze: PASS.
- Flutter tests: 11 passed.
- APK and web builds: PASS.
- Runtime `/health`: HTTP 200.
- Runtime `/ready`: HTTP 200.
- Deterministic AI evaluation: 7/7 cases PASS with `FakeProvider`, including field-level report output.

## Important Limitations

### FakeProvider

`FakeProvider` supports deterministic AI platform checks only. It cannot establish real-model semantic accuracy, hallucination rate, or production-model quality.

### Historical Evidence

The Phase 08 Android E2E PASS is historical evidence and is not current Phase 16 execution evidence.

### Coverage

`NOT AVAILABLE` due missing tooling does not imply a financial correctness failure.

### Performance

The measurements are a baseline only, not a production SLA or enforced regression threshold.

### CI

The local PowerShell gate is not an actual hosted CI workflow.

## Reproduction Commands

```powershell
# Current required backend/mobile validation
python -m pytest apps/api/tests -q
python -m ruff check apps/api/app apps/api/tests
python -m compileall -q apps/api/app apps/worker/app
Set-Location apps/mobile
flutter analyze
flutter test
flutter build apk --debug
flutter build web

# Local automated gate
Set-Location ..\..
scripts\phase16-gate.ps1

# Journey A, when a supported Android device/emulator is available
Set-Location apps/mobile
flutter test integration_test/critical_journey_test.dart -d <android-device> --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

## Closure Rule

Phase 16 critical acceptance criteria are satisfied. Remaining entries in this register are documented limitations, not blockers.

Phase 17 and Phase 18 remain `NOT STARTED` until Phase 16 is closed.
