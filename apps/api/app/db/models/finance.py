from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin, TimestampMixin


class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"


class AccountType(str, Enum):
    CASH = "CASH"
    BANK = "BANK"
    E_WALLET = "E_WALLET"
    CREDIT_CARD = "CREDIT_CARD"
    SAVINGS = "SAVINGS"
    OTHER = "OTHER"


class AccountStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"


class CategoryType(str, Enum):
    EXPENSE = "EXPENSE"
    INCOME = "INCOME"
    BOTH = "BOTH"


class BudgetPeriodType(str, Enum):
    MONTHLY = "MONTHLY"


class BudgetStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"


class GoalStatus(str, Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    PAUSED = "PAUSED"
    ARCHIVED = "ARCHIVED"


class TransactionType(str, Enum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"
    TRANSFER = "TRANSFER"
    REFUND = "REFUND"
    ADJUSTMENT = "ADJUSTMENT"


class TransactionStatus(str, Enum):
    POSTED = "POSTED"
    PENDING = "PENDING"
    VOIDED = "VOIDED"


class TransactionSource(str, Enum):
    MANUAL = "MANUAL"
    IMPORT = "IMPORT"
    OCR = "OCR"
    AI = "AI"
    SYSTEM = "SYSTEM"
    BANK_SYNC = "BANK_SYNC"


class EntryType(str, Enum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"


class User(IdMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    default_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="VND")
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    locale: Mapped[str] = mapped_column(String(16), nullable=False, default="vi-VN")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=UserStatus.ACTIVE.value)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    accounts: Mapped[list["Account"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    categories: Mapped[list["Category"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    budgets: Mapped[list["Budget"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    financial_goals: Mapped[list["FinancialGoal"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    user_preferences: Mapped["UserPreference | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    user_settings: Mapped["UserSetting | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class UserPreference(IdMixin, TimestampMixin, Base):
    __tablename__ = "user_preferences"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    ai_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    smart_notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    weekly_report_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    monthly_report_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    budget_alert_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    anomaly_alert_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    recurring_reminder_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    quiet_hours_start: Mapped[str | None] = mapped_column(String(5), nullable=True)
    quiet_hours_end: Mapped[str | None] = mapped_column(String(5), nullable=True)
    max_notifications_per_day: Mapped[int] = mapped_column(Integer, default=10, nullable=False)

    user: Mapped[User] = relationship(back_populates="user_preferences")


class UserSetting(IdMixin, TimestampMixin, Base):
    __tablename__ = "user_settings"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    theme: Mapped[str] = mapped_column(String(32), default="system", nullable=False)
    week_starts_on: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    financial_month_start: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    minimum_safe_balance: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    default_account_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True
    )

    user: Mapped[User] = relationship(back_populates="user_settings")


class Account(IdMixin, TimestampMixin, Base):
    __tablename__ = "accounts"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    type: Mapped[AccountType] = mapped_column(String(32), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    opening_balance: Mapped[int] = mapped_column(BigInteger, nullable=False)
    current_balance: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    credit_limit: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[AccountStatus] = mapped_column(
        String(32), nullable=False, default=AccountStatus.ACTIVE.value
    )
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="accounts")
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )
    transaction_entries: Mapped[list["TransactionEntry"]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )
    goal_contributions: Mapped[list["GoalContribution"]] = relationship(back_populates="account")

    __table_args__ = (
        CheckConstraint("opening_balance >= 0", name="ck_accounts_opening_balance_nonnegative"),
        CheckConstraint("current_balance >= 0", name="ck_accounts_current_balance_nonnegative"),
        CheckConstraint(
            "credit_limit IS NULL OR credit_limit >= 0", name="ck_accounts_credit_limit_nonnegative"
        ),
        Index("ix_accounts_user_id", "user_id"),
    )


class Category(IdMixin, TimestampMixin, Base):
    __tablename__ = "categories"

    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    type: Mapped[CategoryType] = mapped_column(String(32), nullable=False)
    parent_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("categories.id", ondelete="RESTRICT"), nullable=True
    )
    icon: Mapped[str | None] = mapped_column(String(64), nullable=True)
    color_token: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    user: Mapped[User | None] = relationship(back_populates="categories")
    parent: Mapped["Category | None"] = relationship(
        remote_side="Category.id", back_populates="children"
    )
    children: Mapped[list["Category"]] = relationship(back_populates="parent")
    merchants: Mapped[list["Merchant"]] = relationship(back_populates="category_hint_obj")
    budget_categories: Mapped[list["BudgetCategory"]] = relationship(back_populates="category")
    transaction_items: Mapped[list["TransactionItem"]] = relationship(back_populates="category")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="category")

    __table_args__ = (
        CheckConstraint(
            "(is_system = true AND user_id IS NULL) OR (is_system = false AND user_id IS NOT NULL)",
            name="ck_categories_system_owner",
        ),
        Index("ix_categories_user_id", "user_id"),
        Index(
            "uq_system_category_name_type",
            "name",
            "type",
            unique=True,
            postgresql_where="is_system = true",
        ),
    )


class Merchant(IdMixin, TimestampMixin, Base):
    __tablename__ = "merchants"

    canonical_name: Mapped[str] = mapped_column(String(160), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(160), nullable=False)
    category_hint: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("categories.id"), nullable=True
    )
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")

    category_hint_obj: Mapped[Category | None] = relationship(back_populates="merchants")
    aliases: Mapped[list["MerchantAlias"]] = relationship(
        back_populates="merchant", cascade="all, delete-orphan"
    )
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="merchant")

    __table_args__ = (Index("ix_merchants_normalized_name", "normalized_name"),)


class MerchantAlias(IdMixin, TimestampMixin, Base):
    __tablename__ = "merchant_aliases"

    merchant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False
    )
    alias: Mapped[str] = mapped_column(String(160), nullable=False)
    normalized_alias: Mapped[str] = mapped_column(String(160), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="MANUAL")
    confidence: Mapped[float | None] = mapped_column(nullable=True)

    merchant: Mapped[Merchant] = relationship(back_populates="aliases")

    __table_args__ = (
        UniqueConstraint("merchant_id", "normalized_alias", name="uq_merchant_alias"),
    )


class Transaction(IdMixin, TimestampMixin, Base):
    __tablename__ = "transactions"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    account_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("accounts.id"), nullable=True
    )
    type: Mapped[TransactionType] = mapped_column(String(32), nullable=False)
    status: Mapped[TransactionStatus] = mapped_column(String(32), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    merchant_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("merchants.id"), nullable=True
    )
    category_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("categories.id"), nullable=True
    )
    source: Mapped[TransactionSource] = mapped_column(
        String(32), nullable=False, default=TransactionSource.MANUAL.value
    )
    external_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    parent_transaction_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("transactions.id"), nullable=True
    )
    transfer_group_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="transactions")
    account: Mapped[Account | None] = relationship(back_populates="transactions")
    merchant: Mapped[Merchant | None] = relationship(back_populates="transactions")
    category: Mapped[Category | None] = relationship(back_populates="transactions")
    entries: Mapped[list["TransactionEntry"]] = relationship(
        back_populates="transaction", cascade="all, delete-orphan"
    )
    items: Mapped[list["TransactionItem"]] = relationship(
        back_populates="transaction", cascade="all, delete-orphan"
    )
    parent: Mapped["Transaction | None"] = relationship(remote_side="Transaction.id")

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_transactions_amount_positive"),
        Index("ix_transactions_user_date", "user_id", "transaction_date"),
        Index("ix_transactions_account_date", "account_id", "transaction_date"),
        Index("ix_transactions_category_date", "category_id", "transaction_date"),
        Index("ix_transactions_merchant_date", "merchant_id", "transaction_date"),
    )


class TransactionEntry(IdMixin, TimestampMixin, Base):
    __tablename__ = "transaction_entries"

    transaction_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False
    )
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    entry_type: Mapped[EntryType] = mapped_column(String(32), nullable=False)

    transaction: Mapped[Transaction] = relationship(back_populates="entries")
    account: Mapped[Account] = relationship(back_populates="transaction_entries")

    __table_args__ = (
        CheckConstraint("amount <> 0", name="ck_transaction_entries_amount_nonzero"),
        Index("ix_transaction_entries_transaction_id", "transaction_id"),
        Index("ix_transaction_entries_account_id_created_at", "account_id", "created_at"),
    )


class TransactionItem(IdMixin, TimestampMixin, Base):
    __tablename__ = "transaction_items"

    transaction_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False
    )
    category_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("categories.id"), nullable=True
    )
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    transaction: Mapped[Transaction] = relationship(back_populates="items")
    category: Mapped[Category | None] = relationship(back_populates="transaction_items")

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_transaction_items_amount_positive"),
        CheckConstraint("quantity > 0", name="ck_transaction_items_quantity_positive"),
        Index("ix_transaction_items_transaction_id", "transaction_id"),
        Index("ix_transaction_items_category_id", "category_id"),
    )


class Budget(IdMixin, TimestampMixin, Base):
    __tablename__ = "budgets"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    period_type: Mapped[BudgetPeriodType] = mapped_column(String(32), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_limit: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[BudgetStatus] = mapped_column(String(32), nullable=False)

    user: Mapped[User] = relationship(back_populates="budgets")
    categories: Mapped[list["BudgetCategory"]] = relationship(
        back_populates="budget", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("start_date <= end_date", name="ck_budgets_period_valid"),
        CheckConstraint("total_limit > 0", name="ck_budgets_total_limit_positive"),
        Index("ix_budgets_user_period", "user_id", "start_date", "end_date"),
    )


class BudgetCategory(IdMixin, TimestampMixin, Base):
    __tablename__ = "budget_categories"

    budget_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False
    )
    category_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("categories.id"), nullable=False
    )
    limit_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)

    budget: Mapped[Budget] = relationship(back_populates="categories")
    category: Mapped[Category] = relationship(back_populates="budget_categories")

    __table_args__ = (
        CheckConstraint("limit_amount > 0", name="ck_budget_categories_limit_positive"),
        UniqueConstraint("budget_id", "category_id", name="uq_budget_category"),
    )


class FinancialGoal(IdMixin, TimestampMixin, Base):
    __tablename__ = "financial_goals"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    target_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[GoalStatus] = mapped_column(String(32), nullable=False)

    user: Mapped[User] = relationship(back_populates="financial_goals")
    contributions: Mapped[list["GoalContribution"]] = relationship(
        back_populates="goal", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("target_amount > 0", name="ck_financial_goals_target_positive"),
        Index("ix_financial_goals_user_id", "user_id"),
    )


class GoalContribution(IdMixin, TimestampMixin, Base):
    __tablename__ = "goal_contributions"

    goal_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("financial_goals.id", ondelete="CASCADE"), nullable=False
    )
    account_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("accounts.id"), nullable=True
    )
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    contribution_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    note: Mapped[str | None] = mapped_column(String, nullable=True)

    goal: Mapped[FinancialGoal] = relationship(back_populates="contributions")
    account: Mapped[Account | None] = relationship(back_populates="goal_contributions")

    __table_args__ = (CheckConstraint("amount > 0", name="ck_goal_contributions_amount_positive"),)


def seed_system_categories(session) -> None:
    system_definitions = [
        ("Food", CategoryType.EXPENSE, "expense"),
        ("Housing", CategoryType.EXPENSE, "expense"),
        ("Transportation", CategoryType.EXPENSE, "expense"),
        ("Shopping", CategoryType.EXPENSE, "expense"),
        ("Health", CategoryType.EXPENSE, "expense"),
        ("Education", CategoryType.EXPENSE, "expense"),
        ("Entertainment", CategoryType.EXPENSE, "expense"),
        ("Utilities", CategoryType.EXPENSE, "expense"),
        ("Subscription", CategoryType.EXPENSE, "expense"),
        ("Other", CategoryType.EXPENSE, "expense"),
        ("Salary", CategoryType.INCOME, "income"),
        ("Bonus", CategoryType.INCOME, "income"),
        ("Freelance", CategoryType.INCOME, "income"),
        ("Investment Income", CategoryType.INCOME, "income"),
        ("Other", CategoryType.INCOME, "income"),
    ]

    for name, category_type, _kind in system_definitions:
        exists = (
            session.query(Category)
            .filter(
                Category.is_system.is_(True),
                Category.name == name,
                Category.type == category_type.value,
            )
            .first()
        )
        if exists:
            continue

        session.add(
            Category(
                user_id=None,
                name=name,
                type=category_type,
                is_system=True,
                is_active=True,
                sort_order=1,
            )
        )

    session.flush()
