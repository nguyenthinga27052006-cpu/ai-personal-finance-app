from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import (
    Account,
    Budget,
    BudgetCategory,
    Category,
    FinancialGoal,
    GoalContribution,
    Transaction,
    TransactionStatus,
    TransactionType,
    User,
)


class BudgetGoalError(Exception):
    pass


class ResourceNotFound(BudgetGoalError):
    pass


class ResourceConflict(BudgetGoalError):
    pass


def _local_date(value: datetime, user: User) -> date:
    aware = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return aware.astimezone(ZoneInfo(user.timezone)).date()


def effective_expenses(
    db: Session, user: User, start: date, end: date, currency: str
) -> dict[str | None, int]:
    transactions = list(
        db.scalars(
            select(Transaction)
            .options(selectinload(Transaction.items))
            .where(
                Transaction.user_id == user.id,
                Transaction.currency == currency,
                Transaction.status == TransactionStatus.POSTED.value,
                Transaction.type.in_([TransactionType.EXPENSE.value, TransactionType.REFUND.value]),
            )
        ).all()
    )
    expenses: dict[str | None, int] = {}
    refunds: dict[str, int] = {}
    for transaction in transactions:
        if transaction.type == TransactionType.REFUND.value and transaction.parent_transaction_id:
            refunds[transaction.parent_transaction_id] = (
                refunds.get(transaction.parent_transaction_id, 0) + transaction.amount
            )
    for transaction in transactions:
        if not start <= _local_date(transaction.transaction_date, user) <= end:
            continue
        if transaction.type == TransactionType.REFUND.value and transaction.parent_transaction_id:
            continue
        if transaction.type != TransactionType.EXPENSE.value:
            continue
        effective_amount = max(transaction.amount - refunds.get(transaction.id, 0), 0)
        if transaction.items:
            for item in transaction.items:
                item_amount = effective_amount * item.amount // transaction.amount
                expenses[item.category_id] = expenses.get(item.category_id, 0) + item_amount
        else:
            expenses[transaction.category_id] = (
                expenses.get(transaction.category_id, 0) + effective_amount
            )
    return expenses


def _risk(utilization: Decimal, projected: int, limit: int) -> str:
    projected_ratio = Decimal(projected) / Decimal(limit)
    ratio = max(utilization, projected_ratio)
    if ratio >= Decimal("1"):
        return "OVER"
    if ratio >= Decimal("0.9"):
        return "DANGER"
    if ratio >= Decimal("0.8"):
        return "WARNING"
    return "SAFE"


def budget_calculation(
    db: Session, user: User, budget: Budget, today: date | None = None
) -> dict[str, object]:
    today = today or datetime.now(timezone.utc).astimezone(ZoneInfo(user.timezone)).date()
    spent = sum(
        effective_expenses(db, user, budget.start_date, budget.end_date, budget.currency).values()
    )
    elapsed = (
        0
        if today < budget.start_date
        else min(
            (today - budget.start_date).days + 1, (budget.end_date - budget.start_date).days + 1
        )
    )
    total_days = (budget.end_date - budget.start_date).days + 1
    remaining_days = max(total_days - elapsed, 0)
    velocity = Decimal(spent) / elapsed if elapsed else Decimal(0)
    projected = (
        spent
        if not elapsed or remaining_days == 0
        else int((velocity * total_days).to_integral_value())
    )
    utilization = Decimal(spent) / Decimal(budget.total_limit)
    return {
        "spent": spent,
        "remaining": budget.total_limit - spent,
        "utilization": float(utilization),
        "days_elapsed": elapsed,
        "days_remaining": remaining_days,
        "current_spending_velocity": float(velocity),
        "projected_spending": projected,
        "risk": _risk(utilization, projected, budget.total_limit),
    }


def _budget(db: Session, user: User, budget_id: str) -> Budget:
    budget = db.scalar(
        select(Budget)
        .options(selectinload(Budget.categories))
        .where(Budget.id == budget_id, Budget.user_id == user.id)
    )
    if budget is None:
        raise ResourceNotFound
    return budget


def _category(db: Session, user: User, category_id: str) -> Category:
    category = db.scalar(
        select(Category).where(
            Category.id == category_id,
            Category.is_active.is_(True),
            (Category.is_system.is_(True) | (Category.user_id == user.id)),
        )
    )
    if category is None:
        raise ResourceNotFound
    return category


def _add_categories(
    db: Session, user: User, budget: Budget, categories: list[dict[str, object]]
) -> None:
    seen: set[str] = set()
    for values in categories:
        category_id = str(values["category_id"])
        if category_id in seen or any(
            item.category_id == category_id for item in budget.categories
        ):
            raise ResourceConflict("Category is already assigned to this budget")
        _category(db, user, category_id)
        budget.categories.append(
            BudgetCategory(category_id=category_id, limit_amount=int(values["limit_amount"]))
        )
        seen.add(category_id)


def create_budget(db: Session, user: User, values: dict[str, object]) -> Budget:
    categories = values.pop("categories", [])
    duplicate = db.scalar(
        select(Budget).where(
            Budget.user_id == user.id,
            Budget.period_type == values["period_type"],
            Budget.start_date == values["start_date"],
            Budget.end_date == values["end_date"],
            Budget.currency == values["currency"],
        )
    )
    if duplicate is not None:
        raise ResourceConflict("Budget definition already exists")
    budget = Budget(user_id=user.id, **values)
    db.add(budget)
    db.flush()
    _add_categories(db, user, budget, categories)
    db.flush()
    return budget


def list_budgets(db: Session, user: User) -> list[Budget]:
    return list(
        db.scalars(
            select(Budget)
            .options(selectinload(Budget.categories))
            .where(Budget.user_id == user.id)
            .order_by(Budget.start_date.desc(), Budget.id)
        ).all()
    )


def update_budget(db: Session, user: User, budget_id: str, values: dict[str, object]) -> Budget:
    budget = _budget(db, user, budget_id)
    for key, value in values.items():
        setattr(budget, key, value)
    if budget.start_date > budget.end_date:
        raise BudgetGoalError("Budget start_date must not be after end_date")
    if budget.period_type != "MONTHLY":
        raise BudgetGoalError("Only MONTHLY budgets are supported")
    if budget.status not in {"ACTIVE", "INACTIVE", "ARCHIVED"}:
        raise BudgetGoalError("Invalid budget status")
    duplicate = db.scalar(
        select(Budget).where(
            Budget.id != budget.id,
            Budget.user_id == user.id,
            Budget.period_type == budget.period_type,
            Budget.start_date == budget.start_date,
            Budget.end_date == budget.end_date,
            Budget.currency == budget.currency,
        )
    )
    if duplicate is not None:
        raise ResourceConflict("Budget definition already exists")
    db.flush()
    return budget


def delete_budget(db: Session, user: User, budget_id: str) -> None:
    db.delete(_budget(db, user, budget_id))
    db.flush()


def create_goal(db: Session, user: User, values: dict[str, object]) -> FinancialGoal:
    if values.get("status", "ACTIVE") not in {"ACTIVE", "COMPLETED", "PAUSED", "ARCHIVED"}:
        raise BudgetGoalError("Invalid goal status")
    goal = FinancialGoal(user_id=user.id, **values)
    db.add(goal)
    db.flush()
    return goal


def _goal(db: Session, user: User, goal_id: str) -> FinancialGoal:
    goal = db.scalar(
        select(FinancialGoal)
        .options(selectinload(FinancialGoal.contributions))
        .where(FinancialGoal.id == goal_id, FinancialGoal.user_id == user.id)
    )
    if goal is None:
        raise ResourceNotFound
    return goal


def goal_calculation(goal: FinancialGoal, today: date | None = None) -> dict[str, object]:
    today = today or date.today()
    current = sum(contribution.amount for contribution in goal.contributions)
    remaining = max(goal.target_amount - current, 0)
    progress = min(Decimal(current) / Decimal(goal.target_amount), Decimal(1))
    if remaining == 0 or goal.target_date is None or goal.target_date <= today:
        required = remaining
    else:
        months = max(
            (goal.target_date.year - today.year) * 12
            + goal.target_date.month
            - today.month
            + (1 if goal.target_date.day >= today.day else 0),
            1,
        )
        required = (remaining + months - 1) // months
    actual = current // max((today - goal.created_at.date()).days // 30 + 1, 1)
    forecast = "AHEAD" if actual > required else "ON_TRACK" if actual == required else "BEHIND"
    return {
        "current": current,
        "remaining": remaining,
        "progress": float(progress),
        "required_monthly_saving": required,
        "actual_monthly_saving": actual,
        "forecast": forecast,
    }


def list_goals(db: Session, user: User) -> list[FinancialGoal]:
    return list(
        db.scalars(
            select(FinancialGoal)
            .options(selectinload(FinancialGoal.contributions))
            .where(FinancialGoal.user_id == user.id)
            .order_by(FinancialGoal.priority, FinancialGoal.id)
        ).all()
    )


def create_contribution(
    db: Session, user: User, goal_id: str, values: dict[str, object]
) -> GoalContribution:
    goal = _goal(db, user, goal_id)
    account_id = values.get("account_id")
    if (
        account_id is not None
        and db.scalar(select(Account).where(Account.id == account_id, Account.user_id == user.id))
        is None
    ):
        raise ResourceNotFound
    contribution = GoalContribution(goal_id=goal.id, **values)
    db.add(contribution)
    db.flush()
    return contribution


def list_contributions(db: Session, user: User, goal_id: str) -> list[GoalContribution]:
    goal = _goal(db, user, goal_id)
    return sorted(goal.contributions, key=lambda item: (item.contribution_date, item.id))
