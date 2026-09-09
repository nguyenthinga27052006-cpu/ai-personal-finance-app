# Phase 12 Recommendation Rules

## Policy

Recommendations are deterministic, explainable suggestions. They do not call an LLM, modify transactions, accounts, budgets, or goals, and they are not financial facts. PostgreSQL remains the source of truth.

## Source and Types

The engine consumes active Phase 10 insights, which already consume Phase 09 Financial Facts and Phase 07 budget/goal semantics. Mapping is:

| Source insight | Recommendation type | Action |
|---|---|---|
| `CATEGORY_DOMINANCE` | `REDUCE_CATEGORY` | Review and reduce the dominant category |
| `BUDGET_RISK` | `ADJUST_BUDGET` | Review budget against effective spending |
| `SAVING_DECLINE` / `POSITIVE_BEHAVIOR` | `INCREASE_SAVING` | Set or preserve a planned saving amount |
| `GOAL_RISK` | `GOAL_PACING` | Review required contribution pace |
| `CASHFLOW_RISK` | `CASHFLOW_PREPARATION` | Prepare for projected cashflow pressure |
| No canonical recurring source | `REVIEW_RECURRING_EXPENSE` | **DEFERRED / NOT AVAILABLE** |

No recommendation is emitted without a source insight. Each record stores the source insight ID, source metric, subject, period, reason, action, confidence, and deterministic identity.

## Ranking

The reproducible score is:

`0.30 * relevance + 0.30 * confidence + 0.20 * impact + 0.15 * urgency + 0.05 * feedback`

Relevance is currently `1.00`; confidence comes from the source insight; impact is `1.00` for budget/goal/cashflow risk and `0.70` for other suggestions; urgency is `priority / 3`; feedback starts at `0` and is `+1` for helpful or `-1` for not helpful, normalized by `10`. Scores are Decimal and quantized to four places. Ties sort by priority and deterministic ID.

## Impact and Lifecycle

`expected_impact` is always labeled `ESTIMATE`. It describes a bounded expected effect or cites the source metric; it is never presented as an actual saving. Duplicate identities are suppressed by deterministic hash plus database uniqueness. Dismissed recommendations are suppressed by status for the same identity. Expired recommendations are excluded from active results. Accepting a recommendation only records acceptance and does not perform financial writes.

Feedback and lifecycle events are user-scoped and do not alter Financial Facts or another user's ranking. The API rejects cross-user access.

## Recurring Limitation

There is no canonical recurring-payment entity or source in the repository. The engine does not infer recurrence from arbitrary transactions and does not create fake recurring records. `REVIEW_RECURRING_EXPENSE` is deferred until a canonical recurring source is implemented.