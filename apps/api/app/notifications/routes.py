from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser
from app.core.config import get_settings
from app.db.models import Notification
from app.db.session import get_db
from app.notifications.schemas import (
    NotificationEventCreate,
    NotificationListResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    NotificationResponse,
)
from app.notifications.service import _preference, evaluate_all_users, mark_read, record_event

router = APIRouter(prefix="/api/v1", tags=["notifications"])
DbSession = Annotated[Session, Depends(get_db)]


def _active_filter(now: datetime):
    return Notification.expires_at.is_(None) | (Notification.expires_at > now)


@router.get("/notifications", response_model=NotificationListResponse)
def list_notifications(
    current_user: CurrentUser,
    db: DbSession,
    unread_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> NotificationListResponse:
    now = datetime.now(timezone.utc)
    filters = [Notification.user_id == current_user.id, _active_filter(now)]
    if unread_only:
        filters.append(Notification.read_at.is_(None))
    items = db.scalars(
        select(Notification)
        .where(*filters)
        .order_by(Notification.priority.desc(), Notification.created_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    total = db.scalar(select(func.count(Notification.id)).where(*filters)) or 0
    unread = (
        db.scalar(
            select(func.count(Notification.id)).where(
                Notification.user_id == current_user.id,
                _active_filter(now),
                Notification.read_at.is_(None),
            )
        )
        or 0
    )
    return NotificationListResponse(items=items, total=total, unread=unread)


@router.post("/notifications/{notification_id}/read", response_model=NotificationResponse)
def read_notification(
    notification_id: str, current_user: CurrentUser, db: DbSession
) -> NotificationResponse:
    notification = mark_read(db, current_user, notification_id)
    if notification is None:
        raise HTTPException(status_code=404, detail={"code": "notification_not_found"})
    db.commit()
    db.refresh(notification)
    return notification


@router.post("/notifications/{notification_id}/events", status_code=status.HTTP_201_CREATED)
def notification_event(
    notification_id: str,
    payload: NotificationEventCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, str]:
    event = record_event(
        db,
        current_user,
        notification_id,
        payload.event_type,
        payload.result,
        payload.metadata,
    )
    if event is None:
        raise HTTPException(status_code=404, detail={"code": "notification_not_found"})
    db.commit()
    return {"id": event.id, "status": "recorded"}


@router.get("/preferences/notifications", response_model=NotificationPreferenceResponse)
def get_notification_preferences(
    current_user: CurrentUser, db: DbSession
) -> NotificationPreferenceResponse:
    return _preference(db, current_user)


@router.patch("/preferences/notifications", response_model=NotificationPreferenceResponse)
def update_notification_preferences(
    payload: NotificationPreferenceUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> NotificationPreferenceResponse:
    preference = _preference(db, current_user)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(preference, key, value)
    db.commit()
    db.refresh(preference)
    return preference


@router.post("/internal/notifications/evaluate", include_in_schema=False)
def evaluate_notification_cycle(
    db: DbSession, x_worker_token: str | None = Header(default=None)
) -> int:
    if x_worker_token != get_settings().notification_worker_token:
        raise HTTPException(status_code=401, detail={"code": "invalid_worker_token"})
    return evaluate_all_users(db)
