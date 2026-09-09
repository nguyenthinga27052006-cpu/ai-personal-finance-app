from __future__ import annotations

import logging

from fastapi.testclient import TestClient

from app.ai.usage import AIUsageLimitExceeded, InMemoryAIUsageBudget
from app.error_tracking import LocalErrorTracker, sanitize_context, sanitize_value
from app.main import app
from app.observability import Metrics
from app.tracing import build_trace_context, extract_trace_context


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
    assert "# TYPE app_http_request_duration_ms histogram" in metrics.text
    assert 'route="/health",le="+Inf"' in metrics.text


def test_traceparent_validation_accepts_valid_and_rejects_malformed_values() -> None:
    client = TestClient(app)
    valid = client.get(
        "/health",
        headers={
            "traceparent": "00-0123456789abcdef0123456789abcdef-0123456789abcdef-01",
            "x-trace-id": "fallback-trace",
        },
    )
    assert valid.headers["X-Trace-ID"] == "0123456789abcdef0123456789abcdef"

    for traceparent in (
        "00-0123456789abcdef-0123456789abcdef-01",
        "00-0123456789abcdef0123456789abcdef-01234567-01",
        "00-0123456789abcdef0123456789abcdef-0123456789abcdeg-01",
        "00-0123456789abcdef0123456789abcde0-0123456789abcdef-01-extra",
    ):
        response = client.get(
            "/health",
            headers={"traceparent": traceparent, "x-trace-id": "fallback-trace"},
        )
        assert response.headers["X-Trace-ID"] == "fallback-trace"


def test_traceparent_extraction_does_not_accept_invalid_ids() -> None:
    client = TestClient(app)
    request = client.build_request(
        "GET",
        "/health",
        headers={
            "traceparent": "00-0123456789abcdef0123456789abcdef-0123456789abcdef-02",
            "x-trace-id": "fallback-trace",
        },
    )
    context = extract_trace_context(request)
    assert context.trace_id == "fallback-trace"


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


def test_trace_context_propagates_request_and_span_ids() -> None:
    trace = build_trace_context(
        request_id="req-123",
        trace_id="trace-456",
        parent_span_id="span-789",
    )

    assert trace.request_id == "req-123"
    assert trace.trace_id == "trace-456"
    assert trace.parent_span_id == "span-789"
    assert trace.to_headers()["X-Request-ID"] == "req-123"
    assert trace.to_headers()["X-Trace-ID"] == "trace-456"


def test_error_tracker_redacts_secrets_and_preserves_metadata() -> None:
    tracker = LocalErrorTracker(release="phase17-123", environment="test")
    payload = {
        "password": "secret-password",
        "jwt": "token-123",
        "refresh_token": "refresh-456",
        "api_key": "apikey-789",
        "user_id": "u-42",
        "amount": 149.99,
    }

    result = tracker.capture_exception(
        ValueError("boom"),
        request_id="req-456",
        trace_id="trace-789",
        context=payload,
    )

    assert result["request_id"] == "req-456"
    assert result["trace_id"] == "trace-789"
    assert result["release"] == "phase17-123"
    assert result["environment"] == "test"
    assert result["context"]["password"] == "[REDACTED]"
    assert result["context"]["jwt"] == "[REDACTED]"
    assert result["context"]["refresh_token"] == "[REDACTED]"
    assert result["context"]["api_key"] == "[REDACTED]"
    assert result["context"]["user_id"] == "u-42"
    assert result["context"]["amount"] == 149.99
    assert sanitize_value("keyboard") == "keyboard"
    assert sanitize_value("monkey") == "monkey"
    assert sanitize_value("keynote") == "keynote"
    assert sanitize_context({"nested": {"password": "secret"}})["nested"]["password"] == (
        "[REDACTED]"
    )
    assert sanitize_context({"nested": {"note": "secret token keynote"}})["nested"]["note"] == (
        "secret token keynote"
    )


def test_error_tracker_captures_actual_traceback_without_logging_payload(caplog) -> None:
    tracker = LocalErrorTracker(release="phase17-123", environment="test")
    with caplog.at_level(logging.ERROR, logger="app.error_tracking"):
        try:
            raise RuntimeError("private-key=do-not-log")
        except RuntimeError as exc:
            result = tracker.capture_exception(
                exc,
                request_id="req-1",
                trace_id="trace-1",
                context={"account_id": "acct-1", "private_key": "secret"},
                traceback=exc.__traceback__,
            )

    assert result["type"] == "RuntimeError"
    assert result["context"]["private_key"] == "[REDACTED]"
    record = next(record for record in caplog.records if record.message == "captured_exception")
    assert record.exc_info is not None
    assert record.exc_info[0] is RuntimeError
    assert "private-key=do-not-log" not in record.getMessage()


def test_unhandled_request_is_captured_and_returns_safe_response(monkeypatch) -> None:
    import app.main as main_module

    captured: list[dict[str, object]] = []

    def capture(exc, **kwargs):
        captured.append({"exception": exc, **kwargs})
        return {}

    monkeypatch.setattr(main_module.error_tracker, "capture_exception", capture)

    def fail() -> None:
        raise RuntimeError("database-password=must-not-escape")

    app.add_api_route("/_phase17_unhandled", fail, methods=["GET"])
    response = TestClient(app, raise_server_exceptions=False).get(
        "/_phase17_unhandled",
        headers={"X-Request-ID": "req-runtime"},
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Internal server error",
        "request_id": "req-runtime",
        "trace_id": response.json()["trace_id"],
    }
    assert "release" not in response.json()
    assert "environment" not in response.json()
    assert captured[0]["exception"].args == ("database-password=must-not-escape",)
    assert captured[0]["request_id"] == "req-runtime"
    assert captured[0]["trace_id"] == response.json()["trace_id"]


def test_metrics_storage_is_bounded_and_prometheus_parser_accepts_output() -> None:
    metrics = Metrics(
        requests=__import__("collections").Counter(),
        duration_counts=__import__("collections").Counter(),
        duration_sums_ms=__import__("collections").defaultdict(float),
        duration_buckets={},
    )
    for duration in range(10_000):
        metrics.observe_request("/users/{user_id}", "GET", 200, duration)

    assert sum(len(bucket) for bucket in metrics.duration_buckets.values()) <= len(metrics.BUCKETS)
    output = metrics.prometheus()
    try:
        from prometheus_client.parser import text_string_to_metric_families
    except ImportError:
        assert "# TYPE app_http_request_duration_ms histogram" in output
    else:
        families = list(text_string_to_metric_families(output))
        assert any(family.name == "app_http_request_duration_ms" for family in families)
    assert 'route="/users/{user_id}"' in output
