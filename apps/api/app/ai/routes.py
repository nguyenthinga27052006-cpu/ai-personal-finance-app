from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.ai.context import ExecutionContext
from app.ai.errors import (
    AIError,
    AuthenticationContextError,
    AuthorizationError,
    GuardrailViolation,
    InsufficientDataError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    StructuredOutputError,
    ToolExecutionError,
    ToolNotAllowedError,
    WriteToolsDisabledError,
)
from app.ai.gateway import default_gateway
from app.ai.nl_query import execute_nl_query
from app.ai.schemas import AIExecuteRequest, AIExecuteResponse
from app.ai.usage import AIUsageLimitExceeded, get_ai_usage_budget
from app.auth.dependencies import CurrentUser
from app.auth.rate_limit import AuthRateLimiter, get_ai_rate_limiter
from app.db.session import get_db

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])
DbSession = Annotated[Session, Depends(get_db)]
AIRateLimiter = Annotated[AuthRateLimiter, Depends(get_ai_rate_limiter)]


class NLQueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=2000)
    start: date | None = None
    end: date | None = None
    currency: str = Field(default="VND", min_length=3, max_length=3)

_ERROR_STATUS = {
    AuthenticationContextError: 401,
    AuthorizationError: 403,
    GuardrailViolation: 422,
    InsufficientDataError: 422,
    ProviderTimeoutError: 503,
    ProviderUnavailableError: 503,
    StructuredOutputError: 502,
    ToolExecutionError: 422,
    ToolNotAllowedError: 403,
    WriteToolsDisabledError: 403,
}

_PUBLIC_ERRORS = {
    AuthenticationContextError: (
        "ai_authentication_context_invalid",
        "Authentication context is invalid",
    ),
    AuthorizationError: ("ai_not_authorized", "AI request is not authorized"),
    GuardrailViolation: ("ai_security_policy_violation", "Request violates AI security policy"),
    InsufficientDataError: ("ai_insufficient_data", "Insufficient financial data"),
    ProviderTimeoutError: ("ai_provider_timeout", "AI provider timed out"),
    ProviderUnavailableError: ("ai_provider_unavailable", "AI provider is unavailable"),
    StructuredOutputError: ("ai_invalid_provider_output", "AI provider returned invalid output"),
    ToolExecutionError: ("ai_tool_execution_failed", "AI tool execution failed"),
    ToolNotAllowedError: ("ai_tool_not_allowed", "AI tool is not allowed"),
    WriteToolsDisabledError: ("ai_write_disabled", "AI write operation is disabled"),
}


def _ai_error(exc: AIError) -> HTTPException:
    status_code = next(
        (status for error_type, status in _ERROR_STATUS.items() if isinstance(exc, error_type)),
        422,
    )
    code, message = next(
        (
            public_error
            for error_type, public_error in _PUBLIC_ERRORS.items()
            if isinstance(exc, error_type)
        ),
        ("ai_execution_error", "AI request could not be completed"),
    )
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message},
    )


@router.post("/execute", response_model=AIExecuteResponse)
def execute(
    payload: AIExecuteRequest,
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
    limiter: AIRateLimiter,
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
) -> AIExecuteResponse:
    _check_ai_rate_limit(request, current_user.id, limiter)
    _consume_ai_budget(current_user.id, payload.task)
    task_tools = {
        "financial_summary": {
            "get_current_balance",
            "get_monthly_income",
            "get_monthly_expense",
            "get_budget_status",
            "get_goal_progress",
            "get_insights",
        },
        "spending_analysis": {
            "get_monthly_expense",
            "get_category_spending",
            "get_spending_trend",
            "get_insights",
        },
        "budget_review": {"get_budget_status", "get_goal_progress", "get_insights"},
    }
    context = ExecutionContext(
        db=db,
        user=current_user,
        request_id=x_request_id or str(uuid.uuid4()),
        feature=payload.task,
        allowed_tools=frozenset(task_tools[payload.task]),
    )
    try:
        result = default_gateway().execute(
            context,
            task=payload.task,
            start=payload.start,
            end=payload.end,
            currency=payload.currency,
            tools=payload.tools,
            user_input=payload.user_input,
        )
    except AIError as exc:
        raise _ai_error(exc) from exc
    return AIExecuteResponse(output=result.output, metadata=result.metadata)


@router.post("/query")
def query(
    payload: NLQueryRequest,
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
    limiter: AIRateLimiter,
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
) -> dict[str, object]:
    _check_ai_rate_limit(request, current_user.id, limiter)
    _consume_ai_budget(current_user.id, "nl_query")
    context = ExecutionContext(
        db=db,
        user=current_user,
        request_id=x_request_id or str(uuid.uuid4()),
        feature="nl_query",
        allowed_tools=frozenset(
            {
                "get_monthly_expense",
                "get_monthly_income",
                "get_current_balance",
                "get_budget_status",
                "get_goal_progress",
            }
        ),
    )
    result = execute_nl_query(
        context,
        payload.question,
        start=payload.start,
        end=payload.end,
        currency=payload.currency,
        gateway=default_gateway(),
    )
    return {
        "status": result.status,
        "intent": result.intent,
        "tool": result.tool,
        "answer": result.answer,
        "source": result.source,
        "citations": result.citations,
        "message": result.message,
    }


def _check_ai_rate_limit(request: Request, user_id: str, limiter: AuthRateLimiter) -> None:
    client_ip = request.client.host if request.client else "unknown"
    if not limiter.allow(f"ai:{user_id}:{client_ip}"):
        raise HTTPException(
            status_code=429,
            detail={"code": "rate_limited", "message": "Too many AI requests"},
        )


def _consume_ai_budget(user_id: str, feature: str) -> None:
    try:
        get_ai_usage_budget().consume(user_id, feature, units=1)
    except AIUsageLimitExceeded as exc:
        raise HTTPException(
            status_code=429,
            headers={"Retry-After": str(exc.retry_after)},
            detail={"code": "ai_budget_exceeded", "message": str(exc)},
        ) from exc
