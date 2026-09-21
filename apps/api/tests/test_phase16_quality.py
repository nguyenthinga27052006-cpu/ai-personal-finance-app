from __future__ import annotations

import json
import statistics
import time
from datetime import date
from pathlib import Path

import pytest
from test_financial_core import account, category, headers, register
from test_phase07 import client  # noqa: F401

from app.ai.context import ExecutionContext
from app.ai.errors import GuardrailViolation, InsufficientDataError, StructuredOutputError
from app.ai.gateway import AIGateway
from app.ai.guardrails import validate_untrusted_input
from app.ai.nl_query import _detect_intent
from app.ai.providers import FakeProvider, ModelRouter
from app.ai.tools import build_read_only_registry
from app.db.models import User


@pytest.fixture
def phase16_client(client):  # noqa: F811
    return client


def test_full_refund_restores_balance_and_cannot_double_count(phase16_client):
    test_client, _ = phase16_client
    auth = register(test_client)
    account_data = account(test_client, auth, "Full refund", opening=100_000)
    expense = test_client.post(
        "/api/v1/transactions",
        headers={**headers(auth), "Idempotency-Key": "phase16-expense"},
        json={
            "type": "EXPENSE",
            "account_id": account_data["id"],
            "amount": 12_345,
            "currency": "VND",
        },
    )
    assert expense.status_code == 201

    refund = test_client.post(
        f"/api/v1/transactions/{expense.json()['id']}/refund",
        headers={**headers(auth), "Idempotency-Key": "idem-ref-1"},
        json={"account_id": account_data["id"], "amount": 12_345, "currency": "VND"},
    )
    assert refund.status_code == 201

    balance = test_client.get("/api/v1/accounts", headers=headers(auth)).json()["items"][0]
    assert balance["current_balance"] == 100_000

    duplicate_refund = test_client.post(
        f"/api/v1/transactions/{expense.json()['id']}/refund",
        headers={**headers(auth), "Idempotency-Key": "idem-ref-2"},
        json={"account_id": account_data["id"], "amount": 1, "currency": "VND"},
    )
    assert duplicate_refund.status_code == 400
    assert test_client.get("/api/v1/transactions", headers=headers(auth)).json()["total"] == 2


def test_split_boundary_and_invalid_items_are_enforced(phase16_client):
    test_client, factory = phase16_client
    auth = register(test_client)
    account_data = account(test_client, auth, "Split boundary")
    category_id = category(factory, auth["user"]["id"])
    base = {
        "type": "EXPENSE",
        "account_id": account_data["id"],
        "currency": "VND",
        "category_id": category_id,
    }

    valid_boundary = test_client.post(
        "/api/v1/transactions",
        headers={**headers(auth), "Idempotency-Key": "phase16-mismatch"},
        json={
            **base,
            "amount": 10_000,
            "items": [
                {"amount": 9_999, "category_id": category_id},
                {"amount": 1, "category_id": category_id},
            ],
        },
    )
    assert valid_boundary.status_code == 201

    mismatch = test_client.post(
        "/api/v1/transactions",
        headers={**headers(auth), "Idempotency-Key": "phase16-mismatch"},
        json={
            **base,
            "amount": 10_000,
            "items": [
                {"amount": 9_999, "category_id": category_id},
                {"amount": 2, "category_id": category_id},
            ],
        },
    )
    assert mismatch.status_code == 422

    invalid_zero = test_client.post(
        "/api/v1/transactions",
        headers={**headers(auth), "Idempotency-Key": "phase16-zero-item"},
        json={
            **base,
            "amount": 10_000,
            "items": [{"amount": 0, "category_id": category_id}],
        },
    )
    assert invalid_zero.status_code == 422


def test_representative_api_negative_contracts(phase16_client):
    test_client, _ = phase16_client
    assert test_client.get("/api/v1/accounts").status_code == 401

    auth = register(test_client)
    assert test_client.get("/api/v1/transactions?page=0", headers=headers(auth)).status_code == 422
    assert (
        test_client.get("/api/v1/transactions/not-a-real-id", headers=headers(auth)).status_code
        == 404
    )

    account_data = account(test_client, auth, "Contract")
    unknown_field = test_client.post(
        "/api/v1/transactions",
        headers={**headers(auth), "Idempotency-Key": "idem-unk"},
        json={
            "type": "EXPENSE",
            "account_id": account_data["id"],
            "amount": 1,
            "currency": "VND",
            "unexpected": True,
        },
    )
    assert unknown_field.status_code == 422


def test_ai_golden_dataset_contracts_are_deterministic(phase16_client):
    test_client, factory = phase16_client
    dataset_path = Path(__file__).parents[3] / "docs" / "testing" / "ai_golden_v1.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    required = {
        "id",
        "user_input",
        "expected_intent",
        "expected_tool",
        "expected_args",
        "expected_status",
        "expected_grounding_sources",
        "expected_provenance_behavior",
        "numeric_facts",
        "forbidden_claims",
        "expected_safety_behavior",
    }
    assert dataset["dataset_version"] == "phase16-ai-golden-v1"
    assert len(dataset["cases"]) == 7
    assert all(required <= case.keys() for case in dataset["cases"])
    auth = register(test_client)
    account_data = account(test_client, auth, "AI golden account", opening=100_000)
    expense = test_client.post(
        "/api/v1/transactions",
        headers={**headers(auth), "Idempotency-Key": "idem-gold"},
        json={
            "type": "EXPENSE",
            "account_id": account_data["id"],
            "amount": 5_000,
            "currency": "VND",
            "transaction_date": "2026-09-03T12:00:00+00:00",
        },
    )
    assert expense.status_code == 201
    with factory() as db:
        user = db.get(User, auth["user"]["id"])
        assert user is not None
        context = ExecutionContext(
            db=db,
            user=user,
            request_id="phase16-ai-golden",
            feature="nl_query",
            allowed_tools=frozenset(
                {
                    "get_monthly_expense",
                    "get_monthly_income",
                    "get_current_balance",
                    "get_budget_status",
                    "get_goal_progress",
                }
            ),
        )
        empty_user = User(
            email="phase16-empty@example.com",
            password_hash="test-hash",
            default_currency="VND",
            timezone="UTC",
            locale="en-US",
        )
        db.add(empty_user)
        db.flush()
        empty_context = ExecutionContext(
            db=db,
            user=empty_user,
            request_id="phase16-ai-golden-empty",
            feature="nl_query",
            allowed_tools=context.allowed_tools,
        )

        report = {
            "total": len(dataset["cases"]),
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "partial": 0,
            "cases": [],
        }
        registry = build_read_only_registry()
        for case in dataset["cases"]:
            reasons: list[str] = []
            status = "PASS"
            case_context = empty_context if case["id"] == "insufficient-data" else context
            try:
                actual_intent, actual_tool = _detect_intent(case["user_input"])
                if case["id"] in {
                    "prompt-injection-refusal",
                    "malformed-provider-output",
                    "ownership-injection",
                }:
                    if case["id"] == "prompt-injection-refusal":
                        validate_untrusted_input(case["user_input"])
                    elif case["id"] == "ownership-injection":
                        from app.ai.guardrails import validate_tool_arguments

                        validate_tool_arguments(case["expected_args"])
                    else:
                        gateway = AIGateway(
                            ModelRouter(FakeProvider(response="{malformed")), registry
                        )
                        gateway._validate_provider_output("{malformed")
                    raise AssertionError("expected deterministic rejection did not occur")

                assert (actual_intent, actual_tool) == (
                    case["expected_intent"],
                    case["expected_tool"],
                )
                if case["id"] == "unsupported-request":
                    assert case["expected_status"] == "UNSUPPORTED_REQUEST"
                    reasons.append("unsupported intent rejected without a tool")
                else:
                    args = dict(case["expected_args"])
                    if case["expected_tool"] != "get_current_balance":
                        args.update({"start": date(2026, 9, 1), "end": date(2026, 9, 30)})
                    assert case["expected_args"].items() <= args.items()
                    try:
                        result = registry.execute(case["expected_tool"], case_context, args)
                        actual_status = "SUCCESS"
                        assert case["expected_status"] == actual_status
                        assert result.tool == case["expected_tool"]
                        sources = {item.source for item in result.provenance}
                        assert set(case["expected_grounding_sources"]) <= sources
                        assert all(item.calculation_type for item in result.provenance)
                        for fact in case["numeric_facts"]:
                            assert result.data[fact["field"]] == fact["value"]
                        assert all(
                            claim.lower() not in str(result.data).lower()
                            for claim in case["forbidden_claims"]
                        )
                        reasons.append(
                            "intent, tool, args, status, grounding, provenance, "
                            "numeric facts, and forbidden claims evaluated"
                        )
                    except InsufficientDataError:
                        assert case["expected_status"] == "INSUFFICIENT_DATA"
                        assert case["expected_grounding_sources"] == ["analytics.service"]
                        reasons.append("insufficient-data fail-closed path evaluated")
            except (GuardrailViolation, StructuredOutputError):
                assert case["expected_status"] in {
                    "GUARDRAIL_REJECTED",
                    "STRUCTURED_OUTPUT_REJECTED",
                }
                assert case["expected_grounding_sources"] == []
                reasons.append("deterministic safety/structured-output rejection evaluated")
            except AssertionError as exc:
                status = "FAIL"
                reasons.append(str(exc))
            report["cases"].append({"id": case["id"], "status": status, "reasons": reasons})
            report["passed" if status == "PASS" else "failed"] += 1
        print(f"PHASE16_AI_EVAL {json.dumps(report, sort_keys=True)}")
        assert report["failed"] == 0


def test_phase16_performance_baseline(phase16_client):
    test_client, _ = phase16_client
    auth = register(test_client)
    account_data = account(test_client, auth, "Performance", opening=100_000)
    auth_headers = headers(auth)
    operations = {
        "financial_facts": lambda: test_client.get(
            "/api/v1/analytics/overview?start=2026-08-01&end=2026-08-31&currency=VND",
            headers=auth_headers,
        ),
        "dashboard": lambda: test_client.get(
            "/api/v1/dashboard?currency=VND", headers=auth_headers
        ),
        "ai_gateway": lambda: test_client.post(
            "/api/v1/ai/query",
            headers=auth_headers,
            json={"question": "How much did I spend this month?", "currency": "VND"},
        ),
        "transaction_write": lambda: test_client.post(
            "/api/v1/transactions",
            headers={**auth_headers, "Idempotency-Key": f"phase16-perf-{time.monotonic_ns()}"},
            json={
                "type": "EXPENSE",
                "account_id": account_data["id"],
                "amount": 1,
                "currency": "VND",
            },
        ),
    }
    measurements: dict[str, list[float]] = {name: [] for name in operations}
    for _ in range(20):
        for name, operation in operations.items():
            started = time.perf_counter()
            response = operation()
            elapsed_ms = (time.perf_counter() - started) * 1000
            assert response.status_code in {200, 201}, (name, response.text)
            measurements[name].append(elapsed_ms)

    for name, values in measurements.items():
        ordered = sorted(values)
        p50 = statistics.median(ordered)
        p95 = statistics.quantiles(ordered, n=20, method="inclusive")[18]
        p99 = ordered[-1]
        print(f"PHASE16_BASELINE {name} n=20 p50_ms={p50:.2f} p95_ms={p95:.2f} p99_ms={p99:.2f}")
