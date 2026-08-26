# Phase 01 Implementation Contract

**Project:** AI Personal Finance Assistant  
**Status:** Frozen for Phase 02 foundation  
**Scope:** Product and implementation contract only. No runtime implementation.

## 1. Contract Authority

This document consolidates the reviewed product, domain, database, API, mobile, AI, security, testing and operations blueprints. When a blueprint is ambiguous, this contract and its ADRs are authoritative for Phase 02. A later change requires an explicit ADR update.

## 2. MVP V1 Freeze

MVP V1 includes only the following capabilities:

| Area | Included capability |
|---|---|
| Authentication | Register, login, logout, refresh session, current user |
| User | Basic profile and basic preferences |
| Accounts | Create, list, detail, edit, archive/deactivate and balance |
| Categories | Default expense categories, default income categories where needed, basic custom categories |
| Transactions | Income, expense, transfer, refund, list, detail, policy-based edit, policy-based void/delete and split transaction |
| Dashboard | Total balance, income, expense, saving, recent transactions and basic category breakdown |
| Budget | Monthly budget, category budget, spending, utilization and basic warnings |
| Analytics | Monthly spending, spending by category, income versus expense, current versus previous month and basic spending trend |
| Notifications | Budget 80%, 90%, 100% thresholds and basic notification center |
| AI | Gateway abstraction only; advanced AI is disabled in MVP V1 |

MVP V1 does not include an AI assistant, AI-generated financial facts, autonomous actions or an external AI provider.

## 3. Explicitly Out of Scope

The following are P3 or later and must not enter MVP V1: bank API/open banking, investment or stock/crypto portfolio management, family or multi-user finance, advanced multi-currency, complex offline synchronization, voice assistant, model fine-tuning, complex RAG, broad autonomous agents, microservices, advanced forecasting, advanced personalization, and automated financial actions without confirmation.

Features present in the blueprints but not in MVP V1 are prioritized as follows:

| Priority | Features |
|---|---|
| P0 | Auth, User, Accounts, Categories, Transactions, Transfer, Refund, Dashboard, Budget, Basic Analytics, Basic Notifications |
| P1 | Goals, recurring transactions, receipt OCR, AI categorization, Insight, Recommendation, weekly/monthly reports |
| P2 | Natural-language financial query, AI financial assistant, forecasting, advanced anomaly detection, personalization |
| P3 | Bank integration, investment, family finance, advanced multi-currency, voice and advanced automation |

The priority is unchanged from the reviewed blueprints; the MVP boundary is narrower because this phase freezes a buildable first release.

## 4. Feature Mapping

| Feature | Domain | Database | Canonical API | Mobile surface |
|---|---|---|---|---|
| Auth | Authentication/session | `users`, `device_sessions` | `/api/v1/auth/*`, `GET /api/v1/me` | Auth stack: register, login, session state |
| User | Profile/preferences | `users`, `user_settings`, `user_preferences` | `GET /api/v1/me` and preferences endpoint when implemented | Profile/settings |
| Account | Account ownership and balance | `accounts`, `transaction_entries` | `GET/POST /api/v1/accounts`, `GET/PATCH /api/v1/accounts/{id}` | Account list/detail/edit/archive |
| Category | System and user classification | `categories` | `GET/POST /api/v1/categories` | Category picker and category management |
| Income | Positive financial event | `transactions`, `transaction_entries`, `transaction_items` | `POST /api/v1/transactions` with `type=INCOME` | Add transaction, transaction detail |
| Expense | Outflow financial event | `transactions`, `transaction_entries`, `transaction_items` | `POST /api/v1/transactions` with `type=EXPENSE` | Quick add/add expense, list/detail/edit |
| Transfer | Internal movement between accounts | One `transactions` record plus two `transaction_entries` linked by `transfer_group_id` | `POST /api/v1/transfers` | Transfer form and transaction detail |
| Refund | Reversal/return linked to original expense | `transactions.parent_transaction_id`, `transaction_entries`, `transaction_items` | `POST /api/v1/transactions/{id}/refund` | Refund action from eligible transaction detail |
| Dashboard | Read model over financial facts | Ledger tables plus optional cache/read model | `GET /api/v1/dashboard` | Home/dashboard |
| Budget | Spending limits and utilization | `budgets`, `budget_categories`, expense ledger/items | `GET/POST /api/v1/budgets`, `GET /api/v1/budgets/{id}/status` | Budget overview/detail |
| Analytics | Deterministic aggregates and comparisons | Ledger and transaction item queries | `GET /api/v1/analytics/overview`, `/spending`, `/categories` | Analytics overview and detail |
| Notification | Rule-based budget alerts and center | `notifications`, optional `notification_events` | Notification center endpoint is reserved for foundation follow-up | Notification center |

All financial reads and writes are scoped to the authenticated user on the server. Mobile is a client of the API, never the source of financial calculations.

## 5. Frozen Financial Rules

1. `TRANSFER` is neither expense nor income at user-total level.
2. A transfer requires distinct source and destination accounts belonging to the authenticated user, with a positive amount.
3. A refund must reference an eligible original transaction through `parent_transaction_id`; it reduces effective expense according to the refund policy and is not default income.
4. A split transaction requires the sum of item amounts to equal the transaction amount/outflow under the transaction currency policy.
5. Money uses integer minor units for MVP (for VND, `75000` means 75,000 VND); binary floating point is forbidden for financial values.
6. Every account, category, transaction, budget and other financial resource is ownership-checked server-side. Client-supplied `user_id` is ignored for ownership.
7. Financial writes are atomic database transactions covering the transaction record, entries, items, cached balance update and audit/event side effects that are part of the write contract.
8. The ledger represented by `transaction_entries` is the balance source of truth. `accounts.current_balance` is a cache/read optimization and must be reconcilable.
9. Deterministic financial facts, totals, balances, budget utilization and comparisons are calculated by application code/SQL/rules, never invented by an LLM.
10. AI has no direct database access. AI reads through authorized application tools/services; AI write actions require backend authorization, validation, confirmation when applicable and auditability.
11. User timezone controls day/month boundaries for reporting. Timestamps are stored with timezone; date-only periods must be resolved using the user's configured timezone.
12. Posted financial records are not silently hard-deleted. Edit/void behavior must preserve auditability; MVP may use policy-approved correction/void semantics, with reversal semantics preferred for posted records.
13. MVP uses one account currency per transaction (`transaction.currency` must match `account.currency`). Advanced currency conversion is out of scope.

## 6. API Contract Inventory

Base path: `/api/v1`. All endpoints below require authentication except registration, login and refresh as applicable.

### Authentication

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/me`

### Accounts

- `GET /api/v1/accounts`
- `POST /api/v1/accounts`
- `GET /api/v1/accounts/{id}`
- `PATCH /api/v1/accounts/{id}`

### Categories

- `GET /api/v1/categories`
- `POST /api/v1/categories`

### Transactions and Transfers

- `GET /api/v1/transactions`
- `POST /api/v1/transactions`
- `GET /api/v1/transactions/{id}`
- `PATCH /api/v1/transactions/{id}`
- `POST /api/v1/transactions/{id}/refund`
- `POST /api/v1/transfers`

### Dashboard

- `GET /api/v1/dashboard`

### Budget

- `GET /api/v1/budgets`
- `POST /api/v1/budgets`
- `GET /api/v1/budgets/{id}/status`

### Analytics

- `GET /api/v1/analytics/overview`
- `GET /api/v1/analytics/spending`
- `GET /api/v1/analytics/categories`

API conventions: versioned REST paths, authenticated financial endpoints, server-side ownership checks, request/response schemas, standard error envelope, pagination for lists, request ID, rate limiting on sensitive endpoints and `Idempotency-Key` for retryable financial writes where specified by the Phase 02 API detail contract. This phase does not define a complete OpenAPI document.

## 7. Mobile Contract

The mobile app uses Flutter with feature-first organization and the boundary `View -> ViewModel/Controller -> Use Case/Domain -> Repository -> Service/API`. UI does not calculate balances or call HTTP directly. MVP screens are auth, dashboard, accounts, add transaction, transaction list/detail, budget, analytics and notification center. Every screen must have loading, success, empty and error states where applicable.

## 8. Documentation Structure

```text
docs/
  product/
  domain/
  database/
  api/
  architecture/
    adr/
  analytics/
  ai/
  security/
  privacy/
  testing/
  operations/
```

The existing DOCX blueprints remain in place as source material. Markdown contract artifacts are canonical for implementation decisions from Phase 01 onward.

## 9. Open Risks and Required Clarifications

| Risk | Required handling before or during Phase 02 |
|---|---|
| Refund accounting can be interpreted differently | Implement one explicit effective-expense policy and test original/refund/partial-refund cases |
| Edit versus void/delete for posted records | Define allowed state transitions and audit/reversal behavior before transaction implementation |
| Split transaction amount equality | Define whether item amounts are signed or absolute and enforce at application and database boundaries where practical |
| Cached balance drift | Add reconciliation query/job design and invariant tests; cache never overrides ledger |
| Timezone and period boundaries | Store user timezone and centralize period resolution; test UTC boundary cases |
| Currency precision and VND policy | Keep MVP single-currency-per-account; reject mismatches and defer FX |
| Notification endpoint was absent from requested foundation inventory | Treat notification center as a P0 product capability, but add its canonical endpoint before the notification implementation slice |
| API details are not yet OpenAPI-complete | Phase 02 must define schemas, status codes, error codes, pagination and idempotency persistence |
| Sensitive AI/privacy behavior | Keep AI disabled in MVP runtime; define data minimization and provider policy before enabling any provider |
| README history | `README.md` now references `docs/`; no remaining Markdown reference points to the obsolete documentation root |

## 10. Phase 02 Entry Requirements

Phase 02 may start only with this contract and ADR set accepted. It must produce foundation artifacts without business features: repository skeleton, environment contract, local PostgreSQL/Redis setup, FastAPI/worker/Flutter bootstrap, health checks, initial migration strategy, seed strategy, test/CI scaffolding and documentation for running the foundation. Phase 02 must not mark financial features complete until the relevant invariants and authorization tests exist.
