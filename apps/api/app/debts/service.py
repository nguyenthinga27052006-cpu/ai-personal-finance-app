from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Debt, DebtPayment, DebtStatus, FinancialContact, User
from app.debts.schemas import (
    DebtCreate,
    DebtPaymentCreate,
    DebtSummaryResponse,
    DebtUpdate,
    FinancialContactCreate,
    FinancialContactUpdate,
)

# --- Financial Contacts ---

def create_contact(db: Session, user: User, data: FinancialContactCreate) -> FinancialContact:
    contact = FinancialContact(
        user_id=user.id,
        name=data.name.strip(),
        relationship_type=data.relationship_type.strip() if data.relationship_type else None,
        phone=data.phone.strip() if data.phone else None,
        notes=data.notes.strip() if data.notes else None,
        is_support_contact=data.is_support_contact,
        is_active=data.is_active,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


def list_contacts(
    db: Session, user: User, only_support: bool = False, active_only: bool = True
) -> Sequence[FinancialContact]:
    query = select(FinancialContact).where(FinancialContact.user_id == user.id)
    if only_support:
        query = query.where(FinancialContact.is_support_contact.is_(True))
    if active_only:
        query = query.where(FinancialContact.is_active.is_(True))
    query = query.order_by(FinancialContact.name.asc())
    return db.scalars(query).all()


def get_contact(db: Session, user: User, contact_id: str) -> FinancialContact:
    contact = db.scalar(
        select(FinancialContact).where(
            FinancialContact.id == contact_id, FinancialContact.user_id == user.id
        )
    )
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Financial contact not found"
        )
    return contact


def update_contact(
    db: Session, user: User, contact_id: str, data: FinancialContactUpdate
) -> FinancialContact:
    contact = get_contact(db, user, contact_id)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if isinstance(value, str):
            value = value.strip()
        setattr(contact, field, value)
    db.commit()
    db.refresh(contact)
    return contact


def delete_contact(db: Session, user: User, contact_id: str) -> None:
    contact = get_contact(db, user, contact_id)
    db.delete(contact)
    db.commit()


# --- Debts ---

def create_debt(db: Session, user: User, data: DebtCreate) -> Debt:
    if data.contact_id:
        # Validate contact ownership
        get_contact(db, user, data.contact_id)

    debt = Debt(
        user_id=user.id,
        type=data.type,
        counterparty_name=data.counterparty_name.strip(),
        contact_id=data.contact_id,
        total_amount=data.total_amount,
        remaining_amount=data.total_amount,
        currency=data.currency or user.default_currency or "VND",
        due_date=data.due_date,
        interest_rate=data.interest_rate or 0,
        status=DebtStatus.ACTIVE.value,
        notes=data.notes.strip() if data.notes else None,
    )
    db.add(debt)
    db.commit()
    db.refresh(debt)
    return debt


def list_debts(
    db: Session,
    user: User,
    status_filter: str | None = None,
    debt_type: str | None = None,
) -> Sequence[Debt]:
    query = select(Debt).where(Debt.user_id == user.id)
    if status_filter:
        query = query.where(Debt.status == status_filter)
    if debt_type:
        query = query.where(Debt.type == debt_type)
    query = query.order_by(Debt.due_date.asc().nulls_last(), Debt.created_at.desc())
    return db.scalars(query).all()


def get_debt(db: Session, user: User, debt_id: str) -> Debt:
    debt = db.scalar(select(Debt).where(Debt.id == debt_id, Debt.user_id == user.id))
    if not debt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Debt record not found")
    return debt


def update_debt(db: Session, user: User, debt_id: str, data: DebtUpdate) -> Debt:
    debt = get_debt(db, user, debt_id)
    update_data = data.model_dump(exclude_unset=True)
    if "contact_id" in update_data and update_data["contact_id"]:
        get_contact(db, user, update_data["contact_id"])

    for field, value in update_data.items():
        if isinstance(value, str):
            value = value.strip()
        setattr(debt, field, value)

    # Recalculate remaining if total_amount was modified
    if "total_amount" in update_data:
        paid_sum = sum(p.amount for p in debt.payments)
        remaining = debt.total_amount - paid_sum
        debt.remaining_amount = max(0, remaining)
        if debt.remaining_amount == 0:
            debt.status = DebtStatus.PAID.value

    db.commit()
    db.refresh(debt)
    return debt


def delete_debt(db: Session, user: User, debt_id: str) -> None:
    debt = get_debt(db, user, debt_id)
    db.delete(debt)
    db.commit()


def add_debt_payment(
    db: Session, user: User, debt_id: str, data: DebtPaymentCreate
) -> DebtPayment:
    debt = get_debt(db, user, debt_id)
    if debt.status == DebtStatus.PAID.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Debt has already been fully paid"
        )

    payment = DebtPayment(
        debt_id=debt.id,
        account_id=data.account_id,
        amount=data.amount,
        payment_date=data.payment_date or datetime.now(timezone.utc),
        notes=data.notes.strip() if data.notes else None,
    )
    db.add(payment)

    # Deterministic update of remaining balance
    new_remaining = debt.remaining_amount - data.amount
    if new_remaining <= 0:
        debt.remaining_amount = 0
        debt.status = DebtStatus.PAID.value
    else:
        debt.remaining_amount = new_remaining

    db.commit()
    db.refresh(payment)
    return payment


def get_debt_summary(
    db: Session, user: User, today: date | None = None
) -> DebtSummaryResponse:
    current_date = today or date.today()
    in_7_days = current_date + timedelta(days=7)

    active_debts = list_debts(db, user, status_filter=DebtStatus.ACTIVE.value)

    total_borrow = sum(d.remaining_amount for d in active_debts if d.type == "BORROW")
    total_lend = sum(d.remaining_amount for d in active_debts if d.type == "LEND")

    upcoming = sum(
        1
        for d in active_debts
        if d.type == "BORROW" and d.due_date and current_date <= d.due_date <= in_7_days
    )
    overdue = sum(
        1
        for d in active_debts
        if d.type == "BORROW" and d.due_date and d.due_date < current_date
    )

    return DebtSummaryResponse(
        total_borrow_remaining=total_borrow,
        total_lend_remaining=total_lend,
        upcoming_debts_count=upcoming,
        overdue_debts_count=overdue,
        currency=user.default_currency or "VND",
    )
