# AGENT RULES

## General

1. Do not rewrite existing architecture without justification.
2. Read docs before changing architecture.
3. Never delete working code without explaining why.
4. Never expose secrets.
5. Never hard-code API keys.
6. Never use floating point for financial amounts.
7. Never trust user_id from request body.
8. Never allow AI direct database access.
9. Never skip tests for financial logic.
10. Never mark a task complete if tests fail.

## Financial Rules

1. Transfer is not expense.
2. Refund is not normal income.
3. Financial records require auditability.
4. Account ownership must be validated.
5. All money calculations must be deterministic.
6. Database is source of truth.

## Workflow

Before coding:
- inspect repository
- inspect relevant docs
- inspect existing code

After coding:
- run tests
- run lint/type checks
- report changed files
- report failures
- update AGENT_PROGRESS.md