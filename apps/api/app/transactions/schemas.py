from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.db.models import EntryType, TransactionType


class TransactionItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount: int = Field(gt=0)
    category_id: str | None = None
    description: str | None = None
    quantity: int = Field(default=1, gt=0)
    unit_price: int | None = Field(default=None, gt=0)


class TransactionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: TransactionType
    account_id: str
    amount: int = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    category_id: str | None = None
    merchant_id: str | None = None
    description: str | None = None
    transaction_date: datetime | None = None
    items: list[TransactionItemCreate] = Field(default_factory=list)
    parent_transaction_id: str | None = None
    adjustment_entry_type: EntryType | None = None

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        value = value.strip().upper()
        if len(value) != 3 or not value.isalpha():
            raise ValueError("Currency must be a three-letter ISO code")
        return value

    @model_validator(mode="after")
    def validate_type_fields(self) -> TransactionCreate:
        if self.type == TransactionType.REFUND and not self.parent_transaction_id:
            raise ValueError("Refund requires parent_transaction_id")
        if self.type == TransactionType.ADJUSTMENT and self.adjustment_entry_type is None:
            raise ValueError("Adjustment requires adjustment_entry_type")
        if self.type in {TransactionType.TRANSFER, TransactionType.REFUND} and self.items:
            raise ValueError("Split items are only valid for income or expense")
        if self.items and sum(item.amount for item in self.items) != self.amount:
            raise ValueError("Transaction item amounts must equal transaction amount")
        return self


class TransactionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount: int | None = Field(default=None, gt=0)
    category_id: str | None = None
    merchant_id: str | None = None
    description: str | None = None
    transaction_date: datetime | None = None


class RefundCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str
    amount: int = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    description: str | None = None
    transaction_date: datetime | None = None

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        value = value.strip().upper()
        if len(value) != 3 or not value.isalpha():
            raise ValueError("Currency must be a three-letter ISO code")
        return value


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    account_id: str | None
    type: TransactionType
    status: str
    currency: str
    amount: int
    transaction_date: datetime
    description: str | None
    merchant_id: str | None
    category_id: str | None
    parent_transaction_id: str | None
    transfer_group_id: str | None
    idempotency_key: str | None
    entries: list[TransactionEntryResponse]
    items: list[TransactionItemResponse]


class TransactionEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    account_id: str
    amount: int
    currency: str
    entry_type: EntryType


class TransactionItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    category_id: str | None
    description: str | None
    amount: int
    quantity: int
    unit_price: int | None


class TransactionListResponse(BaseModel):
    items: list[TransactionResponse]
    total: int
    page: int
    page_size: int


TransactionResponse.model_rebuild()
