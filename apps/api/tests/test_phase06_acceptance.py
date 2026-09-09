from unittest.mock import patch

import sqlalchemy as sa
from sqlalchemy.orm import Session
from test_financial_core import account, headers, register
from test_phase07 import client  # noqa: F401

from app.db.models import Account, Transaction, TransactionEntry, User
from app.transactions.schemas import TransactionCreate
from app.transactions.service import create_transaction, create_transfer


def _ledger_balance(db: Session, account_id: str) -> int:
    account_row = db.get(Account, account_id)
    assert account_row is not None
    posted = db.scalar(
        sa.select(sa.func.coalesce(sa.func.sum(TransactionEntry.amount), 0)).where(
            TransactionEntry.account_id == account_id
        )
    )
    return account_row.opening_balance + int(posted or 0)


def test_mixed_ledger_reconciles_cached_balances_and_transfer_is_neutral(client):  # noqa: F811
    test_client, factory = client
    auth = register(test_client)
    source = account(test_client, auth, "Source", 100000)
    destination = account(test_client, auth, "Destination", 20000)
    common = {"headers": headers(auth)}
    assert (
        test_client.post(
            "/api/v1/transactions",
            **common,
            json={"type": "INCOME", "account_id": source["id"], "amount": 5000, "currency": "VND"},
        ).status_code
        == 201
    )
    expense = test_client.post(
        "/api/v1/transactions",
        **common,
        json={"type": "EXPENSE", "account_id": source["id"], "amount": 12000, "currency": "VND"},
    )
    assert expense.status_code == 201
    assert (
        test_client.post(
            f"/api/v1/transactions/{expense.json()['id']}/refund",
            **common,
            json={"account_id": source["id"], "amount": 2000, "currency": "VND"},
        ).status_code
        == 201
    )
    transfer = test_client.post(
        "/api/v1/transfers",
        **common,
        json={
            "source_account_id": source["id"],
            "destination_account_id": destination["id"],
            "amount": 10000,
            "currency": "VND",
        },
    )
    assert transfer.status_code == 201
    with factory() as db:
        assert _ledger_balance(db, source["id"]) == db.get(Account, source["id"]).current_balance
        assert (
            _ledger_balance(db, destination["id"])
            == db.get(Account, destination["id"]).current_balance
        )
        entries = db.scalars(
            sa.select(TransactionEntry).where(
                TransactionEntry.transaction_id == transfer.json()["id"]
            )
        ).all()
        assert sum(entry.amount for entry in entries) == 0


def test_transaction_failure_rolls_back_record_entries_items_and_balance(client):  # noqa: F811
    test_client, factory = client
    auth = register(test_client)
    owner = auth["user"]["id"]
    with factory() as db:
        user = db.get(User, owner)
        assert user is not None
        account_row = Account(
            user_id=owner,
            name="Atomic",
            type="BANK",
            currency="VND",
            opening_balance=100000,
            current_balance=100000,
        )
        db.add(account_row)
        db.flush()
        db.commit()
        payload = TransactionCreate(
            type="EXPENSE", account_id=account_row.id, amount=1000, currency="VND", items=[]
        )
        original_balance = account_row.current_balance
        with patch.object(db, "flush", side_effect=RuntimeError("controlled failure")):
            try:
                create_transaction(db, user, payload, "atomic-failure")
                db.commit()
            except RuntimeError:
                db.rollback()
        assert db.get(Account, account_row.id).current_balance == original_balance
        assert (
            db.scalar(
                sa.select(sa.func.count())
                .select_from(Transaction)
                .where(Transaction.idempotency_key == "atomic-failure")
            )
            == 0
        )
        assert db.scalar(sa.select(sa.func.count()).select_from(TransactionEntry)) == 0


def test_cross_user_transfer_and_refund_are_denied_without_side_effect(client):  # noqa: F811
    test_client, _ = client
    owner = register(test_client)
    attacker = register(test_client)
    owner_account = account(test_client, owner, "Owner", 100000)
    attacker_account = account(test_client, attacker, "Attacker", 100000)
    transfer = test_client.post(
        "/api/v1/transfers",
        headers=headers(attacker),
        json={
            "source_account_id": owner_account["id"],
            "destination_account_id": attacker_account["id"],
            "amount": 1000,
            "currency": "VND",
        },
    )
    assert transfer.status_code == 400
    expense = test_client.post(
        "/api/v1/transactions",
        headers={**headers(owner), "Idempotency-Key": "owner-expense"},
        json={
            "type": "EXPENSE",
            "account_id": owner_account["id"],
            "amount": 1000,
            "currency": "VND",
        },
    ).json()
    refund = test_client.post(
        f"/api/v1/transactions/{expense['id']}/refund",
        headers=headers(attacker),
        json={"account_id": attacker_account["id"], "amount": 500, "currency": "VND"},
    )
    assert refund.status_code == 400
    assert (
        test_client.get(
            f"/api/v1/transactions/{expense['id']}", headers=headers(attacker)
        ).status_code
        == 404
    )


def test_transfer_failure_rolls_back_both_accounts_and_group(client):  # noqa: F811
    test_client, factory = client
    auth = register(test_client)
    source = account(test_client, auth, "Atomic source", 100000)
    destination = account(test_client, auth, "Atomic destination", 20000)
    with factory() as db:
        user = db.get(User, auth["user"]["id"])
        source_row = db.get(Account, source["id"])
        destination_row = db.get(Account, destination["id"])
        assert user is not None and source_row is not None and destination_row is not None
        before = (source_row.current_balance, destination_row.current_balance)
        with patch.object(db, "flush", side_effect=RuntimeError("controlled transfer failure")):
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
                    "atomic-transfer",
                )
                db.commit()
            except RuntimeError:
                db.rollback()
        assert (source_row.current_balance, destination_row.current_balance) == before
        assert (
            db.scalar(
                sa.select(sa.func.count())
                .select_from(Transaction)
                .where(Transaction.idempotency_key == "atomic-transfer")
            )
            == 0
        )


def test_refund_failure_rolls_back_refund_and_balance(client):  # noqa: F811
    test_client, factory = client
    auth = register(test_client)
    account_data = account(test_client, auth, "Atomic refund", 100000)
    expense = test_client.post(
        "/api/v1/transactions",
        headers={**headers(auth), "Idempotency-Key": "atomic-refund-expense"},
        json={
            "type": "EXPENSE",
            "account_id": account_data["id"],
            "amount": 1000,
            "currency": "VND",
        },
    ).json()
    with factory() as db:
        user = db.get(User, auth["user"]["id"])
        account_row = db.get(Account, account_data["id"])
        assert user is not None and account_row is not None
        before = account_row.current_balance
        payload = TransactionCreate(
            type="REFUND",
            account_id=account_data["id"],
            amount=500,
            currency="VND",
            parent_transaction_id=expense["id"],
        )
        with patch.object(db, "flush", side_effect=RuntimeError("controlled refund failure")):
            try:
                create_transaction(db, user, payload, "atomic-refund")
                db.commit()
            except RuntimeError:
                db.rollback()
        assert account_row.current_balance == before
        assert (
            db.scalar(
                sa.select(sa.func.count())
                .select_from(Transaction)
                .where(Transaction.idempotency_key == "atomic-refund")
            )
            == 0
        )
        assert (
            db.scalar(
                sa.select(sa.func.count())
                .select_from(Transaction)
                .where(Transaction.parent_transaction_id == expense["id"])
            )
            == 0
        )
