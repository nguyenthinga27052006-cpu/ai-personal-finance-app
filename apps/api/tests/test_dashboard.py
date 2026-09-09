from test_analytics import canonical_analytics_fixture  # noqa: F401
from test_financial_core import account, headers, register
from test_phase07 import client  # noqa: F401


def test_dashboard_is_empty_and_authenticated(client):  # noqa: F811
    test_client, _ = client
    auth = register(test_client)
    response = test_client.get("/api/v1/dashboard", headers=headers(auth))
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["summary"] == {
        "total_balance": 0,
        "income": 0,
        "expense": 0,
        "saving": 0,
        "saving_rate": "0.000000",
    }
    assert data["accounts"] == []
    assert data["recent_transactions"] == []
    assert test_client.get("/api/v1/dashboard").status_code == 401


def test_dashboard_uses_authoritative_analytics_and_owned_resources(canonical_analytics_fixture):  # noqa: F811
    test_client, auth, account_data = canonical_analytics_fixture
    for key, transaction_type, amount in (
        ("dashboard-income", "INCOME", 50_000),
        ("dashboard-expense", "EXPENSE", 17_000),
    ):
        created = test_client.post(
            "/api/v1/transactions",
            headers={**headers(auth), "Idempotency-Key": key},
            json={
                "type": transaction_type,
                "account_id": account_data["id"],
                "amount": amount,
                "currency": "VND",
                "transaction_date": "2026-09-03T12:00:00+00:00",
            },
        )
        assert created.status_code == 201, created.text
    response = test_client.get("/api/v1/dashboard", headers=headers(auth))
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["summary"]["income"] == 50_000
    assert data["summary"]["expense"] == 17_000
    assert data["summary"]["saving"] == 33_000
    accounts = test_client.get("/api/v1/accounts", headers=headers(auth)).json()["items"]
    assert data["summary"]["total_balance"] == sum(item["current_balance"] for item in accounts)
    assert len(data["recent_transactions"]) == 5
    assert data["categories"] == [
        {"id": "uncategorized", "name": "Uncategorized", "amount": 17_000, "share": "1.000000"}
    ]


def test_dashboard_excludes_other_currency_and_other_user(client):  # noqa: F811
    test_client, _ = client
    owner = register(test_client)
    other = register(test_client)
    owner_account = account(test_client, owner, "Owner")
    other_account = account(test_client, other, "Other")
    response = test_client.get("/api/v1/dashboard", headers=headers(owner))
    assert response.status_code == 200
    assert [item["id"] for item in response.json()["accounts"]] == [owner_account["id"]]
    assert other_account["id"] not in response.text
