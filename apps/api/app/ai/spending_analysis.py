from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.ai.context import ExecutionContext
from app.ai.gateway import AIGateway


@dataclass(frozen=True)
class SpendingAnalysisResult:
    status: Literal["SUCCESS", "INSUFFICIENT_DATA", "VALIDATION_ERROR"]
    answer: str
    source_facts: list[str]
    estimate: str | None = None


class SpendingExplanationOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["SUCCESS", "INSUFFICIENT_DATA"]
    answer: str = Field(min_length=1, max_length=4000)
    citations: list[dict[str, Any]] = Field(default_factory=list)


def analyze_spending(facts: dict[str, Any]) -> SpendingAnalysisResult:
    if not isinstance(facts, dict):
        return SpendingAnalysisResult(
            status="VALIDATION_ERROR",
            answer="Spending analysis requires a structured facts payload.",
            source_facts=[],
            estimate=None,
        )

    summary = facts.get("summary") or {}
    categories = facts.get("category_analysis") or []
    insights = facts.get("insights") or []
    expense = summary.get("expense")
    if expense is None and not categories and not insights:
        return SpendingAnalysisResult(
            status="INSUFFICIENT_DATA",
            answer="I do not have enough canonical financial facts to explain spending behavior.",
            source_facts=[],
            estimate=None,
        )

    source_facts = [
        f"summary.expense={expense}",
        f"category_count={len(categories)}",
        f"insight_count={len(insights)}",
    ]
    contextual = (
        "The current spending pattern is grounded in canonical financial facts "
        "and deterministic insights."
    )
    if expense is not None:
        answer = (
            f"{contextual} Effective expense is {expense}, and the dominant "
            "categories are derived from canonical tracking rather than model "
            "estimation."
        )
    else:
        answer = (
            f"{contextual} No numeric expense fact is available, so the "
            "explanation remains limited to the canonical categories and insights."
        )
    return SpendingAnalysisResult(
        status="SUCCESS",
        answer=answer,
        source_facts=source_facts,
        estimate=(
            "ESTIMATE: pattern interpretation may change as more canonical data "
            "becomes available."
        ),
    )


def analyze_spending_with_gateway(
    facts: dict[str, Any], context: ExecutionContext, gateway: AIGateway
) -> SpendingAnalysisResult:
    baseline = analyze_spending(facts)
    if baseline.status != "SUCCESS":
        return baseline
    result = gateway.execute(
        context,
        task="spending_analysis",
        start=context.user.created_at.date(),
        end=context.user.created_at.date(),
        currency=context.user.default_currency,
        tools=list(context.allowed_tools),
        user_input="Explain the supplied canonical spending facts without changing numeric values.",
        output_model=SpendingExplanationOutput,
        execute_tools=False,
    )
    output = result.output
    if not isinstance(output, SpendingExplanationOutput):
        return SpendingAnalysisResult(
            status="VALIDATION_ERROR",
            answer="The spending explanation could not be validated.",
            source_facts=baseline.source_facts,
        )
    return SpendingAnalysisResult(
        status=output.status,
        answer=f"{output.answer} Canonical facts: {baseline.answer}",
        source_facts=baseline.source_facts,
        estimate=baseline.estimate,
    )
