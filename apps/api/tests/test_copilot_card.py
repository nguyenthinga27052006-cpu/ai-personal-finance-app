from __future__ import annotations

from datetime import date, timedelta

from test_financial_core import account, client, headers, register  # noqa: F401


def test_copilot_card_stable_flow(client):  # noqa: F811
    test_client, _ = client
    auth = register(test_client)

    res = test_client.get("/api/v1/recommendations/copilot-card", headers=headers(auth))
    assert res.status_code == 200, res.text
    card = res.json()
    assert card["status"] == "STABLE"
    assert "headline" in card
    assert "message" in card
    assert "facts" in card
    assert isinstance(card["actions"], list)


def test_copilot_card_risk_with_upcoming_debt_and_cash_gap(client):  # noqa: F811
    test_client, _ = client
    auth = register(test_client)

    # 1. Setup account with 1,000,000 balance
    account(test_client, auth, "Wallet", 1000000)

    # 2. Add support contact
    test_client.post(
        "/api/v1/financial-contacts",
        headers=headers(auth),
        json={"name": "Mẹ", "is_support_contact": True},
    )

    # 3. Add upcoming debt of 3,000,000 due in 3 days (greater than 1,000,000 -> Cash Gap!)
    today = date.today()
    in_3_days = today + timedelta(days=3)
    test_client.post(
        "/api/v1/debts",
        headers=headers(auth),
        json={
            "type": "BORROW",
            "counterparty_name": "Anh Hưng",
            "total_amount": 3000000,
            "currency": "VND",
            "due_date": in_3_days.isoformat(),
        },
    )

    # 4. Fetch copilot card
    res = test_client.get(
        f"/api/v1/recommendations/copilot-card?as_of_date={today.isoformat()}",
        headers=headers(auth),
    )
    assert res.status_code == 200
    card = res.json()
    assert card["status"] == "RISK"
    assert "Nguy cơ thiếu hụt dòng tiền" in card["headline"]
    assert card["facts"]["projected_gap"] == 2000000  # 3,000,000 - 1,000,000
    assert card["facts"]["has_support_contacts"] is True

    action_ids = [a["action_id"] for a in card["actions"]]
    assert "VIEW_DEBTS" in action_ids
    assert "VIEW_SUPPORT" in action_ids


def test_copilot_card_opportunity_pay_debt_when_surplus(client):  # noqa: F811
    test_client, _ = client
    auth = register(test_client)

    # Account with 10,000,000
    acc = account(test_client, auth, "Savings", 10000000)

    # Add income transaction of 20,000,000
    today = date.today()
    test_client.post(
        "/api/v1/transactions",
        headers={**headers(auth), "Idempotency-Key": "copilot-inc"},
        json={
            "type": "INCOME",
            "account_id": acc["id"],
            "amount": 20000000,
            "currency": "VND",
            "transaction_date": today.isoformat(),
        },
    )

    # Add an active debt due next month
    in_20_days = today + timedelta(days=20)
    test_client.post(
        "/api/v1/debts",
        headers=headers(auth),
        json={
            "type": "BORROW",
            "counterparty_name": "Ngân hàng",
            "total_amount": 5000000,
            "currency": "VND",
            "due_date": in_20_days.isoformat(),
        },
    )

    # Fetch card
    res = test_client.get(
        f"/api/v1/recommendations/copilot-card?as_of_date={today.isoformat()}",
        headers=headers(auth),
    )
    assert res.status_code == 200
    card = res.json()
    assert card["status"] == "OPPORTUNITY"
    assert "Cơ hội trả nợ sớm" in card["headline"]
    action_ids = [a["action_id"] for a in card["actions"]]
    assert "PAY_DEBT" in action_ids
