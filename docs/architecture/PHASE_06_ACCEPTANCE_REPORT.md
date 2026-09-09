# Phase 06 Acceptance Report

**Phase:** 06 - Financial Core
**Status:** PASS

## Migration

Migration `9c2d7e4f1a6b_add_transaction_idempotency.py` adds nullable `transactions.idempotency_key` and a per-user uniqueness constraint. It follows `7f4a9b2c1d0e` and preserves one Alembic head. It was applied to the development and isolated integration databases without destructive reset.

## Delivered

- Atomic income and expense creation with signed ledger entries.
- Atomic two-account transfers with balanced entries and shared transfer group.
- Refunds linked to eligible expenses with partial-refund cap.
- Explicit-direction adjustments.
- Split transaction items with exact parent amount validation.
- Idempotent transaction, transfer, and refund writes.
- Idempotency-key reuse with a different request payload is rejected with a conflict.
- Ownership, account status, currency, category, merchant, and pagination/filter validation.
- Mobile quick expense, income, transfer, transaction list, and transaction detail view.

## Verification so far

- Dedicated financial-core and invariant tests: 9 passed.
- PostgreSQL financial-core integration: passed on PostgreSQL 18 `finance_test`.
- Full backend suite: 43 passed, 0 skipped, 6 warnings.
- Ruff: passed.
- Flutter analyzer: passed.
- Flutter tests: passed.

## Runtime verification

The Docker API was rebuilt with the financial-core routes. PostgreSQL 18 and Redis were healthy; `/health` returned `ok` and `/ready` returned `ready`. Authenticated financial-core smoke covered account-backed expense/income/transfer behavior and the transaction read surface.

## Remaining limitations

Deferred limitations are posted-record correction/void workflows, reconciliation jobs, audit event tables, aggregate analytics, and richer mobile editing. These are explicit follow-up boundaries and do not block the Phase 06 critical financial-core gate.

## Technical Debt / Non-Blocking Warnings

**Phase 06 status: PASS**

The verification run reported `43 passed, 6 warnings`. These warnings are non-blocking technical debt and do not change the Phase 06 status.

### TODO #1 - TestClient / httpx deprecation

- Review FastAPI/Starlette `TestClient` dependency compatibility.
- Determine the appropriate `httpx` version or test API migration.
- Update dependencies and/or test setup only when safe.
- Re-run the complete test suite after cleanup.

The warning currently originates from the installed dependency path under `.venv\\Lib\\site-packages\\fastapi\\testclient.py`; dependency code must not be edited directly.

### TODO #2 - `datetime.utcnow()` deprecation

- Review project and dependency usage of naive UTC datetime handling.
- Migrate application-owned datetime usage to timezone-aware UTC datetimes where appropriate.
- Do not modify dependency code under `.venv\\Lib\\site-packages`.
- Re-run the complete test suite after cleanup.

The current warnings are observed through SQLAlchemy internals while exercising existing model defaults. This is future cleanup work, not a financial-core acceptance failure.

### Acceptance rule

These warnings are technical debt only. They do not block Phase 06. Phase 06 remains PASS while functionality, automated tests, PostgreSQL integration, and the Alembic head remain passing.

## Final status

**PHASE 06: PASS**

Critical financial-core tests passed. No later business phase was started.