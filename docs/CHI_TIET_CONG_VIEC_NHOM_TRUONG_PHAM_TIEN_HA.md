# 👑 BẢN ĐẶC TẢ CHI TIẾT CÔNG VIỆC NHÓM TRƯỞNG (TECH LEAD & PROJECT MANAGER)
**Họ và tên:** PHẠM TIẾN HÀ  
**Lớp:** CNTT K23G | **Dự án:** Hệ thống Quản Lý Tài Chính Cá Nhân Tích Hợp AI (*AI Personal Finance Assistant*)  
**Trọng trách:** Trưởng nhóm (Team Leader) • AI & RAG Specialist • OCR Vision Engineer • Backend Core Lead • Quản trị hệ thống & CSDL • DevOps & Hạ tầng  

---

## 🧭 I. TỔNG QUAN VAI TRÒ & PHẠM VI TRÁCH NHIỆM

Nhóm trưởng **Phạm Tiến Hà** giữ vai trò kép: **Quản lý dự án (Project Lead)** và **Kỹ sư trưởng kỹ thuật (Technical Lead)**. Trong mô hình phát triển phần mềm hiện đại, vị trí này chịu trách nhiệm cao nhất về:
1. **Trí tuệ nhân tạo (AI Engine):** Thiết kế và lập trình "bộ não" thông minh của hệ thống bao gồm Chatbot RAG (Retrieval-Augmented Generation) trên nền `pgvector` và Module bóc tách hóa đơn OCR Vision.
2. **Backend Core API:** Thiết kế và lập trình toàn bộ tầng dịch vụ lõi (FastAPI, SQLAlchemy 2.0, kiến trúc kế toán kép Double-entry, quản lý đa ví, ngân sách, mục tiêu).
3. **Quản trị hệ thống & CSDL:** Thiết kế lược đồ CSDL PostgreSQL 18 chuẩn 3NF, cấu hình extension vector, quản trị migration với Alembic, tối ưu hóa câu truy vấn.
4. **Kiểm soát tiến độ chung (Project Management):** Lập kế hoạch Sprint theo Agile/Scrum, thiết lập WBS, điều phối công việc của 4 thành viên, review mã nguồn và kiểm soát chất lượng bàn giao.
5. **DevOps & Hạ tầng:** Container hóa toàn bộ hệ thống bằng Docker & Docker Compose, cấu hình Caching Redis, quản lý biến môi trường bảo mật và triển khai máy chủ.

```
┌────────────────────────────────────────────────────────────────────────┐
│                      PHẠM TIẾN HÀ (TEAM LEADER)                        │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         ▼                         ▼                         ▼
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│   AI & RAG/OCR   │      │   BACKEND CORE   │      │  DEVOPS & ADMIN  │
│  - Gemini Flash  │      │  - FastAPI REST  │      │  - Docker / C.C. │
│  - pgvector RAG  │      │  - Double-Entry  │      │  - Postgres 18   │
│  - OCR Vision    │      │  - Auth JWT/RBAC │      │  - Redis Caching │
│  - Tool Calling  │      │  - Budgets/Goals │      │  - Agile / Scrum │
└──────────────────┘      └──────────────────┘      └──────────────────┘
```

---

## 🧠 II. CHI TIẾT CÔNG NGHỆ & XÂY DỰNG PHÂN HỆ AI CHATBOT RAG

*File mã nguồn phụ trách chính:* `apps/api/app/ai/`, `apps/api/app/ai/rag/generator.py`, `apps/api/app/ai/rag/vector_store.py`, `apps/api/app/ai/context.py`, `apps/api/app/ai/tools.py`, `apps/api/app/ai/gateway.py`

### 1. Bảng Thông Số & Công Nghệ Sử Dụng (Tech Stack)
* **Ngôn ngữ & Runtime:** Python 3.12+ (Async I/O non-blocking).
* **Mô hình Ngôn ngữ Lớn (LLM):** **Google Gemini 3.1 Flash-Lite** (`gemini-3.1-flash-lite`) và **Gemini 2.5 Flash** qua thư viện chính thức `google-genai` SDK.
  * *Đặc điểm:* Hỗ trợ Context Window cực lớn (1M+ tokens), độ trễ suy luận siêu thấp (< 1.2s), hỗ trợ native Function Calling và Structured JSON output.
* **Mô hình Vector Embedding:** **`text-embedding-004` (Google GenAI)**.
  * *Đặc tính vector:* Chiều dài cố định **768 dimensions (768 chiều)**, tối ưu hóa cho bài toán tìm kiếm ngữ nghĩa (Semantic Retrieval).
  * *Khoảng cách đo lường:* **Cosine Distance** ($\text{Cosine Distance} = 1 - \text{Cosine Similarity}$).
* **Cơ sở Dữ liệu Vector (Vector DB):** **`pgvector`** tích hợp trực tiếp trên PostgreSQL 18.
  * *Chỉ mục Vector (Indexing):* **HNSW (Hierarchical Navigable Small World)** với tham số `m=16`, `ef_construction=64`.
* **Công nghệ Tìm kiếm Từ vựng (Sparse Search):** Thuật toán **BM25** kết hợp tách từ tiếng Việt qua `VietnameseBM25Tokenizer` (hỗ trợ `pyvi`, `underthesea` và bộ từ điển tài chính compound words).
* **Thuật toán Hợp nhất Thứ hạng:** **RRF (Reciprocal Rank Fusion)** với hằng số $k = 60$.
* **Cơ chế An toàn & Kiểm soát:** Redis 8 Atomic Counter (Rate limiting 50,000 tokens/ngày/user), PII Masking, Prompt Injection Filters.

---

### 2. Quy Trình Xây Dựng & Phát Triển RAG Từng Bước (Implementation Workflow)

```
                           ┌──────────────────────────────────────────────────────────────┐
                           │               USER INPUT: "Tháng này tôi tiêu gì?"           │
                           └──────────────────────────────┬───────────────────────────────┘
                                                          │
                               ┌──────────────────────────┴──────────────────────────┐
                               ▼                                                     ▼
                [ LAYER 1: SQL GROUND TRUTH ]                         [ LAYER 2: HYBRID VECTOR RETRIEVAL ]
                FinancialContextBuilder                               Text Embedding 768-dim + BM25 Lexical
                - Truy vấn số dư các ví                               - Dense Search: text-embedding-004
                - Truy vấn tổng thu, tổng chi                         - Sparse Search: Vietnamese BM25
                - Phân bổ % theo danh mục                             - Fusion: Reciprocal Rank Fusion (RRF)
                - Gắn cờ deterministic=True                           - Reranking & Threshold filter (> 0.15)
                               │                                                     │
                               └──────────────────────────┬──────────────────────────┘
                                                          │
                                                          ▼
                                    ┌───────────────────────────────────────────┐
                                    │      DYNAMIC PROMPT CONTEXT WINDOW        │
                                    │  - System Prompt (Rules + Guardrails)     │
                                    │  - SQL Financial Facts (Ground Truth)     │
                                    │  - Retrieved Financial Advice Chunks      │
                                    │  - User Query + Chat History (Memory)     │
                                    └─────────────────────┬─────────────────────┘
                                                          │
                                                          ▼
                                    ┌───────────────────────────────────────────┐
                                    │       GEMINI 3.1 FLASH-LITE ENGINE        │
                                    │       - Reasoning & Synthesis             │
                                    │       - Function Calling (nếu cần action) │
                                    └─────────────────────┬─────────────────────┘
                                                          │
                                                          ▼
                                    ┌───────────────────────────────────────────┐
                                    │  STRICT OUTPUT NORMALIZATION & STREAMING  │
                                    │  Pydantic AIOutput Validation -> Frontend │
                                    └───────────────────────────────────────────┘
```

#### Bước 1: Chiến lược Phân mảnh Tài liệu (Chunking Strategy)
Trong file `vector_store.py`, hàm `recursive_chunk_text()` thực hiện chia nhỏ tài liệu tri thức tài chính cá nhân:
* `chunk_size = 400` ký tự, `chunk_overlap = 120` ký tự nhằm giữ trọn vẹn ngữ nghĩa giữa 2 đoạn kề nhau.
* Bảo lưu ngữ cảnh tiêu đề tài liệu bằng tiền tố `[{title}] ` ở mỗi chunk:
  ```python
  prefix = f"[{title}] " if title else ""
  separators = ["\n\n", "\n", ". ", "; ", ", ", " "]
  ```

#### Bước 2: Tách từ tiếng Việt cho BM25 (Vietnamese Tokenization)
File `vector_store.py` cài đặt lớp `VietnameseBM25Tokenizer` với bộ từ điển tài chính ghép nối từ phức (`FINANCIAL_COMPOUNDS`):
* Ghép các từ: "lương về" $\rightarrow$ `lương_về`, "vượt ngân sách" $\rightarrow$ `vượt_ngân_sách`, "quỹ khẩn cấp" $\rightarrow$ `quỹ_khẩn_cấp`, "nhu cầu thiết yếu" $\rightarrow$ `nhu_cầu_thiết_yếu`.
* Fallback tự động qua `pyvi.ViTokenizer` hoặc `underthesea.word_tokenize` nếu có cài đặt.

#### Bước 3: Tìm kiếm lai (Hybrid Search) & Hợp nhất RRF
1. **Dense Search:** Câu hỏi được nhúng thành vector qua `_embedder.embed_text(query)` và tính Cosine Similarity với từng chunk trong `candidate_chunks`.
2. **Sparse Search:** Chấm điểm theo thuật toán BM25 có phạt độ dài văn bản (`length_penalty = math.log(len(c_tokens) + 1.0)`).
3. **RRF Scoring:** Tính điểm hợp nhất cho từng chunk ID:
   $$\text{RRF\_Score}(d) = \frac{1}{60 + \text{rank}_{\text{dense}}(d)} + \frac{1}{60 + \text{rank}_{\text{sparse}}(d)}$$
4. **Lọc ngưỡng tương đồng & Khử trùng lặp (Deduplication):** Loại bỏ chunk có `raw_sim < 0.15` và khử lặp nội dung tương tự trước khi chọn ra `Top 4` chunks chất lượng nhất.

#### Bước 4: Chống ảo giác bằng SQL Ground Truth Binding (`context.py`)
Module `FinancialContextBuilder` trực tiếp lấy dữ liệu từ PostgreSQL:
* Rút trích `total_income`, `total_expense`, `net_cashflow`, `accounts_balance`.
* Ép AI tuân thủ System Prompt: *"CHỈ được sử dụng các số liệu trong context. Nếu không có dữ liệu, hãy trả lời chưa có giao dịch, tuyệt đối không bịa số liệu."*

#### Bước 5: Tự động hóa hành động qua Function Calling (`tools.py`)
Khai báo Tool Calling Schema để LLM tự quyết định thực thi:
* Khi người dùng chat: *"Vừa đổ xăng 50k bằng ví Tiền mặt"*:
  * LLM trích xuất: `{"action": "create_transaction", "amount": 50000, "category": "Đi lại", "wallet": "Tiền mặt", "type": "EXPENSE"}`.
  * Backend gọi trực tiếp service `create_transaction()` trong DB và trả về kết quả đã lưu thành công.

---

## 📷 III. CHI TIẾT CÔNG NGHỆ & XÂY DỰNG PHÂN HỆ OCR VISION (HÓA ĐƠN)

*File mã nguồn phụ trách chính:* `apps/api/app/ai/receipt.py`, `apps/api/app/ai/routes.py`, `apps/api/app/ai/categorization.py`

### 1. Bảng Thông Số & Công Nghệ Sử Dụng (Tech Stack)
* **Mô hình Thị giác Máy tính (Vision AI):** **Gemini 3.1 Flash-Lite Multimodal Vision API**.
* **Định dạng Dữ liệu Đầu vào:** Base64 Data URL (`data:image/jpeg;base64,...`) hoặc Multipart Binary Stream từ Camera/Thư viện ảnh điện thoại.
* **Định dạng Dữ liệu Đầu ra:** Strict JSON Object qua tham số `generationConfig: {"response_mime_type": "application/json"}`.
* **Thư viện Kiểm thực & Chuẩn hóa:** Pydantic v2 Dataclasses (`ReceiptDraft`, `ReceiptExtractionResult`, `ReceiptItem`).
* **Thuật toán Phân loại Danh mục Tự động:** Heuristic Rule-Based Keyword Matcher kết hợp Semantic Embedding Categorization.

---

### 2. Quy Trình Xây Dựng & Phát Triển OCR Từng Bước

```
┌──────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
│   CLIENT CAMERA  │ ───► │  POST /receipts/extract │ ───► │  Gemini Vision API Call │
│  Chụp ảnh/Upload │      │  Check MIME & Size      │      │  Prompt trích xuất JSON │
└──────────────────┘      └─────────────────────────┘      └────────────┬────────────┘
                                                                        │
                                                                        ▼
┌──────────────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
│  Receipt Confirmation UI │ ◄─── │  Confidence Validation  │ ◄─── │  Receipt Normalization  │
│  Hiển thị bảng duyệt     │      │  Check tổng tiền vs món │      │  Parse ngày, tiền, món  │
└────────────┬─────────────┘      └─────────────────────────┘      └─────────────────────────┘
             │
             ▼
┌──────────────────────────┐      ┌─────────────────────────┐
│  POST /receipts/confirm  │ ───► │  Double-Entry Commit    │
│  Lưu vào Sổ giao dịch    │      │  Cập nhật số dư ví      │
└──────────────────────────┘      └─────────────────────────┘
```

#### Bước 1: Tiếp nhận và Tiền xử lý Ảnh (`apps/api/app/ai/routes.py`)
* Client gửi ảnh hóa đơn qua endpoint `POST /api/v1/ai/receipts/extract`.
* Tách Header Base64 và MIME type:
  ```python
  if source.startswith("data:") and ";base64," in source:
      header, base64_data = source.split(";base64,", 1)
      mime_type = header.replace("data:", "")
  ```

#### Bước 2: Thiết kế Prompt Trích xuất Cấu trúc Chuyên sâu (`receipt.py`)
Nhóm trưởng thiết lập Prompt bắt buộc Gemini trả về JSON thuần:
```python
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
```
Gửi payload đa phương thức (`contents.parts: [text, inline_data]`) với `response_mime_type: application/json`.

#### Bước 3: Chuẩn hóa & Đánh giá Độ tin cậy (Confidence & Verification)
Hàm `extract_receipt(payload)` trong `receipt.py` thực thi kiểm tra chặt chẽ:
* Loại bỏ dấu chấm, dấu phẩy trong chuỗi số tiền để ép kiểu thành số nguyên `int`.
* **So khớp tính toàn vẹn (Cross-validation):**
  - Tính tổng tiền các món: $S = \sum \text{item.amount}$.
  - So sánh $S$ với trường `total` của hóa đơn.
  - Nếu độ lệch quá lớn (> 10%) hoặc thiếu trường `merchant`, hệ thống tự động gán trạng thái `status = "LOW_CONFIDENCE"` và đánh dấu `review_required = True`.
* **Phát hiện trùng lặp (Duplicate Detection):** Kiểm tra xem trong vòng 24 giờ qua người dùng đã có giao dịch nào trùng khớp cả `merchant`, `date` và `total` hay chưa. Nếu có, gắn `duplicate = True` để cảnh báo quét trùng.

#### Bước 4: Tự động Ánh xạ Danh mục Chi tiêu (Category Auto-Mapping)
Module `categorization.py` phân tích chuỗi văn bản của `merchant` và `items`:
* Tự động gán: `"Highlands"`, `"Phúc Long"`, `"Cơm tấm"` $\rightarrow$ `Ăn uống`.
* Gán: `"WinMart"`, `"Bách Hóa Xanh"`, `"Co.opmart"` $\rightarrow$ `Đi chợ / Siêu thị`.
* Gán: `"Petrolimex"`, `"Xăng dầu"` $\rightarrow$ `Di chuyển`.
* Trả về kết quả cho Frontend hiển thị hộp thoại duyệt nhanh, người dùng chỉ cần nhấn **"Xác nhận"** là API `POST /api/v1/ai/receipts/confirm` sẽ tự động ghi sổ.

---

## ⚙️ IV. CHI TIẾT CÔNG NGHỆ & XÂY DỰNG PHÂN HỆ BACKEND CORE (FASTAPI)

*File mã nguồn phụ trách chính:* `apps/api/app/main.py`, `apps/api/app/core/`, `apps/api/app/db/`, `apps/api/app/{auth,accounts,transactions,budget_goals,analytics,dashboard}/`

### 1. Bảng Thông Số & Công Nghệ Sử Dụng (Tech Stack)
* **Ngôn ngữ lập trình:** **Python 3.12+** với Strict Type Annotations.
* **Web Framework:** **FastAPI 0.115+** (Asynchronous, High performance, chuẩn OpenAPI 3.1 & JSON Schema).
* **ASGI Server:** **Uvicorn 0.34+** với uvloop tăng tốc độ xử lý I/O.
* **Cơ sở dữ liệu (RDBMS):** **PostgreSQL 18** (Hỗ trợ mở rộng `pgvector`, ACID compliant).
* **Database Driver & ORM:** **SQLAlchemy 2.0** (Mapped Classes, Async/Sync Engine, Connection Pooling) kết hợp driver **`psycopg 3` (psycopg binary 3.2+)**.
* **Database Migration:** **Alembic 1.19+** (Version control cho schema CSDL).
* **Xác thực & Bảo mật (Auth & Security):** **PyJWT 2.10+** (HMAC-SHA256), **`pwdlib[argon2]`** và **`bcrypt`** (12 work rounds).
* **Data Validation & Settings:** **Pydantic v2** & **pydantic-settings 2.7+**.
* **Caching & Message Broker:** **Redis 8** (`redis>=5.2`) cho session, response caching và token atomic rate limit.
* **Testing Suite:** **Pytest 8.3+**, `httpx 0.28+`, `pytest-asyncio`.

---

### 2. Kiến Trúc Hệ Thống & Các Nguyên Lý Thiết Kế Lõi

#### A. Kiến trúc Clean Architecture / Modular Monolith
Hệ thống được Nhóm trưởng module hóa thành các domain độc lập trong `apps/api/app/`:
```
apps/api/app/
├── auth/           # Đăng ký, đăng nhập, JWT, device session revocation
├── accounts/       # Quản lý tài khoản, đa ví (Tiền mặt, Ngân hàng, Thẻ tín dụng, Momo)
├── transactions/   # Nghiệp vụ kế toán kép: Thu, Chi, Chuyển khoản, Định kỳ
├── budget_goals/   # Hạn mức ngân sách danh mục, mục tiêu tiết kiệm tích lũy
├── analytics/      # Tính toán dòng tiền, phân bổ tỷ trọng chi tiêu, cashflow
├── dashboard/      # Tổng hợp KPI cards cho màn hình trang chủ
├── ai/             # RAG Pipeline, Gemini LLM Gateway, OCR Vision, Tool Calling
├── db/             # SQLAlchemy Engine, Session, Models (finance.py)
└── core/           # Config, Security, Exception Handlers, Logging, Tracing
```

#### B. Cơ chế Kế toán kép (Double-Entry Bookkeeping) trong `transactions/service.py`
Để tránh sai lệch dòng tiền, mọi giao dịch được biểu diễn bằng các bút toán nợ/có (`TransactionEntry`) với các loại `EntryType` (DEBIT / CREDIT):
* **Giao dịch Chi tiêu (EXPENSE):**
  - Trừ số dư ví: `Account.current_balance -= amount`.
  - Tạo bút toán nợ vào danh mục chi tiêu, bút toán có xuất quỹ từ ví.
* **Giao dịch Chuyển khoản nội bộ (TRANSFER):**
  - Thực hiện đồng thời: Giảm số dư ví nguồn $A$, tăng số dư ví đích $B$.
  - Toàn bộ thao tác chạy trong một **ACID Database Transaction**:
    ```python
    source_acc = _owned_account(db, user, source_account_id)
    dest_acc = _owned_account(db, user, destination_account_id)
    source_acc.current_balance -= amount
    dest_acc.current_balance += amount
    db.commit()  # Chỉ commit khi cả 2 cập nhật thành công
    ```

#### C. Giải quyết bài toán Race Condition bằng Khóa bi quan (Pessimistic Locking)
Tại hàm `_owned_account()` trong `transactions/service.py`, Nhóm trưởng sử dụng khóa mức hàng của PostgreSQL:
```python
def _owned_account(db: Session, user: User, account_id: str) -> Account:
    account = db.scalar(
        select(Account)
        .where(Account.id == account_id, Account.user_id == user.id)
        .with_for_update()  # SELECT ... FOR UPDATE (Pessimistic Lock)
    )
    ...
```
*Tác dụng:* Khi người dùng thực hiện 2 giao dịch đồng thời (ví dụ vừa thanh toán hóa đơn vừa quét OCR), request đến sau sẽ phải chờ request trước hoàn thành giao dịch, đảm bảo số dư không bao giờ bị tính toán sai do tranh chấp tài nguyên (Concurrency Conflict).

#### D. Cơ chế Chống Trùng lặp Giao dịch (Idempotency Key)
* Header `Idempotency-Key` được kiểm tra trước khi ghi nhận giao dịch.
* Nếu cùng một key được gửi lại trong vòng 60 giây (do mạng chập chờn hoặc người dùng ấn đúp nút lưu), hệ thống phát hiện và kích hoạt lỗi `IdempotencyConflictError`, trả về HTTP 409 Conflict thay vì tạo 2 giao dịch giống hệt nhau.

#### E. Cơ chế Cảnh báo Ngân sách Tự động (Budget Threshold Alerts)
* Khi một giao dịch chi tiêu được tạo thành công, service tự động tính toán tổng chi tiêu của danh mục đó trong tháng hiện tại:
  $$\text{Percentage} = \left( \frac{\text{Current Spent}}{\text{Budget Limit}} \right) \times 100\%$$
* Nếu $\text{Percentage} \ge 80\%$: Kích hoạt cờ cảnh báo mức vàng (`WARNING`).
* Nếu $\text{Percentage} \ge 100\%$: Kích hoạt cảnh báo vượt ngân sách mức đỏ (`EXCEEDED`) và đẩy thông báo tức thì lên ứng dụng.

---

### 3. Vòng Đời Xây Dựng & Triển Khai Backend (Development Lifecycle)
1. **Thiết kế Models:** Khởi tạo các bảng trong `db/models/finance.py`.
2. **Sinh Migration:** Sử dụng Alembic tự động phát hiện thay đổi mô hình và tạo migration scripts (`alembic revision --autogenerate`).
3. **Lập trình Business Logic & Services:** Tách rời hoàn toàn khỏi router để dễ dàng viết Unit Test độc lập.
4. **Kiểm thử tự động (Pytest):** Xây dựng bộ test suite kiểm tra độ chính xác của số dư ví, kịch bản chuyển khoản âm tiền, kịch bản token hết hạn và kịch bản phân quyền.
5. **Đóng gói Docker:** Viết Dockerfile đa tầng (Multi-stage build) và đưa vào `docker-compose.dev.yml` phục vụ vận hành cùng PostgreSQL 18 và Redis 8.


---

## 🗄️ V. CHI TIẾT CÔNG VIỆC 4: QUẢN TRỊ HỆ THỐNG & CƠ SỞ DỮ LIỆU

*File mã nguồn phụ trách chính:* `apps/api/app/db/models/finance.py`, `apps/api/migrations/`, `alembic.ini`

### 1. Thiết kế Cơ sở dữ liệu chuẩn hóa 3NF
Nhóm trưởng trực tiếp thiết kế Lược đồ quan hệ thực thể (ERD) gồm các bảng cốt lõi:
* `users`: Lưu trữ thông tin định danh, email, mật khẩu băm, vai trò, cài đặt tiền tệ.
* `wallets`: Quản lý danh sách các ví/tài khoản của người dùng, loại ví, số dư hiện tại.
* `categories`: Danh mục phân cấp cha - con (Parent - Child), phân loại Thu/Chi, màu sắc và icon.
* `transactions`: Bảng lưu vết giao dịch thu, chi, chuyển tiền, thời gian, ghi chú, trạng thái.
* `budgets`: Thiết lập hạn mức chi tiêu theo tháng và danh mục.
* `savings_goals`: Quản lý các mục tiêu tiết kiệm tài chính cá nhân.
* `embeddings`: Lưu trữ các đoạn tri thức tài chính và vector 768 chiều phục vụ RAG.
* `audit_logs`: Ghi nhận nhật ký hệ thống phục vụ an ninh và kiểm toán.

### 2. Quản trị Extension pgvector & Tối ưu hóa Vector Search
* Cài đặt và kích hoạt extension vector trên PostgreSQL 18:
  ```sql
  CREATE EXTENSION IF NOT EXISTS vector;
  ```
* Định nghĩa cột vector 768 chiều trong SQLAlchemy Model:
  ```python
  from pgvector.sqlalchemy import Vector
  embedding = Column(Vector(768), nullable=True)
  ```
* **Đánh chỉ mục Vector (Vector Indexing):** Tạo chỉ mục **HNSW (Hierarchical Navigable Small World)** hoặc **IVFFlat** với khoảng cách Cosine:
  ```sql
  CREATE INDEX idx_embeddings_vector ON embeddings 
  USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
  ```
  *Ý nghĩa kỹ thuật:* Giảm độ phức tạp tìm kiếm vector từ $O(N)$ xuống $O(\log N)$, phản hồi kết quả tìm kiếm ngữ cảnh chỉ trong vài mili-giây.

### 3. Quản trị Migration với Alembic & Tối ưu hóa Truy vấn
* Nhóm trưởng quản lý toàn bộ vòng đời thay đổi cấu trúc CSDL:
  - Lệnh tạo migration: `alembic revision --autogenerate -m "create_finance_and_vector_tables"`
  - Lệnh nâng cấp CSDL: `alembic upgrade head`
* Đánh chỉ mục B-Tree trên các trường khóa ngoại và các trường thường xuyên lọc: `user_id`, `wallet_id`, `category_id`, `transaction_date`.
* Cấu hình **Connection Pooling** trong SQLAlchemy (`pool_size=10`, `max_overflow=20`, `pool_recycle=1800`) tránh cạn kiệt connection khi có nhiều request đồng thời.

---

## 🚀 VI. CHI TIẾT CÔNG VIỆC 5: DEVOPS & VẬN HÀNH HẠ TẦNG

*File mã nguồn phụ trách chính:* `infra/docker/`, `apps/api/Dockerfile`, `apps/worker/Dockerfile`, `.env.example`

### 1. Đóng gói hệ thống bằng Docker & Docker Compose
Nhóm trưởng thiết kế môi trường container hóa chuẩn production đảm bảo tính nhất quán trên mọi máy tính ("chạy được ở máy tôi là chạy được ở máy bạn"):
* **`postgres` container (PostgreSQL 18 + pgvector):**
  - Cấu hình persistent volume `postgres_data` lưu trữ dữ liệu an toàn.
  - Cấu hình healthcheck tự động: `pg_isready -U postgres -d finance_db`.
* **`redis` container (Redis 8 Alpine):**
  - Phục vụ Caching dữ liệu dashboard, lưu trữ session và Redis atomic counter đếm token AI.
  - Healthcheck tự động: `redis-cli ping`.
* **`api` container (FastAPI Service):**
  - Build từ `apps/api/Dockerfile` đa tầng (multi-stage) tối ưu dung lượng.
  - Tự động mount mã nguồn trong môi trường dev để kích hoạt tính năng **Hot Reloading**.
* **`worker` container (Background Worker Service):**
  - Xử lý các tác vụ ngầm như tính toán cảnh báo ngân sách định kỳ và đồng bộ dữ liệu vector.

### 2. Quản lý Biến Môi trường & Bảo Mật Khóa Bí Mật
* Nhóm trưởng quản lý file cấu hình `.env` phân tách giữa Development và Staging:
  - `DATABASE_URL`: Đường dẫn kết nối CSDL PostgreSQL.
  - `REDIS_URL`: Địa chỉ cache server.
  - `JWT_SECRET`: Khóa bí mật băm chữ ký JWT token.
  - `GEMINI_API_KEY`: Khóa API chính thức kết nối Google GenAI.
* **Kiểm tra chống lộ khóa:** Thiết lập file `.gitignore` và công cụ **Gitleaks** (`.gitleaks.toml`) quét tự động toàn bộ mã nguồn trước khi commit, ngăn chặn tuyệt đối việc đẩy API Keys lên GitHub.

### 3. Giám sát Hệ thống (Observability & Logging)
* Cấu hình Structured JSON Logging cho toàn bộ Backend API.
* Gắn **Correlation ID (Trace ID)** vào từng HTTP Request để dễ dàng theo dõi luồng xử lý từ lúc nhận request đến khi gọi LLM và trả kết quả.
* Cung cấp các endpoints chuẩn Kubernetes / Cloud Healthcheck:
  - `GET /health`: Kiểm tra trạng thái sống của dịch vụ API (Liveness Probe).
  - `GET /health/ready`: Kiểm tra tính sẵn sàng kết nối tới PostgreSQL và Redis (Readiness Probe).

---

## 📈 VII. CHI TIẾT CÔNG VIỆC 6: KIỂM SOÁT TIẾN ĐỘ CHUNG (AGILE/SCRUM)

### 1. Phân chia Sprint & Điều phối công việc 4 thành viên
Nhóm trưởng áp dụng mô hình phát triển phần mềm linh hoạt **Agile/Scrum** trong 9 tuần thực hiện:
* **Sprint 1 (Tuần 1 - Tuần 3): Khảo sát, Thiết kế & Khởi tạo Nền tảng**
  - Điều phối Tuấn hoàn thiện Kiến trúc hệ thống & Wireframe UI.
  - Điều phối Đức xây dựng biểu đồ Use Case, Sequence Diagram & Master Test Plan.
  - Điều phối Hoàng hoàn thiện tài liệu đặc tả SRS, SDD & khảo sát bài toán.
  - Bản thân Hà: Nghiên cứu RAG, OCR, thiết kế ERD CSDL và thiết lập chuẩn mã nguồn.
* **Sprint 2 (Tuần 4 - Tuần 6): Xây dựng Chức năng Cốt lõi & Tích hợp Giao diện**
  - Điều phối Tuấn lập trình toàn diện UI Flutter (Auth, Dashboard, Biểu đồ, Sổ giao dịch).
  - Điều phối Đức kiểm thử chức năng (Tester), bắt lỗi số dư và hỗ trợ kết nối API.
  - Điều phối Hoàng cập nhật tài liệu kỹ thuật, chuẩn bị 100+ giao dịch seeding data.
  - Bản thân Hà: Lập trình hạ tầng Docker, Auth JWT, Core API Giao dịch, Ngân sách và Gateway AI.
* **Sprint 3 (Tuần 7 - Tuần 9): Tích hợp AI (RAG + OCR), Kiểm thử toàn diện & Bảo vệ**
  - Điều phối Tuấn hoàn thiện UI Chatbot AI streaming, UI Camera OCR và Slide thuyết trình.
  - Điều phối Đức chạy kiểm thử toàn diện E2E, bảo mật, tải và nghiệm thu chất lượng.
  - Điều phối Hoàng hoàn thiện Báo cáo đồ án chính thức, tài liệu Hướng dẫn sử dụng và kịch bản Q&A.
  - Bản thân Hà: Lập trình pipeline RAG hoàn chỉnh, OCR Vision, tối ưu hóa hệ thống, đóng gói Docker sản xuất và triển khai máy chủ.

### 2. Quy trình Review Mã Nguồn (Code Review & Git Flow)
* Thiết lập cấu trúc nhánh chuẩn: `main` (Production) $\leftarrow$ `develop` (Staging/Integration) $\leftarrow$ `feature/*`.
* Yêu cầu mọi thành viên tạo Pull Request (PR) trước khi merge vào `develop`.
* Nhóm trưởng trực tiếp kiểm duyệt (Review) từng dòng code: kiểm tra chuẩn PEP8 (Ruff), kiểm tra tính an toàn dữ liệu, ngăn ngừa rò rỉ bộ nhớ hoặc lỗi race condition trong tính toán tiền tệ.

---

## 🗓️ VIII. BẢNG PHÂN RÃ CÔNG VIỆC THEO 9 TUẦN CỦA NHÓM TRƯỞNG

| Tuần | Mục tiêu công việc chính của Nhóm trưởng (Phạm Tiến Hà) | Sản phẩm bàn giao cụ thể (Deliverables) | Tiêu chí nghiệm thu (Checklist) |
| :---: | :--- | :--- | :--- |
| **Tuần 01**<br>*(27/07 – 02/08)* | • Thiết lập WBS, thống nhất mốc bàn giao và kiểm soát tiến độ chung toàn nhóm.<br>• Nghiên cứu khả thi giải pháp AI (Gemini Flash, pgvector RAG, OCR Vision). | • Bảng kế hoạch dự án 9 tuần hoàn chỉnh.<br>• Báo cáo khảo sát công nghệ AI & OCR. | ✅ Phân công rõ ràng 4 vai trò.<br>✅ Thử nghiệm thành công kết nối API Gemini. |
| **Tuần 02**<br>*(03/08 – 09/08)* | • Nghiên cứu kỹ thuật nhúng Vector (Embeddings) và thiết kế sơ bộ pipeline RAG & OCR.<br>• Thiết lập môi trường quản trị mã nguồn (Git branching, conventions), cấu hình base template Backend FastAPI. | • Base repository FastAPI chuẩn Clean Architecture.<br>• Tài liệu kỹ thuật sơ bộ về kiến trúc RAG. | ✅ Template API chạy được `/health`.<br>✅ Định nghĩa chuẩn coding convention (Ruff). |
| **Tuần 03**<br>*(10/08 – 16/08)* | • Thiết kế cấu trúc CSDL quan hệ (ERD): bảng người dùng, ví, giao dịch, ngân sách, mục tiêu, vector embeddings.<br>• Thiết kế chi tiết phân hệ AI: RAG Context Retrieval và Function Calling schema. | • Bản vẽ thiết kế CSDL (ERD Diagram).<br>• Lược đồ bảng `embeddings` với extension `pgvector`.<br>• Tài liệu thiết kế phân hệ AI. | ✅ ERD chuẩn hóa 3NF, không dư thừa dữ liệu.<br>✅ RAG pipeline định nghĩa rõ 2 lớp dữ liệu. |
| **Tuần 04**<br>*(17/08 – 23/08)* | • Thiết kế chi tiết các RESTful API endpoints Backend (Auth, Wallets, Transactions, Budgets, Analytics, AI).<br>• Thiết kế cấu trúc Prompting chuyên sâu cho Trợ lý tài chính, cơ chế Guardrails và PII Masking. | • File Swagger / OpenAPI Spec chi tiết.<br>• Bộ System Prompts mẫu cho Gemini AI.<br>• Thuật toán lọc PII Masking và chống injection. | ✅ Mọi endpoint có schema Request/Response rõ ràng.<br>✅ Prompt có quy tắc chống ảo giác chặt chẽ. |
| **Tuần 05**<br>*(24/08 – 30/08)* | • Khởi tạo hạ tầng DevOps: Docker Compose (PostgreSQL 18 + pgvector, Redis Cache).<br>• Lập trình Backend phân hệ Auth Service (Đăng ký, Đăng nhập bcrypt, JWT, Session).<br>• Lập trình Gateway kết nối mô hình Gemini AI ban đầu. | • File `docker-compose.dev.yml` khởi chạy hoàn chỉnh.<br>• Bộ API `/api/v1/auth/*` hoàn chỉnh.<br>• Module `AIGateway` kết nối Google GenAI SDK. | ✅ `docker compose up` chạy mượt mà 3 containers.<br>✅ Đăng nhập trả về JWT hợp lệ, bảo mật mật khẩu. |
| **Tuần 06**<br>*(31/08 – 06/09)* | • Lập trình Backend phân hệ Quản lý tài khoản/ví và Giao dịch tài chính (Thu, Chi, Chuyển khoản nội bộ).<br>• Lập trình Backend phân hệ Hạn mức ngân sách (Budget Alerts), Mục tiêu tiết kiệm và API Dashboard thống kê. | • Phân hệ `/api/v1/accounts` và `/api/v1/transactions`.<br>• Phân hệ `/api/v1/budgets` và `/api/v1/goals`.<br>• API thống kê `/api/v1/dashboard/summary`. | ✅ Kế toán kép chạy chính xác, không lệch số dư.<br>✅ Chuyển khoản nội bộ chạy trong ACID Transaction. |
| **Tuần 07**<br>*(07/09 – 13/09)* | • Xây dựng pipeline RAG hoàn chỉnh: vector hóa lịch sử tài chính với pgvector, Semantic Search, tích hợp Function Calling.<br>• Xây dựng module OCR Vision AI: bóc tách tự động thông tin từ ảnh chụp hóa đơn (Merchant, Date, Total, Items). | • Pipeline RAG trong `apps/api/app/ai/rag/`.<br>• Module OCR bóc tách hóa đơn trong `receipt.py`.<br>• API `/api/v1/ai/chat` và `/api/v1/ai/receipts/extract`. | ✅ Chatbot trả lời chuẩn số liệu ví của từng user.<br>✅ OCR bóc tách chính xác tên quán và tổng tiền. |
| **Tuần 08**<br>*(14/09 – 20/09)* | • Khắc phục lỗi phát hiện qua kiểm thử, tối ưu hóa truy vấn CSDL PostgreSQL và caching Redis.<br>• Đóng gói hoàn chỉnh hệ thống bằng Docker Compose chuẩn sản xuất (API, Worker, Postgres pgvector, Redis). | • Hệ thống Backend tối ưu thời gian phản hồi < 200ms.<br>• Image Docker sản xuất đa tầng (Multi-stage build).<br>• Script tự động hóa triển khai hệ thống. | ✅ Không còn lỗi logic số dư và lỗi timeout API.<br>✅ Hệ thống đóng gói sẵn sàng mang đi demo. |
| **Tuần 09**<br>*(21/09 – 27/09)* | • Triển khai chính thức hệ thống lên môi trường máy chủ thử nghiệm, thiết lập cơ chế sao lưu CSDL tự động.<br>• Phối hợp tổng duyệt toàn diện kịch bản demo và tham gia bảo vệ đồ án trước Hội đồng. | • Hệ thống chạy ổn định trên môi trường staging.<br>• File backup CSDL `database_dump.sql`.<br>• Kịch bản demo luồng AI & OCR trực tiếp ấn tượng. | ✅ Hệ thống vận hành liên tục không lỗi.<br>✅ Trả lời tự tin mọi câu hỏi phản biện kỹ thuật. |

---

## 🎯 IX. BỘ CÂU HỎI & ĐÁP PHẢN BIỆN CHUYÊN SÂU DÀNH CHO NHÓM TRƯỞNG TRƯỚC HỘI ĐỒNG

### ❓ Câu 1: Tại sao em không chọn phương pháp Fine-tuning mô hình ngôn ngữ mà lại chọn kiến trúc RAG?
> **Trả lời:**  
> Kính thưa Hội đồng, dữ liệu tài chính của người dùng là dữ liệu biến động liên tục theo thời gian thực (từng phút người dùng có thể phát sinh giao dịch mới).  
> 1. Nếu sử dụng **Fine-tuning**: Mỗi khi có giao dịch mới, ta không thể huấn luyện lại mô hình vì chi phí GPU cực kỳ đắt đỏ và tốn thời gian. Hơn nữa, Fine-tuning rất dễ gặp hiện tượng **Catastrophic Forgetting** (mô hình bị suy giảm khả năng suy luận ngôn ngữ gốc).  
> 2. Chúng em lựa chọn **RAG (Retrieval-Augmented Generation)** vì RAG tách bạch rạch ròi giữa:  
>    - **Bộ não suy luận ngôn ngữ:** Pre-trained LLM (Gemini 3.1 Flash-Lite).  
>    - **Dữ liệu thực tế (Ground Truth):** Được module `FinancialContextBuilder` truy vấn trực tiếp từ PostgreSQL và bơm vào Context Window tại thời điểm nhận request. Điều này đảm bảo tính cập nhật thời gian thực 100% và loại bỏ hoàn toàn nguy cơ ảo giác số liệu.

### ❓ Câu 2: Em hãy giải thích cơ chế Vector Search và tại sao lại dùng extension pgvector thay vì các Vector DB chuyên dụng như Milvus hay Pinecone?
> **Trả lời:**  
> - **Cơ chế Vector Search:** Văn bản tài chính được mô hình `text-embedding-004` biến đổi thành Vector 768 chiều. Khi người dùng đặt câu hỏi, câu hỏi cũng được chuyển thành Vector 768 chiều. Hệ thống sử dụng toán tử khoảng cách góc Cosine (`<=>`) trên PostgreSQL để tìm ra các vector tri thức gần nhất với vector câu hỏi.  
> - **Lý do chọn pgvector:**  
>   - Đồ án quản lý tài chính cá nhân đòi hỏi sự gắn kết chặt chẽ giữa dữ liệu quan hệ (Người dùng, Ví, Giao dịch) và dữ liệu ngữ nghĩa (Vector Embeddings).  
>   - `pgvector` cho phép chúng em lưu trữ và truy vấn cả dữ liệu quan hệ và dữ liệu vector trong **cùng một cơ sở dữ liệu PostgreSQL duy nhất**. Điều này giúp hệ thống đạt chuẩn tính toán ACID, không phải đồng bộ dữ liệu phức tạp giữa 2 hệ thống độc lập, tiết kiệm tài nguyên hạ tầng và chi phí vận hành.

### 3. Làm thế nào để giải quyết bài toán Race Condition khi người dùng thực hiện nhiều giao dịch cùng lúc?
> **Trả lời:**  
> Để xử lý xung đột số dư khi có nhiều request đồng thời (ví dụ người dùng vừa quét hóa đơn vừa bấm tạo giao dịch):  
> 1. Chúng em sử dụng cơ chế **Pessimistic Locking (Khóa bi quan)** của PostgreSQL thông qua cú pháp `SELECT ... FOR UPDATE` trong SQLAlchemy trên bản ghi ví (`wallets`).  
> 2. Mọi thao tác cộng/trừ tiền và ghi nhận giao dịch đều được đóng gói trong một **Database Transaction**. Request nào đến trước sẽ giữ khóa của ví đó, cập nhật số dư xong thì mới giải phóng khóa cho request tiếp theo. Nhờ đó, số dư ví không bao giờ bị sai lệch do Race Condition.

### ❓ Câu 4: Phân hệ OCR hoạt động thế nào khi ảnh chụp hóa đơn bị mờ hoặc bị mất góc?
> **Trả lời:**  
> Trong module `apps/api/app/ai/receipt.py`, chúng em thiết kế cơ chế xử lý ngoại lệ đa tầng:  
> 1. Khi ảnh mờ hoặc chất lượng thấp, Gemini Vision API sẽ cố gắng trích xuất các trường nhận dạng được và trả về điểm tin cậy tương ứng.  
> 2. Hàm `_normalize_extraction` sẽ kiểm tra tính toàn vẹn: nếu thiếu các trường bắt buộc như `total` hoặc tổng tiền các món không khớp với `total`, hệ thống sẽ gắn trạng thái `LOW_CONFIDENCE` và bật cờ `review_required=True`.  
> 3. Phía Frontend sẽ không tự động lưu mà mở hộp thoại **Receipt Confirmation Modal**, làm nổi bật các trường dữ liệu bị nghi ngờ để người dùng kiểm tra và chỉnh sửa nhanh bằng tay trước khi lưu vào CSDL.

### ❓ Câu 5: Với vai trò Trưởng nhóm, em làm thế nào khi có thành viên trong nhóm bị trễ tiến độ (Behind Schedule)?
> **Trả lời:**  
> Trong mô hình Agile/Scrum của nhóm:  
> 1. Chúng em tổ chức họp nhanh Daily Standup để phát hiện sớm các "blocker" kỹ thuật từ đầu ngày chứ không đợi đến cuối tuần.  
> 2. Nếu một thành viên gặp khó khăn kỹ thuật (ví dụ: gặp lỗi kết nối API hay cấu hình CSDL), em với vai trò Tech Lead cùng bạn Lưu Anh Đức (Support Lead) sẽ trực tiếp tham gia pair-programming để tháo gỡ điểm nghẽn.  
> 3. Nếu khối lượng công việc của bạn đó quá lớn, em sẽ chủ động điều chỉnh lại backlog của Sprint, ưu tiên hoàn thành các tính năng MVP (Minimum Viable Product) cốt lõi trước, dời các tính năng phụ sang Sprint tiếp theo để đảm bảo dự án luôn bám sát mốc bàn giao của môn học.

---
*Tài liệu này được biên soạn độc quyền và bảo lưu cấu trúc chuẩn cho Nhóm trưởng **Phạm Tiến Hà** phục vụ báo cáo tiến độ và bảo vệ đồ án tốt nghiệp.*
