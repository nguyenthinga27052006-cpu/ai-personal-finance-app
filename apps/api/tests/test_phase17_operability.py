from __future__ import annotations

from fastapi.testclient import TestClient

from app.ai.usage import AIUsageLimitExceeded, InMemoryAIUsageBudget
from app.main import app


def test_request_correlation_and_metrics_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/health", headers={"X-Request-ID": "phase17-request"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "phase17-request"
    assert response.headers["X-Trace-ID"]

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "app_http_requests_total" in metrics.text
    assert 'route="/health"' in metrics.text


def test_ai_usage_budget_is_scoped_and_fails_closed() -> None:
    now = [0.0]
    budget = InMemoryAIUsageBudget(daily_units=2, clock=lambda: now[0])

    assert budget.consume("user-a", "nl_query") == 1
    assert budget.consume("user-a", "nl_query") == 2
    assert budget.consume("user-b", "nl_query") == 1
    try:
        budget.consume("user-a", "nl_query")
    except AIUsageLimitExceeded as error:
        assert error.retry_after == 86_400
    else:
        raise AssertionError("expected AI usage budget to fail closed")

    now[0] = 86_400
    assert budget.consume("user-a", "nl_query") == 1
