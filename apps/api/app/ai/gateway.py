from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from time import monotonic
from typing import Any

from pydantic import BaseModel

from app.ai.context import ExecutionContext, FinancialContext, FinancialContextBuilder
from app.ai.errors import GuardrailViolation, StructuredOutputError, ToolNotAllowedError
from app.ai.guardrails import redact_metadata, validate_untrusted_input
from app.ai.providers import ModelRouter, ProviderRequest
from app.ai.schemas import AILogMetadata, AIOutput
from app.ai.tools import ToolRegistry, ToolResult, build_read_only_registry

logger = logging.getLogger("app.ai")

_DEFAULT_TOOLS = {
    "categorization": frozenset(),
    "receipt_extraction": frozenset(),
    "recommendation_explanation": frozenset(),
    "nl_query": frozenset(
        {
            "get_monthly_expense",
            "get_monthly_income",
            "get_current_balance",
            "get_budget_status",
            "get_goal_progress",
        }
    ),
    "financial_summary": frozenset(
        {
            "get_current_balance",
            "get_monthly_income",
            "get_monthly_expense",
            "get_budget_status",
            "get_goal_progress",
            "get_insights",
        }
    ),
    "spending_analysis": frozenset(
        {"get_monthly_expense", "get_category_spending", "get_spending_trend", "get_insights"}
    ),
    "budget_review": frozenset({"get_budget_status", "get_goal_progress", "get_insights"}),
}


@dataclass(frozen=True)
class GatewayResult:
    output: BaseModel
    metadata: AILogMetadata
    context: FinancialContext
    tool_results: tuple[ToolResult, ...]


class AIGateway:
    def __init__(
        self,
        router: ModelRouter,
        registry: ToolRegistry,
        context_builder: FinancialContextBuilder | None = None,
    ) -> None:
        self.router = router
        self.registry = registry
        self.context_builder = context_builder or FinancialContextBuilder()

    def execute(
        self,
        context: ExecutionContext,
        *,
        task: str,
        start: Any,
        end: Any,
        currency: str,
        tools: list[str] | None = None,
        user_input: str | None = None,
        output_model: type[BaseModel] = AIOutput,
        execute_tools: bool = True,
    ) -> GatewayResult:
        started = monotonic()
        context.require_authenticated()
        validate_untrusted_input(user_input)
        allowed = _DEFAULT_TOOLS.get(task)
        if allowed is None:
            raise ToolNotAllowedError("AI feature is not registered")
        requested = tuple(tools or ())
        if any(name not in allowed for name in requested):
            raise ToolNotAllowedError("Requested tool is not allowed for this feature")
        if context.allowed_tools != allowed:
            raise GuardrailViolation("Execution context tool policy does not match feature policy")

        financial_context = self.context_builder.build(context, task, start, end, currency)
        tool_results = (
            tuple(
                self.registry.execute(
                    name,
                    context,
                    {"start": start, "end": end, "currency": currency},
                )
                for name in requested
            )
            if execute_tools
            else tuple()
        )
        provider_request = ProviderRequest(
            feature=task,
            model="foundation-simple",
            instructions=(
                "Return ONLY a valid JSON object matching this schema: "
                '{"status": "OK"|"INSUFFICIENT_DATA"|"LOW_CONFIDENCE", "answer": "string", "citations": [], "suggested_actions": []}. '
                "Do not include extra fields outside this schema. Do not invent financial facts."
            ),
            context={
                "financial_context": financial_context.facts,
                "provenance": [
                    item.model_dump(mode="json") for item in financial_context.provenance
                ],
                "insufficient_data": financial_context.insufficient_data,
                "tool_results": [item.model_dump(mode="json") for item in tool_results],
                "user_input_present": bool(user_input),
                "user_input": user_input,
            },
            tools=requested,
        )
        response, decision, fallback_used = self.router.generate(provider_request)
        output = self._validate_provider_output(response.content, output_model)
        metadata = AILogMetadata(
            request_id=context.request_id,
            feature=task,
            provider=response.provider,
            model=response.model,
            latency_ms=max(response.latency_ms, int((monotonic() - started) * 1000)),
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            estimated_cost=response.estimated_cost,
            success=True,
            selected_tools=list(requested),
            fallback_used=fallback_used,
            routing=decision.__dict__,
        )
        logger.info("ai_execution %s", redact_metadata(metadata.model_dump()))
        return GatewayResult(output, metadata, financial_context, tool_results)

    @staticmethod
    def _validate_provider_output(
        content: str, output_model: type[BaseModel] = AIOutput
    ) -> BaseModel:
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned).strip()
        try:
            value = json.loads(cleaned)
        except (TypeError, ValueError) as exc:
            logger.error("Provider returned malformed JSON: %s (content: %r)", exc, content)
            raise StructuredOutputError("Provider returned malformed JSON") from exc
        try:
            return output_model.model_validate(value)
        except ValueError as exc:
            logger.error("Provider output failed structured validation: %s (value: %r)", exc, value)
            raise StructuredOutputError(f"Provider output failed structured validation: {exc}") from exc




def default_gateway() -> AIGateway:
    from app.ai.providers import FakeProvider, GeminiLLMProvider, OpenAIProvider
    from app.core.config import get_settings

    settings = get_settings()
    if settings.ai_provider == "gemini" and settings.gemini_api_key:
        primary = GeminiLLMProvider(api_key=settings.gemini_api_key, default_model=settings.ai_model)
        fallback = FakeProvider()
    elif settings.ai_provider == "openai" and settings.openai_api_key:
        primary = OpenAIProvider(api_key=settings.openai_api_key, default_model=settings.ai_model)
        fallback = FakeProvider()
    elif settings.gemini_api_key:
        primary = GeminiLLMProvider(api_key=settings.gemini_api_key, default_model=settings.ai_model)
        fallback = FakeProvider()
    elif settings.openai_api_key:
        primary = OpenAIProvider(api_key=settings.openai_api_key, default_model=settings.ai_model)
        fallback = FakeProvider()
    else:
        primary = FakeProvider()
        fallback = FakeProvider()

    return AIGateway(
        ModelRouter(primary, fallback),
        build_read_only_registry(),
    )


