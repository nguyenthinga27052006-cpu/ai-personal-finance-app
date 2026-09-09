from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class InsightResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    user_id: str
    type: str
    title: str
    description: str
    severity: str
    confidence: Decimal
    relevance: Decimal
    priority: int
    period_start: date
    period_end: date
    source: str
    rule_id: str
    subject_id: str | None
    source_metric: str
    source_value: int | Decimal | None
    baseline: int | Decimal | None
    evidence: dict[str, object]
    expires_at: datetime
    created_at: datetime


class InsightListResponse(BaseModel):
    items: list[InsightResponse]
    total: int
