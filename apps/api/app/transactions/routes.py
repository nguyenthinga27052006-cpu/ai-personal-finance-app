from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser
from app.db.models import TransactionType
from app.db.session import get_db
from app.transactions.schemas import (
    RefundCreate,
    TransactionCreate,
    TransactionListResponse,
    TransactionResponse,
)
from app.transactions.service import (
    IdempotencyConflictError,
    TransactionError,
    TransactionNotFoundError,
    create_transaction,
    create_transfer,
    get_transaction,
    list_transactions,
)

router = APIRouter(prefix="/api/v1/transactions", tags=["transactions"])
transfer_router = APIRouter(prefix="/api/v1", tags=["transactions"])
DbSession = Annotated[Session, Depends(get_db)]


class TransferCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_account_id: str
    destination_account_id: str
    amount: int = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    description: str | None = None
    transaction_date: datetime | None = None

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        value = value.strip().upper()
        if not value.isalpha() or len(value) != 3:
            raise ValueError("Currency must be a three-letter ISO code")
        return value


def domain_error(error: TransactionError) -> HTTPException:
    if isinstance(error, IdempotencyConflictError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "idempotency_conflict",
                "message": "Idempotency key was already used for another request",
            },
        )
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"code": "transaction_validation_error", "message": str(error)},
    )


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create(
    payload: TransactionCreate,
    current_user: CurrentUser,
    db: DbSession,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> TransactionResponse:
    try:
        transaction = create_transaction(db, current_user, payload, idempotency_key)
        db.commit()
        db.refresh(transaction)
        return transaction
    except TransactionError as exc:
        db.rollback()
        raise domain_error(exc) from exc


@router.post("/transfer", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def transfer(
    payload: TransferCreate,
    current_user: CurrentUser,
    db: DbSession,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> TransactionResponse:
    try:
        transaction = create_transfer(
            db,
            current_user,
            payload.source_account_id,
            payload.destination_account_id,
            payload.amount,
            payload.currency,
            payload.description,
            payload.transaction_date,
            idempotency_key,
        )
        db.commit()
        db.refresh(transaction)
        return transaction
    except TransactionError as exc:
        db.rollback()
        raise domain_error(exc) from exc


@transfer_router.post(
    "/transfers", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED
)
def transfer_contract_path(
    payload: TransferCreate,
    current_user: CurrentUser,
    db: DbSession,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> TransactionResponse:
    return transfer(payload, current_user, db, idempotency_key)


@router.post(
    "/{transaction_id}/refund",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
def refund(
    transaction_id: str,
    payload: RefundCreate,
    current_user: CurrentUser,
    db: DbSession,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> TransactionResponse:
    request = TransactionCreate(
        type=TransactionType.REFUND,
        account_id=payload.account_id,
        amount=payload.amount,
        currency=payload.currency,
        description=payload.description,
        transaction_date=payload.transaction_date,
        parent_transaction_id=transaction_id,
    )
    try:
        transaction = create_transaction(db, current_user, request, idempotency_key)
        db.commit()
        db.refresh(transaction)
        return transaction
    except TransactionError as exc:
        db.rollback()
        raise domain_error(exc) from exc


@router.get("", response_model=TransactionListResponse)
def list_route(
    current_user: CurrentUser,
    db: DbSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    account_id: str | None = None,
    type: TransactionType | None = None,
) -> TransactionListResponse:
    items, total = list_transactions(db, current_user, page, page_size, account_id, type)
    return TransactionListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{transaction_id}", response_model=TransactionResponse)
def detail(transaction_id: str, current_user: CurrentUser, db: DbSession) -> TransactionResponse:
    try:
        return get_transaction(db, current_user, transaction_id)
    except TransactionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "transaction_not_found", "message": "Transaction not found"},
        ) from exc
