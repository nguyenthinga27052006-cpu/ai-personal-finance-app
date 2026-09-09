# Phase 17 AI Cost Control

## Controls

- Existing per-user/IP AI rate limiting remains enabled.
- New in-process per-user/per-feature usage budget defaults to 100 units per daily window.
- Budget exhaustion returns HTTP 429 with `ai_budget_exceeded` and `Retry-After`.
- Provider retries must be bounded by `AI_MAX_RETRIES`; no unbounded retry loops.
- `AI_TIMEOUT_SECONDS`, `AI_DAILY_BUDGET_UNITS` and model routing are configuration values.
- Record provider request count, feature, latency, fallback and estimated units without logging prompts or secrets.

The local budget implementation is **LOCALLY VERIFIED**. Shared/distributed accounting and provider token billing are **NOT VERIFIED**.

## Routing policy

Cheap/deterministic routing: classification, categorization and simple summaries. Stronger approved models: complex explanations only after budget and privacy policy checks. Budget exhaustion must fail safely without financial writes.
