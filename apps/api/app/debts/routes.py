from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser
from app.db.session import get_db
from app.debts.schemas import (
    DebtCreate,
    DebtPaymentCreate,
    DebtPaymentResponse,
    DebtResponse,
    DebtSummaryResponse,
    DebtUpdate,
    FinancialContactCreate,
    FinancialContactResponse,
    FinancialContactUpdate,
)
from app.debts.service import (
    add_debt_payment,
    create_contact,
    create_debt,
    delete_contact,
    delete_debt,
    get_contact,
    get_debt,
    get_debt_summary,
    list_contacts,
    list_debts,
    update_contact,
    update_debt,
)

debts_router = APIRouter(prefix="/api/v1/debts", tags=["debts"])
contacts_router = APIRouter(prefix="/api/v1/financial-contacts", tags=["financial-contacts"])

DbSession = Annotated[Session, Depends(get_db)]


# --- Debts Endpoints ---

@debts_router.get("", response_model=list[DebtResponse])
def get_debts(
    current_user: CurrentUser,
    db: DbSession,
    status: str | None = Query(default=None),
    type: str | None = Query(default=None),
) -> list[DebtResponse]:
    debts = list_debts(db, current_user, status_filter=status, debt_type=type)
    return [DebtResponse.model_validate(d) for d in debts]


@debts_router.post("", response_model=DebtResponse, status_code=status.HTTP_201_CREATED)
def post_debt(
    payload: DebtCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> DebtResponse:
    debt = create_debt(db, current_user, payload)
    return DebtResponse.model_validate(debt)


@debts_router.get("/summary", response_model=DebtSummaryResponse)
def get_summary(
    current_user: CurrentUser,
    db: DbSession,
) -> DebtSummaryResponse:
    return get_debt_summary(db, current_user)


@debts_router.get("/{debt_id}", response_model=DebtResponse)
def get_single_debt(
    debt_id: str,
    current_user: CurrentUser,
    db: DbSession,
) -> DebtResponse:
    debt = get_debt(db, current_user, debt_id)
    return DebtResponse.model_validate(debt)


@debts_router.patch("/{debt_id}", response_model=DebtResponse)
def patch_debt(
    debt_id: str,
    payload: DebtUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> DebtResponse:
    debt = update_debt(db, current_user, debt_id, payload)
    return DebtResponse.model_validate(debt)


@debts_router.delete("/{debt_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_debt(
    debt_id: str,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    delete_debt(db, current_user, debt_id)


@debts_router.post(
    "/{debt_id}/payments",
    response_model=DebtPaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_payment(
    debt_id: str,
    payload: DebtPaymentCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> DebtPaymentResponse:
    payment = add_debt_payment(db, current_user, debt_id, payload)
    return DebtPaymentResponse.model_validate(payment)


# --- Financial Contacts Endpoints ---

@contacts_router.get("", response_model=list[FinancialContactResponse])
def get_contacts(
    current_user: CurrentUser,
    db: DbSession,
    only_support: bool = Query(default=False),
) -> list[FinancialContactResponse]:
    contacts = list_contacts(db, current_user, only_support=only_support)
    return [FinancialContactResponse.model_validate(c) for c in contacts]


@contacts_router.post(
    "",
    response_model=FinancialContactResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_contact(
    payload: FinancialContactCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> FinancialContactResponse:
    contact = create_contact(db, current_user, payload)
    return FinancialContactResponse.model_validate(contact)


@contacts_router.get("/{contact_id}", response_model=FinancialContactResponse)
def get_single_contact(
    contact_id: str,
    current_user: CurrentUser,
    db: DbSession,
) -> FinancialContactResponse:
    contact = get_contact(db, current_user, contact_id)
    return FinancialContactResponse.model_validate(contact)


@contacts_router.patch("/{contact_id}", response_model=FinancialContactResponse)
def patch_contact(
    contact_id: str,
    payload: FinancialContactUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> FinancialContactResponse:
    contact = update_contact(db, current_user, contact_id, payload)
    return FinancialContactResponse.model_validate(contact)


@contacts_router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_contact(
    contact_id: str,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    delete_contact(db, current_user, contact_id)
