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
    if recommendation_type == "PAY_DEBT_EARLY":
        return "ESTIMATE: trích một phần thặng dư thanh toán nợ sớm giúp giảm gánh nặng nợ và lãi suất"
    if recommendation_type == "DEBT_DUE_ACTION":
        return "ESTIMATE: chuẩn bị nguồn tiền thanh toán khoản nợ sắp đến hạn để tránh trễ hạn"
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
        "DEBT_DUE_SOON": (
            "DEBT_DUE_ACTION",
            "Chuẩn bị nguồn tiền để thanh toán khoản nợ sắp đến hạn.",
        ),
        "DEBT_OVERDUE": (
            "DEBT_DUE_ACTION",
            "Khoản nợ đã quá hạn, vui lòng ưu tiên liên hệ đối tác hoặc thanh toán ngay.",
        ),
        "DEBT_PAYOFF_OPPORTUNITY": (
            "PAY_DEBT_EARLY",
            "Cân nhắc trích khoản tiền dư để thanh toán bớt nợ trước hạn theo chiến lược tối ưu.",
        ),
    }
    return mapping.get(item.type)


def _ranking(item: Any, feedback_score: int = 0) -> Decimal:
    relevance = Decimal("1.00")
    confidence = Decimal(str(item.confidence))
    impact = (
        Decimal("1.00")
        if item.type in {"CASHFLOW_RISK", "GOAL_RISK", "BUDGET_RISK", "DEBT_DUE_SOON", "DEBT_OVERDUE"}
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


def _generate_copilot_explanation(facts: dict[str, Any], fallback: str) -> str:
    """Uses local Ollama (qwen2.5:3b) to generate natural language explanation of verified facts."""
    try:
        import json
        import urllib.request

        from app.core.config import get_settings

        settings = get_settings()
        if not getattr(settings, "ai_enabled", True):
            return fallback

        ollama_base = settings.ollama_base_url.removesuffix("/v1").rstrip("/")
        ollama_url = f"{ollama_base}/api/generate"
        facts_summary = json.dumps(facts, ensure_ascii=False, default=str)
        prompt = (
            "Bạn là trợ lý tài chính cá nhân thân thiện, khách quan và đồng cảm. "
            "Dựa trên các số liệu thực tế được cung cấp bên dưới, hãy viết đúng 1 đến 2 câu ngắn gọn, mạch lạc "
            "để thông báo tình trạng tài chính và gợi ý hành động hữu ích nhất cho người dùng.\n"
            "QUY TẮC BẮT BUỘC: TUYỆT ĐỐI không bịa ra bất kỳ số liệu nào khác ngoài facts. "
            "Nếu có số tiền hãy giữ nguyên định dạng số dễ đọc (ví dụ: 1.500.000đ). "
            "Chỉ trả lời bằng văn bản ngắn, không thêm lời chào, không thêm dấu gạch đầu dòng.\n\n"
            f"Dữ liệu thực tế (Facts):\n{facts_summary}\n\n"
            "Lời nhắn trợ lý:"
        )
        req = urllib.request.Request(
            ollama_url,
            data=json.dumps({
                "model": settings.ai_model,
                "prompt": prompt,
                "stream": False,
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=6) as res:
            body = json.loads(res.read().decode("utf-8"))
            resp = body.get("response", "").strip().strip('"').strip("'")
            if resp and len(resp) > 10:
                return resp
    except Exception:
        pass
    return fallback


def build_copilot_card(db: Session, user: User, today: date | None = None) -> dict[str, Any]:
    from calendar import monthrange

    from app.accounts.service import list_accounts
    from app.analytics.service import build_overview
    from app.debts.service import list_contacts, list_debts

    current_date = today or date.today()
    start_date = current_date.replace(day=1)
    _, last_day = monthrange(current_date.year, current_date.month)
    end_date = current_date.replace(day=last_day)
    currency = user.default_currency or "VND"

    accounts = list_accounts(db, user)
    available_balance = sum(
        a.current_balance for a in accounts if a.currency == currency and not a.is_archived
    )

    overview = build_overview(db, user, start_date, end_date, currency)
    summary = overview["summary"]
    income = int(summary["income"])
    expense = int(summary["expense"])
    saving = int(summary["saving"])
    saving_rate = float(summary["saving_rate"])

    active_debts = list_debts(db, user, status_filter="ACTIVE")
    active_contacts = list_contacts(db, user, only_support=True)
    has_support_contacts = len(active_contacts) > 0

    # Look for upcoming or overdue borrow debt
    in_7_days = current_date + timedelta(days=7)
    upcoming_borrow = None
    for d in active_debts:
        if d.type == "BORROW" and d.due_date and d.due_date <= in_7_days:
            upcoming_borrow = d
            break

    facts: dict[str, Any] = {
        "period": f"{current_date.month}/{current_date.year}",
        "available_balance": available_balance,
        "income": income,
        "expense": expense,
        "saving": saving,
        "saving_rate": saving_rate,
        "has_support_contacts": has_support_contacts,
        "support_contacts_count": len(active_contacts),
        "currency": currency,
    }

    if upcoming_borrow:
        facts["upcoming_debt"] = {
            "counterparty": upcoming_borrow.counterparty_name,
            "amount": upcoming_borrow.remaining_amount,
            "due_date": upcoming_borrow.due_date.isoformat(),
        }

    # Case 1: Shortfall risk / Cash Gap
    if upcoming_borrow and available_balance < upcoming_borrow.remaining_amount:
        projected_gap = upcoming_borrow.remaining_amount - available_balance
        facts["projected_gap"] = projected_gap
        headline = "Nguy cơ thiếu hụt dòng tiền"
        fallback = (
            f"Khoản nợ {upcoming_borrow.remaining_amount:,} {currency} cho {upcoming_borrow.counterparty_name} "
            f"sắp đến hạn trong khi số dư hiện tại còn thiếu khoảng {projected_gap:,} {currency}. "
            "Bạn nên kiểm tra lại chi tiêu hoặc xem danh bạ người thân hỗ trợ tài chính nhé."
        )
        actions = [
            {"action_id": "VIEW_DEBTS", "label": "Kiểm tra sổ nợ", "target_screen": "/debts"},
            {"action_id": "VIEW_SUPPORT", "label": "Xem người hỗ trợ", "target_screen": "/financial-contacts"},
            {"action_id": "VIEW_BUDGET", "label": "Kiểm tra ngân sách", "target_screen": "/budgets"},
        ]
        status_code = "RISK"
    elif upcoming_borrow:
        headline = f"Khoản nợ sắp đến hạn: {upcoming_borrow.counterparty_name}"
        fallback = (
            f"Bạn có khoản nợ {upcoming_borrow.remaining_amount:,} {currency} cần trả cho {upcoming_borrow.counterparty_name} "
            f"vào ngày {upcoming_borrow.due_date.isoformat()}. Hãy lưu ý chuẩn bị sẵn nguồn tiền nhé."
        )
        actions = [
            {"action_id": "VIEW_DEBTS", "label": "Xem sổ nợ", "target_screen": "/debts"},
            {"action_id": "PAY_DEBT", "label": "Ghi nhận trả nợ", "target_screen": "/debts"},
        ]
        status_code = "RISK"
    elif saving > 0 and any(d.type == "BORROW" for d in active_debts):
        first_borrow = next(d for d in active_debts if d.type == "BORROW")
        headline = "Cơ hội trả nợ sớm"
        fallback = (
            f"Tháng này bạn đang thặng dư khoảng {saving:,} {currency}. "
            f"Bạn có thể cân nhắc trích một phần để trả bớt khoản nợ cho {first_borrow.counterparty_name} "
            "nhằm giảm nhẹ áp lực tài chính."
        )
        actions = [
            {"action_id": "PAY_DEBT", "label": "Trích trả nợ", "target_screen": "/debts"},
            {"action_id": "VIEW_INSIGHTS", "label": "Xem phân tích", "target_screen": "/insights"},
        ]
        status_code = "OPPORTUNITY"
    elif saving > 0:
        headline = "Dòng tiền tích cực"
        fallback = (
            f"Tháng này bạn đang duy trì thói quen tích lũy rất tốt với tỷ lệ tiết kiệm {saving_rate:.0%}. "
            "Hãy tiếp tục duy trì đà này để sớm đạt các mục tiêu tài chính!"
        )
        actions = [
            {"action_id": "VIEW_GOALS", "label": "Xem mục tiêu", "target_screen": "/goals"},
            {"action_id": "VIEW_INSIGHTS", "label": "Xem chi tiết", "target_screen": "/insights"},
        ]
        status_code = "SAVING"
    else:
        headline = "Tài chính ổn định"
        fallback = "Dòng tiền thu chi của bạn đang trong tầm kiểm soát. Hãy tiếp tục theo dõi các khoản chi tiêu hàng ngày."
        actions = [
            {"action_id": "VIEW_INSIGHTS", "label": "Xem phân tích", "target_screen": "/insights"},
        ]
        status_code = "STABLE"

    message = _generate_copilot_explanation(facts, fallback)

    return {
        "status": status_code,
        "headline": headline,
        "message": message,
        "facts": facts,
        "actions": actions,
    }
