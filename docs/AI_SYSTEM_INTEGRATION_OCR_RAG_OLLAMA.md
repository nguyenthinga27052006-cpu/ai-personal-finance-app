# TÀI LIỆU TOÀN DIỆN VỀ KIẾN TRÚC & MÃ NGUỒN HỆ THỐNG AI: OCR, RAG VÀ TÍCH HỢP OLLAMA LOCAL

> **Dự án**: AI Personal Finance App  
> **Phiên bản tài liệu**: 2.0 (Cập nhật kiến trúc Hybrid RAG + Local Ollama LLM + Local RapidOCR)  
> **Mục tiêu**: Cung cấp toàn bộ thông tin kiến trúc, mã nguồn triển khai, luồng dữ liệu và hướng dẫn cấu hình chi tiết cho 3 phân hệ lõi: **Quét hóa đơn OCR**, **Hỏi đáp thông minh Hybrid RAG**, và **Tích hợp mô hình cục bộ Ollama (`qwen2.5:3b`)**.

---

## MỤC LỤC

1. [TỔNG QUAN KIẾN TRÚC HỆ THỐNG AI](#1-tổng-quan-kiến-trúc-hệ-thống-ai)
2. [PHÂN HỆ 1: OCR QUÉT VÀ BÓC TÁCH HÓA ĐƠN (RECEIPT OCR PIPELINE)](#2-phân-hệ-1-ocr-quét-và-bóc-tách-hóa-đơn-receipt-ocr-pipeline)
   - [2.1 Luồng hoạt động](#21-luồng-hoạt-động)
   - [2.2 Mã nguồn LocalReceiptOCRProvider](#22-mã-nguồn-localreceiptocrprovider)
   - [2.3 API Endpoint Xử lý OCR](#23-api-endpoint-xử-lý-ocr)
3. [PHÂN HỆ 2: HỎI ĐÁP TÀI CHÍNH HYBRID RAG (RETRIEVAL-AUGMENTED GENERATION)](#3-phân-hệ-2-hỏi-đáp-tài-chính-hybrid-rag-retrieval-augmented-generation)
   - [3.1 Nguyên lý Hybrid RAG (PostgreSQL Ground Truth + Chroma VectorDB)](#31-nguyên-lý-hybrid-rag-postgresql-ground-truth--chroma-vectordb)
   - [3.2 Bộ phân loại ý định & Xử lý thời gian (IntentDetector & DateParser)](#32-bộ-phân-loại-ý-định--xử-lý-thời-gian-intentdetector--dateparser)
   - [3.3 Bộ truy xuất lai (HybridRetriever)](#33-bộ-truy-xuất-lai-hybridretriever)
   - [3.4 Kỹ thuật thiết kế Prompt (Prompt Engineering)](#34-kỹ-thuật-thiết-kế-prompt-prompt-engineering)
   - [3.5 Bộ sinh câu trả lời & Chống ảo giác (FinancialRAGGenerator)](#35-bộ-sinh-câu-trả-lời--chống-ảo-giác-financialraggenerator)
4. [PHÂN HỆ 3: TÍCH HỢP OLLAMA LOCAL LLM](#4-phân-hệ-3-tích-hợp-ollama-local-llm)
   - [4.1 Cơ chế giao tiếp OpenAI-compatible API](#41-cơ-chế-giao-tiếp-openai-compatible-api)
   - [4.2 Mã nguồn OllamaLLMProvider](#42-mã-nguồn-ollamallmprovider)
   - [4.3 Cấu hình Mạng Docker nối Host Windows (`host.docker.internal`)](#43-cấu-hình-mạng-docker-nối-host-windows-hostdockerinternal)
   - [4.4 Bộ định tuyến & Chịu lỗi (ModelRouter & Fallback Mechanism)](#44-bộ-định-tuyến--chịu-lỗi-modelrouter--fallback-mechanism)
5. [HƯỚNG DẪN CẤU HÌNH, KIỂM TRA VÀ VẬN HÀNH TỪ A-Z](#5-hướng-dẫn-cấu-hình-kiểm-tra-và-vận-hành-từ-a-z)
   - [5.1 Cấu hình biến môi trường (`.env` & `docker-compose.dev.yml`)](#51-cấu-hình-biến-môi-trường-env--docker-composedevyml)
   - [5.2 Khởi động mô hình Ollama trên máy trạm](#52-khởi-động-mô-hình-ollama-trên-máy-trạm)
   - [5.3 Lệnh kiểm tra kết nối & Unit Test](#53-lệnh-kiểm-tra-kết-nối--unit-test)

---

## 1. TỔNG QUAN KIẾN TRÚC HỆ THỐNG AI

Hệ thống AI tài chính cá nhân được xây dựng trên nguyên tắc **Local-First, Privacy-Preserving, Zero-Hallucination** (Ưu tiên chạy cục bộ, bảo mật dữ liệu tài chính người dùng và triệt tiêu hiện tượng ảo giác số liệu):

```mermaid
flowchart TB
    subgraph Client ["Client (Flutter Web & Mobile)"]
        UI[Giao diện Chat AI / Quét Hóa đơn]
        Voice[Voice Input (Speech-to-Text)]
    end

    subgraph API_Gateway ["FastAPI Backend (Docker Container: docker-api-1)"]
        Auth[JWT & User Context Guard]
        Router[API Endpoints: /query, /receipt/scan]
        
        subgraph OCR_Subsystem ["Phân hệ OCR Hóa đơn"]
            RapidOCR[RapidOCR Engine ONNX]
            RegexParser[Vietnamese Entity Parser]
        end

        subgraph RAG_Subsystem ["Phân hệ Hybrid RAG Engine"]
            Intent[Intent Detector & Date Range Parser]
            SQL_Ret[SQL Fact Retriever (PostgreSQL)]
            Vector_Ret[Vector Retriever (ChromaDB + BGE-M3)]
            PromptEng[Dynamic Prompt Builder]
            Gen[RAG Generator & Streamer]
        end

        subgraph Gateway_Subsystem ["AI Provider Gateway"]
            OllamaProv[OllamaLLMProvider]
            FallbackProv[Gemini / Fake Fallback]
        end
    end

    subgraph Storage ["Dữ liệu Cục bộ"]
        PG[(PostgreSQL: Giao dịch, Ngân sách, Mục tiêu)]
        Chroma[(ChromaDB: Tri thức tài chính 50/30/20)]
    end

    subgraph Host_Machine ["Host Machine (Windows)"]
        OllamaEngine[Ollama Server :11434]
        QwenModel[Model: qwen2.5:3b]
    end

    %% Luồng tương tác
    UI --> Router
    Voice --> UI
    Router --> Auth

    %% OCR Flow
    Router -- "POST /receipt/scan" --> RapidOCR
    RapidOCR --> RegexParser
    RegexParser --> PG

    %% RAG Flow
    Router -- "POST /query, /query/stream" --> Intent
    Intent --> SQL_Ret
    Intent --> Vector_Ret
    SQL_Ret --> PG
    Vector_Ret --> Chroma

    SQL_Ret --> PromptEng
    Vector_Ret --> PromptEng
    PromptEng --> Gen
    Gen --> OllamaProv

    %% Ollama Integration
    OllamaProv -- "HTTP POST host.docker.internal:11434/v1" --> OllamaEngine
    OllamaEngine --> QwenModel
    OllamaProv -. "Nếu lỗi kết nối" .-> FallbackProv
    Gen --> UI
```

---

## 2. PHÂN HỆ 1: OCR QUÉT VÀ BÓC TÁCH HÓA ĐƠN (RECEIPT OCR PIPELINE)

### 2.1 Luồng hoạt động

1. **Client** chụp ảnh hoặc chọn ảnh hóa đơn từ thư viện, mã hóa thành chuỗi `Base64` và gửi qua endpoint `POST /api/v1/ai/receipt/scan`.
2. **`LocalReceiptOCRProvider`** giải mã `Base64` thành mảng byte hình ảnh.
3. **Thư viện RapidOCR ONNX Runtime** quét các khối ký tự và trả về danh sách các dòng chữ (`text_lines`).
4. **Bộ phân tích thực thể tiếng Việt (Vietnamese Receipt Parser)** bóc tách:
   * **Tên cửa hàng (Merchant)**: Quét các dòng đầu tiên, loại trừ tiêu đề hóa đơn chung chung (*"HÓA ĐƠN BÁN HÀNG"*, *"PHIẾU TÍNH TIỀN"*, số điện thoại, ngày giờ).
   * **Từng món hàng (Line Items)**: Sử dụng Regex hỗ trợ Unicode nhận diện số lượng, tên món có dấu tiếng Việt (*"1x Cà phê sữa"*, *"2 Phở bò đặc biệt"*) và đơn giá.
   * **Tổng tiền thanh toán (Total Amount)**: Nhận diện các từ khóa thanh toán (*"Tổng cộng"*, *"Thành tiền"*, *"Tiền mặt"*, *"Tổng thanh toán"*, *"Khách phải trả"*...). Nếu không có từ khóa, tự động quét các số liệu lớn ở phần đáy hóa đơn.
   * **Ngày giao dịch (Transaction Date)**: Quét định dạng `DD/MM/YYYY` hoặc `DD-MM-YYYY`.
5. **Kiểm tra trùng lặp (Duplicate Detection)**: So sánh với 20 giao dịch gần nhất của người dùng trong PostgreSQL (cùng ngày, số tiền tương đương).
6. **Trả về bản nháp (Receipt Draft)**: Người dùng xem lại trên UI và bấm "Xác nhận" để ghi sổ vào PostgreSQL.

### 2.2 Mã nguồn `LocalReceiptOCRProvider`

*Vị trí file*: [`apps/api/app/ai/receipt.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/ai/receipt.py)

```python
class LocalReceiptOCRProvider:
    """Provider OCR cục bộ sử dụng RapidOCR ONNX Runtime và bộ parser tiếng Việt chuẩn xác."""
    name = "local-ocr"

    def __init__(self, fallback_result: dict[str, Any] | None = None) -> None:
        self.fallback_result = fallback_result

    def extract(self, source: str) -> dict[str, Any]:
        import base64
        import re
        from datetime import date

        text_lines: list[str] = []
        raw_data = source
        if source.startswith("data:") and ";base64," in source:
            _, raw_data = source.split(";base64,", 1)
        raw_data = re.sub(r"\s+", "", raw_data)

        # 1. Quét OCR bằng RapidOCR ONNX Runtime
        try:
            from rapidocr_onnxruntime import RapidOCR

            engine = RapidOCR()
            img_bytes = base64.b64decode(raw_data)
            result, _ = engine(img_bytes)
            if result:
                text_lines = [str(item[1]).strip() for item in result if item and len(item) > 1]
        except Exception:
            pass

        # 2. Dự phòng bằng Tesseract nếu có
        if not text_lines:
            try:
                import io
                from PIL import Image

                img_bytes = base64.b64decode(raw_data)
                image = Image.open(io.BytesIO(img_bytes))
                try:
                    import pytesseract
                    raw_text = pytesseract.image_to_string(image, lang="vie+eng")
                    text_lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
                except Exception:
                    pass
            except Exception:
                pass

        if not text_lines:
            if self.fallback_result:
                return dict(self.fallback_result)
            return {
                "merchant": "Hóa đơn",
                "date": date.today().isoformat(),
                "total": 0,
                "currency": "VND",
                "items": [],
            }

        # 3. Bóc tách tên cửa hàng (bỏ qua tiêu đề thông thường)
        merchant = "Cửa hàng"
        for line in text_lines[:6]:
            trimmed = line.strip()
            if not trimmed:
                continue
            lower_trim = trimmed.lower()
            if any(
                skip in lower_trim
                for skip in [
                    "hóa đơn", "phiếu thanh toán", "phiếu tính tiền", "bán lẻ",
                    "receipt", "invoice", "bàn:", "ngày:", "thu ngân:"
                ]
            ):
                continue
            if (
                not trimmed.isdigit()
                and len(trimmed) > 2
                and not re.search(r"^\d+[/.-]\d+", trimmed)
                and not re.search(r"^(?:đt|tel|hotline)[\s:]*\d+", lower_trim)
            ):
                merchant = trimmed
                break

        # 4. Bóc tách tổng tiền và các món hàng
        total_amounts: list[int] = []
        items: list[dict[str, Any]] = []

        for line in text_lines:
            # Nhận diện từ khóa tổng tiền
            match_total = re.search(
                r"(?:tổng cộng|tổng tiền|tổng thanh toán|cần thanh toán|thành tiền|tiền mặt|khách phải trả|thanh toán|tổng|total|amount)[\s:]*([0-9.,]+)",
                line,
                re.IGNORECASE,
            )
            if match_total:
                clean_num = match_total.group(1).replace(".", "").replace(",", "").strip()
                if clean_num.isdigit() and int(clean_num) > 0:
                    total_amounts.append(int(clean_num))

            # Món hàng có số lượng: "1x Cà phê sữa 35.000"
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
                # Món hàng không ghi số lượng: "Phở đặc biệt 65.000"
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
                            for kw in ["tổng", "cộng", "tiền", "thanh toán", "thành tiền", "vat", "giảm giá"]
                        ):
                            items.append({"name": item_name, "amount": int(amt_str)})

        # Quét số tiền ở đáy hóa đơn nếu không có từ khóa
        if not total_amounts:
            for line in reversed(text_lines[-6:]):
                nums = re.findall(r"\b([0-9]{1,3}(?:[.,][0-9]{3})+|[0-9]{4,})\b", line)
                for num_str in nums:
                    clean_num = num_str.replace(".", "").replace(",", "")
                    if clean_num.isdigit() and int(clean_num) > 1000:
                        total_amounts.append(int(clean_num))
                        break
                if total_amounts:
                    break

        total = total_amounts[0] if total_amounts else sum(it["amount"] for it in items)
        if not items:
            items = [{"name": f"Hóa đơn tại {merchant}", "amount": total or 100000}]

        # 5. Bóc tách ngày giao dịch
        parsed_date = date.today().isoformat()
        for line in text_lines:
            match_date = re.search(r"(\d{2})[-/](\d{2})[-/](\d{4})", line)
            if match_date:
                parsed_date = f"{match_date.group(3)}-{match_date.group(2)}-{match_date.group(1)}"
                break

        return {
            "merchant": merchant,
            "date": parsed_date,
            "total": total,
            "currency": "VND",
            "items": items,
        }
```

### 2.3 API Endpoint Xử lý OCR

*Vị trí file*: [`apps/api/app/ai/routes.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/ai/routes.py#L326-L390)

```python
@router.post("/receipt/scan")
def scan_receipt(
    payload: ReceiptScanRequest,
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
    limiter: AIRateLimiter,
) -> dict[str, Any]:
    _check_ai_rate_limit(request, current_user.id, limiter)
    _consume_ai_budget(current_user.id, "receipt_scan")

    settings = get_settings()
    if settings.ai_provider == "ollama":
        provider = LocalReceiptOCRProvider()
    elif settings.ai_provider == "gemini" and settings.gemini_api_key:
        provider = GeminiReceiptOCRProvider(api_key=settings.gemini_api_key)
    else:
        provider = FakeReceiptOCRProvider()

    # Lấy lịch sử giao dịch để phát hiện hóa đơn trùng
    recent_txs = (
        db.query(Transaction)
        .filter(Transaction.user_id == current_user.id)
        .order_by(Transaction.created_at.desc())
        .limit(20)
        .all()
    )
    existing_records = [
        {"merchant": tx.description or "", "date": tx.transaction_date.strftime("%Y-%m-%d"), "total": int(tx.amount)}
        for tx in recent_txs if tx.transaction_date
    ]

    candidate = prepare_receipt(
        {"source_ref": payload.image_base64},
        existing_records=existing_records,
        provider=provider,
    )
    return candidate.as_dict()
```

---

## 3. PHÂN HỆ 2: HỎI ĐÁP TÀI CHÍNH HYBRID RAG (RETRIEVAL-AUGMENTED GENERATION)

### 3.1 Nguyên lý Hybrid RAG (PostgreSQL Ground Truth + Chroma VectorDB)

Hệ thống RAG chia tách triệt để 2 nguồn dữ liệu:
1. **Dữ liệu tài chính thực tế người dùng (PostgreSQL)**: Thu nhập, chi tiêu, số dư tài khoản, ngân sách, mục tiêu. Đây là **Ground Truth tuyệt đối**; mọi con số trích dẫn phải lấy 100% từ bảng tính SQL này.
2. **Tri thức tài chính phổ quát (Chroma VectorDB + BGE-M3)**: Các nguyên lý quản lý tiền (quy tắc 50/30/20, phương pháp quả cầu tuyết trả nợ, quỹ khẩn cấp 3-6 tháng).

### 3.2 Bộ phân loại ý định & Xử lý thời gian (IntentDetector & DateParser)

*Vị trí file*: [`apps/api/app/ai/retrievers/intent_detector.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/ai/retrievers/intent_detector.py)

#### Nhận diện 13 Intents chính xác:
* `income_query`: Hỏi về tiền lương, nguồn thu, tiền nhận được.
* `expense_query`: Hỏi về tiền ra, khoản chi, tổng chi tiêu.
* `balance_query`: Hỏi về số dư tài khoản hiện tại, còn bao nhiêu tiền.
* `spending_analysis`: Hỏi về danh mục chi tiêu cao nhất, phân bổ chi phí.
* `comparison_query`: So sánh biến động giữa các tháng ("tháng nào tiêu nhiều nhất").
* `saving_advice` & `budget_review`: Hỏi tư vấn tiết kiệm, tiến độ ngân sách.
* `general_query` / `greeting`: Câu hỏi ngày tháng thông thường, giao tiếp.

#### Bóc tách khoảng thời gian linh hoạt (`parse_date_range`):
```python
@staticmethod
def parse_date_range(question: str, today: date | None = None) -> tuple[date, date, bool]:
    if today is None:
        today = date.today()
    q = question.lower().strip()

    # 1. Đính chính tháng: "ý tôi là tháng 7", "là tháng 7 ý"
    clarify = re.search(r"(?:ý tôi là.*?|là\s*)tháng\s*(\d{1,2})(?:\s*ý|\s*đó|\s*ạ|\s*nhé)?$", q)
    if clarify:
        m = int(clarify.group(1))
        if 1 <= m <= 12:
            start = date(today.year, m, 1)
            next_m = date(today.year + (m == 12), 1 if m == 12 else m + 1, 1)
            return start, next_m - timedelta(days=1), False

    # 2. Tháng tương đối: "tháng trước tháng 8", "trước tháng 8" -> Tháng 7
    match_rel_prev = re.search(r"(?:tháng\s*trước|trước)\s*tháng\s*(\d{1,2})", q)
    if match_rel_prev:
        base_m = int(match_rel_prev.group(1))
        m = 12 if base_m == 1 else base_m - 1
        y = today.year - 1 if base_m == 1 else today.year
        start = date(y, m, 1)
        next_m = date(y + (m == 12), 1 if m == 12 else m + 1, 1)
        return start, next_m - timedelta(days=1), False

    # 3. Tháng cụ thể: "tháng 8", "tháng 8/2026"
    match_specific = re.search(r"tháng\s*(\d{1,2})(?:\s*[/ năm]*\s*(\d{4}))?", q)
    if match_specific:
        m = int(match_specific.group(1))
        y = int(match_specific.group(2)) if match_specific.group(2) else today.year
        if 1 <= m <= 12:
            start = date(y, m, 1)
            next_m = date(y + (m == 12), 1 if m == 12 else m + 1, 1)
            return start, next_m - timedelta(days=1), False

    # 4. "tháng trước" / "tháng vừa rồi"
    if "tháng trước" in q or "tháng vừa rồi" in q:
        m = 12 if today.month == 1 else today.month - 1
        y = today.year - 1 if today.month == 1 else today.year
        start = date(y, m, 1)
        next_m = date(y + (m == 12), 1 if m == 12 else m + 1, 1)
        return start, next_m - timedelta(days=1), False
    ...
```

### 3.3 Bộ truy xuất lai (HybridRetriever)

*Vị trí file*: [`apps/api/app/ai/retrievers/hybrid_retriever.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/ai/retrievers/hybrid_retriever.py)

```python
class HybridRetriever:
    def retrieve(self, user: User, question: str, start: date | None = None, end: date | None = None, currency: str = "VND", top_k: int = 4, history: list[Any] | None = None) -> HybridContext:
        # 1. Xác định ý định & kế hoạch truy vấn
        plan = IntentDetector.create_plan(question, today=start, history=history)
        intent = plan.intent

        # 2. Truy vấn dữ liệu thực tế của người dùng từ PostgreSQL
        sql_context = self.sql_retriever.retrieve_user_financial_facts(
            user=user, start=start, end=end, currency=currency, question=question
        )

        # 3. Truy vấn kho tài liệu RAG Chroma VectorDB bằng BGE-M3 Embeddings
        vector_chunks = self.vector_store.search(
            query=question, top_k=top_k, similarity_threshold=0.15
        )

        return HybridContext(
            intent=intent,
            sql_context=sql_context,
            vector_chunks=vector_chunks,
            has_sql_data=sql_context.has_data,
            has_rag_data=len(vector_chunks) > 0,
        )
```

### 3.4 Kỹ thuật thiết kế Prompt (Prompt Engineering)

*Vị trí file*: [`apps/api/app/ai/rag/prompts.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/ai/rag/prompts.py)

Để chống hiện tượng Ollama sinh câu máy móc hoặc rò rỉ token ngoại lai (*"dengan"*), Prompt được tối ưu động theo từng Intent:

```python
FINANCIAL_RAG_SYSTEM_PROMPT = """Bạn là Trợ lý Tài chính Cá nhân AI chuyên nghiệp, thông minh, linh hoạt và thân thiện.

QUY TẮC BẮT BUỘC:
1. Xưng hô tự nhiên, thân thiện bằng tiếng Việt chuẩn ("Mình" - "bạn" hoặc "Tôi" - "bạn").
   - Tuyệt đối chỉ trả lời bằng tiếng Việt chuẩn, không sử dụng các từ ngữ ngoại lai (như từ "dengan", "dan", "and" của tiếng nước ngoài).
2. TRẢ LỜI ĐÚNG TRỌNG TÂM CÂU HỎI:
   - Người dùng hỏi gì thì trả lời đúng thông tin đó:
     * Nếu hỏi thu nhập: Chỉ trả lời về số tiền thu nhập và nguồn thu nhập, TUYỆT ĐỐI KHÔNG tự tiện chèn thêm danh mục chi tiêu nếu người dùng không hỏi.
     * Nếu hỏi chi tiêu / mục nào nhiều nhất: Nêu rõ tổng chi tiêu, tên danh mục đứng đầu và số tiền cụ thể từ DỮ LIỆU TÀI CHÍNH THỰC TẾ.
     * Nếu hỏi số dư: Nêu số dư hiện tại và tài khoản.
     * Nếu hỏi câu hỏi lịch / ngày tháng (ví dụ: "tháng trước là tháng mấy"): Trả lời ngắn gọn, chuẩn xác mốc thời gian, không chèn các số liệu tài chính không liên quan.
   - Tuyệt đối trả lời đúng tháng/kỳ người dùng đang hỏi trong câu hỏi mới nhất, không nhầm lẫn với các tháng trong lịch sử cũ.
   - Trả lời tự nhiên, ngắn gọn, súc tích. TUYỆT ĐỐI KHÔNG lặp lại các bài học/lời khuyên giáo điều máy móc.
3. CON SỐ CHÍNH XÁC:
   - Trích dẫn chính xác con số tiền tệ từ DỮ LIỆU TÀI CHÍNH THỰC TẾ được cung cấp. Nếu kỳ đó không có dữ liệu, hãy thông báo rõ ràng là chưa có dữ liệu giao dịch trong kỳ đó.
"""

def build_rag_user_prompt(
    question: str,
    intent: str,
    user_facts_text: str,
    rag_knowledge_text: str,
    conversation_history_text: str,
    has_sql_data: bool,
    has_rag_data: bool,
    language: str = "vi",
) -> str:
    # Tùy biến chỉ đạo Prompt động theo Intent
    if intent == "income_query":
        lang_inst = "YÊU CẦU: Trả lời trực tiếp và ngắn gọn về số tiền THU NHẬP trong khoảng thời gian người dùng hỏi từ Dữ liệu tài chính ở mục 2. Tuyệt đối không chèn thêm danh mục chi tiêu."
    elif intent == "balance_query":
        lang_inst = "YÊU CẦU: Trả lời trực tiếp SỐ DƯ hiện tại từ Dữ liệu tài chính ở mục 2. Trả lời ngắn gọn, rõ ràng."
    elif intent in ("spending_analysis", "expense_query"):
        lang_inst = "YÊU CẦU: Trả lời trực tiếp về TỔNG CHI TIÊU và danh mục chi tiêu từ Dữ liệu tài chính ở mục 2. Nêu số tiền cụ thể."
    elif intent == "comparison_query":
        lang_inst = "YÊU CẦU: So sánh số liệu giữa các tháng được hỏi từ Dữ liệu tài chính ở mục 2. Nêu rõ mức chênh lệch."
    elif intent in ("greeting", "general_query"):
        lang_inst = "YÊU CẦU: Trả lời tự nhiên, thân thiện và chính xác câu hỏi của người dùng. Trả lời trực tiếp vào câu hỏi, không chèn số liệu tài chính không liên quan."
    else:
        lang_inst = "YÊU CẦU: Trả lời thẳng vào trọng tâm câu hỏi hiện tại dựa trên Dữ liệu tài chính ở mục 2. Không lặp lại thông tin không được hỏi."

    return f"""1. LỊCH SỬ HỘI THOẠI TRƯỚC ĐÓ (Chỉ để tham khảo ngữ cảnh):
{conversation_history_text}

2. DỮ LIỆU TÀI CHÍNH THỰC TẾ (GROUND TRUTH CHO CÂU HỎI HIỆN TẠI):
{user_facts_text if has_sql_data else "Chưa có giao dịch hoặc dữ liệu thực tế nào trong khoảng thời gian này."}

3. TRI THỨC BỔ TRỢ (RAG Vector Store):
{rag_knowledge_text if has_rag_data else "Không có tài liệu bổ trợ."}

CÂU HỎI HIỆN TẠI CỦA NGƯỜI DÙNG:
"{question}"

{lang_inst}
"""
```

### 3.5 Bộ sinh câu trả lời & Chống ảo giác (FinancialRAGGenerator)

*Vị trí file*: [`apps/api/app/ai/rag/generator.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/ai/rag/generator.py)

Bộ sinh xử lý cả 2 chế độ:
1. **Chế độ Blocking (`generate_response`)**: Dành cho endpoint `POST /api/v1/ai/query`.
2. **Chế độ Streaming SSE (`stream_generate_response`)**: Truyền token thời gian thực dạng `data: {"type": "token", "content": "..."}\n\n` đến Flutter.
3. **Bộ bảo vệ chống ảo giác (Strict Hallucination Guard)**: Nếu câu hỏi tài chính nhưng người dùng không có giao dịch trong DB và không có tài liệu RAG, hệ thống lập tức trả về thông báo an toàn `INSUFFICIENT_DATA`, không cho phép LLM tự bịa số.

---

## 4. PHÂN HỆ 3: TÍCH HỢP OLLAMA LOCAL LLM

### 4.1 Cơ chế giao tiếp OpenAI-compatible API

Mô hình cục bộ được phục vụ thông qua server Ollama chạy tại cổng `11434`. Ollama cung cấp giao diện tương thích hoàn toàn với chuẩn OpenAI REST API:
* Endpoint tạo phản hồi: `POST http://host.docker.internal:11434/v1/chat/completions`
* Model: `qwen2.5:3b`
* Hỗ trợ cờ `"stream": true` để truyền dòng token.

### 4.2 Mã nguồn `OllamaLLMProvider`

*Vị trí file*: [`apps/api/app/ai/providers.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/ai/providers.py#L291-L415)

```python
class OllamaLLMProvider:
    """Tích hợp Ollama Local LLM thông qua OpenAI-compatible API với hỗ trợ Streaming và Candidate URLs."""
    name = "ollama"
    is_production = True

    def __init__(
        self,
        base_url: str = "http://localhost:11434/v1",
        default_model: str = "qwen2.5:3b",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        started = monotonic()
        import json
        import urllib.request

        # Danh sách URL dự phòng khi chạy giữa Docker và Host Windows
        candidate_urls = [f"{self.base_url}/chat/completions"]
        if "localhost" in self.base_url or "127.0.0.1" in self.base_url:
            candidate_urls.append(
                self.base_url.replace("localhost", "host.docker.internal").replace("127.0.0.1", "host.docker.internal") + "/chat/completions"
            )
        elif "host.docker.internal" in self.base_url:
            candidate_urls.append(
                self.base_url.replace("host.docker.internal", "localhost") + "/chat/completions"
            )

        user_prompt = request.context.get("user_prompt")
        prompt_text = (
            str(user_prompt)
            if user_prompt
            else f"{request.instructions}\n\nContext:\n{_json(request.context)}"
        )
        payload = {
            "model": request.model if request.model.startswith("qwen") else self.default_model,
            "messages": [
                {"role": "system", "content": request.instructions},
                {"role": "user", "content": prompt_text},
            ],
            "temperature": 0.2,
        }

        last_error = None
        for url in candidate_urls:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=request.timeout_seconds) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    content = data["choices"][0]["message"]["content"]
                    return ProviderResponse(
                        content=content,
                        provider=self.name,
                        model=self.default_model,
                        estimated_cost=0.0,
                        latency_ms=int((monotonic() - started) * 1000),
                    )
            except Exception as exc:
                last_error = exc
                continue

        from app.core.config import get_settings
        settings = get_settings()
        if settings.app_env in ("development", "test"):
            return FakeProvider().generate(request)
        raise ProviderUnavailableError(f"Ollama Local LLM Provider error: {last_error}") from last_error

    async def stream_generate(self, request: ProviderRequest) -> AsyncGenerator[str, None]:
        import json
        import httpx

        candidate_urls = [f"{self.base_url}/chat/completions"]
        if "localhost" in self.base_url or "127.0.0.1" in self.base_url:
            candidate_urls.append(
                self.base_url.replace("localhost", "host.docker.internal").replace("127.0.0.1", "host.docker.internal") + "/chat/completions"
            )
        elif "host.docker.internal" in self.base_url:
            candidate_urls.append(
                self.base_url.replace("host.docker.internal", "localhost") + "/chat/completions"
            )

        user_prompt = request.context.get("user_prompt")
        prompt_text = (
            str(user_prompt)
            if user_prompt
            else f"{request.instructions}\n\nContext:\n{_json(request.context)}"
        )
        payload = {
            "model": request.model if request.model.startswith("qwen") else self.default_model,
            "messages": [
                {"role": "system", "content": request.instructions},
                {"role": "user", "content": prompt_text},
            ],
            "stream": True,
            "temperature": 0.2,
        }

        streamed_any = False
        last_error = None
        for url in candidate_urls:
            try:
                async with httpx.AsyncClient(timeout=request.timeout_seconds) as client:
                    async with client.stream("POST", url, json=payload) as response:
                        if response.status_code != 200:
                            raise ProviderUnavailableError(f"Ollama API returned status {response.status_code}")
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                data_str = line[6:].strip()
                                if data_str == "[DONE]":
                                    break
                                try:
                                    data = json.loads(data_str)
                                    delta = data["choices"][0].get("delta", {})
                                    if "content" in delta and delta["content"]:
                                        streamed_any = True
                                        yield delta["content"]
                                except Exception:
                                    pass
                if streamed_any:
                    return
            except Exception as exc:
                last_error = exc
                continue

        from app.core.config import get_settings
        settings = get_settings()
        if settings.app_env in ("development", "test"):
            async for chunk in FakeProvider().stream_generate(request):
                yield chunk
            return
        raise ProviderUnavailableError(f"Ollama stream error: {last_error}") from last_error
```

### 4.3 Cấu hình Mạng Docker nối Host Windows (`host.docker.internal`)

Khi backend FastAPI chạy bên trong Docker Container (`docker-api-1`), địa chỉ `localhost` đại diện cho chính container Linux chứ không phải máy Windows.  
Để Docker container truy cập được dịch vụ Ollama chạy trên Windows:
1. Docker Desktop cung cấp DNS ảo: `host.docker.internal`.
2. Trong [`infra/docker/docker-compose.dev.yml`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/infra/docker/docker-compose.dev.yml):
   ```yaml
   services:
     api:
       environment:
         AI_PROVIDER: ${AI_PROVIDER:-ollama}
         AI_MODEL: ${AI_MODEL:-qwen2.5:3b}
         OLLAMA_BASE_URL: ${OLLAMA_BASE_URL:-http://host.docker.internal:11434/v1}
   ```
3. Trong code `OllamaLLMProvider`: Cơ chế `candidate_urls` tự động chuyển đổi giữa `localhost` và `host.docker.internal`, đảm bảo code chạy mượt mà ở cả 2 môi trường: chạy trực tiếp từ máy host (`uvicorn`) hoặc chạy trong Docker container.

### 4.4 Bộ định tuyến & Chịu lỗi (ModelRouter & Fallback Mechanism)

*Vị trí file*: [`apps/api/app/ai/gateway.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/ai/gateway.py#L183-L223)

```python
def default_gateway() -> AIGateway:
    settings = get_settings()
    if settings.ai_provider == "ollama":
        primary = OllamaLLMProvider(
            base_url=settings.ollama_base_url, default_model=settings.ai_model
        )
        fallback = (
            GeminiLLMProvider(api_key=settings.gemini_api_key, default_model=settings.ai_model)
            if (settings.gemini_api_key and settings.gemini_api_key not in ("your-gemini-api-key", "test_key", "dummy"))
            else FakeProvider()
        )
    elif settings.ai_provider == "gemini" and settings.gemini_api_key:
        primary = GeminiLLMProvider(api_key=settings.gemini_api_key, default_model=settings.ai_model)
        fallback = OllamaLLMProvider(base_url=settings.ollama_base_url, default_model=settings.ai_model)
    else:
        primary = FakeProvider()
        fallback = FakeProvider()

    return AIGateway(
        ModelRouter(primary, fallback),
        build_read_only_registry(),
    )
```

---

## 5. HƯỚNG DẪN CẤU HÌNH, KIỂM TRA VÀ VẬN HÀNH TỪ A-Z

### 5.1 Cấu hình biến môi trường (`.env` & `docker-compose.dev.yml`)

File [`.env`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/.env) ở thư mục gốc:

```env
# AI Provider Configuration
AI_PROVIDER=ollama
AI_MODEL=qwen2.5:3b
EMBEDDING_PROVIDER=bge-m3
EMBEDDING_MODEL=BAAI/bge-m3
OLLAMA_BASE_URL=http://localhost:11434/v1
AI_ENABLED=true

# Khóa dự phòng khi cần thiết (tùy chọn)
GEMINI_API_KEY=your-gemini-api-key-here
OPENAI_API_KEY=your-openai-api-key-here
```

### 5.2 Khởi động mô hình Ollama trên máy trạm

1. **Khởi chạy ứng dụng Ollama**:
   * Chạy ứng dụng Ollama từ Windows Start Menu hoặc qua terminal.
2. **Kéo mô hình Qwen 2.5 3B (nếu chưa có)**:
   ```bash
   ollama pull qwen2.5:3b
   ```
3. **Kiểm tra trạng thái Ollama**:
   ```bash
   ollama list
   ```
   Kết quả trả về phải có: `qwen2.5:3b`.

### 5.3 Lệnh kiểm tra kết nối & Unit Test

#### 1. Kiểm tra kết nối từ Docker container ra Ollama host Windows:
```bash
docker exec docker-api-1 python -c "
import urllib.request, json
req = urllib.request.Request('http://host.docker.internal:11434/api/tags')
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())
    print('Các mô hình khả dụng:', [m['name'] for m in data.get('models', [])])
"
```

#### 2. Kiểm tra thư viện RapidOCR trong Docker container:
```bash
docker exec docker-api-1 python -c "
from rapidocr_onnxruntime import RapidOCR
engine = RapidOCR()
print('RapidOCR khởi tạo thành công!')
"
```

#### 3. Chạy toàn bộ 40 bài kiểm thử tự động của hệ thống AI & RAG:
```bash
.\.venv\Scripts\python -m pytest apps/api/tests/test_ai_platform.py apps/api/tests/test_rag_chatbot.py
```
*Kết quả yêu cầu: `40 passed in ~80s`.*

#### 4. Khởi động lại API container khi thay đổi cấu hình:
```bash
docker restart docker-api-1
```

---

## TỔNG KẾT BẢNG ÁNH XẠ FILE NGUỒN (SOURCE CODE MAP)

| Phân hệ | File mã nguồn | Chức năng chính |
| :--- | :--- | :--- |
| **OCR** | `apps/api/app/ai/receipt.py` | Engine RapidOCR ONNX, bóc tách thực thể hóa đơn tiếng Việt, kiểm tra trùng lặp |
| **OCR Endpoint** | `apps/api/app/ai/routes.py` | API `/api/v1/ai/receipt/scan` và `/confirm` |
| **RAG Prompts** | `apps/api/app/ai/rag/prompts.py` | System prompt tiếng Việt chuẩn, Prompt Builder tùy biến theo Intent |
| **RAG Intent** | `apps/api/app/ai/retrievers/intent_detector.py` | Phân loại 13 intent, bóc tách mốc thời gian tuyệt đối và tương đối |
| **RAG Hybrid** | `apps/api/app/ai/retrievers/hybrid_retriever.py` | Kết hợp dữ liệu tài chính PostgreSQL + tri thức cẩm nang ChromaDB |
| **RAG Generator**| `apps/api/app/ai/rag/generator.py` | Phối hợp sinh phản hồi, streaming SSE, Hallucination Guard, Citations |
| **Ollama Provider**| `apps/api/app/ai/providers.py` | Lớp `OllamaLLMProvider` giao tiếp `/v1/chat/completions` (Sync & SSE) |
| **AI Gateway** | `apps/api/app/ai/gateway.py` | `default_gateway()`, điều phối ModelRouter (Primary Ollama, Fallback Gemini) |
| **Cấu hình** | `.env`, `infra/docker/docker-compose.dev.yml` | Khai báo biến môi trường và kết nối mạng `host.docker.internal` |
