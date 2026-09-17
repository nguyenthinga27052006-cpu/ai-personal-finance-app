# 🧠 TÀI LIỆU BÁO CÁO & BẢO VỆ CHUYÊN SÂU: THÀNH VIÊN 3 - AI ENGINE & RAG SPECIALIST

---

## 👨‍💻 I. THÔNG TIN THÀNH VIÊN & NỀN TẢNG CÔNG NGHỆ
* **Họ và tên**: Thành viên 3 (AI & Data Specialist)
* **Vai trò**: Trưởng nhóm Trí tuệ Nhân tạo (AI Engine, RAG Architecture, Prompt Engineering & AI Security)
* **Ngôn ngữ & Thư viện Core**: 
  - **Language**: **Python 3.12**
  - **LLM SDK**: **Google GenAI SDK (`google-genai`)**
  - **LLM Model**: **Google Gemini 3.1 Flash Lite / Gemini 1.5 Flash** (Mô hình đa phương thức tốc độ cao, hỗ trợ Context Window lớn 1M+ tokens)
  - **Embedding Model**: **`text-embedding-004` (Vector 768 chiều, Cosine Similarity distance)**
  - **RAG Technique**: **Hybrid Retrieval (Dense Vector Search 768-dim + Sparse Lexical BM25)** kết hợp thuật toán **Reciprocal Rank Fusion (RRF)**
  - **Data Binding**: **2-Layer Binding (SQL Ground Truth + Vector Knowledge Chunks)**
  - **Output Validation**: Pydantic v2 Strict JSON Parsing (`AIOutput`)

---

## 🎯 II. CHI TIẾT KỸ THUẬT & NHIỆM VỤ ĐÃ THỰC HIỆN

### 1. Phương Pháp "Huấn Luyện" AI: In-Context Learning (RAG) vs Fine-Tuning
Dự án **không huấn luyện lại trọng số mô hình từ đầu (No Weight Re-training)** và **không chọn Fine-tuning**, mà sử dụng **In-Context Learning qua kiến trúc RAG**:

```
                              ┌──────────────────────────────────┐
                              │ Mô hình Pre-trained Gemini Flash │
                              │   (Reasoning & Language Engine)  │
                              └────────────────┬─────────────────┘
                                               │
                                               ▼
                              ┌──────────────────────────────────┐
                              │    Dynamic Prompt Context Window │
                              │ (SQL Facts + Knowledge Chunks)   │
                              └──────────────────────────────────┘
```

- **Lý do không Fine-tune**: Dữ liệu tài chính thu/chi của người dùng biến động liên tục từng phút. Fine-tune không thể cập nhật real-time, tốn chi phí GPU đắt đỏ và dễ gây ra rủi ro **Catastrophic Forgetting** (mô hình quên các khả năng ngôn ngữ gốc).
- **Ưu thế của RAG**: Mô hình Gemini đóng vai trò là "bộ não suy luận", còn dữ liệu SQL thực tế từ PostgreSQL 18 đóng vai trò là "Ground Truth" được bơm trực tiếp vào Context Window tại thời điểm nhận request, đảm bảo **độ chính xác 100% và cập nhật real-time**.

### 2. Quy Trình Liên Kết Dữ Liệu Tài Chính (Data Linking Architecture)
- **Layer 1: SQL Data Binding (`FinancialContextBuilder`)**:
  - Kết nối với PostgreSQL DB để rút ra các thông số thực tế của User: Tổng thu nhập (`total_income`), Tổng chi tiêu (`total_expense`), Số dư các ví (`current_balance`), Phân bổ danh mục.
  - Gắn nhãn **Provenance** xác nhận tính chính xác `deterministic=True` cho từng con số.
  - Gắn cờ `insufficient_data=True` khi không có giao dịch trong khoảng thời gian hỏi để ngăn AI đoán mò.
- **Layer 2: Vector Semantic Linking (Knowledge Retrieval)**:
  - Cắt tài liệu tri thức tài chính thành từng Chunk (512 tokens).
  - Chuyển thành Vector 768 chiều qua model `text-embedding-004`.
  - Đo khoảng cách góc Cosine (**Cosine Similarity**) để rút ra bài viết tư vấn phù hợp nhất.

### 3. AI Gateway, Fallback Router & Quản Lý Chi Phí
- **AI Gateway (`AIGateway`)**: Tách biệt hoàn toàn logic AI khỏi HTTP layer.
- **Model Router Fallback**: Tự động chuyển hướng sang OpenAI/FakeProvider trong milliseconds nếu Gemini API gặp sự cố timeout (> 10s).
- **Token Budget Tracker**: Đếm tổng số token tiêu thụ trong ngày theo User ID bằng Redis atomic counter. Giới hạn `50,000 tokens/ngày/user` chống cào bới API.
- **PII Redaction & Injection Defense**: Lọc bỏ mật khẩu/token trước khi gửi qua API và ngắt các câu hỏi cố tình đổi System Prompt (`GuardrailViolation`).

---

## ❓ III. BỘ CÂU HỎI & ĐÁP BẢO VỆ ĐỒ ÁN KÍN KẼ TUYỆT ĐỐI (DÀNH CHO HỘI ĐỒNG)

### ❓ Câu 1: Em hãy giải thích rõ phương pháp "huấn luyện" AI trong đồ án của em?
> **Trả lời kín kẽ**: 
> - Kính thưa Hội đồng, hệ thống của chúng em **không huấn luyện lại trọng số (Weights)** của mô hình AI từ đầu và cũng **không dùng phương pháp Fine-tuning**.
> - Lý do là dữ liệu tài chính thu/chi của người dùng biến động liên tục từng phút. Việc Fine-tuning không thể cập nhật real-time, rất đắt đỏ và dễ làm mô hình bị lỗi "quên kiến thức cũ (Catastrophic Forgetting)".
> - Thay vào đó, chúng em áp dụng phương pháp **In-Context Learning kết hợp kiến trúc RAG (Retrieval-Augmented Generation)**:
>   - Sử dụng **Google Gemini 3.1 Flash** làm Mô hình ngôn ngữ gốc (Pre-trained LLM) có khả năng lý luận ngôn ngữ cực mạnh.
>   - Mỗi khi người dùng đặt câu hỏi, module `FinancialContextBuilder` sẽ truy vấn Cơ sở dữ liệu SQL để lấy số liệu thực tế mới nhất làm "Ground Truth" và đưa trực tiếp vào Context Window của Prompt. Mô hình AI đọc số liệu này và tổng hợp thành câu trả lời chuẩn xác 100%.

### ❓ Câu 2: Em hiểu Embedding là gì? Kích thước Vector Embedding trong hệ thống là bao nhiêu chiều và dùng thuật toán gì để đo khoảng cách?
> **Trả lời kín kẽ**: 
> - **Embedding** là quá trình biến đổi một đoạn văn bản tự nhiên thành một chuỗi số thực nhiều chiều (Vector) biểu diễn ý nghĩa ngữ nghĩa của đoạn văn đó.
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
