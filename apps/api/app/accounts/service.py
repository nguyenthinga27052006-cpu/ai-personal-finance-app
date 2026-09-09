from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Account, AccountStatus, User


class AccountNotFoundError(Exception):
    pass


class AccountConflictError(Exception):
    pass


def list_accounts(db: Session, user: User, include_archived: bool = False) -> list[Account]:
    statement = (
        select(Account).where(Account.user_id == user.id).order_by(Account.created_at, Account.id)
    )
    if not include_archived:
        statement = statement.where(Account.is_archived.is_(False))
    return list(db.scalars(statement).all())


def get_account(db: Session, user: User, account_id: str) -> Account:
    account = db.scalar(select(Account).where(Account.id == account_id, Account.user_id == user.id))
    if account is None:
        raise AccountNotFoundError
    return account


def create_account(db: Session, user: User, **values: object) -> Account:
    account = Account(user_id=user.id, current_balance=values["opening_balance"], **values)
    db.add(account)
    db.flush()
    return account


def update_account(db: Session, user: User, account_id: str, values: dict[str, object]) -> Account:
    account = get_account(db, user, account_id)
    if account.is_archived and any(key not in {"status", "is_archived"} for key in values):
        raise AccountConflictError("Archived accounts cannot be edited")
    if values.get("is_archived") is True:
        values["status"] = AccountStatus.ARCHIVED
    if values.get("status") == AccountStatus.ARCHIVED:
        values["is_archived"] = True
    for key, value in values.items():
        setattr(account, key, value)
    db.flush()
    return account
