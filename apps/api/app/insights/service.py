from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.analytics.service import build_overview
from app.budget_goals.service import list_budgets, list_goals
from app.db.models import User
from app.insights.rules import (
    ANOMALY_RULES,
    BUDGET_RISK_THRESHOLD,
    CASHFLOW_DEFICIT_THRESHOLD,
    CATEGORY_DOMINANCE_THRESHOLD,
    POSITIVE_SAVING_RATE_THRESHOLD,
    SAVING_RATE_CHANGE_THRESHOLD,
    SPENDING_CHANGE_THRESHOLD,
    WEEKEND_SHARE_THRESHOLD,
)

SOURCE = "phase09.financial_facts"


@dataclass(frozen=True)
class InsightCandidate:
    id: str
    user_id: str
    type: str
    title: str
    description: str
    severity: str
    confidence: Decimal
    relevance: Decimal
    priority: int
    period_start: date
    period_end: date
    source: str
    rule_id: str
    subject_id: str | None
    source_metric: str
    source_value: int | Decimal | None
    baseline: int | Decimal | None
    evidence: dict[str, object]
    expires_at: datetime
    created_at: datetime

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _decimal(value: Any) -> Decimal:
    return Decimal(str(value))


def _dedupe_id(user_id: str, rule_id: str, subject_id: str | None, start: date, end: date) -> str:
    key = "|".join((user_id, rule_id, subject_id or "", start.isoformat(), end.isoformat()))
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:32]


def _candidate(
    user: User,
    start: date,
    end: date,
    *,
    insight_type: str,
    title: str,
    description: str,
    severity: str,
    confidence: str,
    rule_id: str,
    subject_id: str | None,
    source_metric: str,
    source_value: int | Decimal | None,
    baseline: int | Decimal | None,
    evidence: dict[str, object],
) -> InsightCandidate:
    created_at = datetime.combine(start, time.min, tzinfo=timezone.utc)
    priority = {"HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}[severity]
    return InsightCandidate(
        id=_dedupe_id(user.id, rule_id, subject_id, start, end),
        user_id=user.id,
        type=insight_type,
        title=title,
        description=description,
        severity=severity,
        confidence=Decimal(confidence),
        relevance=Decimal("1.0"),
        priority=priority,
        period_start=start,
        period_end=end,
        source=SOURCE,
        rule_id=rule_id,
        subject_id=subject_id,
        source_metric=source_metric,
        source_value=source_value,
        baseline=baseline,
        evidence=evidence,
        expires_at=datetime.combine(end + timedelta(days=30), time.min, tzinfo=timezone.utc),
        created_at=created_at,
    )


def _spending_change(
    user: User, start: date, end: date, overview: dict[str, Any]
) -> list[InsightCandidate]:
    previous = overview["comparison"]["previous"]
    growth = previous.get("expense_growth")
    if growth is None or _decimal(growth).copy_abs() < SPENDING_CHANGE_THRESHOLD:
        return []
    current = int(overview["summary"]["expense"])
    baseline = int(previous["expense"])
    increased = _decimal(growth) > 0
    return [
        _candidate(
            user,
            start,
            end,
            insight_type="SPENDING_INCREASE" if increased else "SPENDING_DECREASE",
            title="Spending increased" if increased else "Spending decreased",
            description=(
                "Effective spending is up versus the previous equivalent period."
                if increased
                else "Effective spending is down versus the previous equivalent period."
            ),
            severity="HIGH" if increased else "INFO",
            confidence="0.95",
            rule_id="spending_change",
            subject_id=None,
            source_metric="comparison.previous.expense_growth",
            source_value=current,
            baseline=baseline,
            evidence={"growth": growth, "threshold": SPENDING_CHANGE_THRESHOLD},
        )
    ]


def _category_dominance(
    user: User, start: date, end: date, overview: dict[str, Any]
) -> list[InsightCandidate]:
    categories = overview["category_analysis"]
    if len(categories) < 2 or not categories:
        return []
    top = categories[0]
    share = _decimal(top["share"])
    if share < CATEGORY_DOMINANCE_THRESHOLD:
        return []
    return [
        _candidate(
            user,
            start,
            end,
            insight_type="CATEGORY_DOMINANCE",
            title=f"{top['name']} dominates spending",
            description=(
                f"{top['name']} accounts for {share:.1%} of effective spending in this period."
            ),
            severity="MEDIUM",
            confidence="0.90",
            rule_id="category_dominance",
            subject_id=str(top["id"]),
            source_metric="category_analysis.share",
            source_value=int(top["amount"]),
            baseline=int(overview["summary"]["expense"]),
            evidence={
                "share": share,
                "threshold": CATEGORY_DOMINANCE_THRESHOLD,
                "category": top["name"],
            },
        )
    ]


def _anomalies(
    user: User, start: date, end: date, overview: dict[str, Any]
) -> list[InsightCandidate]:
    result: list[InsightCandidate] = []
    for anomaly in overview["anomalies"]:
        if anomaly["rule"] not in ANOMALY_RULES:
            continue
        result.append(
            _candidate(
                user,
                start,
                end,
                insight_type="UNUSUAL_TRANSACTION",
                title="Unusual spending detected",
                description=anomaly["reason"],
                severity=anomaly["severity"],
                confidence="0.85",
                rule_id=f"anomaly:{anomaly['rule']}",
                subject_id=None,
                source_metric=f"anomalies.{anomaly['rule']}",
                source_value=anomaly["value"],
                baseline=anomaly["baseline"],
                evidence={"rule": anomaly["rule"], "reason": anomaly["reason"]},
            )
        )
    return result


def _saving_change(
    user: User, start: date, end: date, overview: dict[str, Any]
) -> list[InsightCandidate]:
    current = _decimal(overview["summary"]["saving_rate"])
    previous = overview["comparison"]["previous"]
    if not previous.get("records"):
        return []
    baseline = _decimal(previous["saving_rate"])
    change = current - baseline
    if change.copy_abs() < SAVING_RATE_CHANGE_THRESHOLD:
        return []
    improved = change > 0
    return [
        _candidate(
            user,
            start,
            end,
            insight_type="SAVING_IMPROVEMENT" if improved else "SAVING_DECLINE",
            title="Saving rate improved" if improved else "Saving rate declined",
            description=(
                "Your saving rate changed materially versus the previous equivalent period."
            ),
            severity="INFO" if improved else "MEDIUM",
            confidence="0.90",
            rule_id="saving_rate_change",
            subject_id=None,
            source_metric="summary.saving_rate",
            source_value=current,
            baseline=baseline,
            evidence={"change": change, "threshold": SAVING_RATE_CHANGE_THRESHOLD},
        )
    ]


def _cashflow_risk(
    user: User, start: date, end: date, overview: dict[str, Any]
) -> list[InsightCandidate]:
    summary = overview["summary"]
    income = int(summary["income"])
    saving = int(summary["saving"])
    if income <= 0 or saving >= CASHFLOW_DEFICIT_THRESHOLD:
        return []
    return [
        _candidate(
            user,
            start,
            end,
            insight_type="CASHFLOW_RISK",
            title="Cash flow deficit",
            description="Effective spending exceeded income in this period.",
            severity="HIGH",
            confidence="0.99",
            rule_id="cashflow_deficit",
            subject_id=None,
            source_metric="summary.saving",
            source_value=saving,
            baseline=CASHFLOW_DEFICIT_THRESHOLD,
            evidence={
                "income": income,
                "expense": summary["expense"],
                "threshold": CASHFLOW_DEFICIT_THRESHOLD,
            },
        )
    ]


def _positive_behavior(
    user: User, start: date, end: date, overview: dict[str, Any]
) -> list[InsightCandidate]:
    rate = _decimal(overview["summary"]["saving_rate"])
    if not overview["summary"]["income"] or rate < POSITIVE_SAVING_RATE_THRESHOLD:
        return []
    return [
        _candidate(
            user,
            start,
            end,
            insight_type="POSITIVE_BEHAVIOR",
            title="Healthy saving behavior",
            description="Income exceeded effective spending by a healthy margin in this period.",
            severity="INFO",
            confidence="0.95",
            rule_id="positive_saving_rate",
            subject_id=None,
            source_metric="summary.saving_rate",
            source_value=rate,
            baseline=POSITIVE_SAVING_RATE_THRESHOLD,
            evidence={"saving_rate": rate, "threshold": POSITIVE_SAVING_RATE_THRESHOLD},
        )
    ]


def _weekend_pattern(
    user: User, start: date, end: date, overview: dict[str, Any]
) -> list[InsightCandidate]:
    points = {item["period"]: item for item in overview["time_analysis"]["weekend"]}
    weekday = points.get("weekday")
    weekend = points.get("weekend")
    total = (weekday["amount"] if weekday else 0) + (weekend["amount"] if weekend else 0)
    if not weekend or total == 0:
        return []
    share = _decimal(weekend["amount"]) / Decimal(total)
    if share < WEEKEND_SHARE_THRESHOLD:
        return []
    return [
        _candidate(
            user,
            start,
            end,
            insight_type="WEEKEND_PATTERN",
            title="Weekend spending pattern",
            description="A significant share of effective spending occurs on weekends.",
            severity="LOW",
            confidence="0.80",
            rule_id="weekend_spending_share",
            subject_id=None,
            source_metric="time_analysis.weekend.amount",
            source_value=int(weekend["amount"]),
            baseline=total,
            evidence={"share": share, "threshold": WEEKEND_SHARE_THRESHOLD},
        )
    ]


def _budget_risks(
    db: Session, user: User, start: date, end: date, currency: str
) -> list[InsightCandidate]:
    result: list[InsightCandidate] = []
    for budget in list_budgets(db, user):
        if budget.currency != currency or budget.end_date < start or budget.start_date > end:
            continue
        overview = build_overview(
            db, user, max(start, budget.start_date), min(end, budget.end_date), currency, budget.id
        )
        utilization = overview["summary"]["budget_utilization"]
        if utilization is None or _decimal(utilization) < BUDGET_RISK_THRESHOLD:
            continue
        utilization = _decimal(utilization)
        result.append(
            _candidate(
                user,
                start,
                end,
                insight_type="BUDGET_RISK",
                title=f"Budget risk: {budget.name}",
                description="Effective spending has reached the warning threshold for this budget.",
                severity="HIGH" if _decimal(utilization) >= 1 else "MEDIUM",
                confidence="0.98",
                rule_id="budget_risk",
                subject_id=budget.id,
                source_metric="summary.budget_utilization",
                source_value=utilization,
                baseline=BUDGET_RISK_THRESHOLD,
                evidence={
                    "budget_name": budget.name,
                    "utilization": utilization,
                    "threshold": BUDGET_RISK_THRESHOLD,
                },
            )
        )
    return result


def _goal_insights(
    db: Session, user: User, start: date, end: date, currency: str
) -> list[InsightCandidate]:
    result: list[InsightCandidate] = []
    from app.budget_goals.service import goal_calculation

    for goal in list_goals(db, user):
        if goal.currency != currency or goal.status != "ACTIVE":
            continue
        calculation: dict[str, Any] = goal_calculation(goal, today=end)
        forecast = calculation["forecast"]
        if calculation["progress"] >= 1 or forecast == "AHEAD":
            result.append(
                _candidate(
                    user,
                    start,
                    end,
                    insight_type="GOAL_PROGRESS",
                    title=f"Goal progress: {goal.name}",
                    description="This goal is complete or progressing ahead of its required pace.",
                    severity="INFO",
                    confidence="0.98",
                    rule_id="goal_progress",
                    subject_id=goal.id,
                    source_metric="goal.calculation.progress",
                    source_value=calculation["progress"],
                    baseline=1,
                    evidence={"forecast": forecast, "progress": calculation["progress"]},
                )
            )
        elif forecast == "BEHIND":
            result.append(
                _candidate(
                    user,
                    start,
                    end,
                    insight_type="GOAL_RISK",
                    title=f"Goal risk: {goal.name}",
                    description="This goal is behind its required contribution pace.",
                    severity="MEDIUM",
                    confidence="0.98",
                    rule_id="goal_risk",
                    subject_id=goal.id,
                    source_metric="goal.calculation.forecast",
                    source_value=calculation["actual_monthly_saving"],
                    baseline=calculation["required_monthly_saving"],
                    evidence={"forecast": forecast},
                )
            )
    return result


def generate_insights(
    db: Session,
    user: User,
    start: date,
    end: date,
    currency: str,
) -> list[InsightCandidate]:
    if end < start:
        raise ValueError("end must be on or after start")
    overview = build_overview(db, user, start, end, currency)
    candidates = (
        _spending_change(user, start, end, overview)
        + _category_dominance(user, start, end, overview)
        + _anomalies(user, start, end, overview)
        + _saving_change(user, start, end, overview)
        + _cashflow_risk(user, start, end, overview)
        + _positive_behavior(user, start, end, overview)
        + _weekend_pattern(user, start, end, overview)
        + _budget_risks(db, user, start, end, currency)
        + _goal_insights(db, user, start, end, currency)
    )
    ranked = sorted(
        candidates,
        key=lambda item: (
            item.priority,
            item.relevance,
            item.confidence,
            item.rule_id,
            item.subject_id or "",
        ),
        reverse=True,
    )
    return ranked


def active_insights(
    *args: Any, now: datetime | None = None, **kwargs: Any
) -> list[InsightCandidate]:
    current = now or datetime.now(timezone.utc)
    return [item for item in generate_insights(*args, **kwargs) if item.expires_at > current]


def candidate_json(candidate: InsightCandidate) -> str:
    return json.dumps(candidate.as_dict(), default=str, sort_keys=True)
