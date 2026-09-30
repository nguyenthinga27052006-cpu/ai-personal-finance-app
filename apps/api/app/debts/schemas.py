from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class FinancialContactBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    relationship_type: str | None = Field(default=None, max_length=80)
    phone: str | None = Field(default=None, max_length=30)
    notes: str | None = Field(default=None, max_length=500)
    is_support_contact: bool = True
    is_active: bool = True


class FinancialContactCreate(FinancialContactBase):
    pass


class FinancialContactUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    relationship_type: str | None = None
    phone: str | None = None
    notes: str | None = None
    is_support_contact: bool | None = None
    is_active: bool | None = None


class FinancialContactResponse(FinancialContactBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DebtBase(BaseModel):
    type: str = Field(..., pattern="^(BORROW|LEND)$")  # BORROW = Vay, LEND = Cho vay
    counterparty_name: str = Field(..., min_length=1, max_length=120)
    contact_id: str | None = None
    total_amount: int = Field(..., gt=0)
    currency: str = Field(default="VND", max_length=3)
    due_date: date | None = None
    interest_rate: int = Field(default=0, ge=0)
    notes: str | None = Field(default=None, max_length=500)


class DebtCreate(DebtBase):
    pass


class DebtUpdate(BaseModel):
    counterparty_name: str | None = Field(default=None, min_length=1, max_length=120)
    contact_id: str | None = None
    total_amount: int | None = Field(default=None, gt=0)
    due_date: date | None = None
    interest_rate: int | None = Field(default=None, ge=0)
    status: str | None = Field(default=None, pattern="^(ACTIVE|PAID|CANCELLED)$")
    notes: str | None = None


class DebtPaymentCreate(BaseModel):
    amount: int = Field(..., gt=0)
    payment_date: datetime | None = None
    account_id: str | None = None
    notes: str | None = Field(default=None, max_length=500)


class DebtPaymentResponse(BaseModel):
    id: str
    debt_id: str
    account_id: str | None
    amount: int
    payment_date: datetime
    notes: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DebtResponse(BaseModel):
    id: str
    user_id: str
    type: str
    counterparty_name: str
    contact_id: str | None
    total_amount: int
    remaining_amount: int
    currency: str
    due_date: date | None
    interest_rate: int
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime
    payments: list[DebtPaymentResponse] = []

    model_config = ConfigDict(from_attributes=True)


class DebtSummaryResponse(BaseModel):
    total_borrow_remaining: int
    total_lend_remaining: int
    upcoming_debts_count: int
    overdue_debts_count: int
    currency: str = "VND"
