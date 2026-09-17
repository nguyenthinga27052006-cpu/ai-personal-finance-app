# 🛠️ TÀI LIỆU BÁO CÁO & BẢO VỆ CHUYÊN SÂU: THÀNH VIÊN 4 - DEVOPS, INFRASTRUCTURE & SYSTEM QUALITY LEAD

---

## 👨‍💻 I. THÔNG TIN THÀNH VIÊN & NỀN TẢNG CÔNG NGHỆ
* **Họ và tên**: Thành viên 4 (DevOps & QA Lead)
* **Vai trò**: Trưởng nhóm Hạ tầng Container, Xử lý Tác vụ Chạy ngầm, Kiểm thử Tự động & Quản trị Hệ thống
* **Ngôn ngữ & Công cụ Hạ tầng**: 
  - **Containerization**: **Docker 27.x**, **Docker Compose v2** (Multi-stage builds, Alpine/Debian slim base images).
  - **Background Worker**: **Redis 8** (Message Broker & In-memory Cache) + **Celery Worker** (Hàng chờ tác vụ bất đồng bộ).
  - **Testing Suite**: **Pytest 8.4**, **Pytest-AsyncIO**, `httpx` (Integration Test Client).
  - **System Scripts**: PowerShell Automation Scripts (`dev-up.ps1`, `migrate.ps1`, `seed.ps1`, `test.ps1`).
  - **Security & Network**: Custom Middleware (CORS Policy, Security Headers, Request Size Limiter 1MB).

---

## 🎯 II. CHI TIẾT KỸ THUẬT & NHIỆM VỤ ĐÃ THỰC HIỆN

### 1. Kiến trúc Hạ tầng Container (Docker Multi-Container Architecture)
```
[ Client / Web Browser ] 
        │
        ▼  Port 8000
┌────────────────────────────────────────────────────────┐
│  Docker Internal Network (Bridge Mode)                │
│                                                        │
│  ┌────────────────┐     ┌───────────────────────────┐  │
│  │   API Server   │ ──► │  PostgreSQL 18 Container  │  │
│  │  (FastAPI App) │     │    (Port 5433 -> 5432)    │  │
│  └───────┬────────┘     └───────────────────────────┘  │
│          │                                             │
│          ▼ Task Queue                                  │
│  ┌────────────────┐     ┌───────────────────────────┐  │
│  │  Redis 8 Cache │ ◄── │   Celery Background       │  │
│  │  (Port 6379)   │     │   Worker Container        │  │
│  └────────────────┘     └───────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```
- **Tối ưu Dockerfile (Multi-stage Build)**:
  - Stage 1 (Builder): Cài đặt các thư viện C/C++ cần thiết và build các wheel Python.
  - Stage 2 (Runner): Copy duy nhất phần wheel đã build sang Base Image nhẹ (`python:3.12-slim`), giảm dung lượng Image từ 1.2GB xuống chỉ còn **< 220MB**, loại bỏ toàn bộ lỗ hổng bảo mật của trình biên dịch thừa.
- **Phân tách Cấu hình Dev & Staging**:
  - `docker-compose.dev.yml`: Mount code local vào container (`volumes`) hỗ trợ Hot-Reload khi dev.
  - `docker-compose.staging.yml`: Đóng gói Image bất biến (Immutable Image), kết nối Database quản lý riêng.

### 2. Xử lý Tác vụ Bất đồng bộ Chạy ngầm (Celery Background Workers)
- Kết nối ứng dụng `apps/worker` với Redis 8 Broker.
- Chuyển giao các tác vụ tốn thời gian ra khỏi Main Thread của API:
  - Gửi thông báo đẩy (Push Notification) cho người dùng khi vượt ngân sách.
  - Tổng hợp báo cáo số liệu hàng tháng và xử lý dữ liệu RAG nặng.

### 3. Hệ thống Test Tự động (Automated Test Pipeline & QA)
- Xây dựng bộ test toàn diện đạt **143+ Passed Tests**:
  - `test_ai_platform.py`: Kiểm thử AI Gateway, Prompt Injection, Rate Limiting, Streaming.
  - `test_postgres_auth.py`: Kiểm thử luồng Đăng ký/Đăng nhập thực tế trên Postgres DB.
  - `test_financial_core.py`: Kiểm thử logic số dư tài khoản, tạo giao dịch.

---

## ❓ III. BỘ CÂU HỎI & ĐÁP BẢO VỆ KÍN KẼ (DÀNH CHO HỘI ĐỒNG/GIẢNG VIÊN)

### ❓ Câu 1: Tại sao lại dùng Docker Multi-stage Build? Lợi ích cụ thể trong dự án của bạn là gì?
> **Trả lời kín kẽ**: 
> 1. **Giảm kích thước Image (Image Size Optimization)**: Trong giai đoạn `builder`, chúng tôi phải cài các công cụ biên dịch như `gcc`, `g++`, `libpq-dev`. Nếu giữ lại các công cụ này, Image sẽ rất nặng (>1GB). Multi-stage build cho phép chỉ copy thành phẩm (`site-packages`) sang stage runner (`python:3.12-slim`), giúp Image thu gọn còn **< 220MB**.
> 2. **Tăng cường Bảo mật (Security Hardening)**: Stage runner không chứa trình biên dịch `gcc`, giảm thiểu tối đa diện tích tấn công (Attack Surface) nếu hacker chiếm được quyền truy cập container.

### ❓ Câu 2: Sự khác biệt giữa Docker Bridge Network và Host Network là gì? Tại sao các container của bạn giao tiếp được với nhau?
> **Trả lời kín kẽ**: 
> - **Host Network**: Container dùng chung không gian mạng với máy host, dễ bị xung đột port và kém bảo mật.
> - **Bridge Network (Docker Compose mặc định)**: Docker tạo ra một mạng ảo isolated riêng biệt. Các container trong cùng 1 file compose nằm chung mạng này và giao tiếp với nhau qua **Container Name** (Ví dụ: `api` gọi Postgres qua hostname `postgres:5432` chứ không cần nhớ IP động).
> - Chỉ những cổng được khai báo trong `ports` (như `8000:8000` của API) mới mở ra ngoài máy host, còn kết nối giữa API và Postgres/Redis được bảo vệ hoàn toàn bên trong Docker Internal Network.

### ❓ Câu 3: Tại sao bạn chọn Redis làm Message Broker cho Celery Worker mà không dùng RabbitMQ hay Kafka?
> **Trả lời kín kẽ**: 
> 1. **Tính đa năng (Multi-purpose)**: Redis 8 vừa làm **In-memory Cache** cho hệ thống, vừa làm **Atomic Counter** cho Rate Limiter, vừa đóng vai trò **Message Broker** cho Celery. Chọn Redis giúp hệ thống tinh gọn, không phải vận hành thêm 1 dịch vụ phức tạp như RabbitMQ hay Kafka.
> 2. **Tốc độ cực cao**: Đặt trên bộ nhớ RAM, Redis xử lý hàng trăm nghìn push/pop message mỗi giây với độ trễ thấp ở mức microsecond (`< 1ms`).

### ❓ Câu 4: Middleware bảo mật của bạn xử lý những loại tấn công mạng phổ biến nào?
> **Trả lời kín kẽ**: 
> 1. **MIME Sniffing Attack**: Chèn Header `X-Content-Type-Options: nosniff` ép trình duyệt tuân thủ đúng Content-Type trả về.
> 2. **Clickjacking Attack**: Chèn Header `X-Frame-Options: DENY` ngăn không cho trang web bị nhúng vào `<iframe>` của các trang web lừa đảo khác.
> 3. **Memory Exhaustion / DDoS Attack**: Đặt `Content-Length` Middleware giới hạn body request tối đa 1MB. Nếu kẻ xấu cố tình gửi file rác dung lượng lớn, server sẽ từ chối ngay lập tức với HTTP Status `413 Request Body Too Large` trước khi kịp đọc vào RAM.

### ❓ Câu 5: Sự khác biệt giữa Health check (`/health`) và Readiness check (`/ready`) trong hệ thống là gì?
> **Trả lời kín kẽ**: 
> - **`/health` (Liveness Probe)**: Chỉ kiểm tra xem tiến trình Python FastAPI Server có đang sống hay không. Đơn giản trả về `{"status": "ok"}`.
> - **`/ready` (Readiness Probe)**: Kiểm tra sâu hơn xem hệ thống đã **sẵn sàng nhận traffic dịch vụ** hay chưa. Endpoint này thực sự gửi ping tới PostgreSQL và Redis. Nếu Postgres đang bị nghẽn hoặc ngắt kết nối, `/ready` sẽ trả về lỗi HTTP 503, báo cho Docker Orchestrator/Load Balancer tạm thời ngưng chuyển request tới container này cho đến khi DB phục hồi.
