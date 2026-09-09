# Phase 11 Notification Rules

## Scope

Notifications are deterministic, server-generated in-app records. PostgreSQL is the source of truth. The engine reuses Phase 07 budget calculations and Phase 09/10 Financial Facts and insights; it does not calculate a second analytics model and does not use an LLM as a trigger.

## Rules

| Notification | Source | Trigger |
|---|---|---|
| `BUDGET_THRESHOLD` | `phase07.budget_calculation` | `calculation.utilization >= 0.80`, with independent 80%, 90%, and 100% rule IDs |
| `SPENDING_SPIKE` | `phase09.financial_facts` | Existing Phase 10 anomaly insight |
| `PROJECTED_CASHFLOW_RISK` | `phase09.financial_facts` | Existing Phase 10 cashflow-risk insight |
| `GOAL_RISK` | Phase 07 goal calculation / Phase 10 insight | Existing `GOAL_RISK` insight |
| `POSITIVE_SAVING` | Phase 09/10 insight | Existing positive saving behavior insight |
| `RECURRING_PAYMENT_DUE` | None | Not available. No canonical recurring-payment source exists, so transaction history is not inferred. |

Every record includes source, source reference, rule ID, priority, severity, subject, period, evidence, deterministic dedupe key, creation time, read state, and expiry where applicable.

## Deduplication and Priority

The dedupe identity hashes user, notification rule, subject, period, and threshold. The database unique constraint is the final retry-safe guard. A scheduler retry therefore cannot create a duplicate. High severity is priority 3, medium is 2, low is 1, and informational is 0.

## Preferences

`UserPreference` is the single preference system. `smart_notifications_enabled` is the master switch; budget, anomaly, and recurring toggles gate their corresponding rules. New users receive defaults from the notification service. No client `user_id` is accepted.

## Quiet Hours

Quiet hours use the authenticated user's `User.timezone` and `HH:MM` preference values. Normal intervals use `[start, end)`. If the end is earlier than the start, the interval crosses midnight. Equal start and end means the full day. Non-critical notifications are deferred during quiet hours; `HIGH` notifications bypass quiet hours.

## Frequency Cap

`max_notifications_per_day` is counted using the user's local calendar day, stored as UTC timestamps. Duplicates are suppressed before cap evaluation. Transactional and delivery events do not count. High-severity alerts bypass the cap; normal alerts stop when the cap is reached.

## Scheduler and Delivery

The worker runs one evaluation cycle per minute and calls `/api/v1/internal/notifications/evaluate`. Redis provides a 55-second distributed lock so concurrent worker retries do not run the same cycle. A cycle evaluates active users in batch; failures are logged and retried on the next cycle. The current delivery channel is `IN_APP`. `InAppChannel` reports `stored`; `PushChannel` reports `unavailable` and never falsely reports a push as delivered.

`DELIVERY`, `OPEN`, `READ`, and `ACTION` events are persisted with result and minimal metadata. Reading through the API also records a `READ` event. Expired notifications are excluded from active lists.
