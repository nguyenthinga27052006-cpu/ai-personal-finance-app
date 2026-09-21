from __future__ import annotations

import asyncio
from dataclasses import dataclass
from time import monotonic
from typing import Any, AsyncGenerator, Protocol

from app.ai.errors import ProviderResponseError, ProviderTimeoutError, ProviderUnavailableError


@dataclass(frozen=True)
class ProviderRequest:
    feature: str
    model: str
    instructions: str
    context: dict[str, Any]
    tools: tuple[str, ...]
    timeout_seconds: float = 20.0


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

    async def stream_generate(self, request: ProviderRequest) -> AsyncGenerator[str, None]: ...


class FakeProvider:
    name = "fake"
    test_only = True
    is_production = False
    description = "TEST ONLY - NOT FOR PRODUCTION"
    warning = "WARNING: FakeProvider is enabled. System is NOT production-ready."

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
                        "INSUFFICIENT_DATA" if request.context.get("insufficient_data") else "OK"
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

    async def stream_generate(self, request: ProviderRequest) -> AsyncGenerator[str, None]:
        if self.failure is not None:
            if isinstance(self.failure, TimeoutError):
                raise ProviderTimeoutError("Provider timed out") from self.failure
            raise ProviderUnavailableError("Provider unavailable") from self.failure

        response = self.generate(request)
        words = response.content.split(" ")
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            yield chunk
            await asyncio.sleep(0.01)


class GeminiLLMProvider:
    name = "gemini"

    def __init__(
        self, api_key: str | None = None, default_model: str = "gemini-3.1-flash-lite"
    ) -> None:
        self.api_key = api_key
        self.default_model = default_model

    def _get_model_path(self, model: str) -> str:
        model_name = (
            model
            if (model.startswith("gemini-") or model.startswith("models/"))
            else self.default_model
        )
        if not model_name.startswith("models/"):
            return f"models/{model_name}"
        return model_name

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        if not self.api_key or self.api_key in ("your-gemini-api-key", "test_key", "dummy"):
            raise ProviderUnavailableError(
                "Gemini API key is not configured or is a dummy test key"
            )
        started = monotonic()
        import json
        import urllib.request

        model_path = self._get_model_path(request.model)
        url = f"https://generativelanguage.googleapis.com/v1beta/{model_path}:generateContent?key={self.api_key}"
        prompt_text = f"{request.instructions}\n\nContext:\n{_json(request.context)}"
        body = json.dumps({"contents": [{"parts": [{"text": prompt_text}]}]}).encode("utf-8")
        req = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=request.timeout_seconds) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data["candidates"][0]["content"]["parts"][0]["text"]
                return ProviderResponse(
                    content=content,
                    provider=self.name,
                    model=model_path,
                    estimated_cost=0.0001,
                    latency_ms=int((monotonic() - started) * 1000),
                )
        except Exception as exc:
            raise ProviderUnavailableError(f"Gemini LLM Provider error: {exc}") from exc

    async def stream_generate(self, request: ProviderRequest) -> AsyncGenerator[str, None]:
        if not self.api_key or self.api_key in ("your-gemini-api-key", "test_key", "dummy"):
            raise ProviderUnavailableError(
                "Gemini API key is not configured or is a dummy test key"
            )
        import json

        import httpx

        model_path = self._get_model_path(request.model)
        url = f"https://generativelanguage.googleapis.com/v1beta/{model_path}:streamGenerateContent?alt=sse&key={self.api_key}"
        prompt_text = f"{request.instructions}\n\nContext:\n{_json(request.context)}"
        payload = {"contents": [{"parts": [{"text": prompt_text}]}]}

        try:
            async with httpx.AsyncClient(timeout=request.timeout_seconds) as client:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code != 200:
                        raise ProviderUnavailableError(
                            f"Gemini API returned status {response.status_code}"
                        )
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if not data_str:
                                continue
                            try:
                                data = json.loads(data_str)
                                candidates = data.get("candidates", [])
                                if candidates and "content" in candidates[0]:
                                    parts = candidates[0]["content"].get("parts", [])
                                    for part in parts:
                                        if "text" in part:
                                            yield part["text"]
                            except Exception:
                                pass
        except Exception as exc:
            if isinstance(exc, (ProviderUnavailableError, ProviderTimeoutError)):
                raise
            raise ProviderUnavailableError(f"Gemini stream error: {exc}") from exc


class OpenAIProvider:
    name = "openai"

    def __init__(self, api_key: str | None = None, default_model: str = "gpt-4o-mini") -> None:
        self.api_key = api_key
        self.default_model = default_model

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        if not self.api_key or self.api_key in ("your-openai-api-key", "test_key", "dummy"):
            raise ProviderUnavailableError(
                "OpenAI API key is not configured or is a dummy test key"
            )
        started = monotonic()
        import openai

        model_name = request.model if request.model.startswith("gpt-") else self.default_model
        client = openai.OpenAI(api_key=self.api_key)
        try:
            prompt_text = f"{request.instructions}\n\nContext:\n{_json(request.context)}"
            resp = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": request.instructions},
                    {"role": "user", "content": prompt_text},
                ],
                timeout=request.timeout_seconds,
            )
            content = resp.choices[0].message.content or ""
            return ProviderResponse(
                content=content,
                provider=self.name,
                model=model_name,
                estimated_cost=0.0001,
                latency_ms=int((monotonic() - started) * 1000),
            )
        except Exception as exc:
            raise ProviderUnavailableError(f"OpenAI Provider error: {exc}") from exc

    async def stream_generate(self, request: ProviderRequest) -> AsyncGenerator[str, None]:
        if not self.api_key or self.api_key in ("your-openai-api-key", "test_key", "dummy"):
            raise ProviderUnavailableError(
                "OpenAI API key is not configured or is a dummy test key"
            )
        import openai

        model_name = request.model if request.model.startswith("gpt-") else self.default_model
        client = openai.AsyncOpenAI(api_key=self.api_key)
        try:
            prompt_text = f"{request.instructions}\n\nContext:\n{_json(request.context)}"
            stream = await client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": request.instructions},
                    {"role": "user", "content": prompt_text},
                ],
                stream=True,
                timeout=request.timeout_seconds,
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as exc:
            raise ProviderUnavailableError(f"OpenAI Provider stream error: {exc}") from exc


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

    async def stream_generate(self, request: ProviderRequest) -> AsyncGenerator[str, None]:
        decision = self.decide(request.feature)
        primary_request = ProviderRequest(**{**request.__dict__, "model": decision.primary_model})
        try:
            async for chunk in self.primary.stream_generate(primary_request):
                yield chunk
        except (ProviderTimeoutError, ProviderUnavailableError, ProviderResponseError):
            if self.fallback is None:
                raise
            fallback_request = ProviderRequest(
                **{**request.__dict__, "model": decision.fallback_model or request.model}
            )
            async for chunk in self.fallback.stream_generate(fallback_request):
                yield chunk
