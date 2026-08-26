from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, auth_error
from app.auth.rate_limit import AuthRateLimiter, get_auth_rate_limiter
from app.auth.schemas import (
    AuthResponse,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    UserResponse,
)
from app.auth.security import decode_access_token
from app.auth.service import (
    InvalidCredentialsError,
    SessionInvalidError,
    authenticate_user,
    create_session,
    issue_auth_response,
    register_user,
    rotate_session,
)
from app.db.models import DeviceSession
from app.db.session import get_db

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
me_router = APIRouter(prefix="/api/v1", tags=["authentication"])
DbSession = Annotated[Session, Depends(get_db)]
Limiter = Annotated[AuthRateLimiter, Depends(get_auth_rate_limiter)]
BearerCredentials = Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer())]


def request_metadata(request: Request) -> dict[str, str | None]:
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "device_name": request.headers.get("x-device-name"),
    }


def rate_limit_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={"code": "rate_limited", "message": "Too many authentication attempts"},
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    request: Request,
    db: DbSession,
    limiter: Limiter,
) -> dict[str, object]:
    key = f"register:{request.client.host if request.client else 'unknown'}"
    if not limiter.allow(key):
        raise rate_limit_error()
    try:
        user, session, refresh_token = register_user(
            db, payload.email, payload.password, payload.display_name, **request_metadata(request)
        )
        db.commit()
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "email_already_registered", "message": "Email is already registered"},
        ) from exc
    return issue_auth_response(user, session, refresh_token)


@router.post("/login", response_model=AuthResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db: DbSession,
    limiter: Limiter,
) -> dict[str, object]:
    key = f"login:{request.client.host if request.client else 'unknown'}"
    if not limiter.allow(key):
        raise rate_limit_error()
    try:
        user = authenticate_user(db, payload.email, payload.password)
    except InvalidCredentialsError as exc:
        raise auth_error("invalid_credentials", "Invalid credentials") from exc
    session, refresh_token = create_session(db, user, **request_metadata(request))
    db.commit()
    return issue_auth_response(user, session, refresh_token)


@router.post("/refresh", response_model=AuthResponse)
def refresh(
    payload: RefreshRequest,
    request: Request,
    db: DbSession,
    limiter: Limiter,
) -> dict[str, object]:
    key = f"refresh:{request.client.host if request.client else 'unknown'}"
    if not limiter.allow(key):
        raise rate_limit_error()
    try:
        user, session, refresh_token = rotate_session(
            db, payload.refresh_token, **request_metadata(request)
        )
        db.commit()
    except SessionInvalidError as exc:
        db.rollback()
        raise auth_error("invalid_refresh_session", "Invalid refresh session") from exc
    return issue_auth_response(user, session, refresh_token)


@router.post("/logout", response_model=MessageResponse)
def logout(
    current_user: CurrentUser,
    credentials: BearerCredentials,
    db: DbSession,
) -> MessageResponse:
    del current_user
    session_id = decode_access_token(credentials.credentials)["sid"]
    session = db.get(DeviceSession, session_id)
    if session is not None:
        from datetime import datetime, timezone

        session.revoked_at = datetime.now(timezone.utc)
        db.commit()
    return MessageResponse(message="Logged out")


@router.get("/me", response_model=UserResponse)
@me_router.get("/me", response_model=UserResponse)
def me(current_user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.get("/session", response_model=UserResponse)
def protected_session(current_user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(current_user)
