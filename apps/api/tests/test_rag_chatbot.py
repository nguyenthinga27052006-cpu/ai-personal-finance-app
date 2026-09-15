from __future__ import annotations

import pytest
from datetime import date
from uuid import uuid4

from app.ai.rag.knowledge_docs import KnowledgeDocument, SEED_KNOWLEDGE_DOCUMENTS
from app.ai.rag.vector_store import RAGVectorStore, recursive_chunk_text
from app.ai.rag.memory import RAGMemoryStore
from app.ai.retrievers.intent_detector import IntentDetector
from app.ai.retrievers.hybrid_retriever import HybridRetriever
from app.ai.rag.generator import FinancialRAGGenerator
from app.db.models import User, UserStatus


def test_recursive_chunk_text_params():
    text = (
        "Quy tắc 50/30/20 là phương pháp phân bổ thu nhập ròng hàng tháng thành 3 nhóm chính: "
        "50% Thu nhập dành cho Nhu cầu thiết yếu như tiền nhà, ăn uống cơ bản, điện nước. "
        "30% Thu nhập dành cho Mong muốn cá nhân như giải trí, ăn tiệm, du lịch. "
        "20% Thu nhập dành cho Mục tiêu tài chính và Tiết kiệm như quỹ khẩn cấp."
    )
    chunks = recursive_chunk_text(text, chunk_size=100, chunk_overlap=30)
    assert len(chunks) >= 1
    for c in chunks:
        assert len(c) <= 120  # allow slight margin for word boundaries


def test_vector_store_indexing_and_search():
    store = RAGVectorStore(collection_name="test_personal_finance")
    count = store.index_documents(SEED_KNOWLEDGE_DOCUMENTS, chunk_size=400, chunk_overlap=120)
    assert count >= len(SEED_KNOWLEDGE_DOCUMENTS)

    results = store.search("50/30/20", top_k=2)
    assert len(results) > 0
    assert any("50/30/20" in r.content for r in results)


def test_intent_detector():
    assert IntentDetector.detect("50/30/20 là gì?") == "knowledge"
    assert IntentDetector.detect("Tôi có đủ tiền mua laptop 15 triệu không?") == "affordability"
    assert IntentDetector.detect("Làm sao tiết kiệm chi phí ăn uống?") == "saving_advice"
    assert IntentDetector.detect("Tôi tiêu nhiều tiền nhất ở đâu tháng này?") == "spending_analysis"
    assert IntentDetector.detect("Tình hình ngân sách tháng này ra sao?") == "budget_review"


def test_rag_memory_store_bounded_turns():
    mem = RAGMemoryStore(max_turns=3)
    user_id = str(uuid4())

    for i in range(10):
        mem.add_message(user_id, f"Question {i}", role="user")
        mem.add_message(user_id, f"Answer {i}", role="assistant")

    history = mem.get_history(user_id)
    # max_turns=3 -> max 6 messages
    assert len(history) == 6
    assert history[0].content == "Question 7"
    assert history[-1].content == "Answer 9"


@pytest.mark.postgres
def test_financial_rag_generator_flow(db_session):
    # Setup test user
    user = User(
        id=str(uuid4()),
        email=f"rag_test_{uuid4()}@example.com",
        display_name="RAG Test User",
        password_hash="dummy_hash_for_test",
        status=UserStatus.ACTIVE.value,
        timezone="UTC",
    )
    db_session.add(user)
    db_session.commit()

    generator = FinancialRAGGenerator(db=db_session)
    response = generator.generate_response(
        user=user,
        question="50/30/20 là gì và làm sao áp dụng?",
        start=date(2026, 8, 1),
        end=date(2026, 8, 31),
    )

    assert response.status == "SUCCESS"
    assert response.intent == "knowledge"
    assert "Quy tắc" in response.answer_markdown or "50/30/20" in response.answer_markdown
    assert len(response.citations) > 0


def test_knowledge_document_metadata_and_hash():
    doc = KnowledgeDocument(
        doc_id="test_doc_01",
        title="Test Document Title",
        content="Test content body for hash verification",
        source="Test Source",
        topic="budgeting",
    )
    meta = doc.to_metadata()
    assert meta["document_id"] == "test_doc_01"
    assert meta["doc_id"] == "test_doc_01"
    assert meta["content_hash"] == doc.content_hash
    assert len(meta["content_hash"]) == 64  # SHA256 hex string length


def test_vector_store_upsert_and_delete():
    store = RAGVectorStore(collection_name="test_upsert_delete")
    doc = KnowledgeDocument(
        doc_id="upsert_doc",
        title="Upsert Test Title",
        content="Initial content for upsert testing",
        source="Upsert Source",
        topic="saving",
    )
    store.upsert_document(doc)
    assert "upsert_doc" in store.indexed_docs

    # Upsert with identical content_hash returns False (no-op)
    assert store.upsert_document(doc) is False

    # Delete document
    deleted = store.delete_document("upsert_doc")
    assert deleted is True
    assert "upsert_doc" not in store.indexed_docs


def test_metadata_filtering_and_threshold():
    store = RAGVectorStore(collection_name="test_filter_threshold")
    store.index_documents(SEED_KNOWLEDGE_DOCUMENTS)

    # Search with specific topic filter
    saving_results = store.search("tiết kiệm", filters={"topic": "saving"})
    assert all(r.metadata["topic"] == "saving" for r in saving_results)

    # High threshold filters out weak/irrelevant matches
    strict_results = store.search("hoàn toàn không liên quan xyz123", similarity_threshold=0.9)
    assert len(strict_results) == 0


def test_citation_validator_filters_fake_citations():
    from app.ai.rag.generator import CitationValidator
    from app.ai.retrievers.hybrid_retriever import HybridContext
    from app.ai.retrievers.sql_retriever import SQLUserDataContext
    from decimal import Decimal

    sql_ctx = SQLUserDataContext(
        user_id="user_123",
        period_start=date(2026, 8, 1),
        period_end=date(2026, 8, 31),
        currency="VND",
        total_income=Decimal("10000000"),
        total_expense=Decimal("5000000"),
        net_savings=Decimal("5000000"),
        accounts=[],
        total_balance=Decimal("5000000"),
        top_categories=[],
        recent_transactions=[],
        budgets=[],
        goals=[],
        notifications=[],
        transaction_count=10,
        has_data=True,
    )
    hybrid_context = HybridContext(
        intent="spending_analysis",
        sql_context=sql_ctx,
        vector_chunks=[],
        has_sql_data=True,
        has_rag_data=False,
    )

    fake_citations = ["PostgreSQL (Bịa đặt 9999999 VND)", "Nguồn Không Tồn Tại 123"]
    valid, detailed = CitationValidator.validate(fake_citations, hybrid_context)

    # Fake citations must be filtered out
    assert "Nguồn Không Tồn Tại 123" not in valid
    assert len(valid) > 0


def test_vietnamese_bm25_word_segmentation():
    from app.ai.rag.vector_store import VietnameseBM25Tokenizer

    tokens = VietnameseBM25Tokenizer.tokenize("Hướng dẫn xây dựng quỹ khẩn cấp và tích sản")
    assert "quỹ_khẩn_cấp" in tokens or ("quỹ" in tokens and "khẩn" in tokens and "cấp" in tokens)
    assert "tích_sản" in tokens or ("tích" in tokens and "sản" in tokens)


def test_semantic_synonym_retrieval():
    store = RAGVectorStore(collection_name="test_semantic_synonyms")
    store.index_documents(SEED_KNOWLEDGE_DOCUMENTS)

    # Financial slang 'tích sản' should retrieve investment/saving document
    results = store.search("tích sản", top_k=2)
    assert len(results) > 0
    assert any("investment" in r.metadata.get("topic", "") or "saving" in r.metadata.get("topic", "") or "tích" in r.content.lower() for r in results)


def test_multi_turn_anaphora_context_inheritance():
    """Test 1: Inherit category & intent for follow-up questions ('Thế còn tháng trước thì sao?')."""
    # Turn 1: Initial spending question
    q1 = "Tôi tiêu bao nhiêu tiền ăn uống tháng này?"
    plan1 = IntentDetector.create_plan(q1)
    assert plan1.intent == "spending_analysis"
    assert plan1.entities.category == "ăn uống"

    # Turn 2: Follow-up question referencing past timeframe
    q2 = "Thế còn tháng trước thì sao?"
    history = [
        {"role": "user", "content": q1},
        {"role": "assistant", "content": "Báo cáo chi tiêu ăn uống tháng này của bạn là 3,500,000 VND."},
    ]
    plan2 = IntentDetector.create_plan(q2, history=history)
    assert plan2.intent == "spending_analysis"
    assert plan2.entities.category == "ăn uống"
    assert plan2.time_range.start < plan1.time_range.start  # shifted to previous month


def test_multi_turn_abrupt_context_switching():
    """Test 2: Abrupt switching between SQL user data and Knowledge Base queries."""
    # Turn 1: SQL spending query
    q1 = "Tôi tiêu bao nhiêu tiền ăn uống tháng này?"
    plan1 = IntentDetector.create_plan(q1)
    assert plan1.requires_sql is True

    history = [
        {"role": "user", "content": q1},
        {"role": "assistant", "content": "Tổng chi tiêu ăn uống là 2,000,000 VND."},
    ]

    # Turn 2: Educational knowledge query -> must NOT be trapped in SQL spending context
    q2 = "Lãi suất kép là gì và tính như thế nào?"
    plan2 = IntentDetector.create_plan(q2, history=history)
    assert plan2.intent == "knowledge"
    assert plan2.requires_sql is False
    assert plan2.requires_knowledge is True
    assert plan2.entities.category is None  # no leftover SQL category

    history.extend([
        {"role": "user", "content": q2},
        {"role": "assistant", "content": "Lãi suất kép là việc lãi phát sinh được cộng dồn vào vốn gốc..."},
    ])

    # Turn 3: Switch back to spending query
    q3 = "Quay lại tiền ăn uống, quán nào đắt nhất?"
    plan3 = IntentDetector.create_plan(q3, history=history)
    assert plan3.requires_sql is True
    assert plan3.requires_knowledge is False
    assert plan3.entities.category == "ăn uống"


def test_rag_memory_store_truncation_and_system_prompt():
    """Test 3: Memory store safely truncates old turns while maintaining clean formatting."""
    mem = RAGMemoryStore(max_turns=3)
    user_id = str(uuid4())

    for i in range(8):
        mem.add_message(user_id, f"Câu hỏi {i} về tài chính", role="user")
        mem.add_message(user_id, f"Câu trả lời {i} từ hệ thống", role="assistant")

    history = mem.get_history(user_id)
    assert len(history) == 6  # 3 turns = 6 messages
    assert history[0].content == "Câu hỏi 5 về tài chính"
    assert history[-1].content == "Câu trả lời 7 từ hệ thống"

    formatted = mem.get_formatted_context(user_id)
    assert "Người dùng: Câu hỏi 5 về tài chính" in formatted
    assert "Trợ lý AI: Câu trả lời 7 từ hệ thống" in formatted



