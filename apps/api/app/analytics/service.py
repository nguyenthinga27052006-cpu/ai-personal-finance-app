from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from statistics import median
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import (
    Budget,
    Transaction,
    TransactionItem,
    TransactionStatus,
    TransactionType,
    User,
)

_RATIO_PLACES = Decimal("0.000001")


@dataclass(frozen=True)
class FinancialFact:
    transaction_id: str
    local_date: date
    transaction_type: str
    amount: int
    effective_expense: int
    category_amounts: dict[str | None, int]
    category_names: dict[str | None, str]
    merchant_id: str | None
    merchant_name: str | None


def _ratio(numerator: int | Decimal, denominator: int | Decimal) -> Decimal:
    if denominator == 0:
        return Decimal(0).quantize(_RATIO_PLACES)
    return (Decimal(numerator) / Decimal(denominator)).quantize(_RATIO_PLACES, ROUND_HALF_UP)


def _local_date(value: datetime, timezone_name: str) -> date:
    aware = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return aware.astimezone(ZoneInfo(timezone_name)).date()


def _period_days(start: date, end: date) -> int:
    return max((end - start).days + 1, 0)


def _category_amounts(transaction: Transaction, effective: int) -> dict[str | None, int]:
    if not transaction.items:
        return {transaction.category_id: effective}
    # Phase 07's allocation policy is authoritative: each split item receives
    # floor(item/original * effective amount), with no parent aggregation.
    amounts: dict[str | None, int] = defaultdict(int)
    for item in transaction.items:
        amounts[item.category_id] += item.amount * effective // transaction.amount
    return dict(amounts)


def load_financial_facts(db: Session, user: User, currency: str) -> list[FinancialFact]:
    rows = list(
        db.scalars(
            select(Transaction)
            .options(
                selectinload(Transaction.items).selectinload(TransactionItem.category),
                selectinload(Transaction.category),
                selectinload(Transaction.merchant),
            )
            .where(
                Transaction.user_id == user.id,
                Transaction.currency == currency,
                Transaction.status == TransactionStatus.POSTED.value,
                Transaction.deleted_at.is_(None),
            )
            .order_by(Transaction.transaction_date, Transaction.id)
        ).all()
    )
    refunds: dict[str, int] = defaultdict(int)
    for row in rows:
        if row.type == TransactionType.REFUND.value and row.parent_transaction_id:
            refunds[row.parent_transaction_id] += row.amount
    facts: list[FinancialFact] = []
    for row in rows:
        effective = (
            max(row.amount - refunds.get(row.id, 0), 0)
            if row.type == TransactionType.EXPENSE.value
            else 0
        )
        facts.append(
            FinancialFact(
                transaction_id=row.id,
                local_date=_local_date(row.transaction_date, user.timezone),
                transaction_type=row.type,
                amount=row.amount,
                effective_expense=effective,
                category_amounts=_category_amounts(row, effective) if effective else {},
                category_names={
                    **({row.category_id: row.category.name} if row.category else {}),
                    **{
                        item.category_id: item.category.name
                        for item in row.items
                        if item.category is not None
                    },
                },
                merchant_id=row.merchant_id,
                merchant_name=row.merchant.canonical_name if row.merchant else "Unspecified",
            )
        )
    return facts


def _in_period(fact: FinancialFact, start: date, end: date) -> bool:
    return start <= fact.local_date <= end


def _summary(facts: list[FinancialFact], start: date, end: date) -> dict[str, object]:
    selected = [fact for fact in facts if _in_period(fact, start, end)]
    income = sum(f.amount for f in selected if f.transaction_type == TransactionType.INCOME.value)
    expense = sum(f.effective_expense for f in selected)
    days = _period_days(start, end)
    return {
        "income": income,
        "expense": expense,
        "saving": income - expense,
        "saving_rate": _ratio(income - expense, income),
        "average_daily_spending": _ratio(expense, days),
        "spending_velocity": _ratio(expense, days),
        "days": days,
        "records": len(selected),
    }


def _periods(start: date, end: date, count: int) -> list[tuple[date, date]]:
    size = _period_days(start, end)
    return [
        (start - timedelta(days=size * i), end - timedelta(days=size * i))
        for i in range(1, count + 1)
    ]


def _analysis(
    facts: list[FinancialFact], start: date, end: date, key: str
) -> list[dict[str, object]]:
    selected = [f for f in facts if _in_period(f, start, end) and f.effective_expense]
    groups: dict[str, list[int]] = defaultdict(list)
    names: dict[str, str] = {}
    for fact in selected:
        if key == "category":
            for category_id, amount in fact.category_amounts.items():
                group = category_id or "uncategorized"
                groups[group].append(amount)
                names[group] = fact.category_names.get(category_id, "Uncategorized")
        else:
            group = fact.merchant_id or "unspecified"
            groups[group].append(fact.effective_expense)
            names[group] = fact.merchant_name or "Unspecified"
    total = sum(sum(values) for values in groups.values())
    previous = _analysis_raw(facts, *_periods(start, end, 1)[0], key)
    previous_by_id = {item["id"]: item["amount"] for item in previous}
    result = []
    for group_id in sorted(groups, key=lambda item: (-sum(groups[item]), item)):
        values = groups[group_id]
        amount = sum(values)
        result.append(
            {
                "id": group_id,
                "name": names[group_id],
                "amount": amount,
                "count": len(values),
                "share": _ratio(amount, total),
                "growth": _growth(amount, previous_by_id.get(group_id, 0)),
                "average": _ratio(amount, len(values)),
                "median": Decimal(str(median(values))),
                "largest": max(values),
            }
        )
    return result


def _analysis_raw(
    facts: list[FinancialFact], start: date, end: date, key: str
) -> list[dict[str, object]]:
    selected = [f for f in facts if _in_period(f, start, end) and f.effective_expense]
    groups: dict[str, int] = defaultdict(int)
    for fact in selected:
        if key == "category":
            for group, amount in fact.category_amounts.items():
                groups[group or "uncategorized"] += amount
        else:
            groups[fact.merchant_id or "unspecified"] += fact.effective_expense
    return [{"id": group, "amount": amount} for group, amount in groups.items()]


def _growth(current: int, previous: int) -> Decimal | None:
    return None if previous == 0 else _ratio(current - previous, previous)


def _time_analysis(
    facts: list[FinancialFact], start: date, end: date, mode: str
) -> list[dict[str, object]]:
    values: dict[str, int] = defaultdict(int)
    counts: dict[str, int] = defaultdict(int)
    for fact in facts:
        if not _in_period(fact, start, end) or not fact.effective_expense:
            continue
        if mode == "daily":
            key = fact.local_date.isoformat()
        elif mode == "weekly":
            key = (fact.local_date - timedelta(days=fact.local_date.weekday())).isoformat()
        elif mode == "monthly":
            key = fact.local_date.replace(day=1).isoformat()
        elif mode == "weekday":
            key = str(fact.local_date.weekday())
        else:
            key = "weekend" if fact.local_date.weekday() >= 5 else "weekday"
        values[key] += fact.effective_expense
        counts[key] += 1
    return [{"period": key, "amount": values[key], "count": counts[key]} for key in sorted(values)]


def _comparison(facts: list[FinancialFact], start: date, end: date) -> dict[str, object]:
    current = _summary(facts, start, end)
    previous_start, previous_end = _periods(start, end, 1)[0]
    previous = _summary(facts, previous_start, previous_end)
    rolling_periods = _periods(start, end, 3)
    rolling = [
        int(_summary(facts, item_start, item_end)["expense"])
        for item_start, item_end in rolling_periods
    ]
    average = _ratio(sum(rolling), len(rolling)) if rolling else Decimal(0)
    return {
        "previous": {
            "start": previous_start,
            "end": previous_end,
            **previous,
            "expense_growth": _growth(int(current["expense"]), int(previous["expense"])),
        },
        "rolling_average": {
            "periods": len(rolling),
            "expense": average,
            "expense_delta": Decimal(int(current["expense"])) - average,
        },
    }


def _anomalies(facts: list[FinancialFact], start: date, end: date) -> list[dict[str, object]]:
    current = _summary(facts, start, end)
    history = [_summary(facts, a, b) for a, b in _periods(start, end, 3)]
    baseline = (
        _ratio(sum(int(item["expense"]) for item in history), len(history))
        if history
        else Decimal(0)
    )
    anomalies: list[dict[str, object]] = []
    if baseline and Decimal(int(current["expense"])) >= baseline * Decimal("1.5"):
        anomalies.append(
            {
                "rule": "period_spending_vs_rolling_3",
                "severity": "HIGH",
                "value": current["expense"],
                "baseline": baseline,
                "reason": (
                    "Current effective expense is at least 150% of the three preceding "
                    "equivalent periods."
                ),
            }
        )
    for item in _analysis(facts, start, end, "merchant"):
        if item["amount"] >= max(100000, int(current["expense"]) // 2) and item["count"] == 1:
            anomalies.append(
                {
                    "rule": "large_single_merchant_expense",
                    "severity": "MEDIUM",
                    "value": item["amount"],
                    "baseline": max(100000, int(current["expense"]) // 2),
                    "reason": (
                        "One merchant accounts for at least half of period expense and is a "
                        "single record."
                    ),
                }
            )
    return anomalies


def build_overview(
    db: Session,
    user: User,
    start: date,
    end: date,
    currency: str,
    budget_id: str | None = None,
) -> dict[str, object]:
    if end < start:
        raise ValueError("end must be on or after start")
    facts = load_financial_facts(db, user, currency)
    summary = _summary(facts, start, end)
    budget_utilization = None
    if budget_id:
        budget = db.scalar(select(Budget).where(Budget.id == budget_id, Budget.user_id == user.id))
        if budget is None or budget.currency != currency:
            raise ValueError("budget is not available for this user and currency")
        budget_utilization = _ratio(int(summary["expense"]), budget.total_limit)
    summary["budget_utilization"] = budget_utilization
    return {
        "currency": currency,
        "period": {"start": start, "end": end, "timezone": user.timezone, "days": summary["days"]},
        "summary": {key: value for key, value in summary.items() if key != "days"},
        "category_analysis": _analysis(facts, start, end, "category"),
        "merchant_analysis": _analysis(facts, start, end, "merchant"),
        "time_analysis": {
            mode: _time_analysis(facts, start, end, mode)
            for mode in ("daily", "weekly", "monthly", "weekday", "weekend")
        },
        "comparison": _comparison(facts, start, end),
        "anomalies": _anomalies(facts, start, end),
        "forecast": _forecast(facts, start, end),
    }


def _forecast(facts: list[FinancialFact], start: date, end: date) -> dict[str, object]:
    summary = _summary(facts, start, end)
    days = int(summary["days"])
    if not days or not summary["records"]:
        return {
            "status": "INSUFFICIENT_DATA",
            "projected_expense": None,
            "basis": "No posted canonical facts in period.",
        }
    pace = Decimal(int(summary["expense"])) / Decimal(days)
    return {
        "status": "BASELINE",
        "projected_expense": int((pace * Decimal(days)).to_integral_value(ROUND_HALF_UP)),
        "daily_pace": pace.quantize(Decimal("0.000001")),
        "recurring_expenses": 0,
        "basis": "Current effective expense pace; no recurring-expense source is available.",
    }
