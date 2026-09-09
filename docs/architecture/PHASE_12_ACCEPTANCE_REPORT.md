# Phase 12 Acceptance Report

## Verdict

**PHASE 12 = PASS WITH NON-BLOCKING ISSUES**

The deterministic Recommendation Engine and personalized saving suggestions are implemented and verified for the current scope. This does not claim production readiness. Implementation stops at Phase 12; Phase 13 is not implemented.

## Objective and Scope

Phase 12 converts Phase 10 insights, backed by Phase 09 Financial Facts and Phase 07 budget/goal semantics, into explainable `RecommendationCandidate` records. It provides deterministic ranking, persistence, lifecycle actions, feedback, authenticated APIs, and mobile rendering.

No LLM, AI Gateway, provider, chatbot, AI tool, or automatic financial write was added.

## Recommendation Types

- `REDUCE_CATEGORY`: mapped from `CATEGORY_DOMINANCE`.
- `ADJUST_BUDGET`: mapped from `BUDGET_RISK`.
- `INCREASE_SAVING`: mapped from `SAVING_DECLINE` or `POSITIVE_BEHAVIOR`.
- `GOAL_PACING`: mapped from `GOAL_RISK`.
- `CASHFLOW_PREPARATION`: mapped from `CASHFLOW_RISK`.
- `REVIEW_RECURRING_EXPENSE`: deferred and never emitted without a canonical recurring source.

## Source and Traceability

The source chain is `Recommendation -> Phase 10 Insight -> source metric -> Phase 09 Financial Facts -> period/evidence`. Each persisted recommendation stores source insight ID, source metric, subject, period, reason, action, confidence, expected impact, deterministic ID, and dedupe key. Missing insight evidence produces no recommendation.

## Ranking

The deterministic score is:

`0.30 * relevance + 0.30 * confidence + 0.20 * impact + 0.15 * urgency + 0.05 * feedback`

Relevance is `1.00`; confidence comes from the insight; impact is `1.00` for budget/goal/cashflow risks and `0.70` otherwise; urgency is `priority / 3`; feedback is `+1` helpful or `-1` not helpful, normalized by `10`. Decimal arithmetic is quantized to four places. Ties use priority and deterministic ID.

## Expected Impact

Every expected impact is explicitly prefixed `ESTIMATE`. Estimates cite source evidence or describe a bounded expected effect. They are not actual financial facts and do not change financial records.

## Deduplication, Suppression, and Expiry

The dedupe identity hashes user, recommendation type, subject, period, and source insight. A database uniqueness constraint is the final retry guard. Dismissed and accepted records are not returned as active recommendations for the same identity. Expired records are excluded. Feedback changes only the user's recommendation feedback score.

## Lifecycle and API

Authenticated endpoints:

- `GET /api/v1/recommendations`
- `GET /api/v1/recommendations/{id}`
- `POST /api/v1/recommendations/{id}/accept`
- `POST /api/v1/recommendations/{id}/dismiss`
- `POST /api/v1/recommendations/{id}/feedback`
- `POST /api/v1/recommendations/{id}/events?event_type=SHOWN|ACTION_OUTCOME`

Accept is a recorded decision only; it does not update budget, transaction, goal, or account data. Events store minimal product analytics and are user-isolated.

## Mobile

The existing View -> ViewModel -> Repository -> API boundary now renders recommendation cards with reason, suggested action, `ESTIMATE` impact, and accept/dismiss/helpful actions. Loading, empty, and shared error states are provided. Score and financial metrics are not computed on mobile.

## Database / Worker

Migration `c93e2b7f4a18` adds `recommendations` and `recommendation_events`, with user ownership, indexes, and unique dedupe identity. The worker invokes a recommendation evaluation endpoint using the existing Redis-backed scheduling pattern and a separate distributed lock. Retries are safe because materialization is deterministic and database-deduplicated.

## Recurring Expense

**DEFERRED / NOT AVAILABLE.** The repository has no canonical recurring-payment source. The engine does not infer recurrence from raw transaction history and does not create recurring entities for recommendations.

## Cross-Phase Compatibility

- Phase 07: goal/budget evidence is consumed through existing services and insight output.
- Phase 09: Financial Facts remain the canonical financial source.
- Phase 10: insights are the detection and evidence source; no second analytics engine exists.
- Phase 11: recommendation events and worker evaluation are separate from notification rules; no new notification engine was created.

## Tests and Validation

- `python -m pytest apps/api/tests/test_recommendations.py -q`: 4 passed.
- `python -m pytest apps/api/tests -q`: 78 passed, 9 inherited deprecation warnings.
- `python -m ruff check apps/api/app apps/api/tests apps/api/migrations apps/worker/app`: PASS.
- `Push-Location apps/mobile; flutter test; flutter analyze; Pop-Location`: 10 passed; analyzer PASS.
- `python -m alembic -c apps/api/alembic.ini upgrade head`: migration applied.
- `python -m alembic -c apps/api/alembic.ini current`: `c93e2b7f4a18 (head)`.
- `python -m alembic -c apps/api/alembic.ini heads`: `c93e2b7f4a18 (head)`.
- `git diff --check`: PASS.

## Known Issues and Deferred Items

- Recurring recommendations remain unavailable pending a canonical recurring source.
- Push delivery is outside this phase; lifecycle is in-app and product-event only.
- Existing datetime deprecation warnings remain non-blocking technical debt.
- Current workspace changes are not commit-pinned CI evidence.

## Worker Reliability Revalidation

After acceptance, review found that one outer exception boundary covered both
notification and recommendation cycles. A notification failure could therefore
skip the recommendation cycle for that iteration, and recommendation failures
could be logged as notification failures. `apps/worker/app/main.py` was fixed
with independent cycle functions, explicit `HTTPError`/`URLError` handling, and
subsystem-specific logs. The notification scheduler and recommendation
scheduler retain separate Redis locks and retry-safe deterministic materialization.

Validation after the fix: `python -m ruff check apps/worker/app` passed,
`python -m compileall -q apps/worker/app` passed, and
`python -m pytest apps/api/tests/test_recommendations.py -q` passed with 4 tests.
No worker-specific test directory exists. Phase 12 remains PASS WITH
NON-BLOCKING ISSUES; no current blocker was introduced.

## Changed Files

- `apps/api/app/db/models/finance.py`
- `apps/api/app/db/models/__init__.py`
- `apps/api/app/main.py`
- `apps/api/app/recommendations/__init__.py`
- `apps/api/app/recommendations/schemas.py`
- `apps/api/app/recommendations/service.py`
- `apps/api/app/recommendations/routes.py`
- `apps/api/migrations/versions/c93e2b7f4a18_phase12_recommendations.py`
- `apps/api/tests/test_recommendations.py`
- `apps/mobile/lib/finance/models.dart`
- `apps/mobile/lib/auth/api_client.dart`
- `apps/mobile/lib/finance/finance_repository.dart`
- `apps/mobile/lib/finance/finance_view_model.dart`
- `apps/mobile/lib/finance/finance_home.dart`
- `apps/mobile/test/account_dialog_lifecycle_test.dart`
- `apps/worker/app/main.py`
- `apps/worker/app/recommendation_scheduler.py`
- `docs/api/RECOMMENDATIONS_API.md`
- `docs/recommendations/rules.md`
- `AGENT_PROGRESS.md`
- `README.md`

## Current Project Blocker

NONE.

## Next Phase

Phase 13 - AI Gateway + Tool Layer + Context Builder + Guardrails. Phase 13 was not implemented at the time of this Phase 12 report; it was accepted subsequently.

Phase 12 đã hoàn thành. Implementation dừng tại đây. Toàn bộ tài liệu liên quan và báo cáo Phase 12 đã được cập nhật. Phase 13 CHƯA được triển khai.
