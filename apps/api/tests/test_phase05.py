from __future__ import annotations

import uuid

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.rate_limit import InMemoryAuthRateLimiter, get_auth_rate_limiter
from app.db.base import Base
from app.db.models import Category, CategoryType
from app.db.session import get_db
from app.main import app


@pytest.fixture
def client():
    engine = sa.create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
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
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_auth_rate_limiter, None)
    engine.dispose()


def register(client: TestClient, email: str | None = None) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email or f"phase05-{uuid.uuid4()}@example.com",
            "password": "correct horse battery staple",
            "display_name": "Phase Five",
        },
    )
    assert response.status_code == 201
    return response.json()


def auth_headers(auth: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth['access_token']}"}


def test_account_lifecycle_balance_cache_and_ownership(client):
    test_client, _ = client
    owner = register(test_client)
    other = register(test_client)
    created = test_client.post(
        "/api/v1/accounts",
        headers=auth_headers(owner),
        json={
            "name": "Main bank",
            "type": "BANK",
            "currency": "vnd",
            "opening_balance": 75000,
        },
    )
    assert created.status_code == 201
    account = created.json()
    assert account["currency"] == "VND"
    assert account["current_balance"] == 75000

    assert (
        test_client.get(
            f"/api/v1/accounts/{account['id']}", headers=auth_headers(other)
        ).status_code
        == 404
    )
    listed = test_client.get("/api/v1/accounts", headers=auth_headers(owner))
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    updated = test_client.patch(
        f"/api/v1/accounts/{account['id']}",
        headers=auth_headers(owner),
        json={"name": "Archived bank", "is_archived": True},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "ARCHIVED"
    assert test_client.get("/api/v1/accounts", headers=auth_headers(owner)).json()["total"] == 0
    assert (
        test_client.get(
            "/api/v1/accounts?include_archived=true", headers=auth_headers(owner)
        ).json()["total"]
        == 1
    )


def test_account_validation_and_archived_edit_rejection(client):
    test_client, _ = client
    auth = register(test_client)
    invalid = test_client.post(
        "/api/v1/accounts",
        headers=auth_headers(auth),
        json={"name": "Cash", "type": "NOT_REAL", "currency": "US", "opening_balance": -1},
    )
    assert invalid.status_code == 422
    created = test_client.post(
        "/api/v1/accounts",
        headers=auth_headers(auth),
        json={"name": "Cash", "type": "CASH", "currency": "VND"},
    ).json()
    test_client.patch(
        f"/api/v1/accounts/{created['id']}",
        headers=auth_headers(auth),
        json={"is_archived": True},
    )
    blocked = test_client.patch(
        f"/api/v1/accounts/{created['id']}",
        headers=auth_headers(auth),
        json={"name": "Changed"},
    )
    assert blocked.status_code == 409


def test_category_visibility_custom_hierarchy_and_parent_ownership(client):
    test_client, factory = client
    owner = register(test_client)
    other = register(test_client)
    with factory() as db:
        for name, category_type in (("System Food", CategoryType.EXPENSE.value),):
            db.add(
                Category(
                    name=name,
                    type=category_type,
                    is_system=True,
                    is_active=True,
                    sort_order=1,
                )
            )
        db.commit()
        system_id = db.query(Category).filter_by(name="System Food").one().id
    custom = test_client.post(
        "/api/v1/categories",
        headers=auth_headers(owner),
        json={"name": "Home Food", "type": "EXPENSE", "parent_id": system_id},
    )
    assert custom.status_code == 201
    visible = test_client.get("/api/v1/categories", headers=auth_headers(owner)).json()
    assert {item["name"] for item in visible["items"]} == {"System Food", "Home Food"}
    other_visible = test_client.get("/api/v1/categories", headers=auth_headers(other)).json()
    assert {item["name"] for item in other_visible["items"]} == {"System Food"}
    denied = test_client.post(
        "/api/v1/categories",
        headers=auth_headers(other),
        json={"name": "Invalid Child", "type": "EXPENSE", "parent_id": custom.json()["id"]},
    )
    assert denied.status_code == 400


def test_merchant_normalization_and_alias_lookup(client):
    test_client, _ = client
    auth = register(test_client)
    merchant = test_client.post(
        "/api/v1/merchants",
        headers=auth_headers(auth),
        json={"canonical_name": "Coffee House"},
    )
    assert merchant.status_code == 201
    alias = test_client.post(
        f"/api/v1/merchants/{merchant.json()['id']}/aliases",
        headers=auth_headers(auth),
        json={"alias": "  COFFEE   HOUSE   VN "},
    )
    assert alias.status_code == 200
    lookup = test_client.get(
        "/api/v1/merchants/lookup",
        headers=auth_headers(auth),
        params={"name": "coffee house vn"},
    )
    assert lookup.status_code == 200
    assert lookup.json()["merchant"]["canonical_name"] == "Coffee House"
