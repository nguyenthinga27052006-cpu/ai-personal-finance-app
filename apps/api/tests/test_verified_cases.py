import pytest
from datetime import date
from decimal import Decimal
from uuid import uuid4

from app.db.models import (
    User,
    UserStatus,
    Account,
    AccountType,
    Transaction,
    TransactionType,
    TransactionStatus,
    Category,
    CategoryType,
)
from app.ai.rag.generator import FinancialRAGGenerator
from app.ai.retrievers.intent_detector import IntentDetector

@pytest.mark.postgres
def test_all_11_verified_cases(db_session):
    today = date(2026, 9, 28)

    # Setup test user with accounts and transactions
    user = User(
        id=str(uuid4()),
        email=f"test_fix_{uuid4()}@example.com",
        display_name="Nguyen Van A",
        password_hash="dummy_hash",
        status=UserStatus.ACTIVE.value,
        timezone="Asia/Ho_Chi_Minh",
    )
    db_session.add(user)
    db_session.commit()

    # Add accounts
    acc = Account(
        id=str(uuid4()),
        user_id=user.id,
        name="VCB Digital",
        type=AccountType.BANK.value,
        opening_balance=117440000,
        current_balance=117440000,
        currency="VND",
    )
    db_session.add(acc)

    # Add transactions for this month (Sept 2026)
    cat = Category(id=str(uuid4()), user_id=user.id, name="Ăn uống", type=CategoryType.EXPENSE.value)
    db_session.add(cat)
    db_session.commit()

    tx1 = Transaction(
        id=str(uuid4()),
        user_id=user.id,
        account_id=acc.id,
        category_id=cat.id,
        amount=5000000,
        type=TransactionType.EXPENSE.value,
        status=TransactionStatus.POSTED.value,
        currency="VND",
        transaction_date=date(2026, 9, 15),
        description="Ăn uống tháng 9",
    )
    tx2 = Transaction(
        id=str(uuid4()),
        user_id=user.id,
        account_id=acc.id,
        category_id=cat.id,
        amount=20000000,
        type=TransactionType.INCOME.value,
        status=TransactionStatus.POSTED.value,
        currency="VND",
        transaction_date=date(2026, 9, 5),
        description="Lương tháng 9",
    )
    db_session.add_all([tx1, tx2])
    db_session.commit()

    generator = FinancialRAGGenerator(db=db_session)

    print("\n--- GROUP 1: TIME REFERENCE QUERIES ---")
    time_cases = [
        ("tháng trước tháng 9 là tháng mấy", "tháng 8"),
        ("trước tháng 8 ý", "tháng 7"),
        ("trước tháng 7 thì sao", "tháng 6"),
        ("tháng sau tháng 6 là tháng mấy", "tháng 7"),
        ("tháng trước là tháng mấy", "tháng 8"),
        ("trước tháng 1", "tháng 12"),
        ("sau tháng 12", "tháng 1"),
    ]

    for q, expected in time_cases:
        plan = IntentDetector.create_plan(q, today=today)
        resp = generator.generate_response(user=user, question=q)
        print(f"Question: '{q}'")
        print(f"  -> Intent: {resp.intent}")
        print(f"  -> Answer: {resp.answer_markdown}")
        print(f"  -> requires_sql: {plan.requires_sql}, has_sql_data: {resp.has_sql_data}")
        print(f"  -> requires_rag: {plan.requires_knowledge}, has_rag_data: {resp.has_rag_data}")
        print(f"  -> source: {resp.metadata.get('source')}, provider: {resp.metadata.get('provider')}, model: {resp.metadata.get('model')}")
        assert resp.intent == "time_reference_query", f"Expected time_reference_query, got {resp.intent}"
        assert expected in resp.answer_markdown.lower(), f"Expected '{expected}' in answer, got '{resp.answer_markdown}'"
        assert not resp.has_sql_data, "Expected has_sql_data == False"
        assert not resp.has_rag_data, "Expected has_rag_data == False"
        assert "117,440,000" not in resp.answer_markdown, "Financial balance leaked into time answer!"
        assert resp.metadata.get("source") == "deterministic_time_parser"
        assert resp.metadata.get("active_provider") == "deterministic"
        assert resp.metadata.get("active_model") is None

    print("\n--- GROUP 2: CONTEXT ISOLATION TESTS ---")
    # Test 7: Balance follow-up isolation
    conv_id_6 = f"conv_test_6_{uuid4()}"
    resp_6_1 = generator.generate_response(user=user, question="tháng này tôi còn bao nhiêu tiền?", conversation_id=conv_id_6)
    print(f"Turn 1: 'tháng này tôi còn bao nhiêu tiền?' -> Intent: {resp_6_1.intent}")
    
    resp_6_2 = generator.generate_response(user=user, question="trước tháng 7 là tháng nào?", conversation_id=conv_id_6)
    print(f"Turn 2: 'trước tháng 7 là tháng nào?'")
    print(f"  -> Intent: {resp_6_2.intent}")
    print(f"  -> Answer: {resp_6_2.answer_markdown}")
    print(f"  -> has_sql_data: {resp_6_2.has_sql_data}")
    assert resp_6_2.intent == "time_reference_query"
    assert "tháng 6" in resp_6_2.answer_markdown.lower()
    assert "117,440,000" not in resp_6_2.answer_markdown
    assert "số dư" not in resp_6_2.answer_markdown.lower()

    # Test 8: Expense follow-up isolation
    conv_id_7 = f"conv_test_7_{uuid4()}"
    resp_7_1 = generator.generate_response(user=user, question="tháng này tôi tiêu bao nhiêu?", conversation_id=conv_id_7)
    print(f"Turn 1: 'tháng này tôi tiêu bao nhiêu?' -> Intent: {resp_7_1.intent}")

    resp_7_2 = generator.generate_response(user=user, question="trước tháng 8 là tháng nào?", conversation_id=conv_id_7)
    print(f"Turn 2: 'trước tháng 8 là tháng nào?'")
    print(f"  -> Intent: {resp_7_2.intent}")
    print(f"  -> Answer: {resp_7_2.answer_markdown}")
    print(f"  -> has_sql_data: {resp_7_2.has_sql_data}")
    assert resp_7_2.intent == "time_reference_query"
    assert "tháng 7" in resp_7_2.answer_markdown.lower()
    assert "5,000,000" not in resp_7_2.answer_markdown
    assert "chi tiêu" not in resp_7_2.answer_markdown.lower()

    print("\n--- GROUP 3: KNOWLEDGE / RAG TESTS ---")
    # Test 9: Quy tắc 50/30/20 là gì? -> RAG/knowledge (0 SQL, 1 RAG)
    q9 = "quy tắc 50/30/20 là gì?"
    plan9 = IntentDetector.create_plan(q9, today=today)
    resp9 = generator.generate_response(user=user, question=q9)
    print(f"Test 9: '{q9}'")
    print(f"  -> Intent: {resp9.intent}, requires_sql: {plan9.requires_sql}, requires_knowledge: {plan9.requires_knowledge}")
    print(f"  -> has_sql_data: {resp9.has_sql_data}, has_rag_data: {resp9.has_rag_data}")
    print(f"  -> source: {resp9.metadata.get('source')}, active_provider: {resp9.metadata.get('active_provider')}")
    assert plan9.requires_sql is False
    assert plan9.requires_knowledge is True
    assert resp9.has_sql_data is False
    assert resp9.intent == "knowledge"
    assert resp9.metadata.get("source") == "hybrid_chroma_rag"
    assert "117,440,000" not in resp9.answer_markdown, "Financial balance leaked into knowledge query!"

    print("\n--- GROUP 4: FINANCIAL GROUND TRUTH & ANALYTICS ---")
    # Test 10: Expense query -> PostgreSQL
    q10 = "Tháng này tôi đã chi bao nhiêu?"
    plan10 = IntentDetector.create_plan(q10, today=today)
    resp10 = generator.generate_response(user=user, question=q10)
    print(f"Test 10: '{q10}'")
    print(f"  -> Intent: {resp10.intent}, requires_sql: {plan10.requires_sql}, has_sql_data: {resp10.has_sql_data}")
    assert plan10.requires_sql is True
    assert resp10.has_sql_data is True
    assert resp10.intent == "expense_query"
    assert resp10.metadata.get("source") == "hybrid_postgresql"

    # Test 11: Khoản nào tôi chi nhiều nhất tháng này? -> PostgreSQL + analytics
    q11 = "Khoản nào tôi chi nhiều nhất tháng này?"
    plan11 = IntentDetector.create_plan(q11, today=today)
    resp11 = generator.generate_response(user=user, question=q11)
    print(f"Test 11: '{q11}'")
    print(f"  -> Intent: {resp11.intent}, requires_sql: {plan11.requires_sql}, has_sql_data: {resp11.has_sql_data}")
    assert plan11.requires_sql is True
    assert resp11.has_sql_data is True
    assert resp11.intent == "spending_analysis"
    assert resp11.metadata.get("source") == "hybrid_postgresql"

    # Test 12: Tháng này tôi còn bao nhiêu tiền? -> balance_query
    q12 = "Tháng này tôi còn bao nhiêu tiền?"
    plan12 = IntentDetector.create_plan(q12, today=today)
    resp12 = generator.generate_response(user=user, question=q12)
    print(f"Test 12: '{q12}'")
    print(f"  -> Intent: {resp12.intent}, requires_sql: {plan12.requires_sql}, has_sql_data: {resp12.has_sql_data}")
    assert plan12.requires_sql is True
    assert resp12.has_sql_data is True
    assert resp12.intent == "balance_query"
    assert "117,440,000" in resp12.answer_markdown
    assert resp12.metadata.get("source") == "hybrid_postgresql"

    # Test 13: Phân tích chi tiêu 6 tháng qua của tôi. -> PostgreSQL + monthly analytics
    # First, insert transactions for 2 distinct months to test consistency
    tx_prev = Transaction(
        id=str(uuid4()),
        user_id=user.id,
        account_id=acc.id,
        category_id=cat.id,
        amount=5000000,
        type=TransactionType.EXPENSE.value,
        status=TransactionStatus.POSTED.value,
        currency="VND",
        transaction_date=date(2026, 8, 15),
        description="Ăn uống tháng 8 (bằng tháng 9 để test 'không đổi')",
    )
    db_session.add(tx_prev)
    db_session.commit()

    q13 = "Phân tích chi tiêu 6 tháng qua của tôi."
    plan13 = IntentDetector.create_plan(q13, today=today)
    resp13 = generator.generate_response(user=user, question=q13)
    print(f"Test 13: '{q13}'")
    print(f"  -> Intent: {resp13.intent}, is_multi_month: {plan13.time_range.is_multi_month}")
    print(f"  -> Answer:\n{resp13.answer_markdown}")
    assert plan13.requires_sql is True
    assert plan13.time_range.is_multi_month is True
    assert resp13.has_sql_data is True
    # Test Section XVI: When month 8 = 5M and month 9 = 5M, wording MUST express unchanged expense, NOT increased expense
    has_unchanged = any(
        kw in resp13.answer_markdown.lower()
        for kw in [
            "không đổi",
            "không thay đổi",
            "không có sự thay đổi",
            "không có tháng nào có biến động",
            "không có sự biến động",
            "không có biến động",
            "không biến động",
            "tương tự",
            "đều là",
            "bằng nhau",
            "như trước",
        ]
    )
    assert has_unchanged, f"Expected unchanged wording in answer, got: {resp13.answer_markdown}"
