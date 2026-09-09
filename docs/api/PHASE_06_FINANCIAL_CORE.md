# Phase 06 API: Financial Core

## Scope

Phase 06 implements posted income, expenses, transfers, partial refunds, adjustments, split items, ledger entries, atomic account-cache updates, idempotency, and protected transaction reads. Dashboard, analytics, notifications, AI, and deep posted-record correction workflows remain deferred.

## Endpoints

- `POST /api/v1/transactions`
- `POST /api/v1/transfers`
- `POST /api/v1/transactions/{id}/refund`
- `GET /api/v1/transactions`
- `GET /api/v1/transactions/{id}`

All writes require the Phase 04 bearer identity and accept `Idempotency-Key`. A repeated key for the same user and equivalent request returns the existing transaction instead of creating another one. Reusing a key with a different transaction/account/amount/currency payload returns `409 idempotency_conflict`.

## Ledger policy

Transaction amounts and item amounts are positive integer minor units. Ledger entries are signed: expense/debit is negative, income/refund/credit is positive. Transfers create one transaction with a shared `transfer_group_id`, one debit entry, and one credit entry whose sum is zero. Transfers do not count as user income or expense.

`transaction_entries` is the account-balance source of truth. `accounts.current_balance` is updated atomically as a cache inside the same database transaction. Phase 06 does not provide a reconciliation job; mismatches must not be silently overwritten.

## Validation and ownership

The service validates account ownership/status/currency, category visibility and type, merchant availability, transfer account distinctness and currency, refundable amount, and split-item equality. Cross-user resources return the same unavailable/not-found boundary. The request body cannot select the caller identity.

## Refund and adjustment policy

Refunds reference a posted expense owned by the caller, must use the original account/currency, and cannot exceed the original amount minus prior refunds. Adjustments use a positive amount plus an explicit `CREDIT` or `DEBIT` entry direction and retain a posted transaction record for traceability.

## Current acceptance evidence

- Atomic rollback, ledger/cache reconciliation, and cross-user compound authorization are covered by `apps/api/tests/test_phase06_acceptance.py` and PostgreSQL lifecycle coverage in `apps/api/tests/integration/test_postgres_financial_core.py`.
- Posted transaction edit/void/reversal APIs are absent, so no hard-delete or silent posted-record mutation is provided.

## Known limitations

Posted transaction edit/void/reversal APIs, audit event tables, and richer mobile transaction editing remain deferred to later work. Dashboard and analytics now use read-only derived services.