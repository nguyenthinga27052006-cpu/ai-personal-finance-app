from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.auth.security import create_access_token
from app.db.models import DeviceSession, User
from app.db.session import get_db
from app.main import app

pytestmark = pytest.mark.postgres


@pytest.fixture(scope="module")
def postgres_engine():
    database_url = os.getenv("POSTGRES_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("POSTGRES_TEST_DATABASE_URL is not configured")
    engine = create_engine(database_url)
    with engine.connect() as connection:
        tables = connection.exec_driver_sql(
            "SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public'"
        ).scalars().all()
    if not {"users", "device_sessions"}.issubset(tables):
        pytest.skip("PostgreSQL schema is not migrated; run alembic upgrade head first")
    return engine


@pytest.fixture
def client(postgres_engine):
    def override_get_db():
        with Session(postgres_engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)


def test_auth_lifecycle_persists_and_revokes_postgresql_session(client, postgres_engine):
    email = f"postgres-auth-{uuid.uuid4()}@example.com"
    password = "correct horse battery staple"
    registered = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": "Postgres Auth"},
    )
    assert registered.status_code == 201
    first = registered.json()

    with Session(postgres_engine) as db:
        user = db.scalar(select(User).where(User.email == email))
        assert user is not None
        first_session = db.scalar(
            select(DeviceSession).where(DeviceSession.user_id == user.id)
        )
        assert first_session is not None
        assert first_session.refresh_token_hash not in first["refresh_token"]

    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    second = login.json()
    assert client.get(
        "/api/v1/me", headers={"Authorization": f"Bearer {second['access_token']}"}
    ).json()["email"] == email

    rotated = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": second["refresh_token"]}
    )
    assert rotated.status_code == 200
    assert rotated.json()["refresh_token"] != second["refresh_token"]
    old_refresh = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": second["refresh_token"]}
    )
    assert old_refresh.status_code == 401
    assert old_refresh.json()["detail"]["code"] == "invalid_refresh_session"

    active = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    ).json()
    logout = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {active['access_token']}"},
    )
    assert logout.status_code == 200
    assert client.get(
        "/api/v1/auth/session",
        headers={"Authorization": f"Bearer {active['access_token']}"},
    ).status_code == 401

    with Session(postgres_engine) as db:
        user = db.scalar(select(User).where(User.email == email))
        assert user is not None
        session = db.scalar(
            select(DeviceSession)
            .where(DeviceSession.user_id == user.id)
            .order_by(DeviceSession.created_at.desc())
        )
        assert session is not None
        session.revoked_at = None
        session.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.commit()
        expired_access = create_access_token(user.id, session.id)

    assert client.post(
        "/api/v1/auth/refresh", json={"refresh_token": active["refresh_token"]}
    ).status_code == 401
    assert client.get(
        "/api/v1/me", headers={"Authorization": f"Bearer {expired_access}"}
    ).json()["detail"]["code"] == "session_expired"
