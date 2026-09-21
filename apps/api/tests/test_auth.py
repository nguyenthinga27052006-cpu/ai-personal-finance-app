from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.rate_limit import InMemoryAuthRateLimiter
from app.auth.security import ALGORITHM, hash_password
from app.core.config import get_settings
from app.db.base import Base
from app.db.models import DeviceSession, User, UserStatus
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

    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client, factory
    app.dependency_overrides.clear()
    engine.dispose()


def register(client: TestClient, email: str = "person@example.com") -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "correct horse battery staple", "display_name": "Person"},
    )
    assert response.status_code == 201
    return response.json()


def test_register_login_and_me_do_not_expose_hash(client):
    test_client, _ = client
    auth = register(test_client)
    assert "password_hash" not in auth["user"]
    assert auth["refresh_token"]

    me = test_client.get("/api/v1/me", headers={"Authorization": f"Bearer {auth['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == "person@example.com"

    login = test_client.post(
        "/api/v1/auth/login",
        json={"email": "PERSON@example.com", "password": "correct horse battery staple"},
    )
    assert login.status_code == 200
    assert login.json()["user"]["email"] == "person@example.com"


def test_duplicate_email_and_invalid_password(client):
    test_client, _ = client
    register(test_client)
    duplicate = test_client.post(
        "/api/v1/auth/register",
        json={"email": "person@example.com", "password": "correct horse battery staple"},
    )
    assert duplicate.status_code == 409
    invalid = test_client.post(
        "/api/v1/auth/register",
        json={"email": "new@example.com", "password": "short"},
    )
    assert invalid.status_code == 422


def test_wrong_and_nonexistent_login_have_same_error(client):
    test_client, _ = client
    register(test_client)
    wrong = test_client.post(
        "/api/v1/auth/login", json={"email": "person@example.com", "password": "wrong password"}
    )
    missing = test_client.post(
        "/api/v1/auth/login", json={"email": "missing@example.com", "password": "wrong password"}
    )
    assert wrong.status_code == missing.status_code == 401
    assert (
        wrong.json()
        == missing.json()
        == {"detail": {"code": "invalid_credentials", "message": "Invalid credentials"}}
    )


def test_refresh_rotates_and_old_token_is_rejected(client):
    test_client, factory = client
    auth = register(test_client)
    rotated = test_client.post(
        "/api/v1/auth/refresh", json={"refresh_token": auth["refresh_token"]}
    )
    assert rotated.status_code == 200
    assert rotated.json()["refresh_token"] != auth["refresh_token"]

    old = test_client.post("/api/v1/auth/refresh", json={"refresh_token": auth["refresh_token"]})
    assert old.status_code == 401
    assert old.json()["detail"]["code"] == "invalid_refresh_session"
    with factory() as db:
        assert db.query(DeviceSession).filter(DeviceSession.revoked_at.is_(None)).count() == 0


def test_logout_revokes_current_session_and_protected_access(client):
    test_client, _ = client
    auth = register(test_client)
    headers = {"Authorization": f"Bearer {auth['access_token']}"}
    logout = test_client.post("/api/v1/auth/logout", headers=headers)
    assert logout.status_code == 200
    assert test_client.get("/api/v1/me", headers=headers).status_code == 401
    refresh = test_client.post(
        "/api/v1/auth/refresh", json={"refresh_token": auth["refresh_token"]}
    )
    assert refresh.status_code == 401


def test_malformed_expired_and_invalid_tokens_are_denied(client):
    test_client, _ = client
    assert test_client.get("/api/v1/me").status_code == 401
    assert (
        test_client.get("/api/v1/me", headers={"Authorization": "Bearer not-a-token"}).json()[
            "detail"
        ]["code"]
        == "invalid_token"
    )
    settings = get_settings()
    expired = jwt.encode(
        {
            "sub": "missing",
            "sid": "missing",
            "type": "access",
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
            "iat": datetime.now(timezone.utc) - timedelta(minutes=2),
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        settings.jwt_secret,
        algorithm=ALGORITHM,
    )
    response = test_client.get("/api/v1/me", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "token_expired"


def test_disabled_user_cannot_login_or_use_token(client):
    test_client, factory = client
    auth = register(test_client)
    with factory() as db:
        user = db.query(User).filter_by(email="person@example.com").one()
        user.status = UserStatus.INACTIVE.value
        db.commit()
    login = test_client.post(
        "/api/v1/auth/login",
        json={"email": "person@example.com", "password": "correct horse battery staple"},
    )
    assert login.status_code == 401
    assert (
        test_client.get(
            "/api/v1/me", headers={"Authorization": f"Bearer {auth['access_token']}"}
        ).status_code
        == 401
    )


def test_password_hash_and_rate_limiter():
    password_hash = hash_password("correct horse battery staple")
    assert password_hash != "correct horse battery staple"
    assert password_hash.startswith("$argon2")
    limiter = InMemoryAuthRateLimiter(max_attempts=2, window_seconds=60)
    assert limiter.allow("ip")
    assert limiter.allow("ip")
    assert not limiter.allow("ip")
