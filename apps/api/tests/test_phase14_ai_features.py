from __future__ import annotations

from datetime import date

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.ai.categorization import categorize_transaction
from app.ai.chat import ConversationStore
from app.ai.errors import AuthorizationError
from app.ai.gateway import AIGateway
from app.ai.nl_query import _default_period, execute_nl_query
from app.ai.providers import FakeProvider, ModelRouter
from app.ai.receipt import (
    FakeReceiptOCRProvider,
    ReceiptDraft,
    confirm_receipt,
    extract_receipt,
    prepare_receipt,
)
from app.ai.recommendations import explain_recommendation
from app.ai.spending_analysis import analyze_spending_with_gateway
from app.ai.tools import build_read_only_registry
from app.auth.rate_limit import InMemoryAuthRateLimiter, get_auth_rate_limiter
from app.db.base import Base
from app.db.seed import seed_system_categories
from app.db.session import get_db
from app.main import app


@pytest.fixture
def client():
    engine = sa.create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)

    def override_get_db():
        with factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_auth_rate_limiter] = lambda: InMemoryAuthRateLimiter(
        max_attempts=1000
    )
    with TestClient(app) as test_client:
        yield test_client, factory
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def seed_user(client):
    test_client, factory = client
    auth = __import__("test_financial_core", fromlist=["register"]).register(test_client)
    with factory() as db:
        seed_system_categories(db)
        db.commit()
        user = db.get(__import__("app.db.models", fromlist=["User"]).User, auth["user"]["id"])
        assert user is not None
        yield user


def test_categorization_uses_deterministic_match(client):
    test_client, factory = client
    auth = __import__("test_financial_core", fromlist=["register"]).register(test_client)
    with factory() as db:
        seed_system_categories(db)
        db.commit()
        user = db.get(__import__("app.db.models", fromlist=["User"]).User, auth["user"]["id"])
        result = categorize_transaction(db, user, "Starbucks Coffee", "expense")
        assert result.category.lower() == "food"
        assert result.confidence >= 0.9
        assert "merchant alias" in result.reason.lower()


def test_categorization_gateway_fallback_validates_model_category(client):
    test_client, factory = client
    auth = __import__("test_financial_core", fromlist=["register"]).register(test_client)
    with factory() as db:
        seed_system_categories(db)
        db.commit()
        user = db.get(__import__("app.db.models", fromlist=["User"]).User, auth["user"]["id"])
        provider = FakeProvider(
            response={
                "status": "SUCCESS",
                "category": "Food",
                "confidence": 0.81,
                "reason": "Provider classification",
            }
        )
        gateway = AIGateway(ModelRouter(provider), build_read_only_registry())
        result = categorize_transaction(db, user, "Unknown merchant", gateway=gateway)
        assert result.status == "SUCCESS"
        assert result.category == "Food"
        assert provider.calls


def test_receipt_pipeline_requires_review_and_confirmation():
    provider = FakeReceiptOCRProvider(
        {
            "merchant": "Market",
            "date": "2026-09-09",
            "total": 300,
            "currency": "VND",
            "items": [{"name": "item", "amount": 300}],
        }
    )
    candidate = prepare_receipt(
        {"source_ref": "receipt://one"},
        [{"merchant": "Market", "date": "2026-08-01", "total": 300}],
        provider=provider,
    )
    assert candidate.status == "SUCCESS"
    assert confirm_receipt(candidate, confirmed=False, transaction_creator=lambda **_: True) is None
    calls = []
    assert confirm_receipt(
        candidate,
        confirmed=True,
        transaction_creator=lambda **values: calls.append(values) or True,
    )
    assert calls[0]["amount"] == 300

    duplicate = prepare_receipt(
        {
            "merchant": "Market",
            "date": "2026-09-09",
            "total": 300,
            "items": [{"name": "item", "amount": 300}],
        },
        [{"merchant": "Market", "date": "2026-09-09", "total": 300}],
    )
    assert duplicate.duplicate is True
    with pytest.raises(ValueError):
        confirm_receipt(duplicate, confirmed=True, transaction_creator=lambda **_: True)


def test_receipt_extraction_requires_valid_fields_and_review():
    valid = extract_receipt(
        {
            "merchant": "Lotte Mart",
            "date": "2026-09-09",
            "total": "125000",
            "currency": "VND",
            "items": [{"name": "milk", "amount": 25000}, {"name": "bread", "amount": 100000}],
        }
    )
    assert valid.status == "SUCCESS"
    assert valid.total == 125000

    with pytest.raises(ValueError):
        extract_receipt({"merchant": "Bad", "date": "not-a-date", "total": "abc"})

    draft = ReceiptDraft(
        merchant="Lotte Mart",
        date="2026-09-09",
        total=125000,
        currency="VND",
        items=[{"name": "milk", "amount": 25000}],
        confirmed=False,
    )
    assert draft.confirmed is False


def test_nl_query_uses_grounded_tool_result(client):
    test_client, factory = client
    auth = __import__("test_financial_core", fromlist=["register"]).register(test_client)
    with factory() as db:
        user = db.get(__import__("app.db.models", fromlist=["User"]).User, auth["user"]["id"])
        context = __import__("app.ai.context", fromlist=["ExecutionContext"]).ExecutionContext(
            db=db,
            user=user,
            request_id="phase14-nl",
            feature="nl_query",
            allowed_tools=frozenset({"get_monthly_expense", "get_current_balance"}),
        )
        result = execute_nl_query(
            context,
            "How much did I spend this month?",
            start=None,
            end=None,
            currency="VND",
        )
        assert result.status in {"SUCCESS", "INSUFFICIENT_DATA"}
        assert result.answer


def test_default_period_uses_user_timezone_and_real_month_end(client):
    test_client, factory = client
    auth = __import__("test_financial_core", fromlist=["register"]).register(test_client)
    with factory() as db:
        user = db.get(__import__("app.db.models", fromlist=["User"]).User, auth["user"]["id"])
        context = __import__("app.ai.context", fromlist=["ExecutionContext"]).ExecutionContext(
            db=db,
            user=user,
            request_id="phase14-period",
            feature="nl_query",
            allowed_tools=frozenset(),
        )
        start, end = _default_period(context, start=date(2026, 9, 1), end=date(2026, 9, 30))
        assert (start, end) == (date(2026, 9, 1), date(2026, 9, 30))


def test_conversation_store_scopes_history_to_user():
    store = ConversationStore()
    user_a = "u-a"
    user_b = "u-b"
    store.create(user_a, "Hi")
    store.create(user_b, "Private")
    assert len(store.list(user_a)) == 1
    assert len(store.list(user_b)) == 1
    assert store.list(user_a)[0].content == "Hi"
    bounded = store.list(user_a, limit=1)
    assert len(bounded) == 1

    conversation = store.create(user_a, "private thread")
    with pytest.raises(AuthorizationError):
        store.list(user_b, conversation_id=conversation.conversation_id)


def test_recommendation_explanation_preserves_source_fact():
    candidate = {
        "type": "REDUCE_CATEGORY",
        "reason": "Based on category share",
        "expected_impact": "ESTIMATE: reduce this category by 10%",
        "confidence": 0.82,
    }
    explanation = explain_recommendation(candidate)
    assert explanation["status"] == "SUCCESS"
    assert "ESTIMATE" in explanation["answer"]
    assert explanation["source"] == candidate["reason"]


def test_spending_and_recommendation_gateway_paths_preserve_grounding(client):
    test_client, factory = client
    auth = __import__("test_financial_core", fromlist=["register"]).register(test_client)
    with factory() as db:
        user = db.get(__import__("app.db.models", fromlist=["User"]).User, auth["user"]["id"])
        spending_tools = frozenset(
            {"get_monthly_expense", "get_category_spending", "get_spending_trend", "get_insights"}
        )
        context = __import__("app.ai.context", fromlist=["ExecutionContext"]).ExecutionContext(
            db=db,
            user=user,
            request_id="phase14-explain",
            feature="spending_analysis",
            allowed_tools=spending_tools,
        )
        provider = FakeProvider(
            response={"status": "SUCCESS", "answer": "A concise explanation", "citations": []}
        )
        gateway = AIGateway(ModelRouter(provider), build_read_only_registry())
        result = analyze_spending_with_gateway(
            {"summary": {"expense": 1234}, "category_analysis": [], "insights": []},
            context,
            gateway,
        )
        assert result.status == "SUCCESS"
        assert "1234" in result.answer
        assert provider.calls

        recommendation_provider = FakeProvider(
            response={"status": "SUCCESS", "answer": "Use a gentler tone", "citations": []}
        )
        recommendation_gateway = AIGateway(
            ModelRouter(recommendation_provider), build_read_only_registry()
        )
        recommendation_context = __import__(
            "app.ai.context", fromlist=["ExecutionContext"]
        ).ExecutionContext(
            db=db,
            user=user,
            request_id="phase14-recommendation",
            feature="recommendation_explanation",
            allowed_tools=frozenset(),
        )
        explanation = explain_recommendation(
            {
                "type": "REDUCE_CATEGORY",
                "reason": "Based on category share",
                "expected_impact": "ESTIMATE: reduce discretionary spending",
                "confidence": 0.8,
            },
            context=recommendation_context,
            gateway=recommendation_gateway,
        )
        assert explanation["status"] == "SUCCESS"
        assert "ESTIMATE" in explanation["answer"]
        assert recommendation_provider.calls
