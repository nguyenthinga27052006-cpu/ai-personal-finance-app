from datetime import date

from test_analytics import canonical_analytics_fixture  # noqa: F401
from test_financial_core import headers, register
from test_phase07 import client  # noqa: F401

from app.db.models import User
from app.insights.service import generate_insights


def test_insights_are_traceable_ranked_and_deterministic(canonical_analytics_fixture):  # noqa: F811
    test_client, auth, _ = canonical_analytics_fixture
    response = test_client.get(
        "/api/v1/insights",
        headers=headers(auth),
        params={"start": "2026-08-01", "end": "2026-08-31"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["total"] >= 4
    assert data["items"][0]["severity"] == "HIGH"
    assert all(item["source"] == "phase09.financial_facts" for item in data["items"])
    assert all(item["rule_id"] and item["source_metric"] for item in data["items"])
    assert len({item["id"] for item in data["items"]}) == data["total"]
    repeated = test_client.get(
        "/api/v1/insights",
        headers=headers(auth),
        params={"start": "2026-08-01", "end": "2026-08-31"},
    ).json()
    assert [item["id"] for item in repeated["items"]] == [item["id"] for item in data["items"]]


def test_insights_fail_closed_without_evidence_and_expire(client):  # noqa: F811
    test_client, factory = client
    auth = register(test_client)
    with factory() as db:
        user = db.get(User, auth["user"]["id"])
        assert user is not None
        assert generate_insights(db, user, date(2026, 8, 1), date(2026, 8, 31), "VND") == []
    response = test_client.get(
        "/api/v1/insights",
        headers=headers(auth),
        params={"start": "2026-08-01", "end": "2026-08-31"},
    )
    assert response.json() == {"items": [], "total": 0}


def test_cashflow_risk_requires_income_and_detects_deficit(client):  # noqa: F811
    test_client, _ = client
    auth = register(test_client)
    account_data = test_client.post(
        "/api/v1/accounts",
        headers=headers(auth),
        json={
            "name": "Cash flow",
            "type": "BANK",
            "currency": "VND",
            "opening_balance": 100000,
        },
    ).json()
    for key, transaction_type, amount in (
        ("cashflow-income", "INCOME", 1000),
        ("cashflow-expense", "EXPENSE", 2000),
    ):
        response = test_client.post(
            "/api/v1/transactions",
            headers={**headers(auth), "Idempotency-Key": key},
            json={
                "type": transaction_type,
                "account_id": account_data["id"],
                "amount": amount,
                "currency": "VND",
                "transaction_date": "2026-08-15T12:00:00+00:00",
            },
        )
        assert response.status_code == 201, response.text
    data = test_client.get(
        "/api/v1/insights",
        headers=headers(auth),
        params={"start": "2026-08-01", "end": "2026-08-31"},
    ).json()
    cashflow = [item for item in data["items"] if item["type"] == "CASHFLOW_RISK"]
    assert len(cashflow) == 1
    assert cashflow[0]["source_metric"] == "summary.saving"


def test_insight_detail_ownership_and_expiry(canonical_analytics_fixture):  # noqa: F811
    test_client, auth, _ = canonical_analytics_fixture
    other = register(test_client)
    listing = test_client.get(
        "/api/v1/insights",
        headers=headers(auth),
        params={"start": "2026-08-01", "end": "2026-08-31"},
    ).json()
    insight_id = listing["items"][0]["id"]
    detail = test_client.get(
        f"/api/v1/insights/{insight_id}",
        headers=headers(auth),
        params={"start": "2026-08-01", "end": "2026-08-31"},
    )
    assert detail.status_code == 200
    assert detail.json()["id"] == insight_id
    assert (
        test_client.get(
            f"/api/v1/insights/{insight_id}",
            headers=headers(other),
            params={"start": "2026-08-01", "end": "2026-08-31"},
        ).status_code
        == 404
    )

    with test_client as active_client:
        expired = active_client.get(
            "/api/v1/insights",
            headers=headers(auth),
            params={"start": "2025-01-01", "end": "2025-01-31"},
        )
    assert expired.json() == {"items": [], "total": 0}
