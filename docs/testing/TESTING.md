# Phase 16 Testing Strategy

> **Historical strategy snapshot.** The current canonical status is [docs/project-status/MASTER_STATUS.md](../project-status/MASTER_STATUS.md). The blocked wording below records the pre-emulator state and is superseded by the 2026-09-09 regression evidence.

## Gate Status

**Historical status: BLOCKED.** At the time this strategy snapshot was written, the Android E2E device was unavailable. The current 2026-09-09 status is **PASS WITH DOCUMENTED LIMITATIONS**.

The official unresolved-item register is [PHASE16_UNPASSED_ITEMS.md](PHASE16_UNPASSED_ITEMS.md).

## Baseline

- START HEAD: `ff3ba5b25143edbc046622c28dd48af674a5a3a1`
- Worktree: dirty with pre-existing Phase 01-15 changes; Phase 16 changes are uncommitted.
- Backend baseline: 105 passed, 9 deprecation warnings.
- Flutter baseline: analyze PASS; 10 tests PASS.
- Runtime baseline: `/health` and `/ready` HTTP 200.
- Alembic: current/head `c93e2b7f4a18 (head)`.
- Coverage: `NOT AVAILABLE`; `python -m coverage --version` reports no module named `coverage`.
- Historical Android journey evidence is not counted as new Phase 16 E2E evidence.

## Commands

From the repository root:

```powershell
python -m pytest apps/api/tests -q
python -m ruff check apps/api/app apps/api/tests
python -m compileall -q apps/api/app apps/worker/app
```

From `apps/mobile`:

```powershell
flutter analyze
flutter test
flutter build apk --debug
flutter build web
```

Focused Phase 16 and baseline metrics:

```powershell
python -m pytest apps/api/tests/test_phase16_quality.py -q -s
```

The local blocking gate is `scripts/phase16-gate.ps1`. It does not install packages, change migrations, or use production data.

## Test Pyramid

### Unit

Existing deterministic tests cover domain calculations, budget/goal formulas, insight/recommendation rules, AI guardrails, routing, and structured output. New Phase 16 coverage is in `apps/api/tests/test_phase16_quality.py`.

### Integration

SQLite `StaticPool` fixtures isolate each test. PostgreSQL integration tests remain in `apps/api/tests/integration/` and verify database-specific schema and ledger behavior. External AI providers use `FakeProvider`; Redis/PostgreSQL runtime checks use Docker when explicitly run.

### API Contract

Phase 16 verifies unauthenticated access, invalid pagination/IDs, unknown request fields, split validation, idempotency conflict behavior, AI 401/422/429 behavior, and the 413 request guard. Pydantic request schemas reject unknown fields at transaction, refund, transfer, and item boundaries.

### E2E

Current integration files are `apps/mobile/integration_test/critical_journey_test.dart` for Journey A and `apps/mobile/integration_test/phase16_journeys_test.dart` for Journeys B/C/D. Journey A stalled on the Android run; B/C/D are implemented but the suite produced no test result before it was stopped.

| Journey | Test file/name | Executable now | Dependency | Status |
|---|---|---|---|---|
| A: Register -> Login -> Account -> Income -> Expense -> Dashboard | `critical_journey_test.dart` / `critical Phase 08 user journey` | Android target launched; test stalled without result | Supported Android emulator/device | BLOCKED / TEST STALLED |
| B: Budget -> Expense -> Alert | `phase16_journeys_test.dart` / `Phase 16 Journey B: budget expense alert` | Android suite produced no result | Supported Android emulator/device and worker token define | IMPLEMENTED / BLOCKED |
| C: Goal -> Contribution -> Progress | `phase16_journeys_test.dart` / `Phase 16 Journey C: goal contribution progress` | Android suite produced no result | Supported Android emulator/device | IMPLEMENTED / BLOCKED |
| D: AI Query -> Tool -> Answer | `phase16_journeys_test.dart` / `Phase 16 Journey D: AI query tool answer` | Android suite produced no result | Supported Android emulator/device | IMPLEMENTED / BLOCKED |

The Pixel 10 emulator became online as `emulator-5554`, but Journey A stalled and the B/C/D suite produced no test result before being stopped. Historical Android PASS evidence from Phase 08 is not counted as Phase 16 evidence. API journey coverage in existing Phase 05-14 suites does not replace current mobile E2E results.

## Fixture Strategy

Each test creates an isolated user with a UUID email, owned accounts/categories, deterministic dates and integer VND amounts. Tests use SQLite for unit/integration speed; PostgreSQL integration uses the project test database. No production data is used. Test state is discarded with the fixture database after each test.

## CI Strategy

Blocking commands are backend collection, financial invariant tests, auth/BOLA/security tests, deterministic AI tests, Ruff, compileall, Flutter analyze/tests/builds, and critical E2E when a supported device is available. CI must return non-zero for any blocking failure. Dependency scanning unavailability, coverage-tool unavailability, and real-model evaluation are documented non-blocking capability gaps, but missing critical E2E evidence blocks the Phase 16 gate.

## Flaky Test Policy

No flaky test was observed in the executed suites. The unavailable Flutter E2E is an environment capability gap, not classified as flaky and is not disabled or retried.

## Known Gaps

- No Android emulator/device is connected in this environment.
- Flutter web integration tests are unsupported by the installed Flutter tooling.
- Coverage package is unavailable; no coverage percentage is fabricated.
- Real-model semantic quality, hallucination rate, and production-provider behavior are `NOT VERIFIED` because only `FakeProvider` is configured.
- No production SLA is claimed; performance results are a local baseline only.
