from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.accounts.schemas import AccountCreate, AccountListResponse, AccountResponse, AccountUpdate
from app.accounts.service import (
    AccountConflictError,
    AccountNotFoundError,
    create_account,
    get_account,
    list_accounts,
    update_account,
)
from app.auth.dependencies import CurrentUser
from app.db.session import get_db

router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])
DbSession = Annotated[Session, Depends(get_db)]


def not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "account_not_found", "message": "Account not found"},
    )


@router.get("", response_model=AccountListResponse)
def accounts(
    current_user: CurrentUser,
    db: DbSession,
    include_archived: bool = Query(default=False),
) -> AccountListResponse:
    items = list_accounts(db, current_user, include_archived)
    return AccountListResponse(items=items, total=len(items))


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create(payload: AccountCreate, current_user: CurrentUser, db: DbSession) -> AccountResponse:
    account = create_account(db, current_user, **payload.model_dump())
    db.commit()
    db.refresh(account)
    return account


@router.get("/{account_id}", response_model=AccountResponse)
def detail(account_id: str, current_user: CurrentUser, db: DbSession) -> AccountResponse:
    try:
        return get_account(db, current_user, account_id)
    except AccountNotFoundError as exc:
        raise not_found() from exc


@router.patch("/{account_id}", response_model=AccountResponse)
def update(
    account_id: str, payload: AccountUpdate, current_user: CurrentUser, db: DbSession
) -> AccountResponse:
    try:
        account = update_account(
            db, current_user, account_id, payload.model_dump(exclude_unset=True)
        )
        db.commit()
        db.refresh(account)
        return account
    except AccountNotFoundError as exc:
        raise not_found() from exc
    except AccountConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "account_conflict", "message": str(exc)},
        ) from exc
