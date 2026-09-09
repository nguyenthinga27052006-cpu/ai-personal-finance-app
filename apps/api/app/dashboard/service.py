from __future__ import annotations

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.accounts.service import list_accounts
from app.analytics.service import build_overview
from app.budget_goals.service import budget_calculation, goal_calculation, list_budgets, list_goals
from app.db.models import User
from app.transactions.service import list_transactions


def _month_period(user: User, today: date | None = None) -> tuple[date, date]:
    local_today = today or datetime.now(timezone.utc).astimezone(ZoneInfo(user.timezone)).date()
    start = local_today.replace(day=1)
    if start.month == 12:
        next_month = start.replace(year=start.year + 1, month=1)
    else:
        next_month = start.replace(month=start.month + 1)
    return start, next_month.fromordinal(next_month.toordinal() - 1)


def build_dashboard(db: Session, user: User) -> dict[str, object]:
    start, end = _month_period(user)
    currency = user.default_currency
    overview = build_overview(db, user, start, end, currency)
    accounts = [
        {
            "id": item.id,
            "name": item.name,
            "currency": item.currency,
            "current_balance": item.current_balance,
        }
        for item in list_accounts(db, user)
        if item.currency == currency
    ]
    transactions, _ = list_transactions(db, user, 1, 5, None, None)
    recent = [
        {
            "id": item.id,
            "type": item.type,
            "amount": item.amount,
            "currency": item.currency,
            "transaction_date": item.transaction_date,
            "description": item.description,
        }
        for item in transactions
        if item.currency == currency
    ]
    categories = [
        {
            "id": item["id"],
            "name": item["name"],
            "amount": item["amount"],
            "share": item["share"],
        }
        for item in overview["category_analysis"]
    ]
    budgets = []
    for budget in list_budgets(db, user):
        if budget.currency != currency or budget.status != "ACTIVE":
            continue
        calculation = budget_calculation(db, user, budget)
        budgets.append(
            {
                "id": budget.id,
                "name": budget.name,
                "currency": currency,
                "total_limit": budget.total_limit,
                **calculation,
            }
        )
    goals = []
    for goal in list_goals(db, user):
        if goal.currency != currency or goal.status != "ACTIVE":
            continue
        calculation = goal_calculation(goal, today=end)
        goals.append(
            {
                "id": goal.id,
                "name": goal.name,
                "currency": currency,
                "target_amount": goal.target_amount,
                **calculation,
            }
        )
    summary = overview["summary"]
    return {
        "period": {"start": start, "end": end, "timezone": user.timezone},
        "summary": {
            "total_balance": sum(item["current_balance"] for item in accounts),
            "income": summary["income"],
            "expense": summary["expense"],
            "saving": summary["saving"],
            "saving_rate": summary["saving_rate"],
        },
        "accounts": accounts,
        "recent_transactions": recent,
        "categories": categories,
        "budgets": budgets,
        "goals": goals,
    }
