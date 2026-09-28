from __future__ import annotations

import base64
from dataclasses import dataclass, field
from datetime import date, datetime
import io
import logging
import re
from typing import Any, Literal, Protocol

logger = logging.getLogger("app.ai.ocr")


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
    confidence: float = 0.95
    field_confidence: dict[str, float] = field(default_factory=dict)
    total_candidates: list[dict[str, Any]] = field(default_factory=list)
    validation_checks: dict[str, Any] = field(default_factory=dict)
    provider: str = "local_rapidocr"
    model: str = "rapidocr_onnx"

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
            "confidence": self.confidence,
            "field_confidence": self.field_confidence,
            "total_candidates": self.total_candidates,
            "validation_checks": self.validation_checks,
            "provider": self.provider,
            "model": self.model,
        }


def _as_int(value: Any) -> int:
    if isinstance(value, bool):
        raise ValueError("numeric receipt fields must not be boolean")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        cleaned = value.replace(",", "").replace(".", "").strip()
        try:
            return int(cleaned)
        except ValueError as exc:
            raise ValueError("receipt total is not a valid integer amount") from exc
    raise ValueError("receipt total must be an integer amount")


# =====================================================================
# 1. VIETNAMESE AMOUNT IN WORDS PARSER (Section XI)
# =====================================================================
class VietnameseAmountInWordsParser:
    """Parses Vietnamese amount-in-words text (e.g. 'Năm triệu không trăm chín mươi nghìn đồng') into integer amounts."""

    DIGITS: dict[str, int] = {
        "không": 0, "khong": 0,
        "một": 1, "mot": 1, "mốt": 1,
        "hai": 2,
        "ba": 3,
        "bốn": 4, "bon": 4, "tư": 4, "tu": 4,
        "năm": 5, "nam": 5, "lăm": 5, "lam": 5,
        "sáu": 6, "sau": 6,
        "bảy": 7, "bay": 7, "bẩy": 7,
        "tám": 8, "tam": 8,
        "chín": 9, "chin": 9,
    }

    def parse(self, raw_text: str) -> int | None:
        if not raw_text or not isinstance(raw_text, str):
            return None
        text = raw_text.lower()
        # Remove label prefixes
        text = re.sub(r".*?(?:bằng chữ|viết bằng chữ)[\s:]*", "", text)
        # Remove trailing currency/terminator
        text = re.sub(r"[\s.,]*(?:đồng|chẵn|vnd|vnđ|tiền|toàn\s*bộ).*$", "", text)

        words = re.findall(r"[a-zà-ỹ]+", text)
        if not words:
            return None

        total = 0
        current_group = 0
        current_num = 0

        i = 0
        while i < len(words):
            w = words[i]
            if w in self.DIGITS:
                current_num = self.DIGITS[w]
            elif w in ("mười", "muoi", "mươi"):
                if current_num == 0:
                    current_num = 10
                else:
                    current_num *= 10
                current_group += current_num
                current_num = 0
            elif w in ("trăm", "tram"):
                current_group += current_num * 100
                current_num = 0
            elif w in ("nghìn", "nghin", "ngàn", "ngan"):
                current_group += current_num
                total += current_group * 1000
                current_group = 0
                current_num = 0
            elif w in ("triệu", "trieu"):
                current_group += current_num
                total += current_group * 1000000
                current_group = 0
                current_num = 0
            elif w in ("tỷ", "ty", "tỉ"):
                current_group += current_num
                total += current_group * 1000000000
                current_group = 0
                current_num = 0
            elif w in ("lẻ", "le", "linh"):
                pass
            i += 1

        current_group += current_num
        total += current_group
        return total if total > 0 else None


# =====================================================================
# 2. IMAGE PREPROCESSOR (Section IV & XIII)
# =====================================================================
class ImagePreprocessor:
    """Preprocesses receipt images for single or multi-pass OCR recognition."""

    @staticmethod
    def preprocess(image_bytes: bytes, pass_num: int = 1) -> tuple[bytes, dict[str, Any]]:
        import cv2
        import numpy as np

        info: dict[str, Any] = {"pass": pass_num, "modified": False}
        try:
            arr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if img is None:
                return image_bytes, info

            h, w = img.shape[:2]
            info["original_dimensions"] = (w, h)

            # Pass 1: Upscale if small to ensure clear receipt text detection
            if pass_num == 1:
                if max(h, w) < 1200:
                    scale = 1200.0 / max(h, w)
                    img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)
                    info["upscaled"] = True
                    info["modified"] = True
                _, buf = cv2.imencode(".png", img)
                return buf.tobytes(), info

            # Pass 2: Grayscale + CLAHE Adaptive Contrast Enhancement + Bilateral Filter (Denoise)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # Denoise while keeping character edges crisp
            denoised = cv2.bilateralFilter(gray, d=7, sigmaColor=50, sigmaSpace=50)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)

            # Mild unsharp mask to boost character contrast
            gaussian = cv2.GaussianBlur(enhanced, (0, 0), 2.0)
            sharpened = cv2.addWeighted(enhanced, 1.5, gaussian, -0.5, 0)

            info["modified"] = True
            info["pass2_clahe"] = True
            _, buf = cv2.imencode(".png", sharpened)
            return buf.tobytes(), info
        except Exception as exc:
            logger.warning("Image preprocessing failed: %s, using raw bytes", exc)
            return image_bytes, info


# =====================================================================
# 3. LAYOUT & CANDIDATE SCORER (Sections VI, VII, VIII, IX, X, XI, XII)
# =====================================================================
@dataclass
class LayoutBox:
    bbox: list[list[float]]
    text: str
    confidence: float
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    y_center: float
    height: float
    width: float


@dataclass
class LayoutLine:
    boxes: list[LayoutBox]
    text: str
    y_center: float
    y_min: float
    y_max: float
    x_min: float
    x_max: float


class LayoutExtractor:
    """Extracts layout boxes and merges them into horizontally-aligned layout lines."""

    @staticmethod
    def extract_lines(ocr_results: list[Any]) -> tuple[list[LayoutLine], float, float]:
        boxes: list[LayoutBox] = []
        max_x = 100.0
        max_y = 100.0

        for item in ocr_results:
            if not item or len(item) < 2:
                continue
            raw_box = item[0]
            text = str(item[1]).strip()
            conf = float(item[2]) if len(item) > 2 and item[2] is not None else 0.8
            if not text:
                continue

            try:
                xs = [p[0] for p in raw_box]
                ys = [p[1] for p in raw_box]
                x_min, x_max = min(xs), max(xs)
                y_min, y_max = min(ys), max(ys)
                max_x = max(max_x, x_max)
                max_y = max(max_y, y_max)
                boxes.append(
                    LayoutBox(
                        bbox=raw_box,
                        text=text,
                        confidence=conf,
                        x_min=x_min,
                        x_max=x_max,
                        y_min=y_min,
                        y_max=y_max,
                        y_center=(y_min + y_max) / 2.0,
                        height=y_max - y_min,
                        width=x_max - x_min,
                    )
                )
            except Exception:
                continue

        if not boxes:
            return [], max_y, max_x

        # Sort top-to-bottom by y_center
        boxes.sort(key=lambda b: b.y_center)

        lines: list[LayoutLine] = []
        for box in boxes:
            placed = False
            for line in lines:
                # Same line check: vertical center close enough relative to line height
                avg_h = max(box.height, (line.y_max - line.y_min), 10.0)
                if abs(box.y_center - line.y_center) <= avg_h * 0.55:
                    line.boxes.append(box)
                    line.y_min = min(line.y_min, box.y_min)
                    line.y_max = max(line.y_max, box.y_max)
                    line.y_center = (line.y_min + line.y_max) / 2.0
                    line.x_min = min(line.x_min, box.x_min)
                    line.x_max = max(line.x_max, box.x_max)
                    placed = True
                    break
            if not placed:
                lines.append(
                    LayoutLine(
                        boxes=[box],
                        text=box.text,
                        y_center=box.y_center,
                        y_min=box.y_min,
                        y_max=box.y_max,
                        x_min=box.x_min,
                        x_max=box.x_max,
                    )
                )

        # Sort boxes within each line from left to right
        for line in lines:
            line.boxes.sort(key=lambda b: b.x_min)
            line.text = " ".join(b.text for b in line.boxes)

        # Sort lines top-to-bottom
        lines.sort(key=lambda l: l.y_center)
        return lines, max_y, max_x


def strip_accents(s: str) -> str:
    import unicodedata
    norm = unicodedata.normalize("NFD", s)
    res = "".join(c for c in norm if unicodedata.category(c) != "Mn")
    return res.replace("đ", "d").replace("Đ", "D")


class ReceiptCandidateScorer:
    """Evaluates numbers across the document using positive labels, negative signals, and financial reconciliation."""

    NEGATIVE_PATTERNS = [
        (r"(?:mã\s*số\s*thuế|ma\s*so\s*thue|mst|tax\s*code|mã\s*st|ma\s*st)", -200, "near_tax_code"),
        (r"(?:mã\s*tra\s*cứu|ma\s*tra\s*cuu|tra\s*cứu|tra\s*cuu|mã\s*cqt|ma\s*cqt|mã\s*của\s*cqt|ma\s*cua\s*cqt|lookup)", -250, "near_lookup_code"),
        (r"(?:số\s*hóa\s*đơn|so\s*hoa\s*don|hóa\s*đơn\s*số|hoa\s*don\s*so|invoice\s*no|số\s*hđ|so\s*hd|kí\s*hiệu|ki\s*hieu|ký\s*hiệu|ky\s*hieu|mẫu\s*số|mau\s*so|serial|series)", -180, "near_invoice_number"),
        (r"(?:điện\s*thoại|dien\s*thoai|hotline|tel|phone|fax)", -180, "near_contact_info"),
        (r"(?:số\s*tài\s*khoản|so\s*tai\s*khoan|stk|tài\s*khoản|tai\s*khoan|bank\s*acc|atm|thẻ|the)", -160, "near_bank_account"),
        (r"(?:tiền\s*thừa|tien\s*thua|tiền\s*trả\s*lại|tien\s*tra\s*lai|change|tiền\s*khách\s*đưa|tien\s*khach\s*dua|khách\s*đưa|khach\s*dua|cash\s*tendered)", -180, "near_change_or_tendered"),
        (r"(?:ngày|ngay|date|giờ|gio|time|phút|phut)", -100, "near_date_time"),
        (r"(?:đơn\s*giá|don\s*gia|số\s*lượng|so\s*luong|sl|stt)", -60, "table_header_noise"),
    ]

    HIGH_TOTAL_PATTERNS = [
        r"(?:cộng\s*tiền\s*thanh\s*toán|cong\s*tien\s*thanh\s*toan|tổng\s*cộng\s*tiền\s*thanh\s*toán|tong\s*cong\s*tien\s*thanh\s*toan|tổng\s*tiền\s*thanh\s*toán|tong\s*tien\s*thanh\s*toan|tổng\s*thanh\s*toán|tong\s*thanh\s*toan|khách\s*phải\s*trả|khach\s*phai\s*tra|cần\s*thanh\s*toán|can\s*thanh\s*toan|phải\s*thanh\s*toán|phai\s*thanh\s*toan|grand\s*total|amount\s*due|tổng\s*cộng|tong\s*cong)",
    ]

    MED_TOTAL_PATTERNS = [
        r"(?:tổng\s*tiền|tong\s*tien|thanh\s*toán|thanh\s*toan|total\s*amount|total|tổng|tong)",
    ]

    LOW_TOTAL_PATTERNS = [
        r"(?:tiền\s*mặt|tien\s*mat|cash)",
    ]

    SUBTOTAL_PATTERNS = [
        r"(?:thành\s*tiền\s*trước\s*thuế|thanh\s*tien\s*truoc\s*thue|cộng\s*tiền\s*hàng|cong\s*tien\s*hang|tổng\s*tiền\s*hàng|tong\s*tien\s*hang|tiền\s*hàng|tien\s*hang|subtotal)",
    ]

    VAT_PATTERNS = [
        r"(?:tiền\s*thuế\s*gtgt|tien\s*thue\s*gtgt|tiền\s*thuế\s*vat|tien\s*thue\s*vat|thuế\s*gtgt|thue\s*gtgt|thuế\s*vat|thue\s*vat|tiền\s*thuế|tien\s*thue|vat)",
    ]

    WORDS_PATTERNS = [
        r"(?:số\s*tiền\s*viết\s*bằng\s*chữ|viết\s*bằng\s*chữ|bằng\s*chữ|amount\s*in\s*words)[\s:]*([^\n\r]+)",
    ]

    def __init__(self) -> None:
        self.words_parser = VietnameseAmountInWordsParser()

    def evaluate(
        self,
        lines: list[LayoutLine] | list[str],
        doc_height: float = 1000.0,
        doc_width: float = 1000.0,
        items: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        normalized_lines: list[tuple[str, float, float, float]] = []
        if lines and isinstance(lines[0], LayoutLine):
            for line in lines:  # type: ignore
                norm_y = line.y_center / max(doc_height, 1.0)
                norm_x = line.x_min / max(doc_width, 1.0)
                conf = sum(b.confidence for b in line.boxes) / max(len(line.boxes), 1)
                normalized_lines.append((line.text, norm_y, norm_x, conf))
        else:
            total_n = len(lines)
            for idx, raw_l in enumerate(lines):
                norm_y = idx / max(total_n, 1.0)
                normalized_lines.append((str(raw_l), norm_y, 0.5, 0.8))

        # 1. Parse amount in words
        amount_in_words: int | None = None
        for text, _, _, _ in normalized_lines:
            for pat in self.WORDS_PATTERNS:
                m = re.search(pat, text, re.IGNORECASE)
                if m:
                    parsed = self.words_parser.parse(m.group(0))
                    if parsed:
                        amount_in_words = parsed
                        break
            if amount_in_words:
                break

        # 2. Extract Subtotal & VAT candidates
        subtotal_val: int | None = None
        vat_val: int | None = None

        for text, _, _, _ in normalized_lines:
            if not subtotal_val:
                for pat in self.SUBTOTAL_PATTERNS:
                    if re.search(pat, text, re.IGNORECASE):
                        nums = re.findall(r"([0-9]{1,3}(?:[.,][0-9]{3})+|[0-9]{4,})", text)
                        for n in nums:
                            val = int(n.replace(".", "").replace(",", ""))
                            if val > 1000 and len(str(val)) <= 11:
                                subtotal_val = val
                                break
            if not vat_val:
                for pat in self.VAT_PATTERNS:
                    if re.search(pat, text, re.IGNORECASE):
                        nums = re.findall(r"([0-9]{1,3}(?:[.,][0-9]{3})+|[0-9]{4,})", text)
                        for n in nums:
                            val = int(n.replace(".", "").replace(",", ""))
                            if val > 1000 and len(str(val)) <= 11:
                                vat_val = val
                                break

        # 3. Extract and score all numeric candidates
        candidates: dict[int, dict[str, Any]] = {}

        for line_idx, (text, norm_y, norm_x, conf) in enumerate(normalized_lines):
            # Check if prev_line is an orphaned label for this line (e.g. "Cộng tiền thanh toán:" on line above)
            prev_text = normalized_lines[line_idx - 1][0] if line_idx > 0 else ""
            prev_has_amount = bool(re.search(r"\b[0-9]{1,3}(?:[.,][0-9]{3})+\b|\b[0-9]{4,}\b", prev_text))

            # Only inherit prev_text if prev_text has NO amounts and current line is mostly a lone number
            if prev_has_amount or not prev_text.strip():
                context_text = text.lower()
            else:
                context_text = f"{prev_text} | {text}".lower()

            # Find all numbers in the line
            matches = re.finditer(r"\b([0-9]{1,3}(?:[.,][0-9]{3})+|[0-9]{4,})\b", text)
            for m in matches:
                raw_str = m.group(1)
                clean_str = raw_str.replace(".", "").replace(",", "").strip()
                if not clean_str.isdigit():
                    continue

                # Disqualify numbers with > 11 digits (e.g. 14-digit lookup code 74589218491829 or barcode)
                if len(clean_str) > 11:
                    continue

                amt = int(clean_str)
                if amt < 1000:
                    continue

                line_score = 0.0
                line_reasons: list[str] = []

                # A. Positive Label Match
                matched_label = False
                for pat in self.HIGH_TOTAL_PATTERNS:
                    if re.search(pat, context_text, re.IGNORECASE):
                        line_score += 120.0
                        line_reasons.append("high_priority_total_label")
                        matched_label = True
                        break
                if not matched_label:
                    for pat in self.MED_TOTAL_PATTERNS:
                        if re.search(pat, context_text, re.IGNORECASE):
                            line_score += 90.0
                            line_reasons.append("med_priority_total_label")
                            matched_label = True
                            break
                if not matched_label:
                    for pat in self.LOW_TOTAL_PATTERNS:
                        if re.search(pat, context_text, re.IGNORECASE):
                            line_score += 50.0
                            line_reasons.append("low_priority_total_label")
                            matched_label = True
                            break

                # B. Negative Context Penalties (Section VIII)
                for neg_pat, penalty, neg_reason in self.NEGATIVE_PATTERNS:
                    if re.search(neg_pat, context_text, re.IGNORECASE):
                        line_score += penalty
                        line_reasons.append(f"{neg_reason}({penalty})")

                # C. Document Layout Zone (Section VI)
                # Summary zone (0.55 <= y <= 0.92) is where invoice totals reside
                if 0.55 <= norm_y <= 0.92:
                    line_score += 35.0
                    line_reasons.append("summary_zone_bonus(+35)")
                elif norm_y < 0.28:
                    line_score -= 80.0
                    line_reasons.append("header_zone_penalty(-80)")
                elif norm_y > 0.92:
                    line_score -= 50.0
                    line_reasons.append("footer_code_zone_penalty(-50)")

                # D. OCR Box confidence bonus
                line_score += round(conf * 15.0, 1)

                # Store maximum scoring instance for this amount
                if amt not in candidates or line_score > candidates[amt]["score"]:
                    candidates[amt] = {
                        "amount": amt,
                        "raw_str": raw_str,
                        "score": line_score,
                        "reasons": line_reasons,
                        "line_idx": line_idx,
                        "norm_y": norm_y,
                        "norm_x": norm_x,
                        "conf": conf,
                    }

        # 4. Financial Reconciliation Checks (Section X, XI, XII)
        reconciled_vat = False
        reconciled_words = False
        reconciled_items = False

        # Calculate line items sum if items exist (Section XII)
        items_sum: int | None = None
        if items and len(items) >= 2:
            valid_item_amts = [
                int(it.get("amount", 0)) for it in items if isinstance(it, dict) and it.get("amount")
            ]
            if valid_item_amts:
                items_sum = sum(valid_item_amts)

        for amt, c in candidates.items():
            # Check 1: subtotal + vat == total (Section X)
            if subtotal_val and vat_val and (subtotal_val + vat_val == amt):
                c["score"] += 80.0
                c["reasons"].append("subtotal_plus_vat_reconciled(+80)")
                reconciled_vat = True

            # Check 2: amount in words == candidate (Section XI)
            if amount_in_words and amount_in_words == amt:
                c["score"] += 90.0
                c["reasons"].append("amount_in_words_reconciled(+90)")
                reconciled_words = True
            elif amount_in_words and amount_in_words != amt:
                c["score"] -= 60.0
                c["reasons"].append("amount_in_words_mismatch(-60)")

            # Check 3: line items sum == candidate (Section XII)
            if items_sum and items_sum == amt:
                c["score"] += 80.0
                c["reasons"].append("line_items_sum_reconciled(+80)")
                reconciled_items = True

        # Sort candidates by score descending
        sorted_candidates = sorted(candidates.values(), key=lambda x: x["score"], reverse=True)

        best_total = 0
        total_confidence = 0.50

        if sorted_candidates:
            top = sorted_candidates[0]
            if top["score"] >= 80.0:
                best_total = top["amount"]
                if reconciled_vat or reconciled_words or reconciled_items:
                    total_confidence = 0.98
                elif "high_priority_total_label" in top["reasons"]:
                    total_confidence = 0.95
                else:
                    total_confidence = 0.88
            elif top["score"] > 20.0:
                best_total = top["amount"]
                total_confidence = 0.78
            elif amount_in_words:
                best_total = amount_in_words
                total_confidence = 0.92
            else:
                best_total = top["amount"]
                total_confidence = 0.60
        elif amount_in_words:
            best_total = amount_in_words
            total_confidence = 0.92

        return {
            "best_total": best_total,
            "total_confidence": total_confidence,
            "candidates": sorted_candidates,
            "amount_in_words": amount_in_words,
            "subtotal": subtotal_val,
            "vat": vat_val,
            "items_sum": items_sum,
            "reconciled_vat": reconciled_vat,
            "reconciled_words": reconciled_words,
            "reconciled_items": reconciled_items,
        }


# =====================================================================
# 4. LOCAL RECEIPT OCR PROVIDER WITH MULTI-PASS & GROUND TRUTH
# =====================================================================
class LocalReceiptOCRProvider:
    name = "local-ocr"

    def __init__(self, fallback_result: dict[str, Any] | None = None) -> None:
        self.fallback_result = fallback_result
        self.scorer = ReceiptCandidateScorer()

    @staticmethod
    def _extract_items_from_lines(raw_text_lines: list[str]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for line in raw_text_lines:
            match_item_qty = re.search(
                r"^(\d+)\s*[xX*]?\s+([^\d]+?)\s+([0-9]{1,3}(?:[.,][0-9]{3})+|[0-9]{4,})$", line
            )
            if match_item_qty:
                qty = match_item_qty.group(1)
                item_name = match_item_qty.group(2).strip()
                amt_str = match_item_qty.group(3).replace(".", "").replace(",", "")
                if amt_str.isdigit() and int(amt_str) > 0 and len(item_name) > 1:
                    items.append({"name": f"{qty}x {item_name}", "amount": int(amt_str)})
            else:
                match_item = re.search(
                    r"^([^\d\W][^\d]+?)\s+([0-9]{1,3}(?:[.,][0-9]{3})+|[0-9]{4,})$", line
                )
                if match_item:
                    item_name = match_item.group(1).strip()
                    amt_str = match_item.group(2).replace(".", "").replace(",", "")
                    if amt_str.isdigit() and int(amt_str) > 0 and len(item_name) > 2:
                        lower_name = item_name.lower()
                        if not any(
                            kw in lower_name
                            for kw in [
                                "tổng", "cộng", "tiền", "thanh toán", "thành tiền", "vat",
                                "giảm giá", "mã số thuế", "tra cứu", "thuế",
                            ]
                        ):
                            items.append({"name": item_name, "amount": int(amt_str)})
        return items

    def extract(self, source: str) -> dict[str, Any]:
        """Extract structured financial info from receipt image source locally using RapidOCR & Layout Analysis."""
        import base64
        import re

        img_bytes: bytes | None = None

        if source.startswith("data:") and ";base64," in source:
            _, raw_data = source.split(";base64,", 1)
            raw_data = re.sub(r"\s+", "", raw_data)
            try:
                img_bytes = base64.b64decode(raw_data)
            except Exception:
                pass
        elif len(source) > 200 and not source.startswith("http") and not source.startswith("file:"):
            try:
                raw_data = re.sub(r"\s+", "", source)
                img_bytes = base64.b64decode(raw_data)
            except Exception:
                pass
        else:
            # Check if source is a file path on disk
            try:
                with open(source, "rb") as f:
                    img_bytes = f.read()
            except Exception:
                pass

        if not img_bytes:
            if self.fallback_result:
                return dict(self.fallback_result)
            return self._build_empty_result()

        # Multi-Pass Execution (Section XIII):
        # Pass 1: Normal scale preprocessing + RapidOCR
        second_pass_used = False
        ocr_res_1, lines_1, h1, w1 = self._run_rapid_ocr(img_bytes, pass_num=1)
        raw_lines_1 = [l.text if isinstance(l, LayoutLine) else str(l) for l in lines_1]
        prelim_items_1 = self._extract_items_from_lines(raw_lines_1)
        eval_1 = self.scorer.evaluate(lines_1, doc_height=h1, doc_width=w1, items=prelim_items_1)

        final_eval = eval_1
        final_lines = lines_1
        final_items = prelim_items_1

        # If Pass 1 confidence is lower than threshold (< 0.85), run Pass 2 (CLAHE + Contrast Boost)
        if eval_1["total_confidence"] < 0.85:
            logger.info("Pass 1 confidence %.2f < 0.85; triggering Pass 2 enhancement...", eval_1["total_confidence"])
            ocr_res_2, lines_2, h2, w2 = self._run_rapid_ocr(img_bytes, pass_num=2)
            raw_lines_2 = [l.text if isinstance(l, LayoutLine) else str(l) for l in lines_2]
            prelim_items_2 = self._extract_items_from_lines(raw_lines_2)
            eval_2 = self.scorer.evaluate(lines_2, doc_height=h2, doc_width=w2, items=prelim_items_2)
            second_pass_used = True
            if eval_2["total_confidence"] > eval_1["total_confidence"]:
                final_eval = eval_2
                final_lines = lines_2
                final_items = prelim_items_2

        final_eval["second_pass_used"] = second_pass_used
        return self._build_output_from_lines_and_eval(final_lines, final_eval, items=final_items)

    def _run_rapid_ocr(self, img_bytes: bytes, pass_num: int = 1) -> tuple[list[Any], list[LayoutLine], float, float]:
        processed_bytes, _ = ImagePreprocessor.preprocess(img_bytes, pass_num=pass_num)
        try:
            from rapidocr_onnxruntime import RapidOCR  # type: ignore

            engine = RapidOCR()
            result, _ = engine(processed_bytes)
            if result:
                lines, max_h, max_w = LayoutExtractor.extract_lines(result)
                return result, lines, max_h, max_w
        except Exception as exc:
            logger.warning("RapidOCR execution failed on pass %d: %s", pass_num, exc)

        return [], [], 1000.0, 1000.0

    def _parse_from_lines(self, text_lines: list[str]) -> dict[str, Any]:
        """Direct text line parsing for testing or OCR text line inputs."""
        prelim_items = self._extract_items_from_lines(text_lines)
        eval_res = self.scorer.evaluate(text_lines, items=prelim_items)
        return self._build_output_from_lines_and_eval(text_lines, eval_res, items=prelim_items)

    def _build_output_from_lines_and_eval(
        self,
        lines: list[LayoutLine] | list[str],
        eval_res: dict[str, Any],
        items: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        raw_text_lines = [l.text if isinstance(l, LayoutLine) else str(l) for l in lines]

        # Extract Merchant
        merchant = "Cửa hàng"
        merchant_confidence = 0.50
        for line in raw_text_lines[:8]:
            trimmed = line.strip()
            if not trimmed:
                continue
            lower_trim = trimmed.lower()
            if any(
                skip in lower_trim
                for skip in [
                    "hóa đơn", "phiếu thanh toán", "phiếu tính tiền", "bán lẻ", "biên nhận",
                    "receipt", "invoice", "bàn:", "ngày:", "thu ngân:", "cộng hòa",
                    "độc lập", "mã số thuế", "mst", "địa chỉ", "hotline",
                ]
            ) or re.search(r"\b(?:tel|dt|fax|sđt|sdt)\b[\s:]*", lower_trim):
                continue
            if (
                not trimmed.isdigit()
                and len(trimmed) > 3
                and not re.search(r"^\d+[/.-]\d+", trimmed)
                and not re.search(r"^(?:đt|tel|hotline)[\s:]*\d+", lower_trim)
            ):
                merchant = trimmed
                merchant_confidence = 0.90
                break

        # Extract Date
        parsed_date = date.today().isoformat()
        date_confidence = 0.50
        for line in raw_text_lines:
            m_vn = re.search(r"ngày\s*(\d{1,2})\s*tháng\s*(\d{1,2})\s*năm\s*(\d{4})", line, re.IGNORECASE)
            if m_vn:
                d_str, m_str, y_str = m_vn.group(1).zfill(2), m_vn.group(2).zfill(2), m_vn.group(3)
                parsed_date = f"{y_str}-{m_str}-{d_str}"
                date_confidence = 0.98
                break
            m_date = re.search(r"(\d{2})[-/.](\d{2})[-/.](\d{4})", line)
            if m_date:
                d_str, m_str, y_str = m_date.group(1), m_date.group(2), m_date.group(3)
                # Verify standard DD-MM-YYYY format
                if int(d_str) <= 31 and int(m_str) <= 12:
                    parsed_date = f"{y_str}-{m_str}-{d_str}"
                    date_confidence = 0.95
                    break

        # Extract Line Items if not already provided
        if items is None:
            items = self._extract_items_from_lines(raw_text_lines)

        best_total = eval_res["best_total"]
        if not items:
            items = [{"name": f"Hóa đơn tại {merchant}", "amount": best_total or 100000}]

        items_confidence = 0.90 if len(items) > 1 else 0.70
        total_confidence = eval_res["total_confidence"]

        overall_confidence = round(
            0.55 * total_confidence + 0.25 * merchant_confidence + 0.20 * date_confidence, 2
        )

        return {
            "merchant": merchant,
            "date": parsed_date,
            "total": best_total,
            "currency": "VND",
            "items": items,
            "confidence": overall_confidence,
            "field_confidence": {
                "total": total_confidence,
                "merchant": merchant_confidence,
                "date": date_confidence,
                "items": items_confidence,
            },
            "total_candidates": [
                {"amount": c["amount"], "score": c["score"], "reasons": c["reasons"]}
                for c in eval_res.get("candidates", [])[:5]
            ],
            "validation_checks": {
                "subtotal": eval_res.get("subtotal"),
                "vat": eval_res.get("vat"),
                "subtotal_plus_vat_reconciled": eval_res.get("reconciled_vat", False),
                "amount_in_words": eval_res.get("amount_in_words"),
                "words_reconciled": eval_res.get("reconciled_words", False),
                "line_items_reconciled": eval_res.get("reconciled_items", False),
                "line_items_sum": eval_res.get("items_sum"),
                "second_pass_used": eval_res.get("second_pass_used", False),
                "items_count": len(items),
            },
            "provider": "local_rapidocr",
            "model": "rapidocr_onnx",
        }

    def _build_empty_result(self) -> dict[str, Any]:
        return {
            "merchant": "Hóa đơn",
            "date": date.today().isoformat(),
            "total": 0,
            "currency": "VND",
            "items": [],
            "confidence": 0.0,
            "field_confidence": {"total": 0.0, "merchant": 0.0, "date": 0.0, "items": 0.0},
            "total_candidates": [],
            "validation_checks": {},
            "provider": "local_rapidocr",
            "model": "rapidocr_onnx",
        }


# =====================================================================
# 5. GEMINI OCR PROVIDER (CLOUD FALLBACK ONLY - Section XVII)
# =====================================================================
class GeminiReceiptOCRProvider:
    name = "gemini-ocr"

    def __init__(self, api_key: str | None = None, model: str = "gemini-3.1-flash-lite") -> None:
        from app.core.config import get_settings

        settings = get_settings()
        self.api_key = api_key or getattr(settings, "gemini_api_key", None)
        self.model = model or getattr(settings, "ai_model", "gemini-3.1-flash-lite")

    def extract(self, source: str) -> dict[str, Any]:
        if not self.api_key or self.api_key in ("your-gemini-api-key", "test_key", "dummy"):
            raise ValueError("Gemini API key is not configured or is a dummy test key")

        import json
        import urllib.request

        mime_type = "image/jpeg"
        base64_data = source
        if source.startswith("data:") and ";base64," in source:
            header, base64_data = source.split(";base64,", 1)
            mime_type = header.replace("data:", "")

        model_path = self.model if self.model.startswith("models/") else f"models/{self.model}"
        url = f"https://generativelanguage.googleapis.com/v1beta/{model_path}:generateContent?key={self.api_key}"

        prompt = (
            "You are an expert OCR financial receipt parser. Analyze this receipt image and extract structured information.\n"
            "Respond ONLY with a valid JSON object matching this schema:\n"
            "{\n"
            '  "merchant": "string (name of store/restaurant)",\n'
            '  "date": "string YYYY-MM-DD (or empty string if not found)",\n'
            '  "total": integer (total amount),\n'
            '  "currency": "VND",\n'
            '  "items": [{"name": "item name", "amount": integer_amount}]\n'
            "}\n"
        )

        body_payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": base64_data,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {"response_mime_type": "application/json"},
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(body_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=30.0) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                text_content = res_data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text_content)
        except Exception as exc:
            raise ValueError(f"Gemini OCR extraction failed: {exc}") from exc


# =====================================================================
# 6. RECEIPT PREPARATION & VALIDATION (Sections XIV & XV)
# =====================================================================
def extract_receipt(payload: dict[str, Any]) -> ReceiptExtractionResult:
    if not isinstance(payload, dict):
        raise ValueError("receipt payload must be an object")

    merchant = str(payload.get("merchant") or "").strip()
    text_date = str(payload.get("date") or "").strip()
    currency = str(payload.get("currency") or "VND").upper()
    raw_items = payload.get("items") or []

    date_fallback_used = False
    if not text_date:
        text_date = date.today().isoformat()
        date_fallback_used = True

    if not merchant:
        raise ValueError("receipt merchant is required")
    if len(currency) != 3 or not currency.isalpha():
        raise ValueError("receipt currency must be a three-letter code")
    try:
        datetime.strptime(text_date, "%Y-%m-%d")
    except ValueError as exc:
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

    confidence = float(payload.get("confidence", 0.95))
    field_confidence = payload.get("field_confidence", {})
    total_conf = field_confidence.get("total", confidence)

    # Uncertainty detection: flag for review if confidence is low or totals diverge
    reconciled = abs(amount_total - total) <= max(1, total * 0.05) or len(items) <= 1
    review_required = date_fallback_used or not reconciled or total_conf < 0.75

    if review_required:
        reasons: list[str] = []
        if total_conf < 0.75:
            reasons.append("Không chắc chắn về tổng tiền. Vui lòng kiểm tra kỹ trước khi xác nhận.")
        if date_fallback_used:
            reasons.append("receipt date not detected, default current date applied; please check.")
        if not reconciled:
            reasons.append("receipt totals do not reconcile cleanly; manual review is required before posting.")
        return ReceiptExtractionResult(
            status="LOW_CONFIDENCE",
            merchant=merchant,
            date=text_date,
            total=total,
            currency=currency,
            items=items,
            reason=" ".join(reasons),
            review_required=True,
            confidence=confidence,
            field_confidence=field_confidence,
            total_candidates=payload.get("total_candidates", []),
            validation_checks=payload.get("validation_checks", {}),
            provider=payload.get("provider", "local_rapidocr"),
            model=payload.get("model", "rapidocr_onnx"),
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
        confidence=confidence,
        field_confidence=field_confidence,
        total_candidates=payload.get("total_candidates", []),
        validation_checks=payload.get("validation_checks", {}),
        provider=payload.get("provider", "local_rapidocr"),
        model=payload.get("model", "rapidocr_onnx"),
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
            confidence=candidate.confidence,
            field_confidence=candidate.field_confidence,
            total_candidates=candidate.total_candidates,
            validation_checks=candidate.validation_checks,
            provider=candidate.provider,
            model=candidate.model,
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
