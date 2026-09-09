# Phase 05 Acceptance Report

**Phase:** 05 - Accounts, Categories, and Merchants
**Status:** PASS
**Scope:** Account lifecycle, category visibility/hierarchy, merchant normalization and alias lookup

## Implementation

Backend services and APIs are implemented under `apps/api/app/accounts` and `apps/api/app/catalog`. Existing Phase 03 schema fields are used; no new migration was required. The Phase 04 `current_user` dependency controls all protected endpoints.

Flutter provides a protected account list, account creation/editing/archive flow, and category picker through the centralized authenticated API client.

## Behavioral rules

- Accounts are server-owned by the authenticated user.
- Account type is restricted to the existing enum and currency is normalized to a three-letter uppercase code.
- `current_balance` is initialized from opening balance as a cache; `transaction_entries` remains the source of truth.
- Archived accounts are hidden by default and cannot be edited except for lifecycle fields.
- Category lists contain system categories plus the current user's active custom categories.
- Category parents may be system or same-user categories; cross-user private parents are rejected.
- Merchant names and aliases use trimmed, case-folded, whitespace-collapsed normalization.
- Transaction business logic is not implemented in Phase 05.

## Tests and verification

- Phase 05 API tests: 4 passed.
- Full backend suite: 34 passed, 6 warnings.
- Ruff: PASS.
- Flutter analyzer: PASS.
- Flutter tests: PASS.
- No Phase 05 database migration was needed.

## Live verification

The rebuilt Docker API passed an authenticated smoke flow against the running PostgreSQL application database: account creation returned the opening balance cache, account listing returned the owner account, category listing returned the seeded system categories, and merchant alias lookup returned the canonical merchant. PostgreSQL 18 and Redis were healthy during the check.

The Phase 05 automated suite passed with `34 passed` backend tests, including four focused Phase 05 tests, and Flutter analyzer/tests passed. No migration or transaction business logic was added.

## Final status

**PHASE 05: PASS**

The next phase may address transaction behavior. It was not started by this task.
