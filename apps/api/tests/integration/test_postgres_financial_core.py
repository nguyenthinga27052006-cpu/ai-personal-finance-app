from __future__ import annotations

import os
import uuid
from unittest.mock import patch

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Account, Transaction, TransactionEntry, TransactionType
from app.db.session import get_db
from app.main import app
from app.transactions.service import create_transfer

pytestmark = pytest.mark.postgres


@pytest.fixture(scope="module")
def postgres_engine():
    database_url = os.getenv("POSTGRES_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("POSTGRES_TEST_DATABASE_URL is not configured")
    engine = sa.create_engine(database_url)
    inspector = sa.inspect(engine)
    if not {"users", "accounts", "transactions", "transaction_entries"}.issubset(
        inspector.get_table_names()
    ):
        pytest.skip("PostgreSQL schema is not migrated; run alembic upgrade head first")
    return engine


@pytest.fixture
def client(postgres_engine):
    def override_get_db():
        with Session(postgres_engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)


def test_postgresql_financial_core_atomic_lifecycle(client, postgres_engine):
    email = f"postgres-financial-{uuid.uuid4()}@example.com"
    registered = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "correct horse battery staple"},
    )
    assert registered.status_code == 201
    auth = registered.json()
    headers = {"Authorization": f"Bearer {auth['access_token']}"}

    source = client.post(
        "/api/v1/accounts",
        headers=headers,
        json={
            "name": "Postgres source",
            "type": "BANK",
            "currency": "VND",
            "opening_balance": 100000,
        },
    ).json()
    destination = client.post(
        "/api/v1/accounts",
        headers=headers,
        json={
            "name": "Postgres destination",
            "type": "CASH",
            "currency": "VND",
            "opening_balance": 0,
        },
    ).json()

    expense = client.post(
        "/api/v1/transactions",
        headers={**headers, "Idempotency-Key": "pg-expense"},
        json={"type": "EXPENSE", "account_id": source["id"], "amount": 10000, "currency": "VND"},
    )
    assert expense.status_code == 201
    retry = client.post(
        "/api/v1/transactions",
        headers={**headers, "Idempotency-Key": "pg-expense"},
        json={"type": "EXPENSE", "account_id": source["id"], "amount": 10000, "currency": "VND"},
    )
    assert retry.status_code == 201
    assert retry.json()["id"] == expense.json()["id"]

    transfer = client.post(
        "/api/v1/transfers",
        headers={**headers, "Idempotency-Key": "pg-transfer"},
        json={
            "source_account_id": source["id"],
            "destination_account_id": destination["id"],
            "amount": 25000,
            "currency": "VND",
        },
    )
    assert transfer.status_code == 201

    refund = client.post(
        f"/api/v1/transactions/{expense.json()['id']}/refund",
        headers={**headers, "Idempotency-Key": "pg-refund"},
        json={
            "account_id": source["id"],
            "amount": 5000,
            "currency": "VND",
        },
    )
    assert refund.status_code == 201

    with Session(postgres_engine) as db:
        source_row = db.get(Account, source["id"])
        destination_row = db.get(Account, destination["id"])
        assert source_row is not None and destination_row is not None
        assert source_row.current_balance == 70000
        assert destination_row.current_balance == 25000
        transfer_entries = db.scalars(
            select(TransactionEntry).where(TransactionEntry.transaction_id == transfer.json()["id"])
        ).all()
        assert sum(entry.amount for entry in transfer_entries) == 0
        assert (
            db.scalar(
                select(sa.func.count())
                .select_from(Transaction)
                .where(
                    Transaction.user_id == auth["user"]["id"],
                    Transaction.type == TransactionType.EXPENSE.value,
                )
            )
            == 1
        )
        for account_id in (source["id"], destination["id"]):
            account_row = db.get(Account, account_id)
            assert account_row is not None
            ledger_total = db.scalar(
                select(sa.func.coalesce(sa.func.sum(TransactionEntry.amount), 0)).where(
                    TransactionEntry.account_id == account_id
                )
            )
            assert account_row.current_balance == account_row.opening_balance + int(
                ledger_total or 0
            )


def test_postgresql_transfer_failure_rolls_back_both_sides(client, postgres_engine):
    registered = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"postgres-rollback-{uuid.uuid4()}@example.com",
            "password": "correct horse battery staple",
        },
    )
    assert registered.status_code == 201
    auth = registered.json()
    headers = {"Authorization": f"Bearer {auth['access_token']}"}
    source = client.post(
        "/api/v1/accounts",
        headers=headers,
        json={
            "name": "Rollback source",
            "type": "BANK",
            "currency": "VND",
            "opening_balance": 10000,
        },
    ).json()
    destination = client.post(
        "/api/v1/accounts",
        headers=headers,
        json={
            "name": "Rollback destination",
            "type": "BANK",
            "currency": "VND",
            "opening_balance": 0,
        },
    ).json()
    with Session(postgres_engine) as db:
        from app.db.models import User

        user = db.get(User, auth["user"]["id"])
        source_row = db.get(Account, source["id"])
        destination_row = db.get(Account, destination["id"])
        assert user is not None and source_row is not None and destination_row is not None
        with patch.object(db, "flush", side_effect=RuntimeError("controlled postgres failure")):
            try:
                create_transfer(
                    db,
                    user,
                    source["id"],
                    destination["id"],
                    1000,
                    "VND",
                    None,
                    None,
                    "pg-rollback",
                )
                db.commit()
            except RuntimeError:
                db.rollback()
        assert source_row.current_balance == 10000
        assert destination_row.current_balance == 0
        assert (
            db.scalar(
                select(sa.func.count())
                .select_from(Transaction)
                .where(Transaction.idempotency_key == "pg-rollback")
            )
            == 0
        )
