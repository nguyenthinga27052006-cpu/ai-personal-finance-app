from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any, AsyncGenerator

from sqlalchemy.orm import Session

from app.ai.gateway import AIGateway, default_gateway
from app.ai.providers import ProviderRequest
from app.ai.rag.memory import RAGMemoryStore, get_memory_store
from app.ai.rag.prompts import FINANCIAL_RAG_SYSTEM_PROMPT, build_rag_user_prompt
from app.ai.rag.vector_store import get_vector_store
from app.ai.retrievers.hybrid_retriever import HybridContext, HybridRetriever
from app.ai.retrievers.sql_retriever import FinancialFactValidator
from app.db.models import User

logger = logging.getLogger("app.ai.rag")


FINANCIAL_LEGAL_DISCLAIMER = (
    "\n\n*⚠️ Lưu ý: Phân tích trên dựa trên dữ liệu giao dịch đã ghi nhận và kiến thức tham khảo, "
    "không cấu thành lời khuyên đầu tư hay tư vấn pháp lý chuyên nghiệp.*"
)


class CitationValidator:

    """Validates citations against real retrieved evidence metadata, removing hallucinated citations."""

    @staticmethod
    def validate(
        citations: list[str],
        hybrid_context: HybridContext,
    ) -> tuple[list[str], list[dict[str, Any]]]:
        valid_summary: list[str] = []
        detailed = hybrid_context.detailed_citations()

        # Ground truth allowed sources/titles
        real_sources = {d.get("source") for d in detailed if d.get("source")}
        real_titles = {d.get("title") for d in detailed if d.get("title")}
        allowed_set = real_sources | real_titles
        valid_sql_summary = hybrid_context.citations_summary()

        for c in citations:
            # Must strictly match valid SQL context summary or explicit document titles/sources
            if c in valid_sql_summary or c in allowed_set or any(r in c for r in allowed_set if len(r) > 4):
                if c not in valid_summary:
                    valid_summary.append(c)

        if not valid_summary:
            valid_summary = [c for c in valid_sql_summary if c]

        return valid_summary, detailed


@dataclass(frozen=True)
class RAGResponse:
    answer_markdown: str
    intent: str
    citations: list[str]
    status: str
    has_sql_data: bool
    has_rag_data: bool
    metadata: dict[str, Any]
    suggestions: list[str] = field(default_factory=list)
    confidence: float = 0.95
    detailed_citations: list[dict[str, Any]] = field(default_factory=list)


class FinancialRAGGenerator:
    """Coordinates intent detection, hybrid context retrieval, conversation memory, and natural response generation."""

    def __init__(
        self,
        db: Session,
        gateway: AIGateway | None = None,
        memory_store: RAGMemoryStore | None = None,
    ) -> None:
        self.db = db
        self.gateway = gateway or default_gateway()
        self.memory_store = memory_store or get_memory_store()
        self.hybrid_retriever = HybridRetriever(db=db, vector_store=get_vector_store())

    def generate_response(
        self,
        user: User,
        question: str,
        start: date | None = None,
        end: date | None = None,
        currency: str = "VND",
        conversation_id: str | None = None,
        language: str = "vi",
    ) -> RAGResponse:
        # 1. Get conversation memory (last 10 turns)
        history_msgs = self.memory_store.get_history(user.id, conversation_id)
        history_text = self.memory_store.get_formatted_context(user.id, conversation_id)

        # 2. Retrieve hybrid context (SQL user facts + Chroma VectorDB RAG knowledge)
        hybrid_context: HybridContext = self.hybrid_retriever.retrieve(
            user=user, question=question, start=start, end=end, currency=currency, top_k=4, history=history_msgs
        )

        # Validate financial facts integrity & user ownership
        facts_status = "VALID"
        if hybrid_context.has_sql_data:
            financial_facts = FinancialFactValidator.validate(user.id, hybrid_context.sql_context)
            if any(f.status != "VALID" for f in financial_facts):
                facts_status = financial_facts[0].status

        # Record user question in memory
        self.memory_store.add_message(
            user_id=user.id, content=question, role="user", conversation_id=conversation_id
        )

        # 3. Handle strict Hallucination Guard when no SQL data and no RAG data (skip for general/greeting conversational queries)
        is_general_or_greeting = hybrid_context.intent in ("greeting", "general_query")
        if not hybrid_context.has_sql_data and not hybrid_context.has_rag_data and not is_general_or_greeting:
            if language.lower() in ("en", "english"):
                fallback_answer = (
                    "## Answer\n"
                    "I don't have enough data to draw a conclusion yet.\n\n"
                    "## Quick Analysis\n"
                    "* Spending: No transaction info available\n"
                    "* Rate: 0%\n"
                    "* Trend: No data available\n\n"
                    "## Suggestions\n"
                    "* Please add transactions or connect an account so I can analyze your finances.\n\n"
                    "## Source\n"
                    "* No data source"
                )
            else:
                fallback_answer = (
                    "## Câu trả lời\n"
                    "Mình chưa có dữ liệu để kết luận điều đó.\n\n"
                    "## Phân tích nhanh\n"
                    "* Chi tiêu: Chưa có thông tin giao dịch\n"
                    "* Tỷ lệ: 0%\n"
                    "* Xu hướng: Chưa có dữ liệu\n\n"
                    "## Gợi ý cho bạn\n"
                    "* Hãy thêm giao dịch hoặc kết nối tài khoản để mình phân tích giúp bạn nhé.\n\n"
                    "## Nguồn\n"
                    "* Chưa có nguồn dữ liệu"
                )
            self.memory_store.add_message(
                user_id=user.id, content=fallback_answer, role="assistant", conversation_id=conversation_id
            )
            return RAGResponse(
                answer_markdown=fallback_answer,
                intent=hybrid_context.intent,
                citations=["Chưa có nguồn dữ liệu"],
                status="INSUFFICIENT_DATA",
                has_sql_data=False,
                has_rag_data=False,
                metadata={},
                detailed_citations=[],
            )

        # 4. Build prompt
        user_facts_text = hybrid_context.sql_context.summary_text()
        rag_knowledge_text = hybrid_context.formatted_rag_knowledge()
        raw_citations = hybrid_context.citations_summary()
        citations, detailed_citations = CitationValidator.validate(raw_citations, hybrid_context)

        user_prompt = build_rag_user_prompt(
            question=question,
            intent=hybrid_context.intent,
            user_facts_text=user_facts_text,
            rag_knowledge_text=rag_knowledge_text,
            conversation_history_text=history_text,
            has_sql_data=hybrid_context.has_sql_data,
            has_rag_data=hybrid_context.has_rag_data,
            language=language,
        )

        # 5. Call LLM via Gateway router
        provider_req = ProviderRequest(
            feature="nl_query",
            model="foundation-simple",
            instructions=FINANCIAL_RAG_SYSTEM_PROMPT,
            context={
                "user_prompt": user_prompt,
                "intent": hybrid_context.intent,
                "has_sql_data": hybrid_context.has_sql_data,
                "has_rag_data": hybrid_context.has_rag_data,
            },
            tools=(),
        )

        try:
            resp, decision, _ = self.gateway.router.generate(provider_req)
            generated_text = resp.content
        except Exception as exc:
            logger.warning("Gateway call failed, synthesizing deterministic response: %s", exc)
            generated_text = ""

        # 6. Format final answer structure
        final_markdown = self._format_markdown_response(
            raw_text=generated_text,
            hybrid_context=hybrid_context,
            citations=citations,
        )

        # Save assistant message in memory
        self.memory_store.add_message(
            user_id=user.id, content=final_markdown, role="assistant", conversation_id=conversation_id
        )

        # Generate actionable suggestions
        is_en = language.lower() in ("en", "english")
        suggestions = []
        sql_ctx = hybrid_context.sql_context
        if sql_ctx.has_data:
            if sql_ctx.top_categories:
                top_c = sql_ctx.top_categories[0]
                suggestions.append(f"Optimize 10% expenses for category '{top_c['category']}'" if is_en else f"Tối ưu 10% chi phí cho danh mục '{top_c['category']}'")
            if sql_ctx.net_savings > 0:
                suggestions.append(f"Transfer {sql_ctx.net_savings * Decimal('0.3'):,.0f} VND surplus to Emergency Fund" if is_en else f"Chuyển {sql_ctx.net_savings * Decimal('0.3'):,.0f} VND thặng dư vào Quỹ Khẩn Cấp")
            else:
                suggestions.append("Cut non-essential expenses to create savings surplus" if is_en else "Cắt giảm các khoản chi không thiết yếu để tạo thặng dư")
            if sql_ctx.goals:
                g = sql_ctx.goals[0]
                suggestions.append(f"Contribute more to goal '{g['name']}'" if is_en else f"Đóng góp thêm vào mục tiêu '{g['name']}'")
        else:
            suggestions.append("Add new transactions so AI can analyze cash flow" if is_en else "Thêm giao dịch mới để AI phân tích dòng tiền")
            suggestions.append("Check 50/30/20 financial management guide" if is_en else "Xem cẩm nang quy tắc quản lý tài chính 50/30/20")

        return RAGResponse(
            answer_markdown=final_markdown,
            intent=hybrid_context.intent,
            citations=citations,
            status="SUCCESS" if facts_status == "VALID" else facts_status,
            has_sql_data=hybrid_context.has_sql_data,
            has_rag_data=hybrid_context.has_rag_data,
            metadata={"citations": citations, "intent": hybrid_context.intent, "detailed_citations": detailed_citations},
            suggestions=suggestions,
            confidence=0.95,
            detailed_citations=detailed_citations,
        )

    async def stream_generate_response(
        self,
        user: User,
        question: str,
        start: date | None = None,
        end: date | None = None,
        currency: str = "VND",
        conversation_id: str | None = None,
        language: str = "vi",
    ) -> AsyncGenerator[str, None]:
        # 1. Get conversation memory
        history_msgs = self.memory_store.get_history(user.id, conversation_id)
        history_text = self.memory_store.get_formatted_context(user.id, conversation_id)

        # 2. Retrieve hybrid context (SQL user facts + Chroma VectorDB RAG knowledge)
        hybrid_context: HybridContext = self.hybrid_retriever.retrieve(
            user=user, question=question, start=start, end=end, currency=currency, top_k=4, history=history_msgs
        )

        # Validate financial facts integrity & user ownership
        facts_status = "VALID"
        if hybrid_context.has_sql_data:
            financial_facts = FinancialFactValidator.validate(user.id, hybrid_context.sql_context)
            if any(f.status != "VALID" for f in financial_facts):
                facts_status = financial_facts[0].status

        # Record user question in memory
        self.memory_store.add_message(
            user_id=user.id, content=question, role="user", conversation_id=conversation_id
        )


        # 3. Handle strict Hallucination Guard when no SQL data and no RAG data (skip for general/greeting conversational queries)
        is_general_or_greeting = hybrid_context.intent in ("greeting", "general_query")
        if not hybrid_context.has_sql_data and not hybrid_context.has_rag_data and not is_general_or_greeting:
            if language.lower() in ("en", "english"):
                fallback_answer = (
                    "## Answer\n"
                    "I don't have enough data to draw a conclusion yet.\n\n"
                    "## Quick Analysis\n"
                    "* Spending: No transaction info available\n"
                    "* Rate: 0%\n"
                    "* Trend: No data available\n\n"
                    "## Suggestions\n"
                    "* Please add transactions or connect an account so I can analyze your finances.\n\n"
                    "## Source\n"
                    "* No data source"
                )
            else:
                fallback_answer = (
                    "## Câu trả lời\n"
                    "Mình chưa có dữ liệu để kết luận điều đó.\n\n"
                    "## Phân tích nhanh\n"
                    "* Chi tiêu: Chưa có thông tin giao dịch\n"
                    "* Tỷ lệ: 0%\n"
                    "* Xu hướng: Chưa có dữ liệu\n\n"
                    "## Gợi ý cho bạn\n"
                    "* Hãy thêm giao dịch hoặc kết nối tài khoản để mình phân tích giúp bạn nhé.\n\n"
                    "## Nguồn\n"
                    "* Chưa có nguồn dữ liệu"
                )
            words = fallback_answer.split(" ")
            for i, w in enumerate(words):
                chunk = w + (" " if i < len(words) - 1 else "")
                yield f"data: {json.dumps({'type': 'token', 'content': chunk}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.01)

            self.memory_store.add_message(
                user_id=user.id, content=fallback_answer, role="assistant", conversation_id=conversation_id
            )

            metadata_event = {
                "type": "metadata",
                "status": "INSUFFICIENT_DATA",
                "intent": hybrid_context.intent,
                "citations": ["Chưa có nguồn dữ liệu"],
                "has_sql_data": False,
                "has_rag_data": False,
                "suggestions": [],
            }
            yield f"data: {json.dumps(metadata_event, ensure_ascii=False)}\n\n"
            return

        # 4. Build prompt & citations
        user_facts_text = hybrid_context.sql_context.summary_text()
        rag_knowledge_text = hybrid_context.formatted_rag_knowledge()
        raw_citations = hybrid_context.citations_summary()
        citations, detailed_citations = CitationValidator.validate(raw_citations, hybrid_context)

        user_prompt = build_rag_user_prompt(
            question=question,
            intent=hybrid_context.intent,
            user_facts_text=user_facts_text,
            rag_knowledge_text=rag_knowledge_text,
            conversation_history_text=history_text,
            has_sql_data=hybrid_context.has_sql_data,
            has_rag_data=hybrid_context.has_rag_data,
            language=language,
        )

        provider_req = ProviderRequest(
            feature="nl_query",
            model="foundation-simple",
            instructions=FINANCIAL_RAG_SYSTEM_PROMPT,
            context={
                "user_prompt": user_prompt,
                "intent": hybrid_context.intent,
                "has_sql_data": hybrid_context.has_sql_data,
                "has_rag_data": hybrid_context.has_rag_data,
            },
            tools=(),
        )

        # 5. Stream response tokens
        full_chunks: list[str] = []
        is_real_llm_stream = False

        primary = getattr(self.gateway.router, "primary", None)
        if primary and (getattr(primary, "is_production", False) or getattr(primary, "name", "") in ("gemini", "openai")):
            try:
                async for token_chunk in self.gateway.router.stream_generate(provider_req):
                    is_real_llm_stream = True
                    full_chunks.append(token_chunk)
                    yield f"data: {json.dumps({'type': 'token', 'content': token_chunk}, ensure_ascii=False)}\n\n"
            except Exception as exc:
                logger.warning("Streaming LLM call failed, falling back to deterministic response: %s", exc)
                full_chunks = []
                is_real_llm_stream = False

        if not is_real_llm_stream or not full_chunks:
            fallback_text = self._format_markdown_response(
                raw_text="",
                hybrid_context=hybrid_context,
                citations=citations,
            )
            full_chunks = []
            words = fallback_text.split(" ")
            for i, w in enumerate(words):
                chunk = w + (" " if i < len(words) - 1 else "")
                full_chunks.append(chunk)
                yield f"data: {json.dumps({'type': 'token', 'content': chunk}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.01)

        final_answer = "".join(full_chunks)

        # Save assistant message in memory
        self.memory_store.add_message(
            user_id=user.id, content=final_answer, role="assistant", conversation_id=conversation_id
        )

        # Actionable suggestions
        suggestions = []
        sql_ctx = hybrid_context.sql_context
        if sql_ctx.has_data:
            if sql_ctx.top_categories:
                top_c = sql_ctx.top_categories[0]
                suggestions.append(f"Tối ưu 10% chi phí cho danh mục '{top_c['category']}'")
            if sql_ctx.net_savings > 0:
                suggestions.append(f"Chuyển {sql_ctx.net_savings * Decimal('0.3'):,.0f} VND thặng dư vào Quỹ Khẩn Cấp")
            else:
                suggestions.append("Cắt giảm các khoản chi không thiết yếu để tạo thặng dư")
            if sql_ctx.goals:
                g = sql_ctx.goals[0]
                suggestions.append(f"Đóng góp thêm vào mục tiêu '{g['name']}'")
        else:
            suggestions.append("Thêm giao dịch mới để AI phân tích dòng tiền")
            suggestions.append("Xem cẩm nang quy tắc quản lý tài chính 50/30/20")

        metadata_event = {
            "type": "metadata",
            "status": "SUCCESS" if facts_status == "VALID" else facts_status,
            "intent": hybrid_context.intent,
            "citations": detailed_citations or [
                {"source": c, "type": "postgresql_db" if "PostgreSQL" in c else "knowledge_base"}
                for c in citations
            ],
            "has_sql_data": hybrid_context.has_sql_data,
            "has_rag_data": hybrid_context.has_rag_data,
            "suggestions": suggestions,
        }
        yield f"data: {json.dumps(metadata_event, ensure_ascii=False)}\n\n"



    def _format_markdown_response(
        self,
        raw_text: str,
        hybrid_context: HybridContext,
        citations: list[str],
    ) -> str:
        body = self._build_raw_markdown_response(raw_text, hybrid_context, citations)
        intent = hybrid_context.intent

        disclaimer_intents = {
            "saving_advice",
            "investment",
            "debt_advice",
            "affordability",
            "spending_analysis",
            "budget_review",
            "income_query",
            "expense_query",
            "balance_query",
            "comparison_query",
        }
        needs_disclaimer = (
            intent in disclaimer_intents
            or hybrid_context.has_sql_data
        )
        if needs_disclaimer and intent not in ("greeting", "general_query") and FINANCIAL_LEGAL_DISCLAIMER.strip() not in body:
            body = body.rstrip() + FINANCIAL_LEGAL_DISCLAIMER

        return body

    def _build_raw_markdown_response(
        self,
        raw_text: str,
        hybrid_context: HybridContext,
        citations: list[str],
    ) -> str:
        if (
            raw_text
            and len(raw_text.strip()) > 30
            and "AI provider foundation response" not in raw_text
            and "allowed financial query map" not in raw_text
            and "UNSUPPORTED_REQUEST" not in raw_text
        ):
            return raw_text.strip()


        intent = hybrid_context.intent
        sql_ctx = hybrid_context.sql_context

        # 1. Greetings & General Non-Financial Queries
        if intent in ("greeting", "general_query"):
            return (
                "Chào bạn! 👋\n\n"
                "Mình là **Trợ lý Tài chính AI**. Mình luôn sẵn sàng hỗ trợ bạn:\n"
                "* 💵 **Xem số dư tài khoản & tổng thu chi**\n"
                "* 📊 **Phân tích danh mục chi tiêu chính**\n"
                "* 🎯 **Kiểm tra tiến độ ngân sách & mục tiêu tiết kiệm**\n"
                "* 💡 **Tư vấn lập kế hoạch tài chính cá nhân**\n\n"
                "Bạn cần mình hỗ trợ kiểm tra thông tin tài chính gì hôm nay?"
            )

        # 2. Knowledge Queries (RAG Vector Store)
        if intent == "knowledge" and hybrid_context.vector_chunks:
            chunk = hybrid_context.vector_chunks[0]
            title = chunk.metadata.get('title', 'Quản lý tài chính')
            return f"### {title}\n\n{chunk.content}\n\n💡 *Nguồn: {chunk.metadata.get('source', 'Cẩm nang Tài chính')}*"

        # 3. Multi-Month / Comparison Queries
        if intent == "comparison_query" or (sql_ctx.monthly_breakdown and len(sql_ctx.monthly_breakdown) > 1):
            num_m = len(sql_ctx.monthly_breakdown) if sql_ctx.monthly_breakdown else 1
            lines = [f"Theo thống kê chi tiêu trong **{num_m} tháng gần nhất**:\n"]

            if sql_ctx.monthly_breakdown:
                max_expense_m = max(sql_ctx.monthly_breakdown, key=lambda x: x["expense"])
                min_expense_m = min(sql_ctx.monthly_breakdown, key=lambda x: x["expense"])
                lines.append(f"🏆 **Tháng chi tiêu nhiều nhất**: **{max_expense_m['month']}** với số tiền **{max_expense_m['expense']:,.0f} {sql_ctx.currency}**.")
                if min_expense_m != max_expense_m:
                    lines.append(f"🟢 **Tháng tiết kiệm nhất**: **{min_expense_m['month']}** với số tiền **{min_expense_m['expense']:,.0f} {sql_ctx.currency}**.\n")

            if sql_ctx.top_categories:
                top_cat = sql_ctx.top_categories[0]
                lines.append(f"🛒 **Danh mục chi tiêu cao nhất**: **{top_cat['category']}** với tổng số tiền **{top_cat['amount']:,.0f} {sql_ctx.currency}** (chiếm **{top_cat['percentage']:.1f}%** tổng chi toàn kỳ).\n")

            if sql_ctx.monthly_breakdown:
                lines.append("#### 📅 Bảng tổng hợp các tháng:")
                lines.append("| Tháng | Chi tiêu (VND) | Thu nhập (VND) | Thặng dư (VND) | Biến động |")
                lines.append("|---|---|---|---|---|")
                for m in sql_ctx.monthly_breakdown:
                    chg_str = "-"
                    if m["change_pct"] is not None:
                        if m["change_pct"] > 1000:
                            chg_str = "📈 Tăng mạnh"
                        elif m["change_pct"] > 0:
                            chg_str = f"📈 Tăng {m['change_pct']:.1f}%"
                        elif m["change_pct"] < 0:
                            chg_str = f"📉 Giảm {abs(m['change_pct']):.1f}%"
                        else:
                            chg_str = "➡️ Không đổi"

                    highlight = " 🏆 (Cao nhất)" if m == max_expense_m and len(sql_ctx.monthly_breakdown) > 1 else ""
                    lines.append(f"| **{m['month']}**{highlight} | {m['expense']:,.0f} | {m['income']:,.0f} | {m['savings']:+,.0f} | {chg_str} |")

            return "\n".join(lines)

        # 4. Balance Query
        if intent == "balance_query":
            lines = [f"### 💵 Số dư tài khoản hiện tại\n"]
            lines.append(f"Tổng số dư tài khoản của bạn là **{sql_ctx.total_balance:,.0f} {sql_ctx.currency}** (gồm {len(sql_ctx.accounts)} tài khoản).\n")
            if sql_ctx.accounts:
                lines.append("#### 💳 Chi tiết từng tài khoản:")
                for acc in sql_ctx.accounts:
                    lines.append(f"* **{acc['name']}**: `{acc['balance']:,.0f} {sql_ctx.currency}`")
            lines.append("\n💡 *Dữ liệu được cập nhật từ hồ sơ tài khoản thực tế của bạn.*")
            return "\n".join(lines)

        # 5. Income Query
        if intent == "income_query":
            lines = [f"### 🟢 Tổng thu nhập kỳ này\n"]
            lines.append(f"Trong kỳ từ **{sql_ctx.period_start}** đến **{sql_ctx.period_end}**, tổng thu nhập của bạn là **{sql_ctx.total_income:,.0f} {sql_ctx.currency}**.\n")
            lines.append(f"* ⚖️ **Thặng dư tích lũy kỳ này**: `{sql_ctx.net_savings:,.0f} {sql_ctx.currency}`")
            lines.append(f"* 🔴 **Tổng chi tiêu cùng kỳ**: `{sql_ctx.total_expense:,.0f} {sql_ctx.currency}`")
            return "\n".join(lines)

        # 6. Expense / Spending Query
        if intent in {"expense_query", "spending_analysis"}:
            lines = [f"### 🔴 Báo cáo chi tiêu kỳ này\n"]
            lines.append(f"Trong kỳ từ **{sql_ctx.period_start}** đến **{sql_ctx.period_end}**, tổng chi tiêu của bạn là **{sql_ctx.total_expense:,.0f} {sql_ctx.currency}** (gồm **{sql_ctx.transaction_count}** giao dịch).\n")
            if sql_ctx.top_categories:
                lines.append("#### 🛒 Các danh mục chi tiêu hàng đầu:")
                for cat in sql_ctx.top_categories:
                    lines.append(f"* **{cat['category']}**: `{cat['amount']:,.0f} {sql_ctx.currency}` ({cat['percentage']:.1f}% tổng chi)")
            lines.append(f"\n* 💵 **Số dư tài khoản hiện tại**: `{sql_ctx.total_balance:,.0f} {sql_ctx.currency}`")
            return "\n".join(lines)

        # 7. Budget & Goal Review Query
        if intent == "budget_review":
            lines = ["### 🎯 Tình hình Ngân sách & Mục tiêu\n"]
            if sql_ctx.budgets:
                lines.append("#### 📊 Trạng thái ngân sách:")
                for b in sql_ctx.budgets:
                    lines.append(f"* Ngân sách **{b['name']}**: Đã dùng `{b['spent']:,.0f}/{b['amount']:,.0f} {sql_ctx.currency}` ({b['usage_pct']:.1f}%)")
            else:
                lines.append("* Bạn chưa thiết lập ngân sách hàng tháng.")

            if sql_ctx.goals:
                lines.append("\n#### 🏆 Mục tiêu tiết kiệm:")
                for g in sql_ctx.goals:
                    lines.append(f"* Mục tiêu **{g['name']}**: Tích lũy `{g['current']:,.0f}/{g['target']:,.0f} {sql_ctx.currency}` ({g['progress_pct']:.1f}%)")
            else:
                lines.append("\n* Bạn chưa tạo mục tiêu tiết kiệm nào.")
            return "\n".join(lines)

        # 8. Default SQL Data Summary
        if hybrid_context.has_sql_data:
            lines = ["### 📊 Báo cáo tài chính tổng quan\n"]
            lines.append(f"Trong kỳ từ **{sql_ctx.period_start}** đến **{sql_ctx.period_end}**:\n")
            lines.append(f"* 💵 **Số dư tài khoản**: `{sql_ctx.total_balance:,.0f} {sql_ctx.currency}` ({len(sql_ctx.accounts)} tài khoản)")
            lines.append(f"* 🔴 **Tổng chi tiêu**: `{sql_ctx.total_expense:,.0f} {sql_ctx.currency}` ({sql_ctx.transaction_count} giao dịch)")
            lines.append(f"* 🟢 **Tổng thu nhập**: `{sql_ctx.total_income:,.0f} {sql_ctx.currency}`")
            lines.append(f"* ⚖️ **Thặng dư**: `{sql_ctx.net_savings:,.0f} {sql_ctx.currency}`")
            return "\n".join(lines)

        # 9. Fallback
        return (
            "Mình đã kiểm tra dữ liệu tài khoản của bạn nhưng chưa tìm thấy thông tin phù hợp.\n\n"
            "💡 **Gợi ý**: Bạn hãy thêm các giao dịch thu chi mới hoặc đặt câu hỏi như 'Số dư hiện tại của tôi là bao nhiêu?' để mình hỗ trợ nhé!"
        )
