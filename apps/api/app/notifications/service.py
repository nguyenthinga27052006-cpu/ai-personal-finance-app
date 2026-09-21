from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.budget_goals.service import budget_calculation, list_budgets
from app.db.models import Notification, NotificationEvent, User, UserPreference
from app.insights.service import active_insights

THRESHOLDS = (
    ("budget_80", Decimal("0.80")),
    ("budget_90", Decimal("0.90")),
    ("budget_100", Decimal("1.00")),
)
SOURCE = "phase11.deterministic_notification_engine"


def _local_now(user: User, now: datetime | None = None) -> datetime:
    current = now or datetime.now(timezone.utc)
    return current.astimezone(ZoneInfo(user.timezone))


def _preference(db: Session, user: User) -> UserPreference:
    preference = db.scalar(select(UserPreference).where(UserPreference.user_id == user.id))
    if preference is None:
        preference = UserPreference(user_id=user.id)
        db.add(preference)
        db.flush()
    return preference


def _in_quiet_hours(user: User, preference: UserPreference, now: datetime) -> bool:
    start, end = preference.quiet_hours_start, preference.quiet_hours_end
    if not start or not end:
        return False
    current = now.hour * 60 + now.minute
    start_minutes = int(start[:2]) * 60 + int(start[3:])
    end_minutes = int(end[:2]) * 60 + int(end[3:])
    if start_minutes == end_minutes:
        return True
    if start_minutes < end_minutes:
        return start_minutes <= current < end_minutes
    return current >= start_minutes or current < end_minutes


def _dedupe_key(
    user_id: str, rule_id: str, subject_id: str | None, period: str, suffix: str = ""
) -> str:
    raw = "|".join((user_id, rule_id, subject_id or "", period, str(suffix)))
    return hashlib.sha256(raw.encode()).hexdigest()[:48]


def _period(now: datetime) -> tuple[date, date]:
    start = now.date().replace(day=1)
    if start.month == 12:
        next_month = date(start.year + 1, 1, 1)
    else:
        next_month = date(start.year, start.month + 1, 1)
    return start, next_month.fromordinal(next_month.toordinal() - 1)


def _candidate_from_insight(item: Any, user: User) -> dict[str, Any] | None:
    type_map = {
        "UNUSUAL_TRANSACTION": ("SPENDING_SPIKE", "anomaly_alert_enabled"),
        "CASHFLOW_RISK": ("PROJECTED_CASHFLOW_RISK", "smart_notifications_enabled"),
        "GOAL_RISK": ("GOAL_RISK", "smart_notifications_enabled"),
        "POSITIVE_BEHAVIOR": ("POSITIVE_SAVING", "smart_notifications_enabled"),
    }
    mapped = type_map.get(item.type)
    if mapped is None:
        return None
    notification_type, preference = mapped
    return {
        "type": notification_type,
        "title": item.title,
        "description": item.description,
        "source": item.source,
        "source_reference": item.id,
        "rule_id": f"notification:{item.rule_id}",
        "priority": item.priority,
        "severity": item.severity,
        "subject_id": item.subject_id,
        "period_start": item.period_start,
        "period_end": item.period_end,
        "evidence": {"source_metric": item.source_metric, **item.evidence},
        "expires_at": item.expires_at,
        "preference": preference,
    }


def notification_candidates(
    db: Session, user: User, start: date, end: date, currency: str
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for insight in active_insights(db, user, start, end, currency):
        candidate = _candidate_from_insight(insight, user)
        if candidate:
            candidates.append(candidate)

    for budget in list_budgets(db, user):
        if budget.currency != currency or budget.end_date < start or budget.start_date > end:
            continue
        calculation = budget_calculation(db, user, budget, today=end)
        utilization = Decimal(str(calculation["utilization"] or 0))
        crossed = [rule_id for rule_id, threshold in THRESHOLDS if utilization >= threshold]
        if not crossed:
            continue
        for rule_id in crossed:
            threshold = dict(THRESHOLDS)[rule_id]
            candidates.append(
                {
                    "type": "BUDGET_THRESHOLD",
                    "title": f"Budget alert: {budget.name}",
                    "description": f"{budget.name} has reached {threshold:.0%} of its limit.",
                    "source": "phase07.budget_calculation",
                    "source_reference": budget.id,
                    "rule_id": rule_id,
                    "priority": 3 if threshold >= 1 else 2,
                    "severity": "HIGH" if threshold >= 1 else "MEDIUM",
                    "subject_id": budget.id,
                    "period_start": budget.start_date,
                    "period_end": budget.end_date,
                    "evidence": {
                        "source_metric": "calculation.utilization",
                        "utilization": calculation["utilization"],
                        "threshold": threshold,
                        "spent": calculation["spent"],
                        "limit": budget.total_limit,
                    },
                    "expires_at": datetime.combine(budget.end_date, time.max, tzinfo=timezone.utc),
                    "preference": "budget_alert_enabled",
                }
            )
    return candidates


def evaluate_notifications(
    db: Session,
    user: User,
    start: date,
    end: date,
    currency: str,
    *,
    now: datetime | None = None,
) -> list[Notification]:
    preference = _preference(db, user)
    if not preference.smart_notifications_enabled:
        return []
    local_now = _local_now(user, now)
    quiet = _in_quiet_hours(user, preference, local_now)
    local_today = local_now.date()
    day_start = datetime.combine(local_today, time.min, tzinfo=local_now.tzinfo)
    day_end = datetime.combine(local_today, time.max, tzinfo=local_now.tzinfo)
    created_today = (
        db.scalar(
            select(func.count(Notification.id)).where(
                Notification.user_id == user.id,
                Notification.created_at >= day_start.astimezone(timezone.utc),
                Notification.created_at <= day_end.astimezone(timezone.utc),
            )
        )
        or 0
    )
    created: list[Notification] = []
    for values in notification_candidates(db, user, start, end, currency):
        if not getattr(preference, values["preference"]):
            continue
        if quiet and values["severity"] != "HIGH":
            continue
        dedupe = _dedupe_key(
            user.id,
            values["rule_id"],
            values["subject_id"],
            f"{values['period_start']}:{values['period_end']}",
            values["evidence"].get("threshold", ""),
        )
        if db.scalar(select(Notification.id).where(Notification.dedupe_key == dedupe)):
            continue
        if values["severity"] != "HIGH" and created_today >= preference.max_notifications_per_day:
            continue
        notification = Notification(
            user_id=user.id,
            dedupe_key=dedupe,
            channel="IN_APP",
            **{
                key: (json.loads(json.dumps(value, default=str)) if key == "evidence" else value)
                for key, value in values.items()
                if key != "preference"
            },
        )
        db.add(notification)
        try:
            with db.begin_nested():
                db.flush()
        except IntegrityError:
            continue
        created.append(notification)
        created_today += 1
    return created


def mark_read(db: Session, user: User, notification_id: str) -> Notification | None:
    notification = db.scalar(
        select(Notification).where(
            Notification.id == notification_id, Notification.user_id == user.id
        )
    )
    if notification is None:
        return None
    if notification.read_at is None:
        notification.read_at = datetime.now(timezone.utc)
    db.add(
        NotificationEvent(
            notification_id=notification.id,
            user_id=user.id,
            event_type="READ",
            channel="IN_APP",
            result="accepted",
            event_metadata={},
        )
    )
    return notification


def record_event(
    db: Session,
    user: User,
    notification_id: str,
    event_type: str,
    result: str | None,
    metadata: dict[str, Any],
) -> NotificationEvent | None:
    notification = db.scalar(
        select(Notification).where(
            Notification.id == notification_id, Notification.user_id == user.id
        )
    )
    if notification is None:
        return None
    event = NotificationEvent(
        notification_id=notification.id,
        user_id=user.id,
        event_type=event_type,
        channel="IN_APP",
        result=result,
        event_metadata=metadata,
    )
    db.add(event)
    return event


def evaluate_all_users(db: Session, now: datetime | None = None) -> int:
    users = db.scalars(select(User).where(User.status == "ACTIVE")).all()
    total = 0
    for user in users:
        local = _local_now(user, now)
        start, end = _period(local)
        total += len(evaluate_notifications(db, user, start, end, user.default_currency, now=now))
    db.commit()
    return total
