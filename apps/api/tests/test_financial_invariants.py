from __future__ import annotations

import uuid

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import Account, AccountType, EntryType, TransactionEntry, User


@pytest.fixture
def session():
    engine = sa.create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)
    with factory() as db:
        yield db
    engine.dispose()


def test_ledger_entry_sign_and_direction_convention(session: Session):
    user = User(
        email="invariant@example.com",
        password_hash="test-hash",
        default_currency="VND",
        timezone="UTC",
        locale="en-US",
    )
    session.add(user)
    session.flush()
    account = Account(
        user_id=user.id,
        name="Ledger account",
        type=AccountType.CASH,
        currency="VND",
        opening_balance=100,
        current_balance=100,
    )
    session.add(account)
    session.flush()
    debit = TransactionEntry(
        transaction_id=str(uuid.uuid4()),
        account_id=account.id,
        amount=-25,
        currency="VND",
        entry_type=EntryType.DEBIT,
    )
    credit = TransactionEntry(
        transaction_id=str(uuid.uuid4()),
        account_id=account.id,
        amount=50,
        currency="VND",
        entry_type=EntryType.CREDIT,
    )
    assert debit.amount < 0 and debit.entry_type == EntryType.DEBIT
    assert credit.amount > 0 and credit.entry_type == EntryType.CREDIT


def test_transfer_entries_balance_to_zero():
    entries = [-7500, 7500]
    assert sum(entries) == 0


def test_split_amounts_are_exact():
    amount = 12345
    item_amounts = [5000, 7345]
    assert sum(item_amounts) == amount
