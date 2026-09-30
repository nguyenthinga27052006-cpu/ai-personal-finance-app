from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.ai.retrievers.intent_detector import IntentDetector
from app.db.models import (
    Account,
    Budget,
    Category,
    Debt,
    FinancialGoal,
    Notification,
    Transaction,
    User,
)


@dataclass(frozen=True)
class FinancialFact:
    value: Decimal | float
    currency: str
    source: str
    tool: str
    period_start: date
    period_end: date
    calculation_type: str = "deterministic"
    status: str = "VALID"
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "value": float(self.value) if isinstance(self.value, Decimal) else self.value,
            "currency": self.currency,
            "source": self.source,
            "tool": self.tool,
            "period": {
                "start": self.period_start.isoformat(),
                "end": self.period_end.isoformat(),
            },
            "calculation_type": self.calculation_type,
            "status": self.status,
            "reason": self.reason,
        }


class FinancialFactValidator:
    """Validates financial data integrity, user ownership, and provenance."""

    @staticmethod
    def validate(user_id: str, context: SQLUserDataContext) -> list[FinancialFact]:
        facts: list[FinancialFact] = []

        if context.user_id != user_id:
            facts.append(
                FinancialFact(
                    value=0,
                    currency=context.currency,
                    source="postgresql_db",
                    tool="ownership_check",
                    period_start=context.period_start,
                    period_end=context.period_end,
                    status="INVALID_OWNERSHIP",
                    reason="User ID mismatch in financial facts context",
                )
            )
            return facts

        if not context.has_data:
            facts.append(
                FinancialFact(
                    value=0,
                    currency=context.currency,
                    source="postgresql_db",
                    tool="has_data_check",
                    period_start=context.period_start,
                    period_end=context.period_end,
                    status="INSUFFICIENT_DATA",
                    reason="No transactions or accounts found for period",
                )
            )
            return facts

        # Validate Income
        if context.total_income < Decimal("0"):
            facts.append(
                FinancialFact(
                    value=context.total_income,
                    currency=context.currency,
                    source="postgresql_db",
                    tool="get_monthly_income",
                    period_start=context.period_start,
                    period_end=context.period_end,
                    status="ANOMALY_NEGATIVE_INCOME",
                    reason="Total income is negative",
                )
            )
        else:
            facts.append(
                FinancialFact(
                    value=context.total_income,
                    currency=context.currency,
                    source="postgresql_db",
                    tool="get_monthly_income",
                    period_start=context.period_start,
                    period_end=context.period_end,
                    status="VALID",
                )
            )

        # Validate Expense
        if context.total_expense < Decimal("0"):
            facts.append(
                FinancialFact(
                    value=context.total_expense,
                    currency=context.currency,
                    source="postgresql_db",
                    tool="get_monthly_expense",
                    period_start=context.period_start,
                    period_end=context.period_end,
                    status="ANOMALY_NEGATIVE_EXPENSE",
                    reason="Total expense is negative",
                )
            )
        else:
            facts.append(
                FinancialFact(
                    value=context.total_expense,
                    currency=context.currency,
                    source="postgresql_db",
                    tool="get_monthly_expense",
                    period_start=context.period_start,
                    period_end=context.period_end,
                    status="VALID",
                )
            )

        # Validate Balance
        facts.append(
            FinancialFact(
                value=context.total_balance,
                currency=context.currency,
                source="postgresql_db",
                tool="get_current_balance",
                period_start=context.period_start,
                period_end=context.period_end,
                status="VALID",
            )
        )

        return facts


@dataclass(frozen=True)
class SQLUserDataContext:
    user_id: str = ""
    period_start: date = field(default_factory=date.today)
    period_end: date = field(default_factory=date.today)
    currency: str = "VND"
    total_income: Decimal = Decimal("0")
    total_expense: Decimal = Decimal("0")
    net_savings: Decimal = Decimal("0")
    accounts: list[dict[str, Any]] = field(default_factory=list)
    total_balance: Decimal = Decimal("0")
    top_categories: list[dict[str, Any]] = field(default_factory=list)
    recent_transactions: list[dict[str, Any]] = field(default_factory=list)
    budgets: list[dict[str, Any]] = field(default_factory=list)
    goals: list[dict[str, Any]] = field(default_factory=list)
    notifications: list[dict[str, Any]] = field(default_factory=list)
    debts: list[dict[str, Any]] = field(default_factory=list)
    transaction_count: int = 0
    has_data: bool = False
    monthly_breakdown: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def empty(
        cls,
        user_id: str = "",
        period_start: date | None = None,
        period_end: date | None = None,
        currency: str = "VND",
    ) -> SQLUserDataContext:
        """Constructs a clean empty financial context with no financial facts or transactions."""
        today = date.today()
        return cls(
            user_id=user_id,
            period_start=period_start or today,
            period_end=period_end or today,
            currency=currency.upper(),
            total_income=Decimal("0"),
            total_expense=Decimal("0"),
            net_savings=Decimal("0"),
            accounts=[],
            total_balance=Decimal("0"),
            top_categories=[],
            recent_transactions=[],
            budgets=[],
            goals=[],
            notifications=[],
            debts=[],
            transaction_count=0,
            has_data=False,
            monthly_breakdown=[],
        )

    def summary_text(self, intent: str | None = None) -> str:
        if not self.has_data:
            return "Không tìm thấy giao dịch hoặc dữ liệu tài chính trong khoảng thời gian này."

        if intent in ("knowledge", "greeting", "app_faq", "time_reference_query"):
            return "Không yêu cầu dữ liệu tài chính cho câu hỏi này."

        if intent == "debt_advice":
            parts = [
                "[SỔ NỢ & CHO VAY (DEBTS)]:",
            ]
            borrow_debts = [d for d in self.debts if d.get("type") == "BORROW"]
            lend_debts = [d for d in self.debts if d.get("type") == "LEND"]
            if borrow_debts:
                parts.append("* MỤC 1 - CÁC KHOẢN BẠN NỢ NGƯỜI KHÁC (BẠN LÀ CON NỢ, BẠN PHẢI TRẢ TIỀN):")
                for d in borrow_debts:
                    due_info = f", Hạn trả: {d['due_date']}" if d.get("due_date") else ""
                    notes_info = f", Ghi chú: {d['notes']}" if d.get("notes") else ""
                    parts.append(
                        f"  - Bạn nợ đối tác '{d['counterparty_name']}': Số tiền bạn phải trả là {d['remaining_amount']:,.0f} {d['currency']}{due_info}{notes_info}"
                    )
            else:
                parts.append("* MỤC 1: Hiện tại bạn KHÔNG NỢ ai khoản tiền nào.")

            if lend_debts:
                parts.append("* MỤC 2 - CÁC KHOẢN NGƯỜI KHÁC NỢ BẠN (BẠN CHO VAY, NGƯỜI TA PHẢI TRẢ TIỀN CHO BẠN):")
                for d in lend_debts:
                    due_info = f", Hạn thu: {d['due_date']}" if d.get("due_date") else ""
                    notes_info = f", Ghi chú: {d['notes']}" if d.get("notes") else ""
                    parts.append(
                        f"  - Đối tác '{d['counterparty_name']}' đang nợ bạn (bạn cho vay): Số tiền họ phải trả cho bạn là {d['remaining_amount']:,.0f} {d['currency']}{due_info}{notes_info}"
                    )
            else:
                parts.append("* MỤC 2: Hiện không có ai nợ tiền bạn.")

            parts.append(
                f"\nLƯU Ý: Đây là dữ liệu thực tế từ Sổ Nợ. TUYỆT ĐỐI KHÔNG lấy số dư tài khoản hay số thặng dư thu chi để coi là khoản nợ."
            )
            return "\n".join(parts)

        if intent == "balance_query":
            parts = [
                f"Tổng số dư tài khoản ({len(self.accounts)} tài khoản): {self.total_balance:,.0f} {self.currency}",
            ]
            if self.accounts:
                parts.append("Chi tiết tài khoản:")
                for acc in self.accounts:
                    parts.append(f"* {acc['name']}: {acc['balance']:,.0f} {self.currency}")
            return "\n".join(parts)

        if intent == "income_query":
            return (
                f"Thu nhập tổng kỳ ({self.period_start} đến {self.period_end}): {self.total_income:,.0f} {self.currency}\n"
                f"Thặng dư tích lũy kỳ: {self.net_savings:,.0f} {self.currency}\n"
                f"Tổng chi tiêu cùng kỳ: {self.total_expense:,.0f} {self.currency}"
            )

        if intent in ("expense_query", "spending_analysis", "category_analysis"):
            if self.transaction_count == 0:
                return (
                    f"- Thời gian: Từ {self.period_start} đến {self.period_end}\n"
                    f"- Tổng chi tiêu: 0 {self.currency} (0 giao dịch)\n"
                    f"- TRẠNG THÁI: KHÔNG CÓ GIAO DỊCH NÀO PHÁT SINH TRONG KỲ NÀY.\n"
                    f"- LƯU Ý: Người dùng chưa có bất kỳ giao dịch chi tiêu nào trong khoảng thời gian này. Tuyệt đối không lấy số liệu tháng khác."
                )
            parts = [
                f"- Thời gian: Từ {self.period_start} đến {self.period_end}",
                f"- Tổng chi tiêu thực tế: {self.total_expense:,.0f} {self.currency} (gồm {self.transaction_count} giao dịch)",
            ]
            if self.top_categories:
                parts.append("- Danh mục chi tiêu chi tiết:")
                for c in self.top_categories:
                    parts.append(f"  + {c['category']}: {c['amount']:,.0f} {self.currency} ({c['percentage']:.1f}%)")
            return "\n".join(parts)

        if intent == "comparison_query":
            parts = [
                f"So sánh chi tiêu tổng kỳ ({self.period_start} đến {self.period_end}):",
                f"- Tổng chi tiêu toàn kỳ: {self.total_expense:,.0f} {self.currency} ({self.transaction_count} giao dịch)",
                f"- Tổng thu nhập toàn kỳ: {self.total_income:,.0f} {self.currency}",
            ]
            if self.monthly_breakdown:
                parts.append("\n- Chi tiết từng tháng:")
                for m in self.monthly_breakdown:
                    chg = ""
                    if m["change_pct"] is not None:
                        if m["change_pct"] > 0:
                            chg = f" (Biến động chi tiêu: +{m['change_pct']}% - Tăng)"
                        elif m["change_pct"] < 0:
                            chg = f" (Biến động chi tiêu: {m['change_pct']}% - Giảm)"
                        else:
                            chg = " (Biến động chi tiêu: 0.0% - Không đổi)"
                    parts.append(
                        f"  * {m['month']}: Tổng chi tiêu {m['expense']:,.0f} {self.currency}{chg} | Thu nhập {m['income']:,.0f} {self.currency}"
                    )
                    if m.get("top_categories"):
                        cat_list = [f"{c['category']}: {c['amount']:,.0f} {self.currency}" for c in m["top_categories"][:4]]
                        parts.append(f"    - Các danh mục chi tiêu: {', '.join(cat_list)}")
            return "\n".join(parts)

        parts = [
            f"Tổng số dư tài khoản ({len(self.accounts)} tài khoản): {self.total_balance:,.0f} {self.currency}",
            f"Thu nhập tổng kỳ ({self.period_start} đến {self.period_end}): {self.total_income:,.0f} {self.currency}",
            f"Chi tiêu tổng kỳ: {self.total_expense:,.0f} {self.currency} (gồm {self.transaction_count} giao dịch)",
            f"Thặng dư tiết kiệm tổng kỳ: {self.net_savings:,.0f} {self.currency}",
        ]

        if self.monthly_breakdown and len(self.monthly_breakdown) > 1:
            parts.append(
                f"\nPhân tích & So sánh chi tiết từng tháng ({self.period_start} đến {self.period_end}):"
            )
            for m in self.monthly_breakdown:
                chg = ""
                if m["change_pct"] is not None:
                    if m["change_pct"] > 0:
                        chg = f" (Biến động chi tiêu: +{m['change_pct']}% - Tăng)"
                    elif m["change_pct"] < 0:
                        chg = f" (Biến động chi tiêu: {m['change_pct']}% - Giảm)"
                    else:
                        chg = " (Biến động chi tiêu: 0.0% - Không đổi)"
                parts.append(
                    f"* {m['month']}: Chi tiêu {m['expense']:,.0f} {self.currency}{chg} | Thu nhập {m['income']:,.0f} {self.currency} | Thặng dư {m['savings']:,.0f} {self.currency} (Danh mục chính: {m['top_category']})"
                )

        if self.top_categories:
            cat_strings = [
                f"{c['category']}: {c['amount']:,.0f} {self.currency} ({c['percentage']:.1f}%)"
                for c in self.top_categories[:4]
            ]
            parts.append(f"Danh mục chi tiêu hàng đầu tổng kỳ: {', '.join(cat_strings)}")

        if self.budgets:
            b_strings = [
                f"Ngân sách '{b['name']}': đã dùng {b['spent']:,.0f}/{b['amount']:,.0f} {self.currency} ({b['usage_pct']:.1f}%)"
                for b in self.budgets
            ]
            parts.append(f"Tình hình ngân sách: {'; '.join(b_strings)}")

        if self.goals:
            g_strings = [
                f"Mục tiêu '{g['name']}': tích lũy {g['current']:,.0f}/{g['target']:,.0f} {self.currency} ({g['progress_pct']:.1f}%)"
                for g in self.goals
            ]
            parts.append(f"Mục tiêu tiết kiệm: {'; '.join(g_strings)}")

        if self.debts:
            borrow_debts = [d for d in self.debts if d.get("type") == "BORROW"]
            lend_debts = [d for d in self.debts if d.get("type") == "LEND"]
            d_parts = []
            if borrow_debts:
                d_parts.append(
                    f"Đang nợ {len(borrow_debts)} khoản ("
                    + ", ".join([f"{d['counterparty_name']}: {d['remaining_amount']:,.0f} {d['currency']}" for d in borrow_debts])
                    + ")"
                )
            if lend_debts:
                d_parts.append(
                    f"Cho vay {len(lend_debts)} khoản ("
                    + ", ".join([f"{d['counterparty_name']}: {d['remaining_amount']:,.0f} {d['currency']}" for d in lend_debts])
                    + ")"
                )
            if d_parts:
                parts.append(f"Sổ nợ & Cho vay: {'; '.join(d_parts)}")

        return "\n".join(parts)


EXCHANGE_RATES: dict[str, Decimal] = {
    "VND": Decimal("1"),
    "USD": Decimal("25400"),
    "EUR": Decimal("27500"),
}


class SQLRetriever:
    """Retrieves real user financial data from PostgreSQL across Accounts, Transactions, Budgets, Categories, Income, Goals, Notifications."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def retrieve_user_financial_facts(
        self,
        user: User,
        start: date | None = None,
        end: date | None = None,
        currency: str = "VND",
        question: str | None = None,
    ) -> SQLUserDataContext:
        user_tz = ZoneInfo(user.timezone) if getattr(user, "timezone", None) else timezone.utc
        today = datetime.now(user_tz).date()
        target_currency = currency.upper()
        target_rate = EXCHANGE_RATES.get(target_currency, Decimal("1"))

        if not start or not end:
            if question:
                parsed_start, parsed_end, _ = IntentDetector.parse_date_range(question, today=today)
                start = start or parsed_start
                end = end or parsed_end
            else:
                start = date(today.year, today.month, 1)
                next_month = date(
                    today.year + (today.month == 12), 1 if today.month == 12 else today.month + 1, 1
                )
                end = next_month - timedelta(days=1)

        # 1. Accounts
        accounts_query = self.db.query(Account).filter(Account.user_id == user.id).all()
        accounts_data = []
        total_balance = Decimal("0")

        for acc in accounts_query:
            acc_currency = (acc.currency or "VND").upper()
            acc_rate = EXCHANGE_RATES.get(acc_currency, Decimal("1"))
            raw_balance = Decimal(str(acc.current_balance))
            converted_balance = (raw_balance * acc_rate) / target_rate
            total_balance += converted_balance
            accounts_data.append(
                {
                    "id": acc.id,
                    "name": acc.name,
                    "balance": converted_balance,
                    "raw_balance": raw_balance,
                    "currency": acc_currency,
                }
            )

        # 2. Transactions
        start_dt = datetime.combine(start, datetime.min.time(), tzinfo=user_tz)
        end_dt = datetime.combine(end, datetime.max.time(), tzinfo=user_tz)

        tx_query = (
            self.db.query(Transaction, Category)
            .outerjoin(Category, Transaction.category_id == Category.id)
            .filter(
                Transaction.user_id == user.id,
                Transaction.transaction_date >= start_dt,
                Transaction.transaction_date <= end_dt,
            )
            .order_by(Transaction.transaction_date.asc())
            .all()
        )

        total_income = Decimal("0")
        total_expense = Decimal("0")
        category_sums: dict[str, Decimal] = {}
        monthly_stats: dict[str, dict[str, Any]] = {}
        recent_txs: list[dict[str, Any]] = []

        # Pre-populate all months in [start, end] so empty months are tracked explicitly
        curr_m = date(start.year, start.month, 1)
        while curr_m <= end:
            m_key = curr_m.strftime("%Y-%m")
            monthly_stats[m_key] = {
                "month_label": f"Tháng {curr_m.strftime('%m/%Y')}",
                "income": Decimal("0"),
                "expense": Decimal("0"),
                "tx_count": 0,
                "categories": {},
            }
            next_m = curr_m.month + 1
            next_y = curr_m.year
            if next_m > 12:
                next_m = 1
                next_y += 1
            curr_m = date(next_y, next_m, 1)

        for tx, cat in tx_query:
            amt = Decimal(str(tx.amount))
            raw_type = getattr(tx, "type", getattr(tx, "transaction_type", "EXPENSE"))
            tx_type = raw_type.value if hasattr(raw_type, "value") else str(raw_type)
            cat_name = cat.name if cat else "Khác"
            month_key = tx.transaction_date.strftime("%Y-%m")

            if month_key not in monthly_stats:
                monthly_stats[month_key] = {
                    "month_label": f"Tháng {tx.transaction_date.strftime('%m/%Y')}",
                    "income": Decimal("0"),
                    "expense": Decimal("0"),
                    "tx_count": 0,
                    "categories": {},
                }

            ms = monthly_stats[month_key]
            ms["tx_count"] += 1

            if tx_type == "INCOME":
                total_income += amt
                ms["income"] += amt
            elif tx_type == "EXPENSE":
                total_expense += amt
                ms["expense"] += amt
                category_sums[cat_name] = category_sums.get(cat_name, Decimal("0")) + amt
                ms["categories"][cat_name] = ms["categories"].get(cat_name, Decimal("0")) + amt

            recent_txs.append(
                {
                    "id": tx.id,
                    "date": tx.transaction_date.isoformat(),
                    "amount": amt,
                    "type": tx_type,
                    "category": cat_name,
                    "description": tx.description or "",
                }
            )

        net_savings = total_income - total_expense

        # Sort top categories
        sorted_cats = sorted(category_sums.items(), key=lambda item: item[1], reverse=True)
        top_categories = []
        for cat_name, amt in sorted_cats:
            pct = float((amt / total_expense * 100)) if total_expense > 0 else 0.0
            top_categories.append(
                {
                    "category": cat_name,
                    "amount": amt,
                    "percentage": round(pct, 1),
                }
            )

        # Monthly breakdown
        monthly_breakdown: list[dict[str, Any]] = []
        sorted_month_keys = sorted(monthly_stats.keys())
        prev_expense = None

        for m_key in sorted_month_keys:
            ms = monthly_stats[m_key]
            inc = ms["income"]
            exp = ms["expense"]
            savings = inc - exp
            top_cat = "Chưa có" if ms["tx_count"] == 0 else "Khác"
            if ms["categories"]:
                top_cat = max(ms["categories"].items(), key=lambda x: x[1])[0]

            change_pct = None
            if prev_expense is not None:
                if prev_expense > 0:
                    change_pct = round(float((exp - prev_expense) / prev_expense * 100), 1)
                elif exp > 0:
                    change_pct = 100.0
                else:
                    change_pct = 0.0
            prev_expense = exp

            m_cats = sorted(ms["categories"].items(), key=lambda x: x[1], reverse=True)
            m_top_cats = [
                {
                    "category": c,
                    "amount": a,
                    "percentage": round(float(a / exp * 100), 1) if exp > 0 else 0.0,
                }
                for c, a in m_cats
            ]

            monthly_breakdown.append(
                {
                    "month": ms["month_label"],
                    "income": inc,
                    "expense": exp,
                    "savings": savings,
                    "tx_count": ms["tx_count"],
                    "top_category": top_cat,
                    "top_categories": m_top_cats,
                    "change_pct": change_pct,
                }
            )

        # 3. Budgets
        budgets_query = self.db.query(Budget).filter(Budget.user_id == user.id).all()
        budgets_data = []
        for b in budgets_query:
            amt = Decimal(str(getattr(b, "total_limit", getattr(b, "amount", Decimal("0")))))
            b_spent = Decimal("0")
            for tx, _ in tx_query:
                raw_type = getattr(tx, "type", getattr(tx, "transaction_type", "EXPENSE"))
                tx_type = raw_type.value if hasattr(raw_type, "value") else str(raw_type)
                if tx_type == "EXPENSE":
                    b_spent += Decimal(str(tx.amount))

            pct = float((b_spent / amt * 100)) if amt > 0 else 0.0
            budgets_data.append(
                {
                    "id": b.id,
                    "name": b.name or "Ngân sách tháng",
                    "amount": amt,
                    "spent": b_spent,
                    "remaining": amt - b_spent,
                    "usage_pct": round(pct, 1),
                }
            )

        # 4. Goals
        goals_query = self.db.query(FinancialGoal).filter(FinancialGoal.user_id == user.id).all()
        goals_data = []
        for g in goals_query:
            target = Decimal(str(g.target_amount))
            current = Decimal("0")
            if hasattr(g, "contributions") and g.contributions:
                current = sum((Decimal(str(c.amount)) for c in g.contributions), Decimal("0"))
            else:
                current = Decimal(str(getattr(g, "current_amount", Decimal("0"))))
            pct = float((current / target * 100)) if target > 0 else 0.0
            goals_data.append(
                {
                    "id": g.id,
                    "name": g.name,
                    "target": target,
                    "current": current,
                    "progress_pct": round(pct, 1),
                }
            )

        # 5. Notifications
        notifs_query = (
            self.db.query(Notification)
            .filter(Notification.user_id == user.id)
            .order_by(Notification.created_at.desc())
            .limit(5)
            .all()
        )
        notifs_data = [
            {
                "id": n.id,
                "title": n.title,
                "message": getattr(n, "description", getattr(n, "message", "")),
            }
            for n in notifs_query
        ]

        # 6. Debts (Sổ nợ & Cho vay)
        debts_query = (
            self.db.query(Debt)
            .filter(Debt.user_id == user.id)
            .order_by(Debt.created_at.desc())
            .all()
        )
        debts_data = [
            {
                "id": d.id,
                "type": str(d.type).upper(),
                "counterparty_name": d.counterparty_name,
                "total_amount": Decimal(str(d.total_amount)),
                "remaining_amount": Decimal(str(d.remaining_amount)),
                "currency": (d.currency or "VND").upper(),
                "due_date": d.due_date.isoformat() if d.due_date else None,
                "status": str(d.status).upper(),
                "notes": d.notes or "",
            }
            for d in debts_query
        ]

        has_data = len(tx_query) > 0 or len(accounts_data) > 0 or len(debts_data) > 0

        return SQLUserDataContext(
            user_id=user.id,
            period_start=start,
            period_end=end,
            currency=currency.upper(),
            total_income=total_income,
            total_expense=total_expense,
            net_savings=net_savings,
            accounts=accounts_data,
            total_balance=total_balance,
            top_categories=top_categories,
            recent_transactions=recent_txs,
            budgets=budgets_data,
            goals=goals_data,
            notifications=notifs_data,
            debts=debts_data,
            transaction_count=len(tx_query),
            has_data=has_data,
            monthly_breakdown=monthly_breakdown,
        )
