from __future__ import annotations

from datetime import date

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from test_financial_core import account, headers, register

from app.auth.rate_limit import InMemoryAuthRateLimiter, get_auth_rate_limiter
from app.budget_goals.service import _risk, budget_calculation, goal_calculation
from app.db.base import Base
from app.db.models import Budget, Category, FinancialGoal, User
from app.db.session import get_db
from app.main import app


@pytest.fixture
def client():
    engine = sa.create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
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


def category(factory, user_id: str, name: str) -> str:
    with factory() as db:
        item = Category(user_id=user_id, name=name, type="EXPENSE", is_system=False, is_active=True)
        db.add(item)
        db.commit()
        return item.id


def test_budget_calculation_ignores_income_and_transfer_and_applies_refund(client):
    test_client, factory = client
    auth = register(test_client)
    account_data = account(test_client, auth, "Budget", 100000)
    expense = test_client.post(
        "/api/v1/transactions",
        headers={**headers(auth), "Idempotency-Key": "p07-expense"},
        json={
            "type": "EXPENSE",
            "account_id": account_data["id"],
            "amount": 10000,
            "currency": "VND",
            "transaction_date": "2026-08-10T12:00:00+00:00",
        },
    ).json()
    test_client.post(
        f"/api/v1/transactions/{expense['id']}/refund",
        headers={**headers(auth), "Idempotency-Key": "p07-refund"},
        json={
            "account_id": account_data["id"],
            "amount": 2000,
            "currency": "VND",
            "transaction_date": "2026-08-11T12:00:00+00:00",
        },
    )
    destination_data = account(test_client, auth, "Transfer destination", 20000)
    transfer = test_client.post(
        "/api/v1/transfers",
        headers={**headers(auth), "Idempotency-Key": "p07-transfer"},
        json={
            "source_account_id": account_data["id"],
            "destination_account_id": destination_data["id"],
            "amount": 7000,
            "currency": "VND",
        },
    )
    assert transfer.status_code == 201
    balances = {
        item["id"]: item["current_balance"]
        for item in test_client.get("/api/v1/accounts", headers=headers(auth)).json()["items"]
    }
    assert balances[account_data["id"]] == 85000
    assert balances[destination_data["id"]] == 27000
    test_client.post(
        "/api/v1/transactions",
        headers={**headers(auth), "Idempotency-Key": "p07-income"},
        json={
            "type": "INCOME",
            "account_id": account_data["id"],
            "amount": 50000,
            "currency": "VND",
        },
    )
    budget = test_client.post(
        "/api/v1/budgets",
        headers=headers(auth),
        json={
            "name": "August",
            "start_date": "2026-08-01",
            "end_date": "2026-08-31",
            "total_limit": 10000,
            "currency": "VND",
        },
    )
    assert budget.status_code == 201
    status_response = test_client.get(
        f"/api/v1/budgets/{budget.json()['id']}/status", headers=headers(auth)
    )
    assert status_response.status_code == 200
    with factory() as db:
        user = db.query(User).filter_by(id=auth["user"]["id"]).one()
        persisted_budget = db.query(Budget).filter_by(id=budget.json()["id"]).one()
        status = budget_calculation(db, user, persisted_budget, today=date(2026, 8, 27))
    assert status["spent"] == 8000
    assert status["remaining"] == 2000
    assert status["utilization"] == 0.8
    assert status["risk"] == "DANGER"


def test_budget_timezone_first_local_day_boundary(client):
    test_client, factory = client
    auth = register(test_client)
    with factory() as db:
        db.query(User).filter_by(id=auth["user"]["id"]).one().timezone = "Asia/Ho_Chi_Minh"
        db.commit()
    account_data = account(test_client, auth, "First boundary", 100000)
    for key, transaction_date, amount in (
        ("first-before", "2026-07-31T16:59:59+00:00", 1000),
        ("first-at", "2026-07-31T17:00:00+00:00", 2000),
    ):
        response = test_client.post(
            "/api/v1/transactions",
            headers={**headers(auth), "Idempotency-Key": key},
            json={
                "type": "EXPENSE",
                "account_id": account_data["id"],
                "amount": amount,
                "currency": "VND",
                "transaction_date": transaction_date,
            },
        )
        assert response.status_code == 201
    budget = test_client.post(
        "/api/v1/budgets",
        headers=headers(auth),
        json={
            "name": "First boundary",
            "start_date": "2026-08-01",
            "end_date": "2026-08-31",
            "total_limit": 10000,
            "currency": "VND",
        },
    ).json()
    status = test_client.get(f"/api/v1/budgets/{budget['id']}/status", headers=headers(auth)).json()
    assert status["spent"] == 2000


def test_budget_timezone_last_local_day_boundary(client):
    test_client, factory = client
    auth = register(test_client)
    with factory() as db:
        db.query(User).filter_by(id=auth["user"]["id"]).one().timezone = "Asia/Ho_Chi_Minh"
        db.commit()
    account_data = account(test_client, auth, "Last boundary", 100000)
    for key, transaction_date, amount in (
        ("last-at", "2026-08-31T16:59:59+00:00", 3000),
        ("last-after", "2026-08-31T17:00:01+00:00", 4000),
    ):
        response = test_client.post(
            "/api/v1/transactions",
            headers={**headers(auth), "Idempotency-Key": key},
            json={
                "type": "EXPENSE",
                "account_id": account_data["id"],
                "amount": amount,
                "currency": "VND",
                "transaction_date": transaction_date,
            },
        )
        assert response.status_code == 201
    budget = test_client.post(
        "/api/v1/budgets",
        headers=headers(auth),
        json={
            "name": "Last boundary",
            "start_date": "2026-08-01",
            "end_date": "2026-08-31",
            "total_limit": 10000,
            "currency": "VND",
        },
    ).json()
    status = test_client.get(f"/api/v1/budgets/{budget['id']}/status", headers=headers(auth)).json()
    assert status["spent"] == 3000


def test_budget_velocity_and_projection_are_exact(client):
    test_client, factory = client
    auth = register(test_client)
    account_data = account(test_client, auth, "Velocity", 100000)
    response = test_client.post(
        "/api/v1/transactions",
        headers={**headers(auth), "Idempotency-Key": "velocity-expense"},
        json={
            "type": "EXPENSE",
            "account_id": account_data["id"],
            "amount": 8000,
            "currency": "VND",
            "transaction_date": "2026-08-10T12:00:00+00:00",
        },
    )
    assert response.status_code == 201
    budget_data = test_client.post(
        "/api/v1/budgets",
        headers=headers(auth),
        json={
            "name": "Velocity",
            "start_date": "2026-08-01",
            "end_date": "2026-08-31",
            "total_limit": 10000,
            "currency": "VND",
        },
    ).json()
    with factory() as db:
        user = db.query(User).filter_by(id=auth["user"]["id"]).one()
        budget = db.query(Budget).filter_by(id=budget_data["id"]).one()
        status = budget_calculation(db, user, budget, today=date(2026, 8, 10))
    assert status["current_spending_velocity"] == 800.0
    assert status["projected_spending"] == 24800


def test_goal_deadline_calculations_are_deterministic(client):
    test_client, factory = client
    auth = register(test_client)
    goals = {}
    for name, target_date in (
        ("future", "2026-12-31"),
        ("today", "2026-08-27"),
        ("past", "2026-08-26"),
    ):
        goal = test_client.post(
            "/api/v1/goals",
            headers=headers(auth),
            json={
                "name": name,
                "target_amount": 10000,
                "currency": "VND",
                "target_date": target_date,
            },
        ).json()
        contribution = test_client.post(
            f"/api/v1/goals/{goal['id']}/contributions",
            headers=headers(auth),
            json={"amount": 4000},
        )
        assert contribution.status_code == 201
        goals[name] = goal["id"]
    with factory() as db:
        rows = {
            goal.name: goal
            for goal in db.query(FinancialGoal).filter(FinancialGoal.id.in_(goals.values())).all()
        }
        future = goal_calculation(rows["future"], today=date(2026, 8, 27))
        today = goal_calculation(rows["today"], today=date(2026, 8, 27))
        past = goal_calculation(rows["past"], today=date(2026, 8, 27))
    assert future["remaining"] == today["remaining"] == past["remaining"] == 6000
    assert future["progress"] == today["progress"] == past["progress"] == 0.4
    assert future["required_monthly_saving"] == 1200
    assert today["required_monthly_saving"] == past["required_monthly_saving"] == 6000
    assert future["forecast"] == "AHEAD"
    assert today["forecast"] == past["forecast"] == "BEHIND"


def test_zero_income_zero_target_and_update_validation(client):
    test_client, _ = client
    auth = register(test_client)
    account(test_client, auth, "No income", 100000)
    budget = test_client.post(
        "/api/v1/budgets",
        headers=headers(auth),
        json={
            "name": "No income",
            "start_date": "2026-08-01",
            "end_date": "2026-08-31",
            "total_limit": 10000,
            "currency": "VND",
        },
    ).json()
    status = test_client.get(f"/api/v1/budgets/{budget['id']}/status", headers=headers(auth)).json()
    assert status["spent"] == 0
    assert status["current_spending_velocity"] == 0
    assert status["projected_spending"] == 0
    assert all(
        value not in {float("nan"), float("inf")}
        for value in (status["utilization"], status["current_spending_velocity"])
    )
    assert (
        test_client.post(
            "/api/v1/goals",
            headers=headers(auth),
            json={"name": "Zero", "target_amount": 0, "currency": "VND"},
        ).status_code
        == 422
    )
    assert (
        test_client.patch(
            f"/api/v1/budgets/{budget['id']}", headers=headers(auth), json={"total_limit": -1}
        ).status_code
        == 422
    )
    assert (
        test_client.patch(
            f"/api/v1/budgets/{budget['id']}", headers=headers(auth), json={"status": "INVALID"}
        ).status_code
        == 422
    )
    assert (
        test_client.patch(
            f"/api/v1/budgets/{budget['id']}",
            headers=headers(auth),
            json={"start_date": "2026-09-01", "end_date": "2026-08-01"},
        ).status_code
        == 400
    )
    goal = test_client.post(
        "/api/v1/goals",
        headers=headers(auth),
        json={"name": "Validation", "target_amount": 1000, "currency": "VND"},
    ).json()
    assert (
        test_client.patch(
            f"/api/v1/goals/{goal['id']}", headers=headers(auth), json={"target_amount": -1}
        ).status_code
        == 422
    )
    assert (
        test_client.patch(
            f"/api/v1/goals/{goal['id']}", headers=headers(auth), json={"status": "INVALID"}
        ).status_code
        == 422
    )


def test_budget_split_and_ownership_and_goal_arithmetic(client):
    test_client, factory = client
    owner = register(test_client)
    other = register(test_client)
    owner_account = account(test_client, owner, "Owner", 100000)
    first = category(factory, owner["user"]["id"], "Food")
    second = category(factory, owner["user"]["id"], "Travel")
    transaction = test_client.post(
        "/api/v1/transactions",
        headers=headers(owner),
        json={
            "type": "EXPENSE",
            "account_id": owner_account["id"],
            "amount": 9000,
            "currency": "VND",
            "category_id": first,
            "transaction_date": "2026-08-15T12:00:00+00:00",
            "items": [
                {"amount": 4000, "category_id": first},
                {"amount": 5000, "category_id": second},
            ],
        },
    ).json()
    budget = test_client.post(
        "/api/v1/budgets",
        headers=headers(owner),
        json={
            "name": "Split",
            "start_date": "2026-08-01",
            "end_date": "2026-08-31",
            "total_limit": 10000,
            "currency": "VND",
            "categories": [{"category_id": second, "limit_amount": 6000}],
        },
    ).json()
    assert budget["categories"][0]["limit_amount"] == 6000
    assert budget["categories"][0]["spent"] == 5000
    assert (
        test_client.get(f"/api/v1/budgets/{budget['id']}", headers=headers(other)).status_code
        == 404
    )
    assert (
        test_client.get(
            f"/api/v1/transactions/{transaction['id']}", headers=headers(owner)
        ).status_code
        == 200
    )
    goal = test_client.post(
        "/api/v1/goals",
        headers=headers(owner),
        json={
            "name": "Emergency",
            "target_amount": 10000,
            "currency": "VND",
            "target_date": "2026-12-31",
        },
    ).json()
    contribution = test_client.post(
        f"/api/v1/goals/{goal['id']}/contributions", headers=headers(owner), json={"amount": 4000}
    ).json()
    assert contribution["amount"] == 4000
    status = test_client.get(f"/api/v1/goals/{goal['id']}/status", headers=headers(owner)).json()
    assert status["current"] == 4000
    assert status["remaining"] == 6000
    assert status["progress"] == 0.4
    assert status["required_monthly_saving"] > 0
    assert test_client.get(f"/api/v1/goals/{goal['id']}", headers=headers(other)).status_code == 404


def test_budget_uses_user_timezone_and_risk_thresholds(client):
    test_client, factory = client
    auth = register(test_client)
    with factory() as db:
        user = db.query(User).filter_by(id=auth["user"]["id"]).one()
        user.timezone = "Asia/Ho_Chi_Minh"
        db.commit()
    account_data = account(test_client, auth, "Timezone", 100000)
    test_client.post(
        "/api/v1/transactions",
        headers=headers(auth),
        json={
            "type": "EXPENSE",
            "account_id": account_data["id"],
            "amount": 5000,
            "currency": "VND",
            "transaction_date": "2026-07-31T17:30:00+00:00",
        },
    )
    budget = test_client.post(
        "/api/v1/budgets",
        headers=headers(auth),
        json={
            "name": "Local August",
            "start_date": "2026-08-01",
            "end_date": "2026-08-31",
            "total_limit": 10000,
            "currency": "VND",
        },
    ).json()
    status = test_client.get(f"/api/v1/budgets/{budget['id']}/status", headers=headers(auth)).json()
    assert status["spent"] == 5000
    assert _risk(0.8, 0, 100) == "WARNING"
    assert _risk(0.9, 0, 100) == "DANGER"
    assert _risk(1, 0, 100) == "OVER"
