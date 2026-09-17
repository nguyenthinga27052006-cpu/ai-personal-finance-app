# 📐 PHÂN TÍCH CHI TIẾT QUÁ TRÌNH PHÁT TRIỂN HỆ THỐNG AI PERSONAL FINANCE ASSISTANT
> **Từ Bản Thiết Kế, Nghiên Cứu, Lập Trình Code, Xây Dựng App/Hệ Thống Đến Các Thành Phần Cốt Lõi**

---

## 📑 MỤC LỤC
1. [Giai Đoạn 1: Khảo Sát Bài Toán & Đưa Ra Bản Thiết Kế Blueprint](#-1-giai-đoạn-1-khảo-sát-bài-toán--đưa-ra-bản-thiết-kế-blueprint)
2. [Giai Đoạn 2: Nghiên Cứu Lựa Chọn Công Nghệ & Xây Dựng Hạ Tầng Docker](#-2-giai-đoạn-2-nghiên-cứu-lựa-chọn-công-nghệ--xây-dựng-hạ-tầng-docker)
3. [Giai Đoạn 3: Lập Trình Backend Core & Logic Nghiệp Vụ Tài Chính](#-3-giai-đoạn-3-lập-trình-backend-core--logic-nghiệp-vụ-tài-chính)
4. [Giai Đoạn 4: Nghiên Cứu & Xây Dựng AI RAG Engine Tư Vấn Thông Minh](#-4-giai-đoạn-4-nghiên-cứu--xây-dựng-ai-rag-engine-tư-vấn-thông-minh)
5. [Giai Đoạn 5: Lập Trình & Xây Dựng Ứng Dụng Client (Flutter Web & Mobile)](#-5-giai-đoạn-5-lập-trình--xây-dựng-ứng-dụng-client-flutter-web--mobile)
6. [Giai Đoạn 6: Kiểm Thử, Tối Ưu Bảo Mật & Hệ Thống Quản Trị Admin](#-6-giai-đoạn-6-kiểm-thử-tối-ưu-bảo-mật--hệ-thống-quản-trị-admin)
7. [Các Thành Phần Quan Trọng Cốt Lõi Của Hệ Thống](#-7-các-thành-phần-quan-trọng-cốt-lõi-của-hệ-thống)

---

## 📐 1. GIAI ĐOẠN 1: KHẢO SÁT BÀI TOÁN & ĐƯA RA BẢN THIẾT KẾ BLUEPRINT

### 1.1. Phân Tích Bài Toán Thực Tế (Requirement Gathering)
- **Vấn đề (Pain Point)**: Hầu hết các ứng dụng quản lý chi tiêu hiện nay dừng lại ở việc nhập liệu thủ công và xem biểu đồ tĩnh. Người dùng thiếu một **Trợ lý Tư vấn Tài chính cá nhân hóa**, không biết khoản chi nào đang lãng phí, và không thể đặt câu hỏi bằng tiếng Việt tự nhiên (*"Tháng này tôi đã tiêu bao nhiêu tiền ăn uống?"*).
- **Mục tiêu**: Xây dựng ứng dụng quản lý tài chính cá nhân đa nền tảng (Mobile/Web) tích hợp **AI RAG (Retrieval-Augmented Generation)** tư vấn thông minh dựa trên số liệu thực tế của chính người dùng.

### 1.2. Thiết Kế Kiến Trúc Hệ Thống (System Architecture Map)
```
                                ┌─────────────────────────────────────────┐
                                │     Flutter Client (Mobile & Web)       │
                                └────────────────────┬────────────────────┘
                                                     │ HTTP / REST APIs & SSE Stream
                                                     ▼
                                ┌─────────────────────────────────────────┐
                                │      FastAPI Backend Server (ASGI)      │
                                └──────────┬──────────────────┬───────────┘
                                           │                  │
                    ┌──────────────────────┴┐                ┌┴──────────────────────┐
                    │  PostgreSQL 18 DB     │                │ Redis 8 Cache & Queue │
                    │  (Relational Data)    │                │ (Session/Token/Budget)│
                    └───────────────────────┘                └────────┬──────────────┘
                                                                      │
                                                                      ▼
                                                             ┌────────────────┐
                                                             │ Celery Worker  │
                                                             └────────────────┘
                                                                      │
                                                                      ▼
                                                             ┌────────────────┐
                                                             │ AI RAG Engine  │ ──► Google Gemini API
                                                             └────────────────┘
```

### 1.3. Thiết Kế Cơ Sở Dữ Liệu (ERD Schema Design)
Thiết kế 8 bảng dữ liệu quan hệ đạt chuẩn 3NF:
1. `users`: Thông tin người dùng, mật khẩu Argon2, phân quyền role (`user`/`admin`).
2. `accounts`: Danh sách ví/ngân hàng/tiền mặt, số dư ban đầu, `current_balance`.
3. `categories`: Phân loại thu chi (Icon, loại thu hay chi, mặc định hay tùy chỉnh).
4. `transactions`: Nhật ký giao dịch thu/chi, ngày thực hiện, liên kết ví & danh mục.
5. `budgets`: Ngân sách chi tiêu hàng tháng (`total_limit`, danh mục áp dụng).
6. `saving_goals`: Mục tiêu tiết kiệm (`target_amount`, `target_date`, priority).
7. `refresh_tokens`: Lưu vết mã làm mới token, IP, User-Agent, trạng thái `revoked`.
8. `ai_feedbacks`: Đánh giá 1-5 sao và phản hồi của người dùng cho câu trả lời AI.

---

## 🔬 2. GIAI ĐOẠN 2: NGHIÊN CỨU LỰA CHỌN CÔNG NGHỆ & XÂY DỰNG HẠ TẦNG DOCKER

### 2.1. Quyết Định Lựa Chọn Công Nghệ (Tech Stack Rationale)
- **Mobile/Web**: **Flutter 3.47 + Dart 3.13** ➔ 1 codebase biên dịch ra Native Android/iOS, Windows & Web HTML/CanvasKit với 60 FPS.
- **Backend API**: **Python 3.12 + FastAPI** ➔ Hiệu năng Async I/O cao tiệm cận Node.js/Go, tích hợp mượt nhất với hệ sinh thái AI.
- **Database**: **PostgreSQL 18 + psycopg 3.3 + SQLAlchemy 2.0 ORM** ➔ Bảo đảm tính toàn vẹn tài chính (ACID), chống sai số decimal.
- **Background Queue & Cache**: **Redis 8 + Celery** ➔ Tải tác vụ nặng xuống chạy ngầm, giữ độ trễ API `< 20ms`.
- **AI Core**: **Google Gemini 3.1 Flash Lite (`google-genai`)** ➔ Tốc độ xử lý siêu nhanh, chi phí API rẻ, ngữ cảnh 1M+ tokens.

### 2.2. Xây Dựng Hạ Tầng Đóng Gói Docker (Docker Infrastructure)
- **Multi-stage Dockerfile**: Tách biệt môi trường build (`builder`) và môi trường chạy (`runner` `python:3.12-slim`), giảm dung lượng Image từ 1.2GB xuống **< 220MB**.
- **Docker Compose Setup**: Khởi tạo 4 container kết nối chung trong mạng nội bộ `Bridge Network`:
  - `postgres`: Port `5433` kèm Healthcheck `pg_isready`.
  - `redis`: Port `6379` làm Broker & Cache.
  - `api`: FastAPI Backend server (port `8000`).
  - `worker`: Celery Background worker.

---

## 💻 3. GIAI ĐOẠN 3: LẬP TRÌNH BACKEND CORE & LOGIC NGHIỆP VỤ TÀI CHÍNH

### 3.1. Lập Trình Module Xác Thực & Phân Quyền (Auth Subsystem)
- **Argon2id Hashing**: Mã hóa mật khẩu với `time_cost=3`, `memory_cost=65536 KB`.
- **Dual-JWT Token**:
  - `access_token` (15 phút): Truy cập các API được bảo vệ.
  - `refresh_token` (30 ngày): Lưu mã băm trong DB, cho phép vô hiệu hóa phiên tức thì khi Đăng xuất (`revoked=True`).

### 3.2. Lập Trình Logic Tài Chính Cốt Lõi (Core Finance Business Logic)
- **Transaction Unit of Work (ACID Transaction)**: Đảm bảo khi tạo giao dịch Thu/Chi:
  1. Ghi bản ghi vào `transactions`.
  2. Cộng/Trừ `current_balance` của `accounts`.
  3. Cả 2 thao tác nằm trong 1 SQL Transaction (`await db.commit()`), nếu 1 bước lỗi sẽ tự động `rollback()`.
- **Dynamic Budget Allocation Fix**: Hỗ trợ tự động tính toán tổng ngân sách `total_limit` từ mảng `categories` nếu client không truyền.

### 3.3. Module Báo Cáo & Phân Tích (Analytics Engine)
- Thực thi các truy vấn SQL Aggregation (`SUM`, `COUNT`, `GROUP BY`) để tính toán: Tổng thu nhập, Tổng chi tiêu, Tỷ lệ tiết kiệm, Top danh mục chi tiêu nhiều nhất.

---

## 🧠 4. GIAI ĐOẠN 4: NGHIÊN CỨU & XÂY DỰNG AI RAG ENGINE TƯ VẤN THÔNG MINH

### 4.1. Nghiên Cứu Kiến Trúc RAG (Retrieval-Augmented Generation)
- **So sánh**: Không dùng Fine-tuning (đắt đỏ, chậm cập nhật dữ liệu) mà chọn **RAG (In-Context Learning)** để truy xuất số liệu SQL thực tế của User tại thời điểm hỏi.
- **Hybrid Search**: Kết hợp **Dense Vector Search (Cosine Similarity 768 chiều)** để hiểu ngữ nghĩa + **Sparse Lexical Search (BM25)** để tìm từ khóa chính xác.

### 4.2. Lập Trình Bộ Trích Xuất Ngữ Cảnh (`FinancialContextBuilder`)
- Đóng gói dữ liệu tài chính của user thành `FinancialContext`.
- Gắn nhãn **Provenance** (nguồn gốc tính toán).
- Gắn cờ `insufficient_data` khi không có giao dịch trong tháng (ngăn AI đoán mò).

### 4.3. An Toàn AI & Quản Lý Chi Phí (AI Guardrails & Cost Management)
- **Prompt Injection Defense**: Lọc bỏ các mẫu câu phá bẻ lệnh hệ thống.
- **PII Redaction**: Che/lọc mật khẩu, token, thông tin cá nhân trước khi gửi API.
- **Token Budget Tracker**: Đặt hạn mức `50,000 tokens/ngày/user` bằng Redis atomic counter.
- **Pydantic Structured Output**: Ép AI trả kết quả định dạng JSON `AIOutput`, tự động chuẩn hóa mảng string citations thành đối tượng `Provenance`.

---

## 📱 5. GIAI ĐOẠN 5: LẬP TRÌNH & XÂY DỰNG ỨNG DỤNG CLIENT (FLUTTER WEB & MOBILE)

### 5.1. Kiến Trúc Ứng Dụng Flutter (Clean Presentation Architecture)
```
apps/mobile/lib/
├── core/         # Security Storage, HTTP Client Interceptors, Theme Config
├── models/       # Data Models (User, Account, Transaction, Budget, AIChat)
├── providers/    # State Management (AuthProvider, FinanceViewModel, AIChatProvider)
└── screens/      # UI Views (Login, Home Dashboard, Budgets, Goals, AI Chat)
```

### 5.2. Các Tính Năng Giao Diện Cốt Lõi
- **Bảo mật Cục bộ**: Dùng `flutter_secure_storage` lưu Token mã hóa (Apple Keychain / Android Keystore).
- **HTTP Interceptor**: Tự động chèn `Authorization: Bearer <token>`, tự động gọi API Refresh token khi gặp lỗi HTTP 401.
- **Giao diện Chatbot AI Real-time SSE**: Mở kết nối Server-Sent Events, lắng nghe qua `StreamSubscription` và dùng `Selector` cập nhật text gõ chữ sinh động không gây trễ UI.

---

## 🛠️ 6. GIAI ĐOẠN 6: KIỂM THỬ, TỐI ƯU BẢO MẬT & HỆ THỐNG QUẢN TRỊ ADMIN

### 6.1. Bộ Test Tự Động Pytest (Test Suite Automation)
- Xây dựng 143+ Passed Test Cases:
  - Unit Tests: Kiểm thử mã hóa mật khẩu, kiểm tra AI Output.
  - Integration Tests: Test luồng Đăng ký ↔ Đăng nhập ↔ Postgres DB.
  - Security & Rate Limit Tests: Test giới hạn body request 1MB (HTTP 413) và giới hạn lượt gọi API (HTTP 429).

### 6.2. Bảo Mật Middleware & Hệ Thống Admin
- Chèn các Security Headers (`nosniff`, `DENY` frame, `no-store` cache).
- Hệ thống Admin Dashboard (`/api/v1/admin`): Quản lý danh sách người dùng, xem log telemetry AI, theo dõi lượng token tiêu thụ và chi phí API.

---

## ⭐️ 7. CÁC THÀNH PHẦN QUAN TRỌNG CỐT LÕI CỦA HỆ THỐNG

| STT | Thành phần Cốt lõi | Vai trò & Trách nhiệm trong Hệ thống |
| :--- | :--- | :--- |
| **1** | **FastAPI Core App (`apps/api`)** | Trung tâm xử lý toàn bộ RESTful APIs, Routing, Dependency Injection Auth |
| **2** | **PostgreSQL 18 Database** | Trái tim lưu trữ dữ liệu tài chính với tính toàn vẹn giao dịch tuyệt đối (ACID) |
| **3** | **AI Gateway & Router (`app/ai`)** | Điểm truy cập AI duy nhất, quản lý Gemini API, Fallback Model & Rate Limit |
| **4** | **FinancialContextBuilder** | Đóng vai trò cầu nối RAG trích xuất số liệu SQL thực tế đưa vào Prompt AI |
| **5** | **Redis 8 & Celery Worker** | Bộ nhớ đệm tốc độ cao, đếm token atomic và xử lý các tác vụ ngầm bất đồng bộ |
| **6** | **Flutter Client (`apps/mobile`)** | Giao diện người dùng đa nền tảng mượt mà (Mobile/Web), tích hợp AI Stream Chat |
