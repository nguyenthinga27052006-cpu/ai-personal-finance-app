# Recommendations API

All endpoints are authenticated and enforce ownership from the server-side current user.

- `GET /api/v1/recommendations?start=YYYY-MM-DD&end=YYYY-MM-DD&currency=VND` lists active deterministic recommendations.
- `GET /api/v1/recommendations/{id}` returns one active recommendation.
- `POST /api/v1/recommendations/{id}/accept` records acceptance only; no financial data is changed.
- `POST /api/v1/recommendations/{id}/dismiss` suppresses the recommendation.
- `POST /api/v1/recommendations/{id}/feedback` accepts `HELPFUL` or `NOT_HELPFUL` and updates only that user's ranking feedback.
- `POST /api/v1/recommendations/{id}/events?event_type=SHOWN|ACTION_OUTCOME` stores minimal product analytics.

Recommendations are materialized idempotently using a deterministic dedupe key. The current UI renders reason, suggested action, and `ESTIMATE` impact without calculating metrics or ranking on mobile.