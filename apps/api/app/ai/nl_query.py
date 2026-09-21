from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field

from app.ai.context import ExecutionContext
from app.ai.errors import (
    InsufficientDataError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    StructuredOutputError,
    ToolExecutionError,
)
from app.ai.gateway import AIGateway
from app.ai.guardrails import validate_untrusted_input
from app.ai.tools import build_read_only_registry


@dataclass(frozen=True)
class NLQueryResult:
    status: Literal[
        "SUCCESS",
        "INSUFFICIENT_DATA",
        "UNSUPPORTED_REQUEST",
        "VALIDATION_ERROR",
        "PROVIDER_ERROR",
    ]
    intent: str | None
    tool: str | None
    answer: str
    source: str | None
    citations: list[str]
    message: str | None = None


class IntentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["SUCCESS", "UNSUPPORTED_REQUEST"]
    intent: str | None = None
    tool: str | None = None
    answer: str = Field(min_length=1, max_length=1000)


def _default_period(
    context: ExecutionContext,
    *,
    start: date | None,
    end: date | None,
) -> tuple[date, date]:
    if start and end:
        return start, end
    today = datetime.now(timezone.utc).astimezone(ZoneInfo(context.user.timezone)).date()
    period_start = date(today.year, today.month, 1)
    next_month = date(
        today.year + (today.month == 12),
        1 if today.month == 12 else today.month + 1,
        1,
    )
    return period_start, next_month - timedelta(days=1)


def _detect_intent(question: str) -> tuple[str | None, str | None]:
    lowered = question.lower()
    if "spend" in lowered or "spent" in lowered or "expense" in lowered:
        return "monthly_expense", "get_monthly_expense"
    if "income" in lowered or "earned" in lowered:
        return "monthly_income", "get_monthly_income"
    if "balance" in lowered or "account" in lowered:
        return "current_balance", "get_current_balance"
    if "budget" in lowered:
        return "budget_status", "get_budget_status"
    if "goal" in lowered:
        return "goal_progress", "get_goal_progress"
    return None, None


def execute_nl_query(
    context: ExecutionContext,
    question: str,
    *,
    start: date | None = None,
    end: date | None = None,
    currency: str = "VND",
    gateway: AIGateway | None = None,
) -> NLQueryResult:
    validate_untrusted_input(question)
    if not question or not question.strip():
        return NLQueryResult(
            status="VALIDATION_ERROR",
            intent=None,
            tool=None,
            answer="Please provide a clear financial question.",
            source=None,
            citations=[],
            message="question is empty",
        )

    intent, tool_name = _detect_intent(question)
    if intent is None and gateway is not None:
        period_start, period_end = _default_period(context, start=start, end=end)
        provider_result = gateway.execute(
            context,
            task="nl_query",
            start=period_start,
            end=period_end,
            currency=currency,
            tools=[],
            user_input=question,
            output_model=IntentOutput,
        )
        provider_output = provider_result.output
        allowed_intents = {
            "monthly_expense": "get_monthly_expense",
            "monthly_income": "get_monthly_income",
            "current_balance": "get_current_balance",
            "budget_status": "get_budget_status",
            "goal_progress": "get_goal_progress",
        }
        if (
            isinstance(provider_output, IntentOutput)
            and provider_output.status == "SUCCESS"
            and provider_output.intent in allowed_intents
            and provider_output.tool == allowed_intents[provider_output.intent]
        ):
            intent, tool_name = provider_output.intent, provider_output.tool
    if intent is None or tool_name is None:
        return NLQueryResult(
            status="UNSUPPORTED_REQUEST",
            intent=None,
            tool=None,
            answer=(
                "I can answer questions about spending, income, balances, "
                "budgets, or goals. Please ask one of those topics."
            ),
            source=None,
            citations=[],
            message="unsupported intent",
        )

    period_start, period_end = _default_period(context, start=start, end=end)
    registry = build_read_only_registry()
    if tool_name not in context.allowed_tools:
        return NLQueryResult(
            status="VALIDATION_ERROR",
            intent=intent,
            tool=tool_name,
            answer="That question is not allowed for this authenticated scope.",
            source=None,
            citations=[],
            message="tool not allowed for this context",
        )

    try:
        tool_result = registry.execute(
            tool_name,
            context,
            {"start": period_start, "end": period_end, "currency": currency.upper()},
        )
    except InsufficientDataError as exc:
        return NLQueryResult(
            status="INSUFFICIENT_DATA",
            intent=intent,
            tool=tool_name,
            answer=(
                "I do not have enough financial data for this time period "
                "to give a reliable answer yet."
            ),
            source=None,
            citations=[],
            message=str(exc),
        )
    except (ProviderTimeoutError, ProviderUnavailableError) as exc:
        return NLQueryResult(
            status="PROVIDER_ERROR",
            intent=intent,
            tool=tool_name,
            answer="The AI provider is temporarily unavailable.",
            source=None,
            citations=[],
            message=str(exc),
        )
    except StructuredOutputError as exc:
        return NLQueryResult(
            status="VALIDATION_ERROR",
            intent=intent,
            tool=tool_name,
            answer="The AI response could not be validated.",
            source=None,
            citations=[],
            message=str(exc),
        )
    except ToolExecutionError as exc:
        return NLQueryResult(
            status="VALIDATION_ERROR",
            intent=intent,
            tool=tool_name,
            answer="The canonical financial tool could not validate this request.",
            source=None,
            citations=[],
            message=str(exc),
        )

    if tool_name == "get_monthly_expense":
        value = tool_result.data.get("expense")
        if value is None:
            return NLQueryResult(
                status="INSUFFICIENT_DATA",
                intent=intent,
                tool=tool_name,
                answer=(
                    "I do not have enough financial data for this time period to "
                    "give a reliable answer yet."
                ),
                source=tool_result.provenance[0].source if tool_result.provenance else None,
                citations=[item.source for item in tool_result.provenance],
                message="no canonical fact available",
            )
        answer = (
            f"This month you spent {value} {currency.upper()} according to the "
            "canonical financial summary."
        )
        return NLQueryResult(
            status="SUCCESS",
            intent=intent,
            tool=tool_name,
            answer=answer,
            source=tool_result.provenance[0].source if tool_result.provenance else None,
            citations=[item.source for item in tool_result.provenance],
        )

    if tool_name == "get_current_balance":
        value = tool_result.data.get("total")
        if value is None:
            return NLQueryResult(
                status="INSUFFICIENT_DATA",
                intent=intent,
                tool=tool_name,
                answer="I do not have enough account data to report a current balance.",
                source=tool_result.provenance[0].source if tool_result.provenance else None,
                citations=[item.source for item in tool_result.provenance],
                message="no balance available",
            )
        answer = f"Your current balance is {value} {currency.upper()} based on your owned accounts."
        return NLQueryResult(
            status="SUCCESS",
            intent=intent,
            tool=tool_name,
            answer=answer,
            source=tool_result.provenance[0].source if tool_result.provenance else None,
            citations=[item.source for item in tool_result.provenance],
        )

    answer = f"I checked the canonical financial data for your request: {tool_result.data}."
    return NLQueryResult(
        status="SUCCESS",
        intent=intent,
        tool=tool_name,
        answer=answer,
        source=tool_result.provenance[0].source if tool_result.provenance else None,
        citations=[item.source for item in tool_result.provenance],
    )
