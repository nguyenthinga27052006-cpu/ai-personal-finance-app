from __future__ import annotations

from datetime import date

import pytest
from test_financial_core import account, headers, register
from test_phase07 import client  # noqa: F401

from app.db.models import User


@pytest.fixture
def canonical_analytics_fixture(client):  # noqa: F811
    test_client, _ = client
    auth = register(test_client)
    account_data = account(test_client, auth, "Analytics", 1_000_000)
    destination = account(test_client, auth, "Transfer target", 100_000)
    category = test_client.post(
        "/api/v1/categories", headers=headers(auth), json={"name": "Food", "type": "EXPENSE"}
    ).json()
    second_category = test_client.post(
        "/api/v1/categories", headers=headers(auth), json={"name": "Travel", "type": "EXPENSE"}
    ).json()
    merchant = test_client.post(
        "/api/v1/merchants", headers=headers(auth), json={"canonical_name": "Cafe"}
    ).json()

    def create(key, payload):
        response = test_client.post(
            "/api/v1/transactions", headers={**headers(auth), "Idempotency-Key": key}, json=payload
        )
        assert response.status_code == 201, response.text
        return response.json()

    expense = create(
        "analytics-expense",
        {
            "type": "EXPENSE",
            "account_id": account_data["id"],
            "amount": 10_000,
            "currency": "VND",
            "category_id": category["id"],
            "merchant_id": merchant["id"],
            "transaction_date": "2026-08-10T12:00:00+00:00",
        },
    )
    create(
        "analytics-partial-refund",
        {
            "type": "REFUND",
            "account_id": account_data["id"],
            "amount": 2_000,
            "currency": "VND",
            "parent_transaction_id": expense["id"],
            "transaction_date": "2026-08-11T12:00:00+00:00",
        },
    )
    full = create(
        "analytics-full-expense",
        {
            "type": "EXPENSE",
            "account_id": account_data["id"],
            "amount": 4_000,
            "currency": "VND",
            "category_id": category["id"],
            "transaction_date": "2026-08-12T12:00:00+00:00",
        },
    )
    create(
        "analytics-full-refund",
        {
            "type": "REFUND",
            "account_id": account_data["id"],
            "amount": 4_000,
            "currency": "VND",
            "parent_transaction_id": full["id"],
            "transaction_date": "2026-08-13T12:00:00+00:00",
        },
    )
    create(
        "analytics-split",
        {
            "type": "EXPENSE",
            "account_id": account_data["id"],
            "amount": 9_000,
            "currency": "VND",
            "merchant_id": merchant["id"],
            "transaction_date": "2026-08-14T12:00:00+00:00",
            "items": [
                {"amount": 4_000, "category_id": category["id"]},
                {"amount": 5_000, "category_id": second_category["id"]},
            ],
        },
    )
    create(
        "analytics-income",
        {
            "type": "INCOME",
            "account_id": account_data["id"],
            "amount": 50_000,
            "currency": "VND",
            "transaction_date": "2026-08-15T12:00:00+00:00",
        },
    )
    transfer = test_client.post(
        "/api/v1/transfers",
        headers={**headers(auth), "Idempotency-Key": "analytics-transfer"},
        json={
            "source_account_id": account_data["id"],
            "destination_account_id": destination["id"],
            "amount": 7_000,
            "currency": "VND",
            "transaction_date": "2026-08-16T12:00:00+00:00",
        },
    )
    assert transfer.status_code == 201, transfer.text
    # Previous-period and rolling-window records, including a UTC/local boundary.
    create(
        "analytics-history",
        {
            "type": "EXPENSE",
            "account_id": account_data["id"],
            "amount": 1_000,
            "currency": "VND",
            "transaction_date": "2026-07-31T17:00:00+00:00",
        },
    )
    return test_client, auth, account_data


def test_analytics_overview_uses_canonical_facts_and_schema(canonical_analytics_fixture):
    test_client, auth, _ = canonical_analytics_fixture
    with test_client as active_client:
        response = active_client.get(
            "/api/v1/analytics/overview",
            headers=headers(auth),
            params={"start": "2026-08-01", "end": "2026-08-31"},
        )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["summary"]["income"] == 50_000
    assert data["summary"]["expense"] == 17_000  # 8k + 0 + 9k; transfer/refunds excluded
    assert data["summary"]["saving"] == 33_000
    assert data["summary"]["saving_rate"] == "0.660000"
    assert data["summary"]["average_daily_spending"] == "548.387097"
    assert data["period"]["timezone"] == "UTC"
    assert {item["name"] for item in data["category_analysis"]} == {"Food", "Travel"}
    assert data["forecast"]["status"] == "BASELINE"
    assert data["forecast"]["projected_expense"] == 17_000
    assert all(value not in {"NaN", "Infinity", "-Infinity"} for value in response.text.split('"'))


def test_analytics_timezone_boundary_and_zero_denominators(client):  # noqa: F811
    test_client, factory = client
    auth = register(test_client)
    with factory() as db:
        db.query(User).filter_by(id=auth["user"]["id"]).one().timezone = "Asia/Ho_Chi_Minh"
        db.commit()
    account_data = account(test_client, auth, "Boundary")
    test_client.post(
        "/api/v1/transactions",
        headers={**headers(auth), "Idempotency-Key": "boundary"},
        json={
            "type": "EXPENSE",
            "account_id": account_data["id"],
            "amount": 1_000,
            "currency": "VND",
            "transaction_date": "2026-07-31T17:00:00+00:00",
        },
    )
    response = test_client.get(
        "/api/v1/analytics/overview",
        headers=headers(auth),
        params={"start": "2026-08-01", "end": "2026-08-01"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["expense"] == 1_000
    assert data["summary"]["income"] == 0
    assert data["summary"]["saving_rate"] == "0.000000"
    empty = test_client.get(
        "/api/v1/analytics/overview",
        headers=headers(auth),
        params={"start": "2026-09-01", "end": "2026-09-01"},
    ).json()
    assert empty["forecast"]["status"] == "INSUFFICIENT_DATA"
    assert empty["forecast"]["projected_expense"] is None


def test_analytics_rejects_reversed_period(client):  # noqa: F811
    test_client, _ = client
    auth = register(test_client)
    response = test_client.get(
        "/api/v1/analytics/overview",
        headers=headers(auth),
        params={"start": date(2026, 8, 2), "end": date(2026, 8, 1)},
    )
    assert response.status_code == 422
