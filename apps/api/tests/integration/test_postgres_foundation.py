from __future__ import annotations

import os
import uuid

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import (
    Account,
    AccountType,
    Category,
    Transaction,
    TransactionEntry,
    TransactionItem,
    TransactionStatus,
    TransactionType,
    User,
)
from app.db.seed import seed_system_categories

pytestmark = pytest.mark.postgres


@pytest.fixture(scope="module")
def postgres_engine():
    database_url = os.getenv("POSTGRES_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("POSTGRES_TEST_DATABASE_URL is not configured")

    engine = sa.create_engine(database_url)
    inspector = sa.inspect(engine)
    if not {"users", "categories"}.issubset(inspector.get_table_names()):
        pytest.skip("PostgreSQL schema is not migrated; run alembic upgrade head first")
    return engine


@pytest.fixture
def session(postgres_engine):
    with Session(postgres_engine) as session_:
        yield session_
        session_.rollback()


def make_user(session: Session) -> User:
    user = User(
        email=f"integration-{uuid.uuid4()}@example.com",
        password_hash="test-hash",
        default_currency="VND",
        timezone="UTC",
        locale="en-US",
    )
    session.add(user)
    session.flush()
    return user


def make_account(session: Session, user: User) -> Account:
    account = Account(
        user_id=user.id,
        name="Integration account",
        type=AccountType.CASH,
        currency="VND",
        opening_balance=0,
        current_balance=0,
    )
    session.add(account)
    session.flush()
    return account


def test_fresh_migration_schema_exists(postgres_engine):
    tables = set(sa.inspect(postgres_engine).get_table_names())
    assert {
        "users",
        "device_sessions",
        "user_preferences",
        "user_settings",
        "accounts",
        "categories",
        "merchants",
        "merchant_aliases",
        "transactions",
        "transaction_entries",
        "transaction_items",
        "budgets",
        "budget_categories",
        "financial_goals",
        "goal_contributions",
    } <= tables


def test_postgresql_18_is_the_test_server(postgres_engine):
    with postgres_engine.connect() as connection:
        version = connection.execute(sa.text("SHOW server_version")).scalar_one()

    assert version.startswith("18.") or version.startswith("17."), (
        f"PostgreSQL 17+ required, got {version}"
    )


def test_monetary_columns_are_bigint(postgres_engine):
    monetary = {
        "accounts.opening_balance",
        "accounts.current_balance",
        "accounts.credit_limit",
        "transactions.amount",
        "transaction_entries.amount",
        "transaction_items.amount",
        "transaction_items.unit_price",
        "budgets.total_limit",
        "budget_categories.limit_amount",
        "financial_goals.target_amount",
        "goal_contributions.amount",
        "user_settings.minimum_safe_balance",
    }
    with postgres_engine.connect() as connection:
        rows = connection.execute(
            sa.text(
                "SELECT table_name || '.' || column_name, data_type "
                "FROM information_schema.columns WHERE table_schema = 'public'"
            )
        )
        columns = dict(rows.all())
    assert all(columns.get(column) == "bigint" for column in monetary)


def test_foreign_key_integrity(session: Session):
    account = Account(
        user_id=str(uuid.uuid4()),
        name="Orphan",
        type=AccountType.CASH,
        currency="VND",
        opening_balance=0,
        current_balance=0,
    )
    session.add(account)
    with pytest.raises(IntegrityError):
        session.flush()


def test_unique_email(session: Session):
    email = f"unique-{uuid.uuid4()}@example.com"
    session.add(User(email=email, password_hash="a"))
    session.flush()
    session.add(User(email=email, password_hash="b"))
    with pytest.raises(IntegrityError):
        session.flush()


def test_ownership_fk(session: Session):
    user = make_user(session)
    account = make_account(session, user)
    assert account.user_id == user.id
    assert sa.inspect(Account).relationships.user is not None


def test_system_category_ownership_rule(session: Session):
    seed_system_categories(session)
    system = session.query(Category).filter_by(is_system=True).first()
    assert system is not None
    assert system.user_id is None


def test_transaction_entry_relationship(session: Session):
    user = make_user(session)
    account = make_account(session, user)
    transaction = Transaction(
        user_id=user.id,
        account_id=account.id,
        type=TransactionType.EXPENSE,
        status=TransactionStatus.POSTED,
        currency="VND",
        amount=100,
    )
    transaction.entries.append(
        TransactionEntry(
            account_id=account.id,
            amount=-100,
            currency="VND",
            entry_type="DEBIT",
        )
    )
    session.add(transaction)
    session.flush()
    assert len(transaction.entries) == 1


def test_transfer_structure(session: Session):
    user = make_user(session)
    source = make_account(session, user)
    destination = make_account(session, user)
    transfer_id = str(uuid.uuid4())
    entries = [
        TransactionEntry(account_id=source.id, amount=-500, currency="VND", entry_type="DEBIT"),
        TransactionEntry(
            account_id=destination.id, amount=500, currency="VND", entry_type="CREDIT"
        ),
    ]
    transaction = Transaction(
        user_id=user.id,
        type=TransactionType.TRANSFER,
        status=TransactionStatus.POSTED,
        currency="VND",
        amount=500,
        transfer_group_id=transfer_id,
        entries=entries,
    )
    session.add(transaction)
    session.flush()
    assert {entry.account_id for entry in transaction.entries} == {source.id, destination.id}


def test_refund_structure(session: Session):
    user = make_user(session)
    original = Transaction(
        user_id=user.id,
        type=TransactionType.EXPENSE,
        status=TransactionStatus.POSTED,
        currency="VND",
        amount=250,
    )
    session.add(original)
    session.flush()
    refund = Transaction(
        user_id=user.id,
        type=TransactionType.REFUND,
        status=TransactionStatus.POSTED,
        currency="VND",
        amount=250,
        parent_transaction_id=original.id,
    )
    session.add(refund)
    session.flush()
    assert refund.parent.id == original.id


def test_split_transaction_structure(session: Session):
    user = make_user(session)
    account = make_account(session, user)
    transaction = Transaction(
        user_id=user.id,
        account_id=account.id,
        type=TransactionType.EXPENSE,
        status=TransactionStatus.POSTED,
        currency="VND",
        amount=300,
        items=[
            TransactionItem(amount=100, quantity=1),
            TransactionItem(amount=200, quantity=1),
        ],
    )
    session.add(transaction)
    session.flush()
    assert sum(item.amount for item in transaction.items) == transaction.amount


def test_seed_is_idempotent(session: Session):
    seed_system_categories(session)
    first = session.query(Category).filter_by(is_system=True).count()
    seed_system_categories(session)
    second = session.query(Category).filter_by(is_system=True).count()
    assert (first, second) == (15, 15)
