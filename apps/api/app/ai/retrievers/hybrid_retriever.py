from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Literal

from sqlalchemy.orm import Session

from app.ai.rag.vector_store import DocumentChunk, RAGVectorStore, get_vector_store
from app.ai.retrievers.intent_detector import IntentDetector, IntentType
from app.ai.retrievers.sql_retriever import SQLRetriever, SQLUserDataContext
from app.db.models import User

ContextStatus = Literal["SUPPORTED", "WEAK_CONTEXT", "NO_RELEVANT_CONTEXT", "INSUFFICIENT_DATA"]


@dataclass(frozen=True)
class HybridContext:
    intent: IntentType
    sql_context: SQLUserDataContext
    vector_chunks: list[DocumentChunk]
    has_sql_data: bool
    has_rag_data: bool
    status: ContextStatus = "SUPPORTED"

    def formatted_rag_knowledge(self) -> str:
        if not self.vector_chunks:
            return "Không tìm thấy kiến thức RAG liên quan."
        parts = []
        for idx, chunk in enumerate(self.vector_chunks, start=1):
            source_title = chunk.metadata.get("source") or chunk.metadata.get("title") or "RAG Document"
            parts.append(f"[{idx}] Source: {source_title}\n{chunk.content}")
        return "\n\n".join(parts)

    def citations_summary(self) -> list[str]:
        citations = []
        if self.has_sql_data:
            citations.append(
                f"PostgreSQL ({self.sql_context.transaction_count} giao dịch kỳ {self.sql_context.period_start} đến {self.sql_context.period_end})"
            )
            if self.sql_context.budgets:
                citations.append("Budget & Ngân sách hàng tháng")
            if self.sql_context.goals:
                citations.append("Mục tiêu tích lũy cá nhân")

        for chunk in self.vector_chunks:
            src = chunk.metadata.get("source") or chunk.metadata.get("title")
            if src and src not in citations:
                citations.append(src)

        return citations

    def detailed_citations(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        if self.has_sql_data:
            records.append({
                "citation_id": "sql-user-data",
                "source": "PostgreSQL_Database",
                "title": "Dữ liệu Tài chính Cá nhân",
                "type": "sql_fact",
                "period": f"{self.sql_context.period_start} đến {self.sql_context.period_end}",
            })

        for chunk in self.vector_chunks:
            doc_id = chunk.metadata.get("document_id") or chunk.doc_id
            title = chunk.metadata.get("title") or "Tài liệu Tài chính"
            source = chunk.metadata.get("source") or title
            records.append({
                "citation_id": f"kb-{doc_id}",
                "document_id": doc_id,
                "title": title,
                "source": source,
                "chunk_id": chunk.chunk_id,
                "type": "knowledge_base",
            })
        return records


class HybridRetriever:
    """Executes SQL Retriever and Hybrid Vector Retriever in parallel, prioritizing user PostgreSQL facts over RAG knowledge."""

    def __init__(
        self,
        db: Session,
        vector_store: RAGVectorStore | None = None,
    ) -> None:
        self.sql_retriever = SQLRetriever(db)
        self.vector_store = vector_store or get_vector_store()

    def retrieve(
        self,
        user: User,
        question: str,
        start: date | None = None,
        end: date | None = None,
        currency: str = "VND",
        top_k: int = 4,
        similarity_threshold: float = 0.15,
        history: list[Any] | None = None,
    ) -> HybridContext:
        # 1. Intent & plan resolution (incorporating conversation history for follow-ups)
        plan = IntentDetector.create_plan(question, today=start, history=history)
        intent = plan.intent


        # 2. Topic metadata filtering
        filters = None
        if intent == "saving_advice":
            filters = {"topic": "saving"}
        elif intent == "budget_review":
            filters = {"topic": "budgeting"}
        elif intent == "debt_advice":
            filters = {"topic": "debt"}
        elif intent == "app_faq":
            filters = {"topic": "faq"}

        # 3. SQL Retrieval (User real financial facts)
        sql_context = self.sql_retriever.retrieve_user_financial_facts(
            user=user, start=start, end=end, currency=currency, question=question
        )

        # 4. Hybrid Dense+Sparse Vector Retrieval
        vector_chunks = self.vector_store.search(
            query=question,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            filters=filters,
        )

        # Fallback if topic filter returned no results
        if not vector_chunks and filters:
            vector_chunks = self.vector_store.search(
                query=question,
                top_k=top_k,
                similarity_threshold=similarity_threshold,
                filters=None,
            )

        has_sql_data = sql_context.has_data
        has_rag_data = len(vector_chunks) > 0

        # Determine Context Status
        if not has_sql_data and not has_rag_data:
            status: ContextStatus = "INSUFFICIENT_DATA"
        elif intent in ("knowledge", "saving_advice", "debt_advice") and not has_rag_data:
            status = "NO_RELEVANT_CONTEXT"
        elif has_rag_data and any(c.score < similarity_threshold * 1.5 for c in vector_chunks):
            status = "WEAK_CONTEXT"
        else:
            status = "SUPPORTED"

        return HybridContext(
            intent=intent,
            sql_context=sql_context,
            vector_chunks=vector_chunks,
            has_sql_data=has_sql_data,
            has_rag_data=has_rag_data,
            status=status,
        )

