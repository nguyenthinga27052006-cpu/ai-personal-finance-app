from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class PeriodResponse(BaseModel):
    start: date
    end: date
    timezone: str
    days: int


class SummaryResponse(BaseModel):
    income: int
    expense: int
    saving: int
    saving_rate: Decimal
    average_daily_spending: Decimal
    spending_velocity: Decimal
    budget_utilization: Decimal | None
    records: int


class AnalysisResponse(BaseModel):
    id: str
    name: str
    amount: int
    count: int
    share: Decimal
    growth: Decimal | None
    average: Decimal
    median: Decimal
    largest: int


class TimePointResponse(BaseModel):
    period: str
    amount: int
    count: int


class ComparisonResponse(BaseModel):
    previous: dict[str, object]
    rolling_average: dict[str, object]


class AnomalyResponse(BaseModel):
    rule: str
    severity: str
    value: int
    baseline: Decimal
    reason: str


class ForecastResponse(BaseModel):
    status: str
    projected_expense: int | None
    daily_pace: Decimal | None = None
    recurring_expenses: int | None = None
    basis: str


class AnalyticsOverviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    currency: str
    period: PeriodResponse
    summary: SummaryResponse
    category_analysis: list[AnalysisResponse]
    merchant_analysis: list[AnalysisResponse]
    time_analysis: dict[str, list[TimePointResponse]]
    comparison: ComparisonResponse
    anomalies: list[AnomalyResponse]
    forecast: ForecastResponse
