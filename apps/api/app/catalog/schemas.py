from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.db.models import CategoryType


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    type: CategoryType
    parent_id: str | None = None
    icon: str | None = Field(default=None, max_length=64)
    color_token: str | None = Field(default=None, max_length=64)
    sort_order: int = 0

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Category name must not be empty")
        return value


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    type: CategoryType
    parent_id: str | None
    icon: str | None
    color_token: str | None
    is_system: bool
    is_active: bool
    sort_order: int
    created_at: datetime


class CategoryListResponse(BaseModel):
    items: list[CategoryResponse]
    total: int


class MerchantCreate(BaseModel):
    canonical_name: str = Field(min_length=1, max_length=160)
    category_hint: str | None = None

    @field_validator("canonical_name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Merchant name must not be empty")
        return value


class MerchantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    canonical_name: str
    normalized_name: str
    category_hint: str | None
    status: str
    created_at: datetime


class MerchantAliasCreate(BaseModel):
    alias: str = Field(min_length=1, max_length=160)

    @field_validator("alias")
    @classmethod
    def validate_alias(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Alias must not be empty")
        return value


class MerchantLookupResponse(BaseModel):
    merchant: MerchantResponse | None
