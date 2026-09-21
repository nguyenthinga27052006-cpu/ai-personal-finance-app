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
    hash_pin,
    hash_refresh_token,
    verify_password,
    verify_pin,
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
        device_name=device_name[:120] if device_name else None,
        ip_address=ip_address[:45] if ip_address else None,
        user_agent=user_agent[:512] if user_agent else None,
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
    security_pin: str | None = None,
    **metadata: str | None,
) -> tuple[User, DeviceSession, str]:
    user = User(
        email=email,
        password_hash=hash_password(password),
        security_pin_hash=hash_pin(security_pin) if security_pin else None,
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


def reset_password_with_pin(
    db: Session, email: str, pin: str, new_password: str
) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not user.security_pin_hash:
        raise InvalidCredentialsError("Thông tin xác thực không hợp lệ hoặc tài khoản chưa đặt mã PIN")
    if not verify_pin(pin, user.security_pin_hash):
        raise InvalidCredentialsError("Mã PIN bảo mật không chính xác")
    if user.status != UserStatus.ACTIVE.value:
        raise InvalidCredentialsError("Tài khoản đang bị khóa hoặc không hoạt động")
    user.password_hash = hash_password(new_password)
    db.add(user)
    db.flush()
    return user


def update_user_security_pin(
    db: Session, user: User, current_password: str, new_pin: str
) -> None:
    if not verify_password(current_password, user.password_hash):
        raise InvalidCredentialsError("Mật khẩu hiện tại không chính xác")
    user.security_pin_hash = hash_pin(new_pin)
    db.add(user)
    db.flush()


def change_password_user(db: Session, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.password_hash):
        raise InvalidCredentialsError("Mật khẩu hiện tại không chính xác")
    user.password_hash = hash_password(new_password)
    db.add(user)


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


def delete_user_and_purge_all_data(db: Session, target_user: User) -> None:
    from app.db.models import (
        Account,
        AIChatMessage,
        AIFeedback,
        Budget,
        BudgetCategory,
        DeviceSession,
        FinancialGoal,
        GoalContribution,
        Notification,
        Recommendation,
        Transaction,
        TransactionEntry,
        TransactionItem,
        UserPreference,
        UserSetting,
    )

    user_id = target_user.id

    db.query(DeviceSession).filter(DeviceSession.user_id == user_id).delete(
        synchronize_session=False
    )
    db.query(AIChatMessage).filter(AIChatMessage.user_id == user_id).delete(
        synchronize_session=False
    )
    db.query(AIFeedback).filter(AIFeedback.user_id == user_id).delete(synchronize_session=False)
    db.query(Notification).filter(Notification.user_id == user_id).delete(synchronize_session=False)
    db.query(Recommendation).filter(Recommendation.user_id == user_id).delete(
        synchronize_session=False
    )
    db.query(UserPreference).filter(UserPreference.user_id == user_id).delete(
        synchronize_session=False
    )
    db.query(UserSetting).filter(UserSetting.user_id == user_id).delete(synchronize_session=False)

    goals = db.query(FinancialGoal).filter(FinancialGoal.user_id == user_id).all()
    for g in goals:
        db.query(GoalContribution).filter(GoalContribution.goal_id == g.id).delete(
            synchronize_session=False
        )
    db.query(FinancialGoal).filter(FinancialGoal.user_id == user_id).delete(
        synchronize_session=False
    )

    budgets = db.query(Budget).filter(Budget.user_id == user_id).all()
    for b in budgets:
        db.query(BudgetCategory).filter(BudgetCategory.budget_id == b.id).delete(
            synchronize_session=False
        )
    db.query(Budget).filter(Budget.user_id == user_id).delete(synchronize_session=False)

    transactions = db.query(Transaction).filter(Transaction.user_id == user_id).all()
    for t in transactions:
        db.query(TransactionEntry).filter(TransactionEntry.transaction_id == t.id).delete(
            synchronize_session=False
        )
        db.query(TransactionItem).filter(TransactionItem.transaction_id == t.id).delete(
            synchronize_session=False
        )
    db.query(Transaction).filter(Transaction.user_id == user_id).delete(synchronize_session=False)

    db.query(Account).filter(Account.user_id == user_id).delete(synchronize_session=False)

    db.delete(target_user)
    db.commit()
