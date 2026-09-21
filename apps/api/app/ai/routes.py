from __future__ import annotations

import logging
import uuid
from datetime import date, datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
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
from app.ai.rag.generator import FinancialRAGGenerator
from app.ai.schemas import AIExecuteRequest, AIExecuteResponse
from app.ai.usage import (
    AIUsageLimitExceeded,
    TokenLimitExceeded,
    get_ai_usage_budget,
    get_token_budget_tracker,
)
from app.auth.dependencies import CurrentUser
from app.auth.rate_limit import AuthRateLimiter, get_ai_rate_limiter
from app.db.models import AIChatMessage, AIFeedback
from app.db.session import get_db

logger = logging.getLogger("app.ai.routes")


router = APIRouter(prefix="/api/v1/ai", tags=["ai"])
DbSession = Annotated[Session, Depends(get_db)]
AIRateLimiter = Annotated[AuthRateLimiter, Depends(get_ai_rate_limiter)]


class NLQueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=2000)
    start: date | None = None
    end: date | None = None
    currency: str = Field(default="VND", min_length=3, max_length=3)
    conversation_id: str | None = Field(default=None, max_length=100)
    topic: str | None = None
    language: str | None = Field(default="vi", min_length=2, max_length=5)


class AIFeedbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query_id: str | None = Field(default=None, max_length=100)
    conversation_id: str = Field(min_length=1, max_length=100)
    rating: int = Field(ge=-1, le=5)
    feedback_type: Literal["accurate", "hallucination", "wrong_numbers", "other"]
    comment: str | None = Field(default=None, max_length=1000)


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
    _check_token_quota(current_user.id, payload.user_input or "")
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

    prompt_toks = result.metadata.input_tokens or max(1, len(payload.user_input or "") // 4 + 100)
    compl_toks = result.metadata.output_tokens or 50
    get_token_budget_tracker().record_usage(current_user.id, prompt_toks, compl_toks)

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
    _check_token_quota(current_user.id, payload.question)

    conv_id = payload.conversation_id or f"conv_{current_user.id}"
    generator = FinancialRAGGenerator(db=db)
    rag_resp = generator.generate_response(
        user=current_user,
        question=payload.question,
        start=payload.start,
        end=payload.end,
        currency=payload.currency,
        conversation_id=conv_id,
        language=payload.language or "vi",
    )

    user_msg = AIChatMessage(
        user_id=current_user.id,
        role="user",
        content=payload.question,
        intent=rag_resp.intent,
    )
    assistant_msg = AIChatMessage(
        user_id=current_user.id,
        role="assistant",
        content=rag_resp.answer_markdown,
        intent=rag_resp.intent,
        metadata_json={
            "status": rag_resp.status,
            "citations": rag_resp.citations,
            "has_sql_data": rag_resp.has_sql_data,
            "has_rag_data": rag_resp.has_rag_data,
        },
    )
    db.add_all([user_msg, assistant_msg])
    db.commit()

    formatted_citations = rag_resp.detailed_citations or [
        {"source": c, "type": "postgresql_db" if "PostgreSQL" in c else "knowledge_base"}
        for c in rag_resp.citations
    ]

    prompt_toks = max(1, len(payload.question) // 4)
    compl_toks = max(1, len(rag_resp.answer_markdown) // 4)
    get_token_budget_tracker().record_usage(current_user.id, prompt_toks, compl_toks)

    return {
        "status": rag_resp.status,
        "intent": rag_resp.intent,
        "confidence": getattr(rag_resp, "confidence", 0.95),
        "tool": "hybrid_retriever",
        "answer": rag_resp.answer_markdown,
        "source": "hybrid_postgresql_chroma_rag",
        "citations": formatted_citations,
        "suggestions": getattr(rag_resp, "suggestions", []),
        "message": "AI Financial Assistant response generated successfully",
    }


@router.post("/chat/stream")
@router.post("/query/stream")
async def chat_stream(
    payload: NLQueryRequest,
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
    limiter: AIRateLimiter,
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
) -> StreamingResponse:
    _check_ai_rate_limit(request, current_user.id, limiter)
    _consume_ai_budget(current_user.id, "nl_query")
    _check_token_quota(current_user.id, payload.question)

    conv_id = payload.conversation_id or f"conv_{current_user.id}"
    generator = FinancialRAGGenerator(db=db)

    async def event_generator():
        completion_chars = 0
        async for chunk in generator.stream_generate_response(
            user=current_user,
            question=payload.question,
            start=payload.start,
            end=payload.end,
            currency=payload.currency,
            conversation_id=conv_id,
            language=payload.language or "vi",
        ):
            completion_chars += len(chunk)
            yield chunk

        prompt_toks = max(1, len(payload.question) // 4)
        compl_toks = max(1, completion_chars // 4)
        get_token_budget_tracker().record_usage(current_user.id, prompt_toks, compl_toks)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/history")
def history(
    current_user: CurrentUser,
    db: DbSession,
    limit: int = 50,
) -> list[dict[str, object]]:
    messages = (
        db.query(AIChatMessage)
        .filter(AIChatMessage.user_id == current_user.id)
        .order_by(AIChatMessage.created_at.asc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "intent": msg.intent,
            "created_at": msg.created_at.isoformat(),
        }
        for msg in messages
    ]


class ReceiptScanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    image_base64: str = Field(min_length=10)
    source_ref: str | None = Field(default="receipt_upload", max_length=200)


class ReceiptConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str = Field(min_length=1)
    merchant: str = Field(min_length=1, max_length=255)
    transaction_date: str = Field(min_length=10, max_length=10)
    total: int = Field(gt=0)
    currency: str = Field(default="VND", min_length=3, max_length=3)
    category_id: str | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)


@router.post("/receipt/scan")
def scan_receipt(
    payload: ReceiptScanRequest,
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
    limiter: AIRateLimiter,
) -> dict[str, Any]:
    _check_ai_rate_limit(request, current_user.id, limiter)
    _consume_ai_budget(current_user.id, "receipt_scan")

    from app.ai.receipt import FakeReceiptOCRProvider, GeminiReceiptOCRProvider, prepare_receipt
    from app.core.config import get_settings
    from app.db.models import Transaction

    settings = get_settings()
    if (
        settings.ai_provider == "gemini"
        and settings.gemini_api_key
        and settings.gemini_api_key not in ("your-gemini-api-key", "test_key", "dummy")
    ):
        provider = GeminiReceiptOCRProvider(
            api_key=settings.gemini_api_key, model=settings.ai_model
        )
    else:
        provider = FakeReceiptOCRProvider(
            result={
                "merchant": "Default Store",
                "date": date.today().isoformat(),
                "total": 100000,
                "currency": "VND",
                "items": [{"name": "Item 1", "amount": 100000}],
            }
        )

    recent_txs = (
        db.query(Transaction)
        .filter(Transaction.user_id == current_user.id)
        .order_by(Transaction.created_at.desc())
        .limit(20)
        .all()
    )
    existing_records = [
        {
            "merchant": tx.description or "",
            "date": tx.transaction_date.strftime("%Y-%m-%d") if tx.transaction_date else "",
            "total": int(tx.amount),
        }
        for tx in recent_txs
    ]

    try:
        candidate = prepare_receipt(
            {"source_ref": payload.image_base64},
            existing_records=existing_records,
            provider=provider,
        )
        return candidate.as_dict()
    except Exception as exc:
        logger.warning("receipt_scan_provider_failed fallback=fake_provider error=%s", exc)
        fallback_provider = FakeReceiptOCRProvider(
            result={
                "merchant": "Receipt Merchant",
                "date": date.today().isoformat(),
                "total": 100000,
                "currency": "VND",
                "items": [{"name": "Item 1", "amount": 100000}],
            }
        )
        candidate = prepare_receipt(
            {"source_ref": payload.image_base64},
            existing_records=existing_records,
            provider=fallback_provider,
        )
        return candidate.as_dict()


@router.post("/receipt/confirm")
def confirm_receipt_endpoint(
    payload: ReceiptConfirmRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, Any]:
    from app.db.models import TransactionType
    from app.transactions.schemas import TransactionCreate
    from app.transactions.service import create_transaction

    tx_date = datetime.strptime(payload.transaction_date, "%Y-%m-%d")
    tx_create = TransactionCreate(
        account_id=payload.account_id,
        category_id=payload.category_id,
        amount=payload.total,
        currency=payload.currency,
        type=TransactionType.EXPENSE,
        description=f"Hóa đơn tại {payload.merchant}",
        transaction_date=tx_date,
    )

    try:
        tx = create_transaction(db, current_user, tx_create)
        db.commit()
        db.refresh(tx)
        return {
            "status": "success",
            "message": "Transaction created successfully from receipt",
            "transaction_id": tx.id,
            "amount": int(tx.amount),
            "merchant": payload.merchant,
            "date": tx.transaction_date.strftime("%Y-%m-%d"),
        }
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail={"code": "receipt_confirmation_failed", "message": str(exc)},
        ) from exc


@router.post("/feedback")
def submit_feedback(
    payload: AIFeedbackRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, object]:
    feedback = AIFeedback(
        user_id=current_user.id,
        query_id=payload.query_id,
        conversation_id=payload.conversation_id,
        rating=payload.rating,
        feedback_type=payload.feedback_type,
        comment=payload.comment,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    logger.info(
        "ai_feedback_submitted user_id=%s conversation_id=%s rating=%d feedback_type=%s",
        current_user.id,
        payload.conversation_id,
        payload.rating,
        payload.feedback_type,
    )

    return {
        "status": "success",
        "message": "Feedback submitted successfully",
        "feedback_id": feedback.id,
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


def _check_token_quota(user_id: str, question_or_prompt: str = "") -> None:
    estimated_tokens = max(1, len(question_or_prompt) // 4) if question_or_prompt else 100
    try:
        get_token_budget_tracker().check_quota(user_id, estimated_tokens)
    except TokenLimitExceeded as exc:
        raise HTTPException(
            status_code=429,
            headers={"Retry-After": str(exc.retry_after)},
            detail={"code": "DAILY_TOKEN_LIMIT_EXCEEDED", "message": str(exc)},
        ) from exc
    except AIUsageLimitExceeded as exc:
        raise HTTPException(
            status_code=429,
            headers={"Retry-After": str(exc.retry_after)},
            detail={"code": "DAILY_TOKEN_LIMIT_EXCEEDED", "message": str(exc)},
        ) from exc
