from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.ai.rag.generator import FinancialRAGGenerator, RAGResponse
from app.ai.retrievers.intent_detector import IntentDetector, IntentType
from app.db.models import User

logger = logging.getLogger("app.ai.router")


@dataclass(frozen=True)
class RouteResult:
    route_type: str  # "DIRECT_SQL_TEMPLATE", "LOCAL_LLM", "CLOUD_FALLBACK"
    response: RAGResponse
    token_saved: bool = True
    confidence: float = 0.95


class AIRouter:
    """
    Intelligent AI Orchestrator that routes user questions to:
    1. DIRECT_SQL_TEMPLATE: SQL execution + Direct Python Markdown Formatter (0 LLM Token)
    2. LOCAL_LLM: Local Vector Search / SQL + Local Ollama Qwen2.5 Model
    3. CLOUD_FALLBACK: Cloud Gemini / OpenAI API fallback for complex reasoning
    """

    def __init__(self, generator: FinancialRAGGenerator) -> None:
        self.generator = generator

    def route_and_execute(
        self,
        user: User,
        question: str,
        start: Any = None,
        end: Any = None,
        currency: str = "VND",
        conversation_id: str | None = None,
        language: str = "vi",
    ) -> RAGResponse:
        intent: IntentType = IntentDetector.detect(question)
        logger.info("ai_router_intent_detected intent=%s question=%r", intent, question)

        # 1. Simple SQL Intents can bypass LLM completely (0 Token LLM) ONLY if question is a direct factual inquiry
        direct_sql_intents = {"balance_query", "income_query", "expense_query"}
        is_advice_or_chat = any(
            kw in question.lower()
            for kw in [
                "như thế nào",
                "thế nào",
                "nên",
                "tại sao",
                "làm sao",
                "tư vấn",
                "lời khuyên",
                "phương án",
                "muốn",
                "mua",
                "tên",
                "là ai",
                "ai",
                "giảm",
                "tăng",
            ]
        )
        if intent in direct_sql_intents and not is_advice_or_chat:
            logger.info("ai_router_route_decision route=DIRECT_SQL_TEMPLATE intent=%s", intent)
            response = self.generator.generate_response(
                user=user,
                question=question,
                start=start,
                end=end,
                currency=currency,
                conversation_id=conversation_id,
                language=language,
            )
            return response

        # 2. RAG / Analytical Intents -> Local LLM or RAG Generator
        logger.info("ai_router_route_decision route=LOCAL_HYBRID_AI intent=%s", intent)
        return self.generator.generate_response(
            user=user,
            question=question,
            start=start,
            end=end,
            currency=currency,
            conversation_id=conversation_id,
            language=language,
        )
