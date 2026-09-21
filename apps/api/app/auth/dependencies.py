from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.security import as_utc, decode_access_token
from app.db.models import DeviceSession, User, UserStatus
from app.db.session import get_db

bearer_scheme = HTTPBearer(auto_error=False)


def auth_error(code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": code, "message": message},
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise auth_error("unauthorized", "Authentication required")
    try:
        claims = decode_access_token(credentials.credentials)
    except jwt.ExpiredSignatureError as exc:
        raise auth_error("token_expired", "Access token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise auth_error("invalid_token", "Invalid access token") from exc

    user_id = claims.get("sub")
    session_id = claims.get("sid")
    user = db.get(User, user_id) if isinstance(user_id, str) else None
    session = db.get(DeviceSession, session_id) if isinstance(session_id, str) else None
    now = datetime.now(timezone.utc)
    if user is None or session is None or session.user_id != user.id:
        raise auth_error("unauthorized", "Authentication required")
    if user.status != UserStatus.ACTIVE.value:
        raise auth_error("user_inactive", "User is not active")
    if session.revoked_at is not None:
        raise auth_error("session_revoked", "Session has been revoked")
    if as_utc(session.expires_at) <= now:
        raise auth_error("session_expired", "Session has expired")
    return user


def get_current_admin_user(current_user: CurrentUser) -> User:
    from app.db.models import UserRole

    if getattr(current_user, "role", None) != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "admin_required", "message": "Admin privileges required"},
        )
    return current_user


CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentAdminUser = Annotated[User, Depends(get_current_admin_user)]
