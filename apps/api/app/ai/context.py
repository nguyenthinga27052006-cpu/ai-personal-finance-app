from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.analytics.service import build_overview
from app.db.models import User
from app.insights.service import active_insights

_MAX_PERIOD_DAYS = 366
_MAX_CATEGORIES = 5
_MAX_INSIGHTS = 5


class Provenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str
    period_start: date | None = None
    period_end: date | None = None
    as_of: date | None = None
    calculation_type: str
    deterministic: bool = True


class FinancialContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task: str
    currency: str
    period_start: date
    period_end: date
    facts: dict[str, Any] = Field(default_factory=dict)
    provenance: list[Provenance] = Field(default_factory=list)
    insufficient_data: bool = False


@dataclass(frozen=True)
class ExecutionContext:
    db: Session
    user: User
    request_id: str
    feature: str
    allowed_tools: frozenset[str]

    def require_authenticated(self) -> None:
        if not self.user or not self.user.id:
            from app.ai.errors import AuthenticationContextError

            raise AuthenticationContextError("Authenticated user context is required")


class FinancialContextBuilder:
    def build(
        self,
        context: ExecutionContext,
        task: str,
        start: date,
        end: date,
        currency: str,
    ) -> FinancialContext:
        context.require_authenticated()
        currency = currency.upper()
        if end < start:
            raise ValueError("end must be on or after start")
        if end - start > timedelta(days=_MAX_PERIOD_DAYS - 1):
            raise ValueError("AI context period must not exceed 366 days")

        overview = build_overview(context.db, context.user, start, end, currency)
        insights = active_insights(context.db, context.user, start, end, currency)[:_MAX_INSIGHTS]
        facts = {
            "summary": overview["summary"],
            "category_analysis": overview["category_analysis"][:_MAX_CATEGORIES],
            "time_analysis": {"monthly": overview["time_analysis"]["monthly"][-12:]},
            "forecast": overview["forecast"],
            "insights": [
                {
                    "id": item.id,
                    "type": item.type,
                    "severity": item.severity,
                    "source_metric": item.source_metric,
                    "source_value": item.source_value,
                    "period_start": item.period_start,
                    "period_end": item.period_end,
                }
                for item in insights
            ],
        }
        insufficient = not overview["summary"]["records"]
        provenance = [
            Provenance(
                source="phase09.financial_facts",
                period_start=start,
                period_end=end,
                calculation_type="canonical_analytics_overview",
            ),
            Provenance(
                source="phase10.insights",
                period_start=start,
                period_end=end,
                calculation_type="deterministic_insight_rules",
            ),
        ]
        return FinancialContext(
            task=task,
            currency=currency,
            period_start=start,
            period_end=end,
            facts=facts,
            provenance=provenance,
            insufficient_data=insufficient,
        )
