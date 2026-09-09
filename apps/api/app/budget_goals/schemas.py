from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def currency(value: str) -> str:
    value = value.strip().upper()
    if len(value) != 3 or not value.isalpha():
        raise ValueError("Currency must be a three-letter ISO code")
    return value


class BudgetCategoryCreate(BaseModel):
    category_id: str
    limit_amount: int = Field(gt=0)


class BudgetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    period_type: str = "MONTHLY"
    start_date: date
    end_date: date
    total_limit: int = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    status: str = "ACTIVE"
    categories: list[BudgetCategoryCreate] = Field(default_factory=list)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return currency(value)

    @model_validator(mode="after")
    def validate_period(self) -> BudgetCreate:
        if self.period_type != "MONTHLY":
            raise ValueError("Only MONTHLY budgets are supported")
        if self.start_date > self.end_date:
            raise ValueError("Budget start_date must not be after end_date")
        if self.status not in {"ACTIVE", "INACTIVE", "ARCHIVED"}:
            raise ValueError("Invalid budget status")
        return self


class BudgetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    period_type: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    total_limit: int | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    status: str | None = None

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        return currency(value) if value is not None else None

    @model_validator(mode="after")
    def validate_update(self) -> BudgetUpdate:
        if self.period_type is not None and self.period_type != "MONTHLY":
            raise ValueError("Only MONTHLY budgets are supported")
        if self.status is not None and self.status not in {"ACTIVE", "INACTIVE", "ARCHIVED"}:
            raise ValueError("Invalid budget status")
        return self


class BudgetCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    category_id: str
    limit_amount: int
    spent: int = 0
    remaining: int = 0
    utilization: float = 0
    risk: str = "SAFE"


class BudgetStatusResponse(BaseModel):
    spent: int
    remaining: int
    utilization: float
    days_elapsed: int
    days_remaining: int
    current_spending_velocity: float
    projected_spending: int
    risk: str


class BudgetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    name: str
    period_type: str
    start_date: date
    end_date: date
    total_limit: int
    currency: str
    status: str
    categories: list[BudgetCategoryResponse]
    calculation: BudgetStatusResponse


class GoalCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    target_amount: int = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    target_date: date | None = None
    priority: int = Field(default=1, ge=1)
    status: str = "ACTIVE"

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return currency(value)


class GoalUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    target_amount: int | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    target_date: date | None = None
    priority: int | None = Field(default=None, ge=1)
    status: str | None = None

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        return currency(value) if value is not None else None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is not None and value not in {"ACTIVE", "COMPLETED", "PAUSED", "ARCHIVED"}:
            raise ValueError("Invalid goal status")
        return value


class ContributionCreate(BaseModel):
    amount: int = Field(gt=0)
    contribution_date: datetime | None = None
    account_id: str | None = None
    note: str | None = None


class ContributionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    goal_id: str
    account_id: str | None
    amount: int
    contribution_date: datetime
    note: str | None


class GoalStatusResponse(BaseModel):
    current: int
    remaining: int
    progress: float
    required_monthly_saving: int
    actual_monthly_saving: int
    forecast: str


class GoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    name: str
    description: str | None
    target_amount: int
    currency: str
    target_date: date | None
    priority: int
    status: str
    contributions: list[ContributionResponse]
    calculation: GoalStatusResponse
