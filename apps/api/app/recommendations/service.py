from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Recommendation, RecommendationEvent, User
from app.insights.service import active_insights

SOURCE = "phase10.insights"
ACTIVE = "ACTIVE"
DISMISSED = "DISMISSED"
ACCEPTED = "ACCEPTED"
EXPIRED = "EXPIRED"


@dataclass(frozen=True)
class RecommendationCandidate:
    user_id: str
    type: str
    reason: str
    suggested_action: str
    expected_impact: str
    priority: int
    confidence: Decimal
    source_insight_id: str
    source_metric: str
    subject_id: str | None
    period_start: date
    period_end: date
    expires_at: datetime
    deterministic_id: str
    dedupe_key: str
    ranking_score: Decimal

    def as_dict(self) -> dict[str, object]:
        return {
            "user_id": self.user_id,
            "type": self.type,
            "reason": self.reason,
            "suggested_action": self.suggested_action,
            "expected_impact": self.expected_impact,
            "priority": self.priority,
            "confidence": float(self.confidence),
            "source_insight_id": self.source_insight_id,
            "source_metric": self.source_metric,
            "subject_id": self.subject_id,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "expires_at": self.expires_at,
            "deterministic_id": self.deterministic_id,
            "dedupe_key": self.dedupe_key,
            "ranking_score": float(self.ranking_score),
        }


def _hash_key(*parts: object) -> str:
    return hashlib.sha256("|".join(str(part or "") for part in parts).encode()).hexdigest()[:48]


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _priority(severity: str) -> int:
    return {"HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}.get(severity, 0)


def _impact(item: Any, recommendation_type: str) -> str:
    evidence = item.evidence
    if recommendation_type == "REDUCE_CATEGORY" and evidence.get("category"):
        return (
            "ESTIMATE: reducing this category's spending may improve monthly headroom; "
            f"source share={evidence['share']}"
        )
    if recommendation_type == "ADJUST_BUDGET":
        return f"ESTIMATE: review budget headroom; source utilization={evidence.get('utilization')}"
    if recommendation_type == "INCREASE_SAVING":
        return (
            "ESTIMATE: increasing the saving rate from the source value may improve future saving"
        )
    if recommendation_type == "GOAL_PACING":
        return (
            "ESTIMATE: meeting the required contribution pace may improve goal completion "
            "likelihood"
        )
    if recommendation_type == "CASHFLOW_PREPARATION":
        return (
            "ESTIMATE: preparing for the projected deficit may reduce near-term cashflow pressure"
        )
    return "ESTIMATE: impact depends on the user's confirmed action"


def _map_insight(item: Any) -> tuple[str, str] | None:
    mapping = {
        "CATEGORY_DOMINANCE": (
            "REDUCE_CATEGORY",
            "Review the dominant spending category and set a deliberate reduction target.",
        ),
        "BUDGET_RISK": (
            "ADJUST_BUDGET",
            "Review this budget against effective spending and adjust it deliberately if needed.",
        ),
        "SAVING_DECLINE": (
            "INCREASE_SAVING",
            "Set aside a planned amount before discretionary spending.",
        ),
        "POSITIVE_BEHAVIOR": (
            "INCREASE_SAVING",
            "Preserve this saving behavior and consider a small planned increase.",
        ),
        "GOAL_RISK": (
            "GOAL_PACING",
            "Review the goal contribution pace and schedule the required saving amount.",
        ),
        "CASHFLOW_RISK": (
            "CASHFLOW_PREPARATION",
            "Review upcoming discretionary spending and prepare for the projected cashflow risk.",
        ),
    }
    return mapping.get(item.type)


def _ranking(item: Any, feedback_score: int = 0) -> Decimal:
    relevance = Decimal("1.00")
    confidence = Decimal(str(item.confidence))
    impact = (
        Decimal("1.00")
        if item.type in {"CASHFLOW_RISK", "GOAL_RISK", "BUDGET_RISK"}
        else Decimal("0.70")
    )
    urgency = Decimal(item.priority) / Decimal("3")
    feedback = Decimal(feedback_score) / Decimal("10")
    return (
        relevance * Decimal("0.30")
        + confidence * Decimal("0.30")
        + impact * Decimal("0.20")
        + urgency * Decimal("0.15")
        + feedback * Decimal("0.05")
    ).quantize(Decimal("0.0001"))


def generate_candidates(
    db: Session, user: User, start: date, end: date, currency: str
) -> list[RecommendationCandidate]:
    candidates: list[RecommendationCandidate] = []
    for insight in active_insights(db, user, start, end, currency):
        mapped = _map_insight(insight)
        if mapped is None:
            continue
        recommendation_type, action = mapped
        dedupe = _hash_key(user.id, recommendation_type, insight.subject_id, start, end, insight.id)
        candidates.append(
            RecommendationCandidate(
                user_id=user.id,
                type=recommendation_type,
                reason=f"Based on {insight.source_metric}: {insight.description}",
                suggested_action=action,
                expected_impact=_impact(insight, recommendation_type),
                priority=insight.priority,
                confidence=insight.confidence,
                source_insight_id=insight.id,
                source_metric=insight.source_metric,
                subject_id=insight.subject_id,
                period_start=start,
                period_end=end,
                expires_at=insight.expires_at,
                deterministic_id=dedupe,
                dedupe_key=dedupe,
                ranking_score=_ranking(insight),
            )
        )
    return sorted(
        candidates,
        key=lambda item: (-item.ranking_score, -item.priority, item.deterministic_id),
    )


def materialize(
    db: Session, user: User, start: date, end: date, currency: str
) -> list[Recommendation]:
    now = datetime.now(timezone.utc)
    created: list[Recommendation] = []
    for candidate in generate_candidates(db, user, start, end, currency):
        existing = db.scalar(
            select(Recommendation).where(Recommendation.dedupe_key == candidate.dedupe_key)
        )
        if existing:
            if (
                existing.status == ACTIVE
                and existing.expires_at
                and _as_utc(existing.expires_at) <= now
            ):
                existing.status = EXPIRED
            continue
        item = Recommendation(**candidate.as_dict(), status=ACTIVE)
        db.add(item)
        try:
            with db.begin_nested():
                db.flush()
        except IntegrityError:
            continue
        created.append(item)
    return created


def active_recommendations(
    db: Session, user: User, start: date, end: date, currency: str
) -> list[Recommendation]:
    materialize(db, user, start, end, currency)
    now = datetime.now(timezone.utc)
    items = db.scalars(
        select(Recommendation)
        .where(
            Recommendation.user_id == user.id,
            Recommendation.period_start <= end,
            Recommendation.period_end >= start,
            Recommendation.status == ACTIVE,
            (Recommendation.expires_at.is_(None) | (Recommendation.expires_at > now)),
        )
        .order_by(
            Recommendation.ranking_score.desc(),
            Recommendation.priority.desc(),
            Recommendation.deterministic_id,
        )
    ).all()
    return list(items)


def transition(
    db: Session, user: User, recommendation_id: str, status: str
) -> Recommendation | None:
    item = db.scalar(
        select(Recommendation).where(
            Recommendation.id == recommendation_id, Recommendation.user_id == user.id
        )
    )
    if item is None:
        return None
    item.status = status
    db.add(
        RecommendationEvent(
            recommendation_id=item.id,
            user_id=user.id,
            event_type=status,
            metadata_json={"financial_write": False},
        )
    )
    return item


def add_feedback(
    db: Session,
    user: User,
    recommendation_id: str,
    feedback: str,
    metadata: dict[str, Any],
) -> Recommendation | None:
    item = db.scalar(
        select(Recommendation).where(
            Recommendation.id == recommendation_id, Recommendation.user_id == user.id
        )
    )
    if item is None:
        return None
    item.feedback_score += 1 if feedback == "HELPFUL" else -1
    db.add(
        RecommendationEvent(
            recommendation_id=item.id,
            user_id=user.id,
            event_type="FEEDBACK",
            feedback=feedback,
            metadata_json=metadata,
        )
    )
    return item


def evaluate_all_users(db: Session, now: datetime | None = None) -> int:
    users = db.scalars(select(User).where(User.status == "ACTIVE")).all()
    total = 0
    current = now or datetime.now(timezone.utc)
    for user in users:
        local = current.astimezone(ZoneInfo(user.timezone))
        start = local.date().replace(day=1)
        next_month = date(
            start.year + (start.month == 12),
            1 if start.month == 12 else start.month + 1,
            1,
        )
        end = next_month - timedelta(days=1)
        total += len(materialize(db, user, start, end, user.default_currency))
    db.commit()
    return total
