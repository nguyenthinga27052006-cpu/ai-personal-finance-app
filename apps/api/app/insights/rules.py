from decimal import Decimal

SPENDING_CHANGE_THRESHOLD = Decimal("0.20")
SAVING_RATE_CHANGE_THRESHOLD = Decimal("0.10")
CATEGORY_DOMINANCE_THRESHOLD = Decimal("0.50")
BUDGET_RISK_THRESHOLD = Decimal("0.80")
CASHFLOW_DEFICIT_THRESHOLD = Decimal("0")
WEEKEND_SHARE_THRESHOLD = Decimal("0.40")
POSITIVE_SAVING_RATE_THRESHOLD = Decimal("0.20")
ANOMALY_RULES = frozenset({"period_spending_vs_rolling_3", "large_single_merchant_expense"})
