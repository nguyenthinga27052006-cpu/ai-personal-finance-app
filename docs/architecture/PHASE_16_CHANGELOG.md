# Phase 16 Changelog

## Tests

- Added Phase 16 financial/API contract tests in `apps/api/tests/test_phase16_quality.py`.
- Added deterministic AI golden dataset `docs/testing/ai_golden_v1.json` and contract validation.
- Added reproducible local performance baseline for financial facts, dashboard, AI query, and transaction write paths.
- Enforced unknown-field rejection for transaction, transfer, refund, and transaction-item request schemas.

## Tooling

- Added `scripts/phase16-gate.ps1` as the local CI-equivalent blocking gate.
- No dependency installation or package cache change.

## Documentation

- Added `docs/testing/TESTING.md`.
- Added `docs/testing/TEST_MATRIX.md`.
- Added `docs/testing/FINANCIAL_INVARIANTS.md`.
- Added `docs/testing/AI_EVALUATION.md`.
- Added the official unresolved-items register `docs/testing/PHASE16_UNPASSED_ITEMS.md`.
- Added `docs/architecture/PHASE_16_CLOSURE_REPORT.md`.
- Added current Android integration harness `apps/mobile/integration_test/phase16_journeys_test.dart` for Journeys B, C, and D.
- Replaced schema-only golden validation with a 7-case deterministic field-level evaluator and per-case report.
- Added Phase 16 acceptance report and final checkpoint.

## Database and Financial Core

- No migration added or applied.
- No financial semantic behavior was changed.
- Existing financial implementation was tested; request-schema strictness was corrected for API contract compliance.

## Gate

- Status: BLOCKED because the critical Flutter E2E journey was unavailable in this environment.
- Register: `P16-E2E-A` through `P16-CI` remain explicitly tracked with PASS, PARTIAL, NOT VERIFIED, NOT AVAILABLE, or BLOCKED status.
- Current Android execution: emulator online, but Journey A stalled and B/C/D produced no completed test result.
- Phase 17/18: not implemented or opened.
