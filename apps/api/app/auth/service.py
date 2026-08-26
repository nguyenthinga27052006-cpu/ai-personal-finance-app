from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.security import (
    as_utc,
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.core.config import get_settings
from app.db.models import DeviceSession, User, UserStatus


class AuthServiceError(Exception):
    pass


class InvalidCredentialsError(AuthServiceError):
    pass


class SessionInvalidError(AuthServiceError):
    pass


def create_session(
    db: Session,
    user: User,
    *,
    family_id: str | None = None,
    device_name: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> tuple[DeviceSession, str]:
    refresh_token = generate_refresh_token()
    settings = get_settings()
    session = DeviceSession(
        user_id=user.id,
        family_id=family_id or str(uuid.uuid4()),
        refresh_token_hash=hash_refresh_token(refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_session_ttl_days),
        device_name=device_name,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(session)
    db.flush()
    return session, refresh_token


def issue_auth_response(
    user: User, session: DeviceSession, refresh_token: str
) -> dict[str, object]:
    settings = get_settings()
    return {
        "access_token": create_access_token(user.id, session.id),
        "token_type": "bearer",
        "expires_in": settings.access_token_ttl_minutes * 60,
        "refresh_token": refresh_token,
        "user": user,
    }


def register_user(
    db: Session,
    email: str,
    password: str,
    display_name: str | None,
    **metadata: str | None,
) -> tuple[User, DeviceSession, str]:
    user = User(
        email=email,
        password_hash=hash_password(password),
        display_name=display_name,
        status=UserStatus.ACTIVE.value,
    )
    db.add(user)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise InvalidCredentialsError from exc
    session, refresh_token = create_session(db, user, **metadata)
    return user, session, refresh_token


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError
    if user.status != UserStatus.ACTIVE.value:
        raise InvalidCredentialsError
    return user


def rotate_session(
    db: Session,
    refresh_token: str,
    **metadata: str | None,
) -> tuple[User, DeviceSession, str]:
    token_hash = hash_refresh_token(refresh_token)
    session = db.scalar(select(DeviceSession).where(DeviceSession.refresh_token_hash == token_hash))
    now = datetime.now(timezone.utc)
    if session is None:
        raise SessionInvalidError
    if session.revoked_at is not None:
        db.execute(
            update(DeviceSession)
            .where(
                DeviceSession.family_id == session.family_id,
                DeviceSession.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        db.commit()
        raise SessionInvalidError
    if as_utc(session.expires_at) <= now:
        session.revoked_at = now
        raise SessionInvalidError

    user = db.get(User, session.user_id)
    if user is None or user.status != UserStatus.ACTIVE.value:
        session.revoked_at = now
        raise SessionInvalidError

    session.revoked_at = now
    session.last_used_at = now
    replacement, new_refresh_token = create_session(
        db,
        user,
        family_id=session.family_id,
        device_name=metadata.get("device_name") or session.device_name,
        ip_address=metadata.get("ip_address") or session.ip_address,
        user_agent=metadata.get("user_agent") or session.user_agent,
    )
    return user, replacement, new_refresh_token
