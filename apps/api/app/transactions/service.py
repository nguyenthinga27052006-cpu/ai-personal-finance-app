from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db.models import (
    Account,
    AccountStatus,
    Category,
    CategoryType,
    EntryType,
    Merchant,
    Transaction,
    TransactionEntry,
    TransactionItem,
    TransactionStatus,
    TransactionType,
    User,
)
from app.transactions.schemas import TransactionCreate


class TransactionError(Exception):
    pass


class TransactionNotFoundError(TransactionError):
    pass


class IdempotencyConflictError(TransactionError):
    pass


def _owned_account(db: Session, user: User, account_id: str) -> Account:
    account = db.scalar(
        select(Account)
        .where(Account.id == account_id, Account.user_id == user.id)
        .with_for_update()
    )
    if account is None or account.status != AccountStatus.ACTIVE.value or account.is_archived:
        raise TransactionError("Account is not available")
    return account


def _category_allowed(
    db: Session, user: User, category_id: str | None, transaction_type: TransactionType
) -> Category | None:
    if category_id is None:
        return None
    category = db.scalar(
        select(Category).where(
            Category.id == category_id,
            Category.is_active.is_(True),
            (Category.is_system.is_(True) | (Category.user_id == user.id)),
        )
    )
    if category is None:
        raise TransactionError("Category is not available")
    if transaction_type == TransactionType.EXPENSE and category.type not in (
        CategoryType.EXPENSE.value,
        CategoryType.BOTH.value,
    ):
        raise TransactionError("Category type does not match transaction")
    if transaction_type == TransactionType.INCOME and category.type not in (
        CategoryType.INCOME.value,
        CategoryType.BOTH.value,
    ):
        raise TransactionError("Category type does not match transaction")
    return category


def _merchant(db: Session, merchant_id: str | None) -> Merchant | None:
    if merchant_id is None:
        return None
    merchant = db.get(Merchant, merchant_id)
    if merchant is None or merchant.status != "ACTIVE":
        raise TransactionError("Merchant is not available")
    return merchant


def _existing_idempotent(db: Session, user: User, key: str | None) -> Transaction | None:
    if not key:
        return None
    return db.scalar(
        select(Transaction)
        .options(selectinload(Transaction.entries), selectinload(Transaction.items))
        .where(Transaction.user_id == user.id, Transaction.idempotency_key == key)
    )


def _entry(account: Account, amount: int, entry_type: EntryType) -> TransactionEntry:
    return TransactionEntry(
        account_id=account.id,
        amount=amount,
        currency=account.currency,
        entry_type=entry_type,
    )


def create_transaction(
    db: Session, user: User, payload: TransactionCreate, idempotency_key: str | None
) -> Transaction:
    if idempotency_key and len(idempotency_key) > 128:
        raise TransactionError("Idempotency-Key must not exceed 128 characters")
    existing = _existing_idempotent(db, user, idempotency_key)
    if existing:
        if (
            existing.type != payload.type.value
            or existing.account_id != payload.account_id
            or existing.amount != payload.amount
            or existing.currency != payload.currency
        ):
            raise IdempotencyConflictError
        return existing
    account = _owned_account(db, user, payload.account_id)
    if account.currency != payload.currency:
        raise TransactionError("Transaction currency must match account currency")
    _category_allowed(db, user, payload.category_id, payload.type)
    for item in payload.items:
        _category_allowed(db, user, item.category_id, payload.type)
    _merchant(db, payload.merchant_id)
    if payload.type == TransactionType.TRANSFER:
        raise TransactionError("Use the transfer endpoint for transfers")
    if payload.type == TransactionType.REFUND:
        return _create_refund(db, user, payload, idempotency_key, account)
    if payload.type == TransactionType.ADJUSTMENT:
        entry_type = payload.adjustment_entry_type
    else:
        entry_type = EntryType.CREDIT if payload.type == TransactionType.INCOME else EntryType.DEBIT
    signed_amount = payload.amount if entry_type == EntryType.CREDIT else -payload.amount
    if account.current_balance + signed_amount < 0:
        raise TransactionError("Insufficient account balance")
    transaction = Transaction(
        user_id=user.id,
        account_id=account.id,
        type=payload.type,
        status=TransactionStatus.POSTED.value,
        currency=payload.currency,
        amount=payload.amount,
        transaction_date=payload.transaction_date or datetime.now(timezone.utc),
        description=payload.description,
        merchant_id=payload.merchant_id,
        category_id=payload.category_id,
        idempotency_key=idempotency_key,
        entries=[_entry(account, signed_amount, entry_type)],
        items=[TransactionItem(**item.model_dump()) for item in payload.items],
    )
    db.add(transaction)
    account.current_balance += signed_amount
    db.flush()
    return transaction


def _create_refund(
    db: Session, user: User, payload: TransactionCreate, key: str | None, account: Account
) -> Transaction:
    original = db.scalar(
        select(Transaction)
        .options(selectinload(Transaction.entries))
        .where(Transaction.id == payload.parent_transaction_id, Transaction.user_id == user.id)
    )
    if (
        original is None
        or original.type != TransactionType.EXPENSE.value
        or original.status != TransactionStatus.POSTED.value
    ):
        raise TransactionError("Refund original is not eligible")
    refunded = db.scalar(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.parent_transaction_id == original.id,
            Transaction.type == TransactionType.REFUND.value,
            Transaction.status == TransactionStatus.POSTED.value,
        )
    )
    if refunded + payload.amount > original.amount:
        raise TransactionError("Refund exceeds refundable amount")
    if original.account_id != account.id or original.currency != payload.currency:
        raise TransactionError("Refund account or currency does not match original")
    transaction = Transaction(
        user_id=user.id,
        account_id=account.id,
        type=TransactionType.REFUND,
        status=TransactionStatus.POSTED.value,
        currency=payload.currency,
        amount=payload.amount,
        transaction_date=payload.transaction_date or datetime.now(timezone.utc),
        description=payload.description,
        merchant_id=payload.merchant_id,
        category_id=payload.category_id,
        parent_transaction_id=original.id,
        idempotency_key=key,
        entries=[_entry(account, payload.amount, EntryType.CREDIT)],
    )
    db.add(transaction)
    account.current_balance += payload.amount
    db.flush()
    return transaction


def create_transfer(
    db: Session,
    user: User,
    source_id: str,
    destination_id: str,
    amount: int,
    currency: str,
    description: str | None,
    transaction_date: datetime | None,
    key: str | None,
) -> Transaction:
    existing = _existing_idempotent(db, user, key)
    if existing:
        existing_destination = next(
            (
                entry.account_id
                for entry in existing.entries
                if entry.account_id != existing.account_id
            ),
            None,
        )
        if (
            existing.type != TransactionType.TRANSFER.value
            or existing.account_id != source_id
            or existing_destination != destination_id
            or existing.amount != amount
            or existing.currency != currency
        ):
            raise IdempotencyConflictError
        return existing
    if amount <= 0 or source_id == destination_id:
        raise TransactionError("Transfer requires distinct positive source and destination")
    accounts = list(
        db.scalars(
            select(Account)
            .where(Account.id.in_([source_id, destination_id]), Account.user_id == user.id)
            .with_for_update()
        ).all()
    )
    by_id = {account.id: account for account in accounts}
    source = by_id.get(source_id)
    destination = by_id.get(destination_id)
    if (
        source is None
        or destination is None
        or any(
            account.is_archived or account.status != AccountStatus.ACTIVE.value
            for account in (source, destination)
        )
    ):
        raise TransactionError("Transfer account is not available")
    if source.currency != destination.currency or source.currency != currency:
        raise TransactionError("Transfer currency must match both accounts")
    if source.current_balance - amount < 0:
        raise TransactionError("Insufficient source account balance")
    group_id = str(uuid.uuid4())
    transaction = Transaction(
        user_id=user.id,
        account_id=source.id,
        type=TransactionType.TRANSFER,
        status=TransactionStatus.POSTED.value,
        currency=currency,
        amount=amount,
        transaction_date=transaction_date or datetime.now(timezone.utc),
        description=description,
        transfer_group_id=group_id,
        idempotency_key=key,
        entries=[
            _entry(source, -amount, EntryType.DEBIT),
            _entry(destination, amount, EntryType.CREDIT),
        ],
    )
    db.add(transaction)
    source.current_balance -= amount
    destination.current_balance += amount
    db.flush()
    return transaction


def list_transactions(
    db: Session,
    user: User,
    page: int,
    page_size: int,
    account_id: str | None,
    transaction_type: TransactionType | None,
) -> tuple[list[Transaction], int]:
    base = select(Transaction).where(Transaction.user_id == user.id)
    if account_id:
        base = base.where(Transaction.account_id == account_id)
    if transaction_type:
        base = base.where(Transaction.type == transaction_type.value)
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    statement = (
        base.options(selectinload(Transaction.entries), selectinload(Transaction.items))
        .order_by(Transaction.transaction_date.desc(), Transaction.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(db.scalars(statement).all()), total


def get_transaction(db: Session, user: User, transaction_id: str) -> Transaction:
    transaction = db.scalar(
        select(Transaction)
        .options(selectinload(Transaction.entries), selectinload(Transaction.items))
        .where(Transaction.id == transaction_id, Transaction.user_id == user.id)
    )
    if transaction is None:
        raise TransactionNotFoundError
    return transaction
