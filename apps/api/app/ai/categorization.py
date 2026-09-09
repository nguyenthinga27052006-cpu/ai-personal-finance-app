from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.ai.context import ExecutionContext
from app.ai.gateway import AIGateway
from app.ai.guardrails import validate_untrusted_input
from app.catalog.service import lookup_merchant, visible_categories
from app.db.models import User


@dataclass(frozen=True)
class CategoryClassification:
    category: str
    confidence: float
    reason: str
    status: Literal["SUCCESS", "LOW_CONFIDENCE", "VALIDATION_ERROR"] = "SUCCESS"
    source: str = "deterministic_rule"

    def as_dict(self) -> dict[str, object]:
        return {
            "category": self.category,
            "confidence": self.confidence,
            "reason": self.reason,
            "status": self.status,
            "source": self.source,
        }


class CategorizationOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["SUCCESS", "LOW_CONFIDENCE", "VALIDATION_ERROR"]
    category: str
    confidence: float = Field(ge=0, le=1)
    reason: str = Field(min_length=1, max_length=1000)


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").strip().lower()).strip()


def _merchant_alias_map() -> dict[str, str]:
    return {
        "starbucks": "Food",
        "coffee": "Food",
        "cafe": "Food",
        "mcdonald": "Food",
        "burger king": "Food",
        "grab": "Transportation",
        "gojek": "Transportation",
        "petrol": "Transportation",
        "shell": "Transportation",
        "airline": "Travel",
        "hotel": "Travel",
        "pharmacy": "Health",
        "clinic": "Health",
        "netflix": "Entertainment",
        "spotify": "Entertainment",
        "rent": "Housing",
        "electricity": "Utilities",
    }


def validate_category_candidate(db: Session, user: User, category_name: str) -> bool:
    normalized = _normalize(category_name)
    if not normalized:
        return False
    for category in visible_categories(db, user):
        if _normalize(category.name) == normalized:
            return True
    return False


def _gateway_fallback(
    db: Session,
    user: User,
    merchant_text: str,
    transaction_type: str,
    gateway: AIGateway,
) -> CategoryClassification:
    context = ExecutionContext(
        db=db,
        user=user,
        request_id="categorization-fallback",
        feature="categorization",
        allowed_tools=frozenset(),
    )
    result = gateway.execute(
        context,
        task="categorization",
        start=user.created_at.date(),
        end=user.created_at.date(),
        currency=user.default_currency,
        tools=[],
        user_input=f"merchant={merchant_text}; transaction_type={transaction_type}",
        output_model=CategorizationOutput,
    )
    output = result.output
    if not isinstance(output, CategorizationOutput):
        raise ValueError("categorization provider returned an invalid contract")
    if not validate_category_candidate(db, user, output.category):
        return CategoryClassification(
            category="Uncategorized",
            confidence=output.confidence,
            reason="Provider category is not visible to the authenticated user.",
            status="VALIDATION_ERROR",
            source="gateway",
        )
    status = output.status
    if output.confidence < 0.7 and status == "SUCCESS":
        status = "LOW_CONFIDENCE"
    return CategoryClassification(
        category=output.category,
        confidence=output.confidence,
        reason=output.reason,
        status=status,
        source="gateway",
    )


def categorize_transaction(
    db: Session,
    user: User,
    merchant_text: str,
    transaction_type: str = "expense",
    gateway: AIGateway | None = None,
) -> CategoryClassification:
    validate_untrusted_input(merchant_text)
    if not merchant_text or not merchant_text.strip():
        raise ValueError("merchant text must not be empty")

    lowered = _normalize(merchant_text)
    alias_map = _merchant_alias_map()
    for key, category in alias_map.items():
        if key in lowered:
            if not validate_category_candidate(db, user, category):
                continue
            return CategoryClassification(
                category=category,
                confidence=0.94,
                reason=(
                    f"merchant alias match for '{merchant_text}' resolved to "
                    f"{category} via deterministic merchant alias policy."
                ),
                status="SUCCESS",
                source="merchant_alias",
            )

    merchant = lookup_merchant(db, merchant_text)
    if merchant and merchant.category_hint_obj is not None:
        category = merchant.category_hint_obj.name
        if validate_category_candidate(db, user, category):
            return CategoryClassification(
                category=category,
                confidence=0.88,
                reason=(
                    f"merchant catalog match for '{merchant_text}' resolved to the "
                    "canonical category on the merchant record."
                ),
                source="merchant_catalog",
            )

    for category in visible_categories(db, user):
        if _normalize(category.name) in lowered or lowered in _normalize(category.name):
            return CategoryClassification(
                category=category.name,
                confidence=0.72,
                reason=(
                    f"name-based deterministic match for '{merchant_text}' "
                    f"resolved against the allowed category '{category.name}'."
                ),
                source="category_name",
            )

    if gateway is not None:
        return _gateway_fallback(db, user, merchant_text, transaction_type, gateway)

    return CategoryClassification(
        category="Uncategorized",
        confidence=0.28,
        reason=(
            "deterministic rules could not resolve a safe category; requires user confirmation or "
            "controlled fallback before posting financial data."
        ),
        status="LOW_CONFIDENCE",
        source="llm_fallback_required",
    )
