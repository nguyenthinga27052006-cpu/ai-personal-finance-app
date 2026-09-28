from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Literal

IntentType = Literal[
    "balance_query",
    "income_query",
    "expense_query",
    "income_analysis",
    "category_analysis",
    "spending_trend",
    "budget_status",
    "saving_goal_progress",
    "comparison_query",
    "spending_analysis",
    "budget_review",
    "affordability",
    "saving_advice",
    "debt_advice",
    "recurring_expense",
    "unusual_transaction",
    "financial_forecast",
    "knowledge",
    "app_faq",
    "greeting",
    "unsupported_request",
    "general_query",
    "time_reference_query",
]


@dataclass(frozen=True)
class QueryEntities:
    category: str | None = None
    amount: float | None = None
    time_phrase: str | None = None
    raw_query: str = ""


@dataclass(frozen=True)
class QueryTimeRange:
    type: str  # "day" | "week" | "month" | "quarter" | "year"
    start: date
    end: date
    is_multi_month: bool = False


@dataclass(frozen=True)
class QueryPlan:
    intent: IntentType
    confidence: float
    entities: QueryEntities
    time_range: QueryTimeRange
    requires_sql: bool
    requires_knowledge: bool
    sub_queries: list[dict[str, Any]] = field(default_factory=list)


class IntentDetector:
    """Classifies financial questions into specific high-precision intents and parses date/entity constraints."""

    @staticmethod
    def resolve_time_reference(question: str, today: date | None = None) -> str:
        """Deterministic resolver for calendar and relative time reference questions without invoking LLM or SQL."""
        if today is None:
            today = date.today()
        q = question.lower().strip()

        # Pattern 1: (tháng trước|trước) tháng X
        match_prev = re.search(r"(?:tháng\s*trước|trước)\s*tháng\s*(\d{1,2})", q)
        if match_prev:
            base_m = int(match_prev.group(1))
            target_m = 12 if base_m == 1 else base_m - 1
            prefix = "Tháng trước" if "tháng trước" in q else "Trước"
            if base_m == 1:
                return f"{prefix} tháng 1 là tháng 12 năm trước."
            return f"{prefix} tháng {base_m} là tháng {target_m}."

        # Pattern 2: (tháng sau|sau) tháng X
        match_next = re.search(r"(?:tháng\s*sau|sau)\s*tháng\s*(\d{1,2})", q)
        if match_next:
            base_m = int(match_next.group(1))
            target_m = 1 if base_m == 12 else base_m + 1
            prefix = "Tháng sau" if "tháng sau" in q else "Sau"
            if base_m == 12:
                return f"{prefix} tháng 12 là tháng 1 năm sau."
            return f"{prefix} tháng {base_m} là tháng {target_m}."

        # Pattern 3: tháng trước là tháng mấy / tháng trước là tháng nào
        if "tháng trước" in q:
            target_m = 12 if today.month == 1 else today.month - 1
            target_y = today.year - 1 if today.month == 1 else today.year
            return f"Tháng trước là tháng {target_m}/{target_y} (do hiện tại đang là tháng {today.month}/{today.year})."

        # Pattern 4: tháng sau là tháng mấy / tháng sau là tháng nào
        if "tháng sau" in q or "tháng tới" in q:
            target_m = 1 if today.month == 12 else today.month + 1
            target_y = today.year + 1 if today.month == 12 else today.year
            return f"Tháng sau là tháng {target_m}/{target_y} (do hiện tại đang là tháng {today.month}/{today.year})."

        # Pattern 5: hôm nay
        if "hôm nay" in q:
            d_str = today.strftime("%d/%m/%Y")
            return f"Hôm nay là ngày {d_str}."

        # Pattern 6: tháng này / bây giờ
        if "tháng này" in q or "bây giờ" in q or "hiện tại" in q:
            return f"Hiện tại đang là tháng {today.month}/{today.year}."

        return f"Mốc thời gian bạn hỏi là tháng {today.month}/{today.year}."

    @staticmethod
    def detect(question: str) -> IntentType:
        lowered = question.lower().strip()

        # 1. Greetings
        if lowered in {"hi", "hello", "xin chào", "chào bạn", "chào", "hey", "halo"}:
            return "greeting"

        # 1.1 Pure Time Reference & Calendar Queries (Deterministic, no financial/SQL/Chroma needed)
        has_financial_keywords = any(
            kw in lowered
            for kw in [
                "tiêu", "chi", "thu", "lương", "số dư", "tài khoản", "tiết kiệm",
                "ngân sách", "mua", "nợ", "bao nhiêu tiền", "hóa đơn", "giao dịch",
                "thặng dư", "vượt hạn mức", "hạn mức", "tiến độ"
            ]
        )
        if not has_financial_keywords:
            time_ref_patterns = [
                r"(?:tháng\s*trước|trước|tháng\s*sau|sau)\s*tháng\s*\d+",
                r"tháng\s*trước\s*là\s*tháng\s*(?:mấy|nào)",
                r"tháng\s*sau\s*là\s*tháng\s*(?:mấy|nào)",
                r"hôm\s*nay\s*là\s*(?:ngày|thứ|tháng)\s*(?:mấy|nào|gì)",
                r"bây\s*giờ\s*là\s*tháng\s*(?:mấy|nào)",
                r"tháng\s*\d+\s*là\s*tháng\s*(?:mấy|nào)",
                r"trước\s*tháng\s*\d+\s*(?:ý|đó|nhé|nha|ạ)?$",
                r"sau\s*tháng\s*\d+\s*(?:ý|đó|nhé|nha|ạ)?$",
                r"trước\s*tháng\s*\d+\s*thì\s*sao",
                r"sau\s*tháng\s*\d+\s*thì\s*sao",
                r"tháng\s*trước\s*là\s*tháng\s*mấy",
                r"tháng\s*sau\s*là\s*tháng\s*mấy",
                r"tháng\s*(?:mấy|nào)\s*(?:nhỉ|vậy|thế|đó|\?)?$",
            ]
            if any(re.search(p, lowered) for p in time_ref_patterns):
                return "time_reference_query"

        is_personal = any(
            p in lowered
            for p in [
                "của tôi",
                "của mình",
                "với số dư",
                "với tổng dư",
                "thặng dư",
                "ngân sách hiện có",
                "tài khoản của tôi",
                "tháng này của tôi",
            ]
        )

        # 2. Hybrid queries prioritize advice/affordability over generic keywords
        if any(
            kw in lowered
            for kw in [
                "đủ tiền",
                "mua được",
                "mua laptop",
                "mua điện thoại",
                "mua xe",
                "muốn mua",
                "có nên mua",
                "có thể bắt đầu",
                "phương án chi tiêu",
                "afford",
            ]
        ):
            return "affordability"
        if any(kw in lowered for kw in ["trả nợ", "khoản nợ", "nợ nào"]):
            return "debt_advice"
        if any(kw in lowered for kw in ["vượt hạn mức", "mục tiêu tiết kiệm"]):
            return "budget_review"
        if any(
            kw in lowered
            for kw in [
                "nên giảm",
                "nên tăng",
                "giảm chi tiêu",
                "tăng chi tiêu",
                "chi tiêu mục nào",
                "tiết kiệm",
                "phân bổ",
                "tối ưu",
                "giảm chi",
                "cắt giảm",
                "trích",
                "xây dựng",
            ]
        ):
            return "saving_advice"

        # 3. Knowledge queries (Educational / Framework / Financial rules)
        if any(
            kw in lowered
            for kw in [
                "50/30/20 là gì",
                "quỹ khẩn cấp là gì",
                "tuyết lăn là gì",
                "tuyết lở là gì",
                "snowball",
                "avalanche",
                "khác gì",
                "phương pháp trả nợ",
                "cẩm nang",
                "lạm phát",
                "định nghĩa",
            ]
        ) or (
            ("là gì" in lowered or "khái niệm" in lowered or "definition" in lowered)
            and not any(
                b in lowered
                for b in [
                    "số dư",
                    "balance",
                    "tài khoản",
                    "ngân sách",
                    "thu nhập",
                    "tôi",
                    "tên",
                    "mình",
                    "tuổi",
                ]
            )
        ):
            return "knowledge"

        # 4. Category Spending & Breakdown ("Tôi tiêu nhiều nhất ở đâu", "ăn uống", "danh mục")
        if any(kw in lowered for kw in ["ở đâu", "danh mục", "khoản nào", "top chi tiêu"]) or (
            any(
                kw in lowered
                for kw in ["ăn uống", "mua sắm", "đi lại", "giải trí", "hóa đơn", "tiền nhà"]
            )
            and any(
                kw in lowered
                for kw in ["chi tiêu", "đã tiêu", "tiêu bao nhiêu", "tổng chi", "tiêu"]
            )
        ):
            return "spending_analysis"

        # 5. Saving Advice & Optimization
        if any(
            kw in lowered
            for kw in [
                "tiết kiệm",
                "tối ưu chi tiêu",
                "giảm chi phí",
                "lời khuyên",
                "tư vấn",
                "cách tiết kiệm",
                "tiết kiệm chi phí",
                "giảm chi",
                "cắt giảm",
                "reduce expense",
                "làm sao để giảm",
                "làm thế nào để giảm",
            ]
        ):
            return "saving_advice"

        # 6. Multi-month / Comparison & Analytical Extreme queries
        if any(
            kw in lowered
            for kw in [
                "so sánh",
                "so sanh",
                "biến động",
                "tăng giảm",
                "các tháng",
                "xu hướng",
                "compare",
                "comparison",
                "tháng nào",
                "năm nào",
                "nhiều nhất",
                "ít nhất",
                "cao nhất",
                "thấp nhất",
                "max",
                "min",
                "kỷ lục",
            ]
        ) or re.search(r"\d+\s*tháng", lowered):
            return "comparison_query"

        # 7. Balance Queries
        if any(
            kw in lowered
            for kw in [
                "số dư",
                "tài khoản",
                "balance",
                "my balance",
                "current balance",
                "tổng dư",
                "còn bao nhiêu tiền",
                "bao nhiêu tiền trong tài khoản",
            ]
        ):
            return "balance_query"

        # 8. Income Queries
        if any(
            kw in lowered
            for kw in [
                "thu nhập",
                "lương",
                "income",
                "receive",
                "received",
                "earned",
                "nhận được",
                "tiền vào",
                "kiếm được",
            ]
        ):
            return "income_query"

        # 9. Expense / Spending Queries
        if any(
            kw in lowered
            for kw in [
                "chi tiêu",
                "đã tiêu",
                "tổng chi",
                "spend",
                "spent",
                "expense",
                "expenses",
                "tiền ra",
                "tiêu hết",
                "khoản chi",
                "tiêu nhiều tiền",
                "chi bao nhiêu",
                "tiêu bao nhiêu",
                "đã chi",
                "tôi chi",
                "tôi tiêu",
                "khoản nào tôi chi",
                "khoản nào chi",
                "mục nào chi",
            ]
        ):
            return "expense_query"

        # 10. Budget & Goal Review Queries
        if any(
            kw in lowered
            for kw in [
                "ngân sách",
                "budget",
                "vượt hạn mức",
                "hạn mức",
                "mục tiêu",
                "tiến độ",
                "goal",
                "status",
            ]
        ):
            return "budget_review"

        # 11. Affordability Queries
        if any(
            kw in lowered
            for kw in [
                "đủ tiền",
                "mua được",
                "mua laptop",
                "mua điện thoại",
                "có nên mua",
                "chi trả",
                "afford",
                "can i buy",
                "can i afford",
            ]
        ):
            return "affordability"

        # 12. Debt Advice
        if any(kw in lowered for kw in ["nợ", "trả nợ", "khoản nợ", "lãi suất"]):
            return "debt_advice"

        # 13. App FAQ
        if any(kw in lowered for kw in ["ứng dụng", "tính năng", "bảo mật", "cách dùng", "faq"]):
            return "app_faq"

        return "general_query"

    @staticmethod
    def parse_date_range(question: str, today: date | None = None) -> tuple[date, date, bool]:
        """
        Extracts start date, end date, and multi_month flag from a natural language user question.
        Returns (start_date, end_date, is_multi_month).
        """
        if today is None:
            today = date.today()

        q = question.lower().strip()

        # 0a. Match clarification pattern: "ý tôi là ... là tháng X" or "ý tôi là tháng X" or "là tháng X"
        clarify = re.search(
            r"(?:ý tôi là.*?|là\s*)tháng\s*(\d{1,2})(?:\s*ý|\s*đó|\s*ạ|\s*nhé)?$", q
        )
        if clarify:
            m = int(clarify.group(1))
            y = today.year
            if 1 <= m <= 12:
                start = date(y, m, 1)
                next_m = date(y + (m == 12), 1 if m == 12 else m + 1, 1)
                end = next_m - timedelta(days=1)
                return start, end, False

        # 0b. Match relative to month: "tháng trước tháng X" or "trước tháng X" (e.g. tháng trước tháng 8 -> tháng 7)
        match_rel_prev = re.search(
            r"(?:tháng\s*trước|trước)\s*tháng\s*(\d{1,2})(?:\s*[/ năm]*\s*(\d{4}))?", q
        )
        if match_rel_prev:
            base_m = int(match_rel_prev.group(1))
            y = int(match_rel_prev.group(2)) if match_rel_prev.group(2) else today.year
            m = base_m - 1
            if m == 0:
                m = 12
                y -= 1
            if 1 <= m <= 12:
                start = date(y, m, 1)
                next_m = date(y + (m == 12), 1 if m == 12 else m + 1, 1)
                end = next_m - timedelta(days=1)
                return start, end, False

        # 1. Match specific month FIRST: "tháng X" or "tháng X/YYYY" (e.g. tháng 5, tháng 08, tháng 8/2026)
        match_specific_month = re.search(r"tháng\s*(\d{1,2})(?:\s*[/ năm]*\s*(\d{4}))?", q)
        if match_specific_month:
            m = int(match_specific_month.group(1))
            y = int(match_specific_month.group(2)) if match_specific_month.group(2) else today.year
            if 1 <= m <= 12:
                start = date(y, m, 1)
                next_m = date(y + (m == 12), 1 if m == 12 else m + 1, 1)
                end = next_m - timedelta(days=1)
                return start, end, False

        # 2. Match "tháng trước" or "tháng vừa rồi"
        if "tháng trước" in q or "tháng vừa rồi" in q:
            m = today.month - 1
            y = today.year
            if m == 0:
                m = 12
                y -= 1
            start = date(y, m, 1)
            next_m = date(y + (m == 12), 1 if m == 12 else m + 1, 1)
            end = next_m - timedelta(days=1)
            return start, end, False

        # 3. Check for historical extreme analytical questions without specific month ("tháng nào", "nhiều nhất", "ít nhất", etc.)
        if any(
            kw in q
            for kw in [
                "tháng nào",
                "nhiều nhất",
                "ít nhất",
                "cao nhất",
                "thấp nhất",
                "max",
                "min",
                "kỷ lục",
            ]
        ):
            num_months = 12
            start_month = today.month - num_months + 1
            start_year = today.year
            while start_month <= 0:
                start_month += 12
                start_year -= 1
            start = date(start_year, start_month, 1)

            next_month = date(
                today.year + (today.month == 12), 1 if today.month == 12 else today.month + 1, 1
            )
            end = next_month - timedelta(days=1)
            return start, end, True

        # 4. Match "X tháng gần nhất" / "X tháng qua" / "X tháng vừa qua" / "X tháng"
        match_recent_months = re.search(r"(\d+)\s*tháng", q)
        if match_recent_months:
            num_months = int(match_recent_months.group(1))
            num_months = max(1, min(num_months, 12))  # cap between 1 and 12
            start_month = today.month - num_months + 1
            start_year = today.year
            while start_month <= 0:
                start_month += 12
                start_year -= 1
            start = date(start_year, start_month, 1)

            next_month = date(
                today.year + (today.month == 12), 1 if today.month == 12 else today.month + 1, 1
            )
            end = next_month - timedelta(days=1)
            return start, end, num_months > 1

        # 3. Match "tháng trước" or "tháng vừa rồi"
        if "tháng trước" in q or "tháng vừa rồi" in q:
            m = today.month - 1
            y = today.year
            if m == 0:
                m = 12
                y -= 1
            start = date(y, m, 1)
            next_m = date(y + (m == 12), 1 if m == 12 else m + 1, 1)
            end = next_m - timedelta(days=1)
            return start, end, False

        # 4. Match "hôm nay" / "hôm qua"
        if "hôm nay" in q:
            return today, today, False
        if "hôm qua" in q:
            yesterday = today - timedelta(days=1)
            return yesterday, yesterday, False

        # 5. Match "tuần này"
        if "tuần này" in q:
            start = today - timedelta(days=today.weekday())
            end = start + timedelta(days=6)
            return start, end, False

        # 6. Match "tháng này" or "tháng hiện tại"
        if "tháng này" in q or "tháng hiện tại" in q:
            start = date(today.year, today.month, 1)
            next_m = date(
                today.year + (today.month == 12), 1 if today.month == 12 else today.month + 1, 1
            )
            end = next_m - timedelta(days=1)
            return start, end, False

        # Default fallback: current month
        start = date(today.year, today.month, 1)
        next_m = date(
            today.year + (today.month == 12), 1 if today.month == 12 else today.month + 1, 1
        )
        end = next_m - timedelta(days=1)
        return start, end, False

    @classmethod
    def create_plan(
        cls,
        question: str,
        today: date | None = None,
        history: list[Any] | None = None,
    ) -> QueryPlan:
        """Decomposes user question into a structured QueryPlan with entity/time parsing and optional follow-up context resolution."""
        intent = cls.detect(question)
        start, end, is_multi = cls.parse_date_range(question, today=today)
        lowered = question.lower().strip()

        is_followup_phrase = (
            lowered.startswith("còn ")
            or "thế còn" in lowered
            or "vậy còn" in lowered
            or "thì sao" in lowered
        ) and not any(kw in lowered for kw in ["còn bao nhiêu tiền", "còn tiền", "còn dư", "còn nợ"])

        # Check if follow-up refers to relative month based on previous user query (e.g. "Còn tháng trước?")
        if history and (
            "còn tháng trước" in lowered
            or "tháng trước đó" in lowered
            or ("tháng trước" in lowered and is_followup_phrase)
        ):
            prev_user_month = None
            prev_user_year = today.year if today else date.today().year
            for msg in reversed(history):
                role = getattr(msg, "role", None) or (msg.get("role") if isinstance(msg, dict) else None)
                if role and role != "user":
                    continue
                content = (
                    getattr(msg, "content", "")
                    if hasattr(msg, "content")
                    else str(msg.get("content", "") if isinstance(msg, dict) else msg)
                )
                if content:
                    m_match = re.search(r"tháng\s*(\d{1,2})(?:\s*[/ năm]*\s*(\d{4}))?", content.lower())
                    if m_match:
                        prev_user_month = int(m_match.group(1))
                        if m_match.group(2):
                            prev_user_year = int(m_match.group(2))
                        break
            if prev_user_month and 1 <= prev_user_month <= 12:
                target_m = 12 if prev_user_month == 1 else prev_user_month - 1
                target_y = prev_user_year - 1 if prev_user_month == 1 else prev_user_year
                start = date(target_y, target_m, 1)
                next_m = date(target_y + (target_m == 12), 1 if target_m == 12 else target_m + 1, 1)
                end = next_m - timedelta(days=1)
                is_multi = False

        # Entity extraction
        cat_match = None
        for cat in [
            "ăn uống",
            "mua sắm",
            "đi lại",
            "giải trí",
            "hóa đơn",
            "tiền nhà",
            "y tế",
            "công nghệ",
        ]:
            if cat in lowered:
                cat_match = cat
                break

        # Follow-up context inheritance from history (ONLY inspect USER messages, NEVER assistant!)
        prev_intent = None
        prev_cat = None
        if history:
            for msg in reversed(history):
                role = getattr(msg, "role", None) or (msg.get("role") if isinstance(msg, dict) else None)
                if role and role != "user":
                    continue
                content = (
                    getattr(msg, "content", "")
                    if hasattr(msg, "content")
                    else str(msg.get("content", "") if isinstance(msg, dict) else msg)
                )
                if content:
                    content_lowered = content.lower()
                    for cat in [
                        "ăn uống",
                        "mua sắm",
                        "đi lại",
                        "giải trí",
                        "hóa đơn",
                        "tiền nhà",
                        "y tế",
                        "công nghệ",
                    ]:
                        if cat in content_lowered:
                            prev_cat = cat
                            break
                    detected_prev = cls.detect(content)
                    if detected_prev not in (
                        "general_query",
                        "greeting",
                        "knowledge",
                        "time_reference_query",
                    ):
                        prev_intent = detected_prev
                    if prev_cat and prev_intent:
                        break

        # If it's a follow-up or general query and previous turn had a specific intent, inherit context (unless it's personal chat or specific non-financial query)
        is_personal_chat = any(
            w in lowered for w in ["tên", "tuổi", "bạn là ai", "tôi là ai", "ai đấy", "ai đây"]
        )

        if (
            (is_followup_phrase or intent == "general_query")
            and prev_intent
            and intent not in (
                "knowledge",
                "greeting",
                "app_faq",
                "time_reference_query",
                "balance_query",
                "income_query",
            )
        ):
            intent = prev_intent
        if (
            cat_match is None
            and prev_cat
            and intent not in ("knowledge", "greeting", "app_faq", "time_reference_query")
            and (
                is_followup_phrase
                or intent in ("spending_analysis", "expense_query", "category_analysis")
            )
        ):
            cat_match = prev_cat

        amt_match = None
        match_amt = re.search(r"(\d+)\s*(triệu|tr|k|đ|vnd)", lowered)
        if match_amt:
            val = float(match_amt.group(1))
            unit = match_amt.group(2)
            if unit in ("triệu", "tr"):
                amt_match = val * 1_000_000
            elif unit == "k":
                amt_match = val * 1_000

        is_personal_financial = any(
            p in lowered
            for p in [
                "của tôi",
                "của mình",
                "với số dư",
                "với tổng dư",
                "thặng dư",
                "ngân sách hiện có",
                "tài khoản của tôi",
                "tháng này của tôi",
                "tôi chi",
                "tôi tiêu",
                "tôi thu",
                "tiêu bao nhiêu",
                "chi bao nhiêu",
                "thu bao nhiêu",
                "lương của tôi",
                "số dư của tôi",
            ]
        )
        requires_sql = intent not in (
            "knowledge",
            "greeting",
            "app_faq",
            "time_reference_query",
        ) and (intent != "general_query" or is_personal_financial)
        requires_knowledge = intent in (
            "knowledge",
            "saving_advice",
            "debt_advice",
            "affordability",
            "app_faq",
        ) or ("và" in lowered and "như thế nào" in lowered)

        sub_queries = []
        if "và" in lowered and ("làm sao" in lowered or "thế nào" in lowered):
            sub_queries.append(
                {"type": "sql", "query": "Retrieving financial stats from PostgreSQL"}
            )
            sub_queries.append({"type": "knowledge", "query": "Searching advice knowledge base"})

        return QueryPlan(
            intent=intent,
            confidence=0.95 if intent != "general_query" else 0.60,
            entities=QueryEntities(
                category=cat_match,
                amount=amt_match,
                raw_query=question,
            ),
            time_range=QueryTimeRange(
                type="month",
                start=start,
                end=end,
                is_multi_month=is_multi,
            ),
            requires_sql=requires_sql,
            requires_knowledge=requires_knowledge,
            sub_queries=sub_queries,
        )
