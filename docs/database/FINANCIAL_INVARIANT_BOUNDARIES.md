# Financial Invariant Boundaries

**Phase:** 06 - Financial Core

This document separates what PostgreSQL guarantees from rules that remain deferred to domain and application layers. A column or relationship existing in the schema does not mean the corresponding business rule is implemented.

## Database Invariants: Enforced Now

- Primary keys identify every persisted entity.
- Foreign keys protect references between users, accounts, categories, merchants, transactions, entries, items, budgets, goals, and settings.
- User-owned rows require an ownership foreign key where the model defines `user_id`.
- Unique constraints protect user email, one preference/settings row per user, budget-category pairs, and merchant aliases.
- Required fields are non-null.
- Monetary columns use SQLAlchemy `BigInteger` and PostgreSQL `BIGINT`.
- Account balances and credit limits are non-negative.
- Transaction, item, budget, goal, and contribution amounts are positive.
- Ledger entry amounts are non-zero.
- Budget start date cannot be after end date.
- System categories have `user_id IS NULL`; user categories require an owner.
- Cascade rules protect dependent records according to the ORM foreign-key policy.

## Domain Invariants: Implemented in Phase 06

These rules require coordinated domain logic and are intentionally not implemented as application services in Phase 03.5:

- A transfer source account differs from its destination account.
- Both transfer accounts belong to the same user and use the same currency.
- Transfer debit and credit entries balance exactly.
- A refund references an eligible original transaction.
- Refund amount does not exceed the refundable amount, including partial refunds.
- Refund accounting is not treated as ordinary income.
- Split item amounts equal the parent transaction amount.
- Transaction currency matches the account currency.
- Transfer is not counted as user-level income or expense.

## Application Invariants: Implemented in Phase 06

These rules require authorization, orchestration, audit/event behavior, or operational jobs:

- User authorization and server-side ownership checks at API boundaries.
- Client-supplied `user_id` is ignored for ownership decisions.
- Financial writes are atomic across transaction, entries, items, and balance cache.
- Idempotency keys for transaction, transfer, and refund writes.
- Timezone-aware transaction timestamps are accepted and preserved.

## Current Acceptance Evidence

- `apps/api/tests/test_phase06_acceptance.py` verifies transaction, transfer, and refund rollback with controlled failure injection; no financial records, entries, items, transfer group, or cached balance remain after rollback.
- The same suite verifies mixed income/expense/refund/transfer ledger reconciliation against cached balances and explicit cross-user transfer/refund denial without side effects.
- `apps/api/tests/integration/test_postgres_financial_core.py` verifies the mixed financial lifecycle and PostgreSQL ledger-to-cache reconciliation.

## Application Invariants: Deferred

- Posted-record edit/void policy and reversal semantics.
- Audit events and immutable financial history.
- Cached balance reconciliation against the ledger.
- Timezone-aware day/month reporting boundaries for aggregates.
- Notification, dashboard, analytics, and AI behavior.
- Persisted audit-event history and posted-record correction/void workflows remain deferred; posted records are not exposed through a hard-delete endpoint.

## Balance Policy

`transaction_entries` is the financial ledger and source of truth. `accounts.current_balance` is a cached read optimization.

Future reconciliation must:

1. Calculate ledger balance from opening balance plus entries.
2. Compare it with `current_balance`.
3. Alert on mismatch.
4. Preserve evidence and auditability.
5. Never silently overwrite a mismatched balance.

No reconciliation job or account application service is implemented in Phase 03.5.

## Testing Implication

- Unit tests use SQLite for fast ORM and relationship checks.
- PostgreSQL integration tests verify database-specific types, migrations, constraints, and seed behavior.
- Neither test layer alone proves deferred domain or application invariants.
