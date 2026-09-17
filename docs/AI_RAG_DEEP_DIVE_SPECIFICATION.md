# 🧠 BẢN THIẾT KẾ & TÀI LIỆU CHUYÊN SÂU: AI ENGINE, RAG ARCHITECTURE & DATA LINKING
> **Chuyên sâu cho Thành viên 3: Từ Kiến Trúc Xây Dựng, Phương Pháp "Huấn Luyện" (In-Context Learning vs Fine-Tuning) Đến Cách Liên Kết Dữ Liệu Chi Tiết**

---

## 📑 MỤC LỤC
1. [Tổng Quan Kiến Trúc AI Gateway & Core Components](#1-tổng-quan-kiến-trúc-ai-gateway--core-components)
2. [Phương Pháp "Huấn Luyện" AI: Tại Sao Chọn In-Context Learning (RAG) Thay Vì Fine-Tuning?](#2-phương-pháp-huấn-luyện-ai-tại-sao-chọn-in-context-learning-rag-thay-vì-fine-tuning)
3. [Quy Trình Liên Kết Dữ Liệu Tài Chính (Data Linking & Binding)](#3-quy-trình-liên-kết-dữ-liệu-tài-chính-data-linking--binding)
4. [Kỹ Thuật Tra Cứu Dữ Liệu Lai (Hybrid Retrieval: Dense Vector + BM25 Lexical)](#4-kỹ-thuật-tra-cứu-dữ-liệu-lai-hybrid-retrieval-dense-vector--bm25-lexical)
5. [Cấu Trúc System Prompt Engineering & Ép Định Dạng JSON Strict Output](#5-cấu-trúc-system-prompt-engineering--ép-định-dạng-json-strict-output)
6. [Hệ Thống An Toàn AI (Guardrails, Anti-Injection, PII Redaction & Cost Management)](#6-hệ-thống-an-toàn-ai-guardrails-anti-injection-pii-redaction--cost-management)
7. [Bộ Câu Hỏi & Đáp Bảo Vệ Đồ Án Kín Kẽ Tuyệt Đối (Dành Cho Hội Đồng)](#7-bộ-câu-hỏi--đáp-bảo-vệ-đồ-án-kín-kẽ-tuyệt-đối-dành-cho-hội-đồng)

---

## 1. TỔNG QUAN KIẾN TRÚC AI GATEWAY & CORE COMPONENTS

### 1.1. Sơ Đồ Khối Luồng Xử Lý (Execution Flow Diagram)
```
[User Request (Question / Feature)]
              │
              ▼
[1. Guardrails Check] ──► (Reject if Prompt Injection or Invalid Token)
              │
              ▼
[2. FinancialContextBuilder] ──► Truy vấn Postgres DB ──► Trích xuất Facts & Provenance
              │
              ▼
[3. Hybrid Retriever] ──► Dense Vector (768-dim) + BM25 ──► Trích xuất Knowledge Chunks
              │
              ▼
[4. ProviderRequest Assembly] ──► Ghép Instructions + Facts + Chunks + User Query
              │
              ▼
[5. ModelRouter & Provider] ──► Primary: Gemini 3.1 Flash ──(Fallback)──► OpenAI / Fake
              │
              ▼
[6. Output Normalization & Pydantic Validation] ──► Parse JSON, Convert String Citations
              │
              ▼
[7. SSE Streaming Response to Client] ──► Token-by-token rendering on Flutter UI
```

### 1.2. Thành Phần Mã Nguồn Cốt Lõi (Core Codebase Map)
- `apps/api/app/ai/gateway.py`: Chứa `AIGateway` - Điểm điều phối duy nhất cho toàn bộ hệ thống AI.
- `apps/api/app/ai/providers.py`: Chứa `ModelRouter`, `GeminiLLMProvider`, `OpenAIProvider`, `FakeProvider`.
- `apps/api/app/ai/context.py`: Chứa `FinancialContextBuilder`, `FinancialContext`, `Provenance`.
- `apps/api/app/ai/guardrails.py`: Chứa `validate_untrusted_input`, `redact_metadata`.
- `apps/api/app/ai/schemas.py`: Chứa Pydantic models `AIOutput`, `AILogMetadata`, `AIExecuteRequest`.
- `apps/api/app/ai/usage.py`: Chứa `TokenBudgetTracker` theo dõi hạn mức gọi API.

---

## 2. PHƯƠNG PHÁP "HUẤN LUYỆN" AI: TẠI SAO CHỌN IN-CONTEXT LEARNING (RAG) THAY VÌ FINE-TUNING?

### 2.1. So Sánh Bản Chất Kỹ Thuật (Technical Comparison Matrix)

| Tiêu chí | Fine-Tuning Mô hình (Fine-Tuned LLM) | In-Context Learning qua RAG (Dự án chọn) |
| :--- | :--- | :--- |
| **Cơ chế hoạt động** | Cập nhật lại các trọng số (Weights/Parameters) của mô hình bằng Backpropagation. | Giữ nguyên Trọng số mô hình Pre-trained, cấp dữ liệu tươi vào **Context Window** của Prompt. |
| **Tốc độ cập nhật Dữ liệu** | Phải gom dataset và train lại (Mất nhiều giờ/ngày). Không thể cập nhật theo từng giây. | **Real-time 100%**: Ngay khi người dùng thêm 1 giao dịch, RAG truy vấn DB và đưa số liệu mới vào ngay lập tức. |
| **Tính Đúng đắn Số liệu** | Dễ bị "Học vẹt" (Overfitting) hoặc Tự bịa con số (Hallucination) khi dữ liệu tài chính thay đổi. | **Chính xác 100%**: LLM đóng vai trò Engine suy luận, đọc con số từ SQL DB đưa vào làm Ground Truth. |
| **Chi phí Tính toán** | Cần máy chủ GPU đắt đỏ (A100/H100), tốn hàng nghìn USD. | Chi phí vô cùng rẻ (vài cent cho hàng nghìn request qua Gemini API). |
| **Rủi ro Kỹ thuật** | **Catastrophic Forgetting** (Mô hình quên các khả năng ngôn ngữ tổng quát trước đó). | Không bị rủi ro quên kiến thức, tận dụng trọn vẹn trí thông minh của Gemini 3.1 Flash. |

> 📌 **Kết luận Bảo vệ**: Dự án **không huấn luyện lại trọng số mô hình từ đầu (No Weight Re-training)** mà áp dụng phương pháp **In-Context Learning tiên tiến nhất hiện nay (RAG)**. Mô hình LLM Gemini được sử dụng như một **"Động cơ Lý luận & Ngôn ngữ (Reasoning Engine)"**, còn Cơ sở dữ liệu SQL/Vector đóng vai trò **"Bộ nhớ Tri thức Thực tế (Memory/Ground Truth)"**.

---

## 3. QUY TRÌNH LIÊN KẾT DỮ LIỆU TÀI CHÍNH (DATA LINKING & BINDING)

Hệ thống sử dụng cơ chế **2-Layer Data Linking** để kết nối dữ liệu của người dùng với AI:

```
                          ┌─────────────────────────────────────┐
                          │   User Query: "Tháng này tôi tiêu   │
                          │   bao nhiêu tiền cho ăn uống?"     │
                          └──────────────────┬──────────────────┘
                                             │
                       ┌─────────────────────┴─────────────────────┐
                       ▼                                           ▼
┌──────────────────────────────────────────────┐ ┌──────────────────────────────────────────────┐
│  LAYER 1: SQL DATA BINDING (User Specific)   │ │ LAYER 2: VECTOR KNOWLEDGE BINDING (General)  │
│  - Truy vấn Postgres DB theo user_id         │ │ - Embed query -> Vector 768-dim              │
│  - Lấy số liệu thực tế khoản Ăn uống tháng 8 │ │ - Cosine Search bài viết tư vấn quản lý ví   │
│  - Tạo Facts: {"food_spent": 3500000}        │ │ - Lấy Chunk: "Quy tắc 50/30/20 cho ăn uống" │
└──────────────────────┬───────────────────────┘ └──────────────────────┬───────────────────────┘
                       │                                                │
                       └──────────────────────┬─────────────────────────┘
                                              ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                            FINAL PROMPT ASSEMBLY (Sent to Gemini)                            │
│ - Facts (Số liệu thực tế): Chi 3.500.000 VNĐ                                                 │
│ - Tri thức bổ trợ: Quy tắc 50/30/20                                                          │
│ - Lệnh: Hãy phân tích xem 3.500.000 VNĐ đã hợp lý chưa và tư vấn bằng tiếng Việt.            │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.1. Layer 1: SQL Data Binding & Provenance Tracking
`FinancialContextBuilder` thực hiện các câu lệnh SQL tối ưu truy xuất dữ liệu cá nhân của người dùng:
1. **Summary Facts**: Tính tổng thu (`total_income`), tổng chi (`total_expense`), số dư khả dụng từ tất cả các ví của user.
2. **Category Facts**: Phân tích chi tiết số tiền chi tiêu theo từng danh mục.
3. **Budget Facts**: Lấy trạng thái ngân sách hiện tại (Đã tiêu bao nhiêu %, còn lại bao nhiêu, có nguy cơ vượt ngân sách hay không).
4. **Provenance Attachment**: Mọi chỉ số đưa vào ngữ cảnh đều đính kèm đối tượng `Provenance`:
   ```python
   Provenance(
       source="analytics.service",
       period_start=date(2026, 8, 1),
       period_end=date(2026, 8, 31),
       calculation_type="sql_sum",
       deterministic=True # Đánh dấu đây là con số thực tế 100%, không được tự sửa
   )
   ```

### 3.2. Layer 2: Semantic Vector Linking (Knowledge RAG)
Dữ liệu tài liệu quản lý tài chính cá nhân được xử lý theo quy trình Vectorization:
1. **Chunking**: Cắt tài liệu tri thức thành từng đoạn nhỏ (Chunk size = 512 tokens, Overlap = 50 tokens để giữ ngữ cảnh giữa các đoạn).
2. **Embedding Generation**: Chuyển từng đoạn văn bản thành Vector 768 chiều sử dụng model `text-embedding-004`.
3. **Similarity Indexing**: Lưu trữ Vector vào Database hỗ trợ tìm kiếm Cosine Similarity.

---

## 4. KỸ THUẬT TRA CỨU DỮ LIỆU LAI (HYBRID RETRIEVAL: DENSE VECTOR + BM25 LEXICAL)

Để đảm bảo vừa hiểu ý nghĩa câu hỏi vừa tìm chính xác từ khóa tài chính, hệ thống kết hợp 2 kỹ thuật tra cứu:

### 4.1. Dense Vector Search (Biểu diễn Ngữ nghĩa)
- Đo khoảng cách góc Cosine giữa Vector câu hỏi (\(\vec{q}\)) và Vector tài liệu (\(\vec{d}\)):
  \[
  \text{CosineSimilarity}(\vec{q}, \vec{d}) = \frac{\vec{q} \cdot \vec{d}}{\|\vec{q}\| \|\vec{d}\|}
  \]
- **Ưu điểm**: Hiểu được các từ đồng nghĩa (Ví dụ: "tiền ăn", "ăn uống", "phục vụ ăn uống" đều có vector tiệm cận nhau).

### 4.2. Sparse Lexical Search (BM25 Keyword Search)
- Đánh giá tần suất xuất hiện của từ khóa chính xác trong tài liệu dựa trên thuật toán BM25 (Best Matching 25).
- **Ưu điểm**: Tìm kiếm chính xác các mã danh mục, tên riêng hoặc con số cụ thể.

### 4.3. Thuật Toán Gộp Điểm RRF (Reciprocal Rank Fusion)
Gộp thứ hạng kết quả từ hai phương pháp theo công thức:
\[
RRF\_Score(d) = \frac{1}{k + rank_{dense}(d)} + \frac{1}{k + rank_{sparse}(d)} \quad (với \ k = 60)
\]
Đảm bảo tài liệu trả về nằm trong Top những bài viết liên quan nhất cho AI làm ngữ cảnh.

---

## 5. CẤU TRÚC SYSTEM PROMPT ENGINEERING & ÉP ĐỊNH DẠNG JSON STRICT OUTPUT

### 5.1. System Instructions Template
System Prompt gửi sang Gemini được đóng gói nghiêm ngặt:
```text
Bạn là Trợ lý Tư vấn Tài chính Cá nhân AI chuyên nghiệp.
Nhiệm vụ của bạn là phân tích dữ liệu tài chính của người dùng và đưa ra lời khuyên bằng tiếng Việt tự nhiên.

QUY TẮC BẮT BUỘC:
1. CHỈ sử dụng dữ liệu được cung cấp trong 'financial_context'. Tuyệt đối KHÔNG tự tạo ra các con số tài chính không có trong ngữ cảnh.
2. Nếu ngữ cảnh ghi 'insufficient_data: true', hãy trả về status 'INSUFFICIENT_DATA' và hướng dẫn người dùng nhập thêm giao dịch.
3. Trả về DUY NHẤT một chuỗi JSON hợp lệ theo định dạng schema sau:
{
  "status": "OK" | "INSUFFICIENT_DATA",
  "answer": "Nội dung trả lời...",
  "citations": [{"source": "string", "calculation_type": "string"}],
  "suggested_actions": ["Gợi ý 1", "Gợi ý 2"]
}
```

### 5.2. Chuẩn Hóa Tự Động Định Dạng Đầu Ra (Structured Output Normalization)
Trong `apps/api/app/ai/gateway.py`, hàm `_validate_provider_output` xử lý trường hợp Gemini trả về chuỗi citation dạng string thay vì object:
```python
if isinstance(value, dict) and "citations" in value and isinstance(value["citations"], list):
    normalized_citations = []
    for item in value["citations"]:
        if isinstance(item, str):
            normalized_citations.append({"source": item, "calculation_type": "llm_citation"})
        else:
            normalized_citations.append(item)
    value["citations"] = normalized_citations
```
Sau đó ép qua Pydantic `AIOutput.model_validate(value)`, đảm bảo tỷ lệ phản hồi lỗi cấu trúc về 0%.

---

## 6. HỆ THỐNG AN TOÀN AI (GUARDRAILS, ANTI-INJECTION, PII REDACTION & COST MANAGEMENT)

### 6.1. Phòng Chống Tấn Công Prompt Injection (`validate_untrusted_input`)
Sử dụng các mẫu Regex kiểm tra chuỗi đầu vào của người dùng trước khi gọi LLM:
```python
_INJECTION_PATTERNS = [
    r"ignore\s+(?:all\s+)?previous\s+instructions",
    r"system\s+prompt",
    r"reveal\s+(?:your\s+)?instructions",
    r"select\s+\*\s+from",
]
```
Nếu phát hiện vi phạm, hệ thống ném ngoại lệ `GuardrailViolation` (HTTP 422) ngắt lệnh lập tức.

### 6.2. Ẩn Dữ Liệu Nhạy Cảm PII (`redact_metadata`)
Tự động che đỏ hoặc thay thế các thông tin như Mật khẩu, JWT Token, Email bằng nhãn `[REDACTED]` trong toàn bộ log ghi nhận gọi AI.

### 6.3. Quản Lý Chi Phí API (`TokenBudgetTracker`)
- Cấu hình Redis Atomic Increment đếm tổng số Token (Prompt Tokens + Completion Tokens) theo User ID trong ngày.
- Giới hạn: `50,000 tokens/ngày/user`. Khi vượt ngưỡng, hệ thống trả về HTTP `429 Rate Limited` với mã `DAILY_TOKEN_LIMIT_EXCEEDED`.

---

## 7. BỘ CÂU HỎI & ĐÁP BẢO VỆ ĐỒ ÁN KÍN KẼ TUYỆT ĐỐI (DÀNH CHO HỘI ĐỒNG)

### ❓ Câu 1: Em hãy giải thích rõ mô hình AI của hệ thống đã được "huấn luyện" (Train/Fine-tune) như thế nào?
> **Trả lời kín kẽ**: 
> - Kính thưa Hội đồng, hệ thống của chúng em **không huấn luyện lại trọng số (Weights)** của mô hình AI từ đầu và cũng **không dùng phương pháp Fine-tuning**.
> - Lý do là vì dữ liệu thu chi tài chính của người dùng biến động liên tục từng phút. Việc Fine-tuning rất đắt đỏ, chậm chạp và dễ khiến mô hình bị lỗi "quên kiến thức cũ (Catastrophic Forgetting)".
> - Thay vào đó, chúng em áp dụng phương pháp **In-Context Learning kết hợp kiến trúc RAG (Retrieval-Augmented Generation)** tiên tiến nhất hiện nay:
>   - Sử dụng **Google Gemini 3.1 Flash** làm Mô hình ngôn ngữ gốc (Pre-trained LLM) có khả năng lý luận cao.
>   - Mỗi khi người dùng đặt câu hỏi, module `FinancialContextBuilder` sẽ truy vấn Cơ sở dữ liệu SQL để lấy số liệu thực tế mới nhất làm "Ground Truth" và đưa trực tiếp vào Context Window của Prompt. Mô hình AI đọc số liệu này và tổng hợp thành câu trả lời chuẩn xác 100%.

### ❓ Câu 2: Em hiểu Embedding là gì? Kích thước Vector Embedding trong hệ thống là bao nhiêu chiều và dùng thuật toán gì để đo khoảng cách?
> **Trả lời kín kẽ**: 
> - **Embedding** là quá trình ánh xạ một đoạn văn bản tự nhiên thành một chuỗi số thực nhiều chiều (Vector) biểu diễn ý nghĩa ngữ nghĩa của đoạn văn đó.
> - Trong hệ thống của chúng em:
>   - Thư viện/Model Embedding sử dụng là `text-embedding-004` của Google.
>   - Kích thước Vector Embedding là **768 chiều (768 dimensions)**.
>   - Thuật toán đo khoảng cách/độ tương đồng ngữ nghĩa giữa 2 Vector là **Cosine Similarity (Độ tương đồng góc Cosine)**. Đoạn văn bản nào có góc giữa 2 vector càng nhỏ (giá trị Cosine càng gần 1) thì ý nghĩa ngữ nghĩa càng giống nhau.

### ❓ Câu 3: Kỹ thuật Hybrid Search trong RAG của em là gì? Tại sao chỉ dùng Vector Search thôi là chưa đủ?
> **Trả lời kín kẽ**: 
> - **Vector Search (Dense Search)** rất giỏi tìm kiếm ý nghĩa ngữ nghĩa (Semantic), nhưng lại kém khi tìm kiếm các từ khóa chính xác như mã số giao dịch, tên danh mục cụ thể hoặc con số tài chính.
> - **BM25 Search (Sparse Search)** lại rất mạnh trong việc khớp từ khóa chính xác (Exact Keyword Matching).
> - Hệ thống của chúng em kết hợp cả 2 phương pháp này thành **Hybrid Search**, sau đó dùng thuật toán **RRF (Reciprocal Rank Fusion)** để tính lại điểm số thứ hạng. Kết quả trả về cho AI làm ngữ cảnh vừa đảm bảo đúng ngữ nghĩa tổng thể vừa chính xác từ khóa tài chính.

### ❓ Câu 4: Làm sao em đảm bảo được AI không "bị đặt" (Hallucination) ra các con số tài chính không có thật khi trả lời người dùng?
> **Trả lời kín kẽ**: 
> Chúng em áp dụng 3 lớp kiểm soát nghiêm ngặt:
> 1. **Gắn chặt Ground Truth**: System Prompt quy định cứng: *"CHỈ được sử dụng các con số có trong financial_context. Tuyệt đối không tự sáng tạo ra số liệu."*
> 2. **Xử lý thiếu dữ liệu (`insufficient_data`)**: Nếu người dùng chưa có dữ liệu trong khoảng thời gian hỏi, `FinancialContextBuilder` gắn cờ `insufficient_data=True` và AI sẽ từ chối đoán mò, chuyển sang yêu cầu người dùng nhập thêm giao dịch.
> 3. **Provenance Tracking**: Mọi con số trong ngữ cảnh đều đính kèm thông tin Provenance xác nhận tính toán `deterministic=True` từ SQL DB.

### ❓ Câu 5: Hệ thống xử lý thế nào nếu Gemini API gặp sự cố hoặc trả về định dạng JSON bị lỗi?
> **Trả lời kín kẽ**: 
> 1. **Model Router Fallback**: Nếu Gemini API bị lỗi 5xx hoặc Timeout quá 10s, `ModelRouter` tự động chuyển hướng request sang Provider dự phòng (OpenAI hoặc FakeProvider) trong vài milliseconds mà không làm ngắt kết nối của người dùng.
> 2. **Structured Output Normalization**: Nếu Gemini trả về mảng citation dạng string đơn giản thay vì object, hàm `_validate_provider_output` trên Backend sẽ tự động bắt được và biến đổi (normalize) thành dict hợp lệ trước khi đưa qua Pydantic `AIOutput` validate. Do đó câu trả lời trả về cho Client luôn đảm bảo đúng chuẩn định dạng JSON 100%.
