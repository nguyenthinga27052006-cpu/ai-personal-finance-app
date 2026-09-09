from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class DashboardPeriod(BaseModel):
    start: date
    end: date
    timezone: str


class DashboardSummary(BaseModel):
    total_balance: int
    income: int
    expense: int
    saving: int
    saving_rate: Decimal


class DashboardAccount(BaseModel):
    id: str
    name: str
    currency: str
    current_balance: int


class DashboardTransaction(BaseModel):
    id: str
    type: str
    amount: int
    currency: str
    transaction_date: datetime
    description: str | None


class DashboardCategory(BaseModel):
    id: str
    name: str
    amount: int
    share: Decimal


class DashboardBudget(BaseModel):
    id: str
    name: str
    currency: str
    spent: int
    total_limit: int
    utilization: Decimal
    risk: str


class DashboardGoal(BaseModel):
    id: str
    name: str
    currency: str
    current: int
    target_amount: int
    progress: Decimal
    forecast: str


class DashboardResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    period: DashboardPeriod
    summary: DashboardSummary
    accounts: list[DashboardAccount]
    recent_transactions: list[DashboardTransaction]
    categories: list[DashboardCategory]
    budgets: list[DashboardBudget]
    goals: list[DashboardGoal]
