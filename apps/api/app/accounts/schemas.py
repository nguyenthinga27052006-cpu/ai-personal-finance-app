from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.db.models import AccountStatus, AccountType


class AccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    type: AccountType
    currency: str = Field(min_length=3, max_length=3)
    opening_balance: int = Field(default=0, ge=0)
    credit_limit: int | None = Field(default=None, ge=0)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Account name must not be empty")
        return value

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        value = value.strip().upper()
        if len(value) != 3 or not value.isalpha():
            raise ValueError("Currency must be a three-letter ISO code")
        return value

    @field_validator("credit_limit")
    @classmethod
    def validate_credit_limit(cls, value: int | None, info):
        if value is not None and info.data.get("type") != AccountType.CREDIT_CARD:
            raise ValueError("Credit limit is only valid for credit card accounts")
        return value


class AccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    type: AccountType | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    credit_limit: int | None = Field(default=None, ge=0)
    status: AccountStatus | None = None
    is_archived: bool | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Account name must not be empty")
        return value

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip().upper()
        if len(value) != 3 or not value.isalpha():
            raise ValueError("Currency must be a three-letter ISO code")
        return value


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    type: AccountType
    currency: str
    opening_balance: int
    current_balance: int
    credit_limit: int | None
    status: AccountStatus
    is_archived: bool
    created_at: datetime
    updated_at: datetime


class AccountListResponse(BaseModel):
    items: list[AccountResponse]
    total: int
