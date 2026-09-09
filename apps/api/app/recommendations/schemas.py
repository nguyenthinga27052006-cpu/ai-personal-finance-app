from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RecommendationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    user_id: str
    type: str
    reason: str
    suggested_action: str
    expected_impact: str
    priority: int
    confidence: float
    source_insight_id: str | None
    source_metric: str
    subject_id: str | None
    period_start: date
    period_end: date
    deterministic_id: str
    dedupe_key: str
    ranking_score: float
    status: str
    feedback_score: int
    expires_at: datetime | None
    created_at: datetime


class RecommendationListResponse(BaseModel):
    items: list[RecommendationResponse]
    total: int


class RecommendationFeedbackRequest(BaseModel):
    feedback: str = Field(pattern="^(HELPFUL|NOT_HELPFUL)$")
    metadata: dict[str, Any] = Field(default_factory=dict)


class RecommendationEventResponse(BaseModel):
    id: str
    status: str

    model_config = ConfigDict(extra="forbid")
