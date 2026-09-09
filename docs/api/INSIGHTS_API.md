# Insights API

Phase 10 exposes authenticated, read-only derived insights:

```text
GET /api/v1/insights?start=YYYY-MM-DD&end=YYYY-MM-DD
GET /api/v1/insights/{insight_id}?start=YYYY-MM-DD&end=YYYY-MM-DD
```

Optional query parameters are `currency`, `type`, and `severity`. The server
uses the authenticated user for ownership and never accepts `user_id` from the
client. Detail requests return `404` for another user's or expired insight.

The list response is:

```json
{"items": [], "total": 0}
```

Each item contains its stable ID, type, title, description, severity,
confidence, source, rule ID, source metric, period, subject when applicable,
source value/baseline, evidence, creation time, and expiry time.

Insight generation is stateless and read-only. It calls the Phase 09 analytics
Financial Facts layer for numeric transaction facts. No transaction, account,
budget, goal, balance, cache, read model, or migration is changed by generation.
