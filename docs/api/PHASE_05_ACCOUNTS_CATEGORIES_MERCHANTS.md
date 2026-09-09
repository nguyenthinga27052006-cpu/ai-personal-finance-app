# Phase 05 API: Accounts, Categories, and Merchants

## Scope

Phase 05 adds account lifecycle, visible category catalog, custom category hierarchy, and minimal merchant normalization/alias lookup. Transaction posting, ledger mutation, transfers, refunds, budgets, and analytics remain outside this phase.

## Accounts

- `GET /api/v1/accounts`
- `POST /api/v1/accounts`
- `GET /api/v1/accounts/{id}`
- `PATCH /api/v1/accounts/{id}`

All account queries are scoped by `current_user`; another user's account is indistinguishable from not found. Account types are `CASH`, `BANK`, `E_WALLET`, `CREDIT_CARD`, `SAVINGS`, and `OTHER`. Currency is normalized to a three-letter uppercase ISO-style code. Opening and cached balances are non-negative integer minor units.

Creating an account initializes `current_balance` from `opening_balance` as a cache. The transaction ledger, specifically `transaction_entries`, remains the balance source of truth. Phase 05 does not post transactions or mutate ledger entries.

Archive is a soft lifecycle transition through `PATCH` with `is_archived=true` or `status=ARCHIVED`. Archived accounts are hidden from the default list and cannot be edited except for lifecycle fields.

## Categories

- `GET /api/v1/categories`
- `POST /api/v1/categories`

The list includes active system categories and active categories owned by the authenticated user. Custom categories reject duplicate name/type pairs for the same user. The existing `parent_id` hierarchy is supported; a custom category may use a system parent or a parent owned by the same user. A user cannot attach a private category belonging to another user.

## Merchants

- `POST /api/v1/merchants`
- `POST /api/v1/merchants/{merchant_id}/aliases`
- `GET /api/v1/merchants/lookup?name=...`

Merchants are shared catalog records because the existing schema has no merchant `user_id`. Canonical names and aliases are normalized by trimming, case-folding, and collapsing whitespace. A lookup checks canonical normalized names and then normalized aliases. No transaction is created or modified by these endpoints.

## Authorization and errors

Every endpoint requires the Phase 04 bearer authentication dependency. The server derives ownership from the authenticated token subject; client-supplied user identity is not accepted. Errors use the existing structured `detail.code` and `detail.message` envelope.
