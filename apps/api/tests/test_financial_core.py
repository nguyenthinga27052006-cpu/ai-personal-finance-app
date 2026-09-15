from __future__ import annotations

import uuid

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.rate_limit import InMemoryAuthRateLimiter, get_auth_rate_limiter
from app.db.base import Base
from app.db.models import Category, TransactionEntry
from app.db.session import get_db
from app.main import app


@pytest.fixture
def client():
    engine = sa.create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)

    def override_get_db():
        with factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_auth_rate_limiter] = lambda: InMemoryAuthRateLimiter(
        max_attempts=1000
    )
    with TestClient(app) as test_client:
        yield test_client, factory
    app.dependency_overrides.clear()
    engine.dispose()


def register(client: TestClient) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"financial-{uuid.uuid4()}@example.com",
            "password": "correct horse battery staple",
        },
    )
    assert response.status_code == 201
    return response.json()


def headers(auth: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth['access_token']}"}


def account(client: TestClient, auth: dict, name: str, opening: int = 100000) -> dict:
    response = client.post(
        "/api/v1/accounts",
        headers=headers(auth),
        json={"name": name, "type": "BANK", "currency": "VND", "opening_balance": opening},
    )
    assert response.status_code == 201
    return response.json()


def category(factory, user_id: str, category_type: str = "EXPENSE") -> str:
    with factory() as db:
        item = Category(
            user_id=user_id,
            name=f"Category {uuid.uuid4()}",
            type=category_type,
            is_system=False,
            is_active=True,
        )
        db.add(item)
        db.commit()
        return item.id


def test_expense_income_change_balance_and_write_signed_ledger(client):
    test_client, factory = client
    auth = register(test_client)
    account_data = account(test_client, auth, "Cash")
    expense = test_client.post(
        "/api/v1/transactions",
        headers={**headers(auth), "Idempotency-Key": "expense-1"},
        json={
            "type": "EXPENSE",
            "account_id": account_data["id"],
            "amount": 1200,
            "currency": "VND",
        },
    )
    assert expense.status_code == 201
    assert expense.json()["entries"][0]["amount"] == -1200
    income = test_client.post(
        "/api/v1/transactions",
        headers={**headers(auth), "Idempotency-Key": "income-1"},
        json={
            "type": "INCOME",
            "account_id": account_data["id"],
            "amount": 5000,
            "currency": "VND",
        },
    )
    assert income.status_code == 201
    listed = test_client.get("/api/v1/accounts", headers=headers(auth)).json()["items"][0]
    assert listed["current_balance"] == 103800
    with factory() as db:
        entries = db.query(TransactionEntry).all()
        assert {entry.amount for entry in entries} == {-1200, 5000}


def test_transfer_preserves_total_wealth_and_group(client):
    test_client, _ = client
    auth = register(test_client)
    source = account(test_client, auth, "Source")
    destination = account(test_client, auth, "Destination", opening=20000)
    transfer = test_client.post(
        "/api/v1/transfers",
        headers={**headers(auth), "Idempotency-Key": "transfer-1"},
        json={
            "source_account_id": source["id"],
            "destination_account_id": destination["id"],
            "amount": 7500,
            "currency": "VND",
        },
    )
    assert transfer.status_code == 201
    data = transfer.json()
    assert len(data["entries"]) == 2
    assert data["entries"][0]["amount"] + data["entries"][1]["amount"] == 0
    assert data["transfer_group_id"]
    balances = test_client.get("/api/v1/accounts", headers=headers(auth)).json()["items"]
    assert sum(item["current_balance"] for item in balances) == 120000


def test_refund_reverses_expense_and_enforces_refundable_amount(client):
    test_client, _ = client
    auth = register(test_client)
    account_data = account(test_client, auth, "Refund account")
    expense = test_client.post(
        "/api/v1/transactions",
        headers={**headers(auth), "Idempotency-Key": "refund-expense"},
        json={
            "type": "EXPENSE",
            "account_id": account_data["id"],
            "amount": 9000,
            "currency": "VND",
        },
    ).json()
    refund = test_client.post(
        f"/api/v1/transactions/{expense['id']}/refund",
        headers={**headers(auth), "Idempotency-Key": "refund-1"},
        json={
            "account_id": account_data["id"],
            "amount": 4000,
            "currency": "VND",
        },
    )
    assert refund.status_code == 201
    over_refund = test_client.post(
        f"/api/v1/transactions/{expense['id']}/refund",
        headers={**headers(auth), "Idempotency-Key": "refund-2"},
        json={
            "account_id": account_data["id"],
            "amount": 6000,
            "currency": "VND",
        },
    )
    assert over_refund.status_code == 400
    balance = test_client.get("/api/v1/accounts", headers=headers(auth)).json()["items"][0][
        "current_balance"
    ]
    assert balance == 95000


def test_split_idempotency_and_cross_user_access(client):
    test_client, _ = client
    owner = register(test_client)
    other = register(test_client)
    owner_account = account(test_client, owner, "Owner")
    category_id = category(client[1], owner["user"]["id"])
    payload = {
        "type": "EXPENSE",
        "account_id": owner_account["id"],
        "amount": 3000,
        "currency": "VND",
        "category_id": category_id,
        "items": [
            {"amount": 1000, "category_id": category_id},
            {"amount": 2000, "category_id": category_id},
        ],
    }
    first = test_client.post(
        "/api/v1/transactions",
        headers={**headers(owner), "Idempotency-Key": "split-1"},
        json=payload,
    )
    second = test_client.post(
        "/api/v1/transactions",
        headers={**headers(owner), "Idempotency-Key": "split-1"},
        json=payload,
    )
    assert first.status_code == second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert len(first.json()["items"]) == 2
    conflict = test_client.post(
        "/api/v1/transactions",
        headers={**headers(owner), "Idempotency-Key": "split-1"},
        json={
            **payload,
            "amount": 3001,
            "items": [
                {"amount": 1001, "category_id": category_id},
                {"amount": 2000, "category_id": category_id},
            ],
        },
    )
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["code"] == "idempotency_conflict"
    assert (
        test_client.get(
            f"/api/v1/transactions/{first.json()['id']}", headers=headers(other)
        ).status_code
        == 404
    )


def test_invalid_category_currency_and_timezone_date_are_rejected_or_preserved(client):
    test_client, _ = client
    auth = register(test_client)
    account_data = account(test_client, auth, "Date account")
    date_value = "2026-08-27T12:30:00+07:00"
    invalid = test_client.post(
        "/api/v1/transactions",
        headers={**headers(auth), "Idempotency-Key": "invalid-1"},
        json={
            "type": "EXPENSE",
            "account_id": account_data["id"],
            "amount": 100,
            "currency": "USD",
        },
    )
    assert invalid.status_code == 400
    valid = test_client.post(
        "/api/v1/transactions",
        headers={**headers(auth), "Idempotency-Key": "date-1"},
        json={
            "type": "INCOME",
            "account_id": account_data["id"],
            "amount": 100,
            "currency": "VND",
            "transaction_date": date_value,
        },
    )
    assert valid.status_code == 201
    assert valid.json()["transaction_date"].startswith("2026-08-27T12:30:00")


def test_update_and_delete_transaction_updates_balance(client):
    test_client, _ = client
    auth = register(test_client)
    acc = account(test_client, auth, "Update Delete Account", opening=100000)

    # 1. Create Expense
    tx = test_client.post(
        "/api/v1/transactions",
        headers=headers(auth),
        json={
            "type": "EXPENSE",
            "account_id": acc["id"],
            "amount": 20000,
            "currency": "VND",
            "description": "Lunch",
        },
    )
    assert tx.status_code == 201
    tx_id = tx.json()["id"]

    # Balance should now be 100000 - 20000 = 80000
    acc_check = test_client.get(f"/api/v1/accounts/{acc['id']}", headers=headers(auth)).json()
    assert acc_check["current_balance"] == 80000

    # 2. Update transaction amount to 30000
    updated = test_client.put(
        f"/api/v1/transactions/{tx_id}",
        headers=headers(auth),
        json={"amount": 30000, "description": "Updated Lunch"},
    )
    assert updated.status_code == 200
    assert updated.json()["amount"] == 30000
    assert updated.json()["description"] == "Updated Lunch"

    # Balance should now be 100000 - 30000 = 70000
    acc_check = test_client.get(f"/api/v1/accounts/{acc['id']}", headers=headers(auth)).json()
    assert acc_check["current_balance"] == 70000

    # 3. Delete transaction
    deleted = test_client.delete(f"/api/v1/transactions/{tx_id}", headers=headers(auth))
    assert deleted.status_code == 204

    # Balance should be restored to opening 100000
    acc_check = test_client.get(f"/api/v1/accounts/{acc['id']}", headers=headers(auth)).json()
    assert acc_check["current_balance"] == 100000

    # Getting deleted transaction returns 404
    assert test_client.get(f"/api/v1/transactions/{tx_id}", headers=headers(auth)).status_code == 404

