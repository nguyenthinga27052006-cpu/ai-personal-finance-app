from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from typing import Any, Protocol

from app.ai.errors import ProviderResponseError, ProviderTimeoutError, ProviderUnavailableError


@dataclass(frozen=True)
class ProviderRequest:
    feature: str
    model: str
    instructions: str
    context: dict[str, Any]
    tools: tuple[str, ...]
    timeout_seconds: float = 10.0


@dataclass(frozen=True)
class ProviderResponse:
    content: str
    provider: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    estimated_cost: float | None = None
    latency_ms: int = 0


class Provider(Protocol):
    name: str

    def generate(self, request: ProviderRequest) -> ProviderResponse: ...


class FakeProvider:
    name = "fake"

    def __init__(
        self,
        response: dict[str, Any] | str | None = None,
        *,
        failure: Exception | None = None,
    ) -> None:
        self.response = response
        self.failure = failure
        self.calls: list[ProviderRequest] = []

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        started = monotonic()
        self.calls.append(request)
        if self.failure is not None:
            if isinstance(self.failure, TimeoutError):
                raise ProviderTimeoutError("Provider timed out") from self.failure
            raise ProviderUnavailableError("Provider unavailable") from self.failure
        if self.response is None:
            if request.feature == "categorization":
                payload = {
                    "status": "LOW_CONFIDENCE",
                    "category": "Other",
                    "confidence": 0.45,
                    "reason": "Fake provider fallback requires user confirmation.",
                }
            elif request.feature == "nl_query":
                question = str(request.context.get("user_input") or "").lower()
                if "income" in question or "earned" in question:
                    intent, tool = "monthly_income", "get_monthly_income"
                elif "balance" in question or "account" in question:
                    intent, tool = "current_balance", "get_current_balance"
                elif "budget" in question:
                    intent, tool = "budget_status", "get_budget_status"
                elif "goal" in question:
                    intent, tool = "goal_progress", "get_goal_progress"
                elif "spend" in question or "expense" in question:
                    intent, tool = "monthly_expense", "get_monthly_expense"
                else:
                    intent, tool = None, None
                payload = {
                    "status": "SUCCESS" if intent else "UNSUPPORTED_REQUEST",
                    "intent": intent,
                    "tool": tool,
                    "answer": "Intent selected from the allowed financial query map.",
                }
            else:
                payload = {
                    "status": (
                        "INSUFFICIENT_DATA"
                        if request.context.get("insufficient_data")
                        else "OK"
                    ),
                    "answer": "AI provider foundation response; no financial action was taken.",
                    "citations": request.context.get("provenance", []),
                    "suggested_actions": [],
                }
        elif isinstance(self.response, dict):
            payload = self.response
        else:
            return ProviderResponse(
                content=self.response,
                provider=self.name,
                model=request.model,
                estimated_cost=0.0,
                latency_ms=int((monotonic() - started) * 1000),
            )
        return ProviderResponse(
            content=payload if isinstance(payload, str) else _json(payload),
            provider=self.name,
            model=request.model,
            input_tokens=None,
            output_tokens=None,
            estimated_cost=0.0,
            latency_ms=int((monotonic() - started) * 1000),
        )


def _json(value: dict[str, Any]) -> str:
    import json

    try:
        return json.dumps(value, default=str, sort_keys=True)
    except (TypeError, ValueError) as exc:
        raise ProviderResponseError("Provider returned an unserializable response") from exc


@dataclass(frozen=True)
class RouteDecision:
    task: str
    complexity: str
    primary_provider: str
    primary_model: str
    fallback_provider: str | None
    fallback_model: str | None


class ModelRouter:
    def __init__(
        self,
        primary: Provider,
        fallback: Provider | None = None,
        *,
        primary_model: str = "foundation-simple",
        fallback_model: str = "foundation-fallback",
    ) -> None:
        self.primary = primary
        self.fallback = fallback
        self.primary_model = primary_model
        self.fallback_model = fallback_model

    def decide(self, task: str) -> RouteDecision:
        complexity = "complex" if task in {"spending_analysis", "financial_summary"} else "simple"
        return RouteDecision(
            task=task,
            complexity=complexity,
            primary_provider=self.primary.name,
            primary_model=self.primary_model,
            fallback_provider=self.fallback.name if self.fallback else None,
            fallback_model=self.fallback_model if self.fallback else None,
        )

    def generate(self, request: ProviderRequest) -> tuple[ProviderResponse, RouteDecision, bool]:
        decision = self.decide(request.feature)
        primary_request = ProviderRequest(**{**request.__dict__, "model": decision.primary_model})
        try:
            return self.primary.generate(primary_request), decision, False
        except (ProviderTimeoutError, ProviderUnavailableError, ProviderResponseError):
            if self.fallback is None:
                raise
            fallback_request = ProviderRequest(
                **{**request.__dict__, "model": decision.fallback_model or request.model}
            )
            return self.fallback.generate(fallback_request), decision, True
