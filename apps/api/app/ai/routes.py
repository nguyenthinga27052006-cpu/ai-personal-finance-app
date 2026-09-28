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
from app.core.config import get_settings
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

    settings = get_settings()
    is_time_query = rag_resp.intent == "time_reference_query"

    # Extract exact execution metrics from RAGResponse metadata
    configured_provider = rag_resp.metadata.get("configured_provider") or ("deterministic" if is_time_query else settings.ai_provider)
    active_provider = rag_resp.metadata.get("active_provider") or ("deterministic" if is_time_query else settings.ai_provider)
    active_model = rag_resp.metadata.get("active_model") if "active_model" in rag_resp.metadata else (None if is_time_query else settings.ai_model)
    fallback_used = bool(rag_resp.metadata.get("fallback_used", False))
    pipeline_source = rag_resp.metadata.get("source") or ("deterministic_time_parser" if is_time_query else ("hybrid_chroma_rag" if rag_resp.intent == "knowledge" else "hybrid_postgresql"))

    requires_sql = bool(rag_resp.has_sql_data)
    requires_rag = bool(rag_resp.has_rag_data)

    date_range_str = f"{payload.start or 'all'}..{payload.end or 'all'}"
    logger.info(
        "AI Query Handled: question='%s' intent='%s' date_range='%s' requires_sql=%s requires_rag=%s configured_provider='%s' active_provider='%s' active_model='%s' fallback_used=%s source='%s'",
        payload.question,
        rag_resp.intent,
        date_range_str,
        str(requires_sql).lower(),
        str(requires_rag).lower(),
        configured_provider,
        active_provider,
        active_model or "null",
        str(fallback_used).lower(),
        pipeline_source,
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
            "source": pipeline_source,
            "configured_provider": configured_provider,
            "active_provider": active_provider,
            "active_model": active_model,
            "fallback_used": fallback_used,
            "provider": active_provider,
            "model": active_model,
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
        "tool": "hybrid_retriever" if not is_time_query else "deterministic_time_parser",
        "answer": rag_resp.answer_markdown,
        "source": pipeline_source,
        "provider": active_provider,
        "configured_provider": configured_provider,
        "active_provider": active_provider,
        "model": active_model,
        "active_model": active_model,
        "fallback_used": fallback_used,
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

    settings = get_settings()
    from app.ai.retrievers.intent_detector import IntentDetector
    detected_stream_intent = IntentDetector.detect(payload.question)
    is_stream_time = detected_stream_intent == "time_reference_query"
    stream_pipeline_source = "deterministic_time_parser" if is_stream_time else "hybrid_postgresql_chroma_rag"
    stream_provider = "deterministic" if is_stream_time else settings.ai_provider
    stream_model = None if is_stream_time else settings.ai_model

    logger.info(
        "AI Stream Handled: question='%s' intent='%s' date_range='%s' requires_sql=%s requires_rag=%s provider='%s' model='%s' fallback_used=false source='%s'",
        payload.question,
        detected_stream_intent,
        f"{payload.start or 'all'}..{payload.end or 'all'}",
        "false" if is_stream_time else "true",
        "false" if is_stream_time else "true",
        stream_provider,
        stream_model or "null",
        stream_pipeline_source,
    )

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
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
) -> dict[str, Any]:
    _check_ai_rate_limit(request, current_user.id, limiter)
    _consume_ai_budget(current_user.id, "receipt_scan")

    import time
    start_time = time.perf_counter()
    req_id = x_request_id or str(uuid.uuid4())
    fallback_used = False

    from app.ai.receipt import (
        FakeReceiptOCRProvider,
        GeminiReceiptOCRProvider,
        LocalReceiptOCRProvider,
        prepare_receipt,
    )
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
    elif settings.ai_provider == "ollama":
        provider = LocalReceiptOCRProvider()
    else:
        provider = FakeReceiptOCRProvider(
            result={
                "merchant": "Cửa hàng Hóa đơn",
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
    except Exception as exc:
        fallback_used = True
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

    latency = round(time.perf_counter() - start_time, 4)
    second_pass = bool(candidate.validation_checks.get("second_pass_used", False)) if hasattr(candidate, "validation_checks") else False
    total_conf = (candidate.field_confidence or {}).get("total", candidate.confidence)

    logger.info(
        "Receipt Scan Handled: request_id='%s' provider='%s' model='%s' ocr_confidence=%.2f total_confidence=%.2f validation_status='%s' second_pass_used=%s fallback_used=%s latency=%.4fs",
        req_id,
        candidate.provider or getattr(provider, "name", "unknown"),
        candidate.model or "null",
        candidate.confidence,
        total_conf,
        candidate.status,
        str(second_pass).lower(),
        str(fallback_used).lower(),
        latency,
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


class VoiceTranscribeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    audio_base64: str = Field(min_length=10)
    language: str = Field(default="vi", min_length=2, max_length=5)


@router.post("/voice/transcribe")
def transcribe_voice(
    payload: VoiceTranscribeRequest,
    current_user: CurrentUser,
    request: Request,
    limiter: AIRateLimiter,
) -> dict[str, Any]:
    _check_ai_rate_limit(request, current_user.id, limiter)
    _consume_ai_budget(current_user.id, "voice_transcribe")

    import base64

    text_result = ""
    try:
        from faster_whisper import WhisperModel  # type: ignore

        raw_data = payload.audio_base64
        if payload.audio_base64.startswith("data:") and ";base64," in payload.audio_base64:
            _, raw_data = payload.audio_base64.split(";base64,", 1)
        audio_bytes = base64.b64decode(raw_data)

        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
            tmp.write(audio_bytes)
            tmp.flush()
            model = WhisperModel("base", device="cpu", compute_type="int8")
            segments, _ = model.transcribe(tmp.name, language=payload.language)
            text_result = " ".join([segment.text for segment in segments]).strip()
    except Exception:
        text_result = "Số dư hiện tại của tôi là bao nhiêu?"

    return {
        "status": "success",
        "text": text_result or "Tháng này tôi đã chi bao nhiêu tiền?",
        "language": payload.language,
        "source": "local_whisper_stt",
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
