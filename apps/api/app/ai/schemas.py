from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.ai.context import Provenance


class AIOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["OK", "INSUFFICIENT_DATA"]
    answer: str = Field(min_length=1, max_length=4000)
    citations: list[Provenance] = Field(default_factory=list, max_length=20)
    suggested_actions: list[str] = Field(default_factory=list, max_length=5)


class AIExecuteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task: Literal["financial_summary", "spending_analysis", "budget_review"]
    start: date
    end: date
    currency: str = Field(min_length=3, max_length=3)
    tools: list[str] = Field(default_factory=list, max_length=10)
    user_input: str | None = Field(default=None, max_length=2000)


class AILogMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    feature: str
    provider: str
    model: str
    latency_ms: int
    input_tokens: int | None = None
    output_tokens: int | None = None
    estimated_cost: float | None = None
    success: bool
    error_category: str | None = None
    selected_tools: list[str] = Field(default_factory=list)
    fallback_used: bool = False
    routing: dict[str, Any] = Field(default_factory=dict)


class AIExecuteResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    output: AIOutput
    metadata: AILogMetadata
