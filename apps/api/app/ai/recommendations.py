from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.ai.context import ExecutionContext
from app.ai.gateway import AIGateway


class RecommendationExplanationOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = Field(pattern="^(SUCCESS|INSUFFICIENT_DATA)$")
    answer: str = Field(min_length=1, max_length=4000)
    citations: list[dict[str, Any]] = Field(default_factory=list)


def explain_recommendation(
    candidate: dict[str, Any],
    *,
    context: ExecutionContext | None = None,
    gateway: AIGateway | None = None,
) -> dict[str, Any]:
    if not isinstance(candidate, dict):
        return {
            "status": "VALIDATION_ERROR",
            "answer": "Recommendation data is malformed.",
            "source": None,
            "citations": [],
        }

    recommendation_type = str(candidate.get("type") or "UNKNOWN")
    reason = str(candidate.get("reason") or "Recommendation source is unavailable.")
    expected_impact = str(
        candidate.get("expected_impact") or "ESTIMATE: impact depends on the action."
    )
    confidence = candidate.get("confidence")

    if not reason.strip() or not expected_impact.startswith("ESTIMATE"):
        return {
            "status": "VALIDATION_ERROR",
            "answer": "The recommendation candidate is missing grounded source data.",
            "source": reason,
            "citations": [],
        }

    if recommendation_type == "UNKNOWN":
        return {
            "status": "VALIDATION_ERROR",
            "answer": "The recommendation candidate is missing a valid type.",
            "source": reason,
            "citations": [],
        }

    answer = (
        f"Recommendation: {recommendation_type}. "
        f"{reason} The expected impact is {expected_impact}. "
        f"This is an estimate, not a guaranteed result, and the confidence is {confidence}."
    )
    if context is not None and gateway is not None:
        result = gateway.execute(
            context,
            task="recommendation_explanation",
            start=context.user.created_at.date(),
            end=context.user.created_at.date(),
            currency=context.user.default_currency,
            tools=[],
            user_input=answer,
            output_model=RecommendationExplanationOutput,
        )
        output = result.output
        if not isinstance(output, RecommendationExplanationOutput):
            return {
                "status": "VALIDATION_ERROR",
                "answer": "The recommendation explanation could not be validated.",
                "source": reason,
                "citations": [reason],
            }
        answer = f"{output.answer} Grounded source: {reason} Impact: {expected_impact}"

    return {
        "status": "SUCCESS",
        "answer": answer,
        "source": reason,
        "citations": [reason],
    }
