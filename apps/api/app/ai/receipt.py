from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal, Protocol


@dataclass(frozen=True)
class ReceiptItem:
    name: str
    amount: int


@dataclass
class ReceiptDraft:
    merchant: str
    date: str
    total: int
    currency: str = "VND"
    items: list[dict[str, Any]] = field(default_factory=list)
    confirmed: bool = False
    source_ref: str | None = None


class ReceiptOCRProvider(Protocol):
    name: str

    def extract(self, source: str) -> dict[str, Any]: ...


class FakeReceiptOCRProvider:
    name = "fake-ocr"

    def __init__(self, result: dict[str, Any] | None = None, *, failure: Exception | None = None):
        self.result = result or {}
        self.failure = failure
        self.calls: list[str] = []

    def extract(self, source: str) -> dict[str, Any]:
        self.calls.append(source)
        if self.failure is not None:
            raise self.failure
        return dict(self.result)


@dataclass(frozen=True)
class ReceiptExtractionResult:
    status: Literal["SUCCESS", "LOW_CONFIDENCE", "VALIDATION_ERROR", "INSUFFICIENT_DATA"]
    merchant: str | None
    date: str | None
    total: int | None
    currency: str | None
    items: list[dict[str, Any]]
    reason: str
    duplicate: bool = False
    review_required: bool = False
    source: str = "ocr_candidate"

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "merchant": self.merchant,
            "date": self.date,
            "total": self.total,
            "currency": self.currency,
            "items": self.items,
            "reason": self.reason,
            "duplicate": self.duplicate,
            "review_required": self.review_required,
            "source": self.source,
        }


def _as_int(value: Any) -> int:
    if isinstance(value, bool):
        raise ValueError("numeric receipt fields must not be boolean")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        cleaned = value.replace(",", "").replace(".", "")
        try:
            return int(cleaned)
        except ValueError as exc:  # pragma: no cover - defensive branch
            raise ValueError("receipt total is not a valid integer amount") from exc
    raise ValueError("receipt total must be an integer amount")


def extract_receipt(payload: dict[str, Any]) -> ReceiptExtractionResult:
    if not isinstance(payload, dict):
        raise ValueError("receipt payload must be an object")

    merchant = str(payload.get("merchant") or "").strip()
    text_date = str(payload.get("date") or "").strip()
    currency = str(payload.get("currency") or "VND").upper()
    raw_items = payload.get("items") or []

    if not merchant:
        raise ValueError("receipt merchant is required")
    if len(currency) != 3 or not currency.isalpha():
        raise ValueError("receipt currency must be a three-letter code")
    if not text_date:
        raise ValueError("receipt date is required")
    try:
        datetime.strptime(text_date, "%Y-%m-%d")
    except ValueError as exc:  # pragma: no cover - defensive branch
        raise ValueError("receipt date must be ISO YYYY-MM-DD") from exc

    total_value = payload.get("total")
    try:
        total = _as_int(total_value)
    except ValueError as exc:
        raise ValueError("receipt total must be a valid positive amount") from exc
    if total <= 0:
        raise ValueError("receipt total must be greater than zero")

    if not isinstance(raw_items, list) or not raw_items:
        raise ValueError("receipt items are required")

    items: list[dict[str, Any]] = []
    amount_total = 0
    for item in raw_items:
        if not isinstance(item, dict):
            raise ValueError("receipt items must be objects")
        name = str(item.get("name") or "").strip()
        if not name:
            raise ValueError("receipt item names are required")
        item_amount = _as_int(item.get("amount"))
        if item_amount <= 0:
            raise ValueError("receipt item amounts must be greater than zero")
        amount_total += item_amount
        items.append({"name": name, "amount": item_amount})

    if abs(amount_total - total) > max(1, total * 0.02):
        return ReceiptExtractionResult(
            status="LOW_CONFIDENCE",
            merchant=merchant,
            date=text_date,
            total=total,
            currency=currency,
            items=items,
            reason=(
                "receipt totals do not reconcile cleanly; manual review is required "
                "before posting."
            ),
            review_required=True,
        )

    return ReceiptExtractionResult(
        status="SUCCESS",
        merchant=merchant,
        date=text_date,
        total=total,
        currency=currency,
        items=items,
        reason="extracted receipt candidate passed structured validation and is ready for review.",
        source="ocr_candidate",
    )


def prepare_receipt(
    payload: dict[str, Any],
    existing_records: list[dict[str, Any]],
    *,
    provider: ReceiptOCRProvider | None = None,
) -> ReceiptExtractionResult:
    extracted = payload
    if provider is not None:
        source = str(payload.get("source_ref") or payload.get("image_ref") or "")
        if not source:
            raise ValueError("receipt source reference is required for OCR")
        extracted = provider.extract(source)
    candidate = extract_receipt(extracted)
    duplicate = duplicate_receipt_check(existing_records, candidate)
    if duplicate:
        return ReceiptExtractionResult(
            status="LOW_CONFIDENCE",
            merchant=candidate.merchant,
            date=candidate.date,
            total=candidate.total,
            currency=candidate.currency,
            items=candidate.items,
            reason="A matching receipt already exists; review is required.",
            duplicate=True,
            review_required=True,
            source=candidate.source,
        )
    return candidate


def confirm_receipt(
    candidate: ReceiptExtractionResult,
    *,
    confirmed: bool,
    transaction_creator: Any,
) -> Any:
    if not confirmed:
        return None
    if candidate.status != "SUCCESS" or candidate.review_required or candidate.duplicate:
        raise ValueError("receipt must pass review before confirmation")
    return transaction_creator(
        merchant=candidate.merchant,
        transaction_date=candidate.date,
        amount=candidate.total,
        currency=candidate.currency,
        items=candidate.items,
    )


def duplicate_receipt_check(
    existing_records: list[dict[str, Any]], candidate: ReceiptExtractionResult
) -> bool:
    for record in existing_records:
        if (
            record.get("merchant") == candidate.merchant
            and record.get("date") == candidate.date
            and int(record.get("total", 0)) == candidate.total
        ):
            return True
    return False
