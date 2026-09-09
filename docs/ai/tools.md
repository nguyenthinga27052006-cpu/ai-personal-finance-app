# Phase 13 AI Tools

## Registry

Only definitions registered by `build_read_only_registry()` are exposed. Each definition has a name, description, input schema, output contract, capability, authorization requirement, and canonical handler.

The registered read-only tools are:

- `get_current_balance`
- `get_monthly_income`
- `get_monthly_expense`
- `get_category_spending`
- `get_spending_trend`
- `get_budget_status`
- `get_goal_progress`
- `get_recent_transactions`
- `get_insights`

Tool schemas deliberately omit `user_id`. The registry injects the authenticated user from `ExecutionContext` and rejects arguments that try to provide ownership fields. Every result includes provenance with source, period/as-of information, calculation type, and deterministic status.

## Canonical service boundary

Tools delegate to existing services:

- analytics tools use `app.analytics.service.build_overview`
- balance uses `app.accounts.service.list_accounts`
- budget and goal tools use `app.budget_goals.service`
- recent transactions use `app.transactions.service.list_transactions`
- insights use `app.insights.service.active_insights`

No AI tool contains raw SQL, direct table access, duplicated financial calculations, or financial writes.

## Writes

`WriteTool` is an abstraction-only boundary. It always raises `WriteToolsDisabledError` in Phase 13. Confirmation, authorization, validation, idempotency, and auditability remain required extension points for a later phase.
