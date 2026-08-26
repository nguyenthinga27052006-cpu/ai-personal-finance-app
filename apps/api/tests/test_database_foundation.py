from __future__ import annotations

import uuid

import pytest
import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models import (
    Account,
    AccountType,
    Category,
    CategoryType,
    FinancialGoal,
    GoalStatus,
    Merchant,
    Transaction,
    TransactionEntry,
    TransactionItem,
    TransactionStatus,
    TransactionType,
    User,
)
from app.db.seed import seed_system_categories


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if dbapi_connection.__class__.__module__.split(".", maxsplit=1)[0] != "sqlite3":
        return
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture
def session() -> Session:
    engine = sa.create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session_:
        yield session_


def test_fresh_migration_creates_expected_tables(session: Session) -> None:
    tables = sa.inspect(session.bind).get_table_names()
    required = {
        "users",
        "accounts",
        "categories",
        "merchants",
        "transactions",
        "transaction_entries",
        "transaction_items",
        "budgets",
        "budget_categories",
        "financial_goals",
        "goal_contributions",
        "user_preferences",
        "user_settings",
        "merchant_aliases",
    }

    assert required.issubset(set(tables))


def test_unique_email_and_foreign_key_integrity(session: Session) -> None:
    user = User(
        email="user@example.com",
        password_hash="hash",
        display_name="Tester",
        default_currency="VND",
        timezone="Asia/Ho_Chi_Minh",
        locale="vi-VN",
    )
    session.add(user)
    session.commit()

    duplicate = User(
        email="user@example.com",
        password_hash="hash-2",
        display_name="Duplicate",
        default_currency="VND",
        timezone="UTC",
        locale="en-US",
    )
    session.add(duplicate)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

    bad_account = Account(
        user_id=str(uuid.uuid4()),
        name="Orphan account",
        type=AccountType.CASH,
        currency="VND",
        opening_balance=0,
        current_balance=0,
    )
    session.add(bad_account)
    with pytest.raises(IntegrityError):
        session.flush()


def test_money_and_relationship_structure(session: Session) -> None:
    user = User(
        email="money@example.com",
        password_hash="hash",
        display_name="Money",
        default_currency="VND",
        timezone="Asia/Ho_Chi_Minh",
        locale="vi-VN",
    )
    session.add(user)
    session.flush()

    account = Account(
        user_id=user.id,
        name="Checking",
        type=AccountType.BANK,
        currency="VND",
        opening_balance=0,
        current_balance=250000,
    )
    session.add(account)
    session.flush()

    category = Category(
        user_id=user.id,
        name="Food",
        type=CategoryType.EXPENSE,
        is_system=False,
        is_active=True,
        sort_order=1,
    )
    session.add(category)
    session.flush()

    transaction = Transaction(
        user_id=user.id,
        account_id=account.id,
        category_id=category.id,
        type=TransactionType.EXPENSE,
        status=TransactionStatus.POSTED,
        currency="VND",
        amount=75000,
        transaction_date=sa.func.now(),
        description="Lunch",
    )
    session.add(transaction)
    session.flush()

    entry = TransactionEntry(
        transaction_id=transaction.id,
        account_id=account.id,
        amount=75000,
        currency="VND",
        entry_type="DEBIT",
    )
    session.add(entry)
    session.flush()

    item = TransactionItem(
        transaction_id=transaction.id,
        category_id=category.id,
        description="Restaurant",
        amount=75000,
        quantity=1,
    )
    session.add(item)
    session.flush()

    assert transaction.amount == 75000
    assert entry.amount == 75000
    assert item.amount == 75000
    assert item.transaction_id == transaction.id


def test_split_transaction_structure(session: Session) -> None:
    user = User(
        email="split@example.com",
        password_hash="hash",
        display_name="Split",
        default_currency="VND",
        timezone="UTC",
        locale="en-US",
    )
    session.add(user)
    session.flush()

    account = Account(
        user_id=user.id,
        name="Cash",
        type=AccountType.CASH,
        currency="VND",
        opening_balance=0,
        current_balance=150000,
    )
    session.add(account)
    session.flush()

    category = Category(
        user_id=user.id,
        name="Shopping",
        type=CategoryType.EXPENSE,
        is_system=False,
        is_active=True,
        sort_order=2,
    )
    session.add(category)
    session.flush()

    transaction = Transaction(
        user_id=user.id,
        account_id=account.id,
        category_id=category.id,
        type=TransactionType.EXPENSE,
        status=TransactionStatus.POSTED,
        currency="VND",
        amount=150000,
        transaction_date=sa.func.now(),
        description="Split purchase",
    )
    session.add(transaction)
    session.flush()

    session.add_all(
        [
            TransactionItem(
                transaction_id=transaction.id, category_id=category.id, amount=100000, quantity=1
            ),
            TransactionItem(
                transaction_id=transaction.id, category_id=category.id, amount=50000, quantity=1
            ),
        ]
    )
    session.flush()

    total = (
        session.query(sa.func.sum(TransactionItem.amount))
        .filter_by(transaction_id=transaction.id)
        .scalar()
    )
    assert total == 150000


def test_seed_is_idempotent(session: Session) -> None:
    seed_system_categories(session)
    first_count = session.query(Category).filter_by(is_system=True).count()

    seed_system_categories(session)
    second_count = session.query(Category).filter_by(is_system=True).count()

    assert first_count == second_count
    assert first_count >= 10


def test_goal_and_merchant_relationships(session: Session) -> None:
    user = User(
        email="goal@example.com",
        password_hash="hash",
        display_name="Goal",
        default_currency="VND",
        timezone="UTC",
        locale="en-US",
    )
    session.add(user)
    session.flush()

    goal = FinancialGoal(
        user_id=user.id,
        name="Emergency Fund",
        target_amount=1000000,
        currency="VND",
        status=GoalStatus.ACTIVE,
    )
    session.add(goal)
    session.flush()

    merchant = Merchant(
        canonical_name="Cofee House", normalized_name="coffee house", status="ACTIVE"
    )
    session.add(merchant)
    session.flush()

    assert goal.user_id == user.id
    assert merchant.canonical_name == "Cofee House"
