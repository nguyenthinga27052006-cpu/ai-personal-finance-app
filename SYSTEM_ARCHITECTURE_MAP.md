# BẢN ĐỒ KIẾN TRÚC HỆ THỐNG VÀ ĐƯỜNG DẪN CÁC FILE QUAN TRỌNG
*(System Architecture & Key File Path Index)*

> **Dự án**: AI Personal Finance App (Ứng dụng Quản lý Tài chính Cá nhân Tích hợp AI & RAG)  
> **Thư mục gốc**: `d:\Projects\ai-personal-finance\ai-personal-finance-app`

---

## 📋 MỤC LỤC

1. [Backend (API Engine - FastAPI)](#1-backend-api-engine---fastapi)
2. [Frontend (Mobile Client - Flutter)](#2-frontend-mobile-client---flutter)
3. [Hệ Thống RAG & AI Chatbot](#3-hệ-thống-rag--ai-chatbot)
4. [Cơ Sở Dữ Liệu & Migrations (Database)](#4-cơ-sở-dữ-liệu--migrations-database)
5. [Quản Lý Quá Trình Run & Docker (Infrastructure)](#5-quản-lý-quá-trình-run--docker-infrastructure)
6. [Background Worker (Xử lý bất đồng bộ)](#6-background-worker-xử-lý-bất-đồng-bộ)
7. [Kịch Bản Script & Công Cụ Quản Lý Systems](#7-kịch-bản-script--công-cụ-quản-lý-systems)

---

## 1. BACKEND (API Engine - FastAPI)

* **Thư mục chính Backend**: [`apps/api`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api)
* **Thư mục Source Code**: [`apps/api/app`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app)

### Các File / Thư Mục Quan Trọng Trong Backend:
* 🚀 **Main Entrypoint (Điểm khởi chạy API)**:
  * [`apps/api/app/main.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/main.py) - Khởi tạo FastAPI app, đăng ký middlewares, CORS, routers và exception handlers.
* ⚙️ **Cấu hình hệ thống (Configuration)**:
  * [`apps/api/app/core/config.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/core/config.py) - Quản lý biến môi trường (`Settings`), kết nối DB, JWT secret keys, API keys của AI providers.
  * [`apps/api/app/core/security.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/core/security.py) - Xử lý mã hóa mật khẩu (hashing), tạo & verify JWT token.
* 🔌 **API Routes (Các Endpoint chính)**:
  * 🔐 **Authentication**: [`apps/api/app/auth/routes.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/auth/routes.py) - Đăng ký, đăng nhập, lấy thông tin user, refresh token.
  * 💳 **Tài khoản (Accounts)**: [`apps/api/app/accounts/routes.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/accounts/routes.py) - Quản lý danh sách tài khoản ngân hàng, ví, số dư.
  * 💸 **Giao dịch (Transactions)**: [`apps/api/app/transactions/routes.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/transactions/routes.py) - Tạo, sửa, xóa, truy vấn lịch sử thu chi.
  * 🎯 **Ngân sách & Mục tiêu**: [`apps/api/app/budget_goals/routes.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/budget_goals/routes.py) - Thiết lập hạn mức chi tiêu và mục tiêu tiết kiệm.
  * 📊 **Phân tích (Analytics & Insights)**: [`apps/api/app/analytics/routes.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/analytics/routes.py), [`apps/api/app/insights/routes.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/insights/routes.py) - Báo cáo thống kê, biểu đồ thu chi.
  * 🧠 **AI API Routes**: [`apps/api/app/ai/routes.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/ai/routes.py) - Các endpoint nhận câu hỏi chat, OCR hóa đơn, tư vấn tài chính.
* 🩺 **Giám sát & Observability**:
  * [`apps/api/app/health.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/health.py) - Health check endpoints (`/healthz`, `/ready`).
  * [`apps/api/app/observability.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/observability.py) & [`apps/api/app/tracing.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/tracing.py) - Logging, metrics, OpenTelemetry tracing.

---

## 2. FRONTEND (Mobile Client - Flutter)

* **Thư mục chính Frontend**: [`apps/mobile`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/mobile)
* **Thư mục Source Code**: [`apps/mobile/lib`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/mobile/lib)

### Các File / Thư Mục Quan Trọng Trong Frontend:
* 🚀 **Điểm khởi chạy app**:
  * [`apps/mobile/lib/main.dart`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/mobile/lib/main.dart) - Điểm bắt đầu ứng dụng Flutter, cấu hình routing, theme và providers.
* 📦 **Quản lý dependencies**:
  * [`apps/mobile/pubspec.yaml`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/mobile/pubspec.yaml) - Khai báo các thư viện (Riverpod, Dio, Flutter UI widgets,...).
* 📱 **Thư mục Mô-đun Giao diện & Logic**:
  * 🔐 **Xác thực**: [`apps/mobile/lib/auth`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/mobile/lib/auth) - Màn hình đăng nhập/đăng ký, AuthController.
  * 💰 **Tài chính**: [`apps/mobile/lib/finance`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/mobile/lib/finance) - Các màn hình danh mục tài khoản, giao dịch, ngân sách, báo cáo.
  * 🤖 **AI Assistant**: [`apps/mobile/lib/ai`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/mobile/lib/ai) - Giao diện chat với Bot tài chính, chụp hóa đơn OCR.
  * ⚙️ **Cài đặt**: [`apps/mobile/lib/settings`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/mobile/lib/settings) - Màn hình cài đặt tài khoản, cấu hình app.
  * 🛡️ **Admin**: [`apps/mobile/lib/admin`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/mobile/lib/admin) - Màn hình dành cho quản trị viên hệ thống.

---

## 3. HỆ THỐNG RAG & AI CHATBOT

* **Thư mục chính AI**: [`apps/api/app/ai`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/ai)
* **Thư mục RAG Core**: [`apps/api/app/ai/rag`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/ai/rag)

### Các File Logic Cốt Lõi AI & RAG:
* ⚡ **Core RAG Logic**:
  * [`apps/api/app/ai/rag/generator.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/ai/rag/generator.py) - Bộ sinh câu trả lời RAG (RAG Generator), tích hợp context retrieval và LLM synthesis.
  * [`apps/api/app/ai/rag/vector_store.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/ai/rag/vector_store.py) - Tương tác với pgvector (tìm kiếm vector tương đồng / Cosine Similarity).
  * [`apps/api/app/ai/rag/knowledge_docs.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/ai/rag/knowledge_docs.py) - Quản lý kho tài liệu kiến thức tài chính (knowledge base chunks).
  * [`apps/api/app/ai/rag/memory.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/ai/rag/memory.py) - Bộ nhớ quản lý ngữ cảnh hội thoại (Conversation Memory / History).
  * [`apps/api/app/ai/rag/prompts.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/ai/rag/prompts.py) - Quản lý các mẫu prompt chuyên sâu cho Chatbot RAG.
* 💬 **Chat Engine & Natural Language Query**:
  * [`apps/api/app/ai/chat.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/ai/chat.py) - Điểm điều phối luồng trò chuyện Chatbot.
  * [`apps/api/app/ai/nl_query.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/ai/nl_query.py) - Chuyển đổi truy vấn tự nhiên thành SQL / data lookup.
* 🛡️ **Guardrails & An toàn thông tin**:
  * [`apps/api/app/ai/guardrails.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/ai/guardrails.py) - Kiểm tra tính an toàn, lọc câu hỏi ngoài phạm vi tài chính.
* 🛠️ **AI Tools & Function Calling**:
  * [`apps/api/app/ai/tools.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/ai/tools.py) - Các công cụ Function Calling cho LLM (vụ tra cứu số dư, tạo giao dịch qua chat).
* 🔌 **LLM Providers & Gateway**:
  * [`apps/api/app/ai/providers.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/ai/providers.py) & [`apps/api/app/ai/gateway.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/ai/gateway.py) - Cổng kết nối đa LLM (OpenAI / Gemini / Ollama fallback).
* 🧾 **Thành phần AI bổ trợ**:
  * [`apps/api/app/ai/receipt.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/ai/receipt.py) - Xử lý bóc tách thông tin hóa đơn (Receipt OCR).
  * [`apps/api/app/ai/categorization.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/ai/categorization.py) - Tự động phân loại giao dịch bằng AI.

---

## 4. CƠ SỞ DỮ LIỆU & MIGRATIONS (Database)

* **Thư mục DB Package**: [`apps/api/app/db`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/db)
* **Thư mục Alembic Migrations**: [`apps/api/migrations`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/migrations)

### Các File Quản Lý Dữ Liệu & Schemas:
* 🗄️ **Kết nối & Phiên làm việc (Session)**:
  * [`apps/api/app/db/session.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/db/session.py) - Tạo Async Engine & SessionMaker cho SQLAlchemy (PostgreSQL).
  * [`apps/api/app/db/base.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/db/base.py) - Định nghĩa Base class cho tất cả ORM models.
* 📐 **Mô hình Dữ liệu (ORM Models)**:
  * [`apps/api/app/db/models/finance.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/db/models/finance.py) - Chứa toàn bộ SQLAlchemy Models (User, Account, Transaction, Category, Budget, Goal, Embedding Vector, ChatSession, Message,...).
* 🔄 **Database Migrations (Alembic)**:
  * [`apps/api/alembic.ini`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/alembic.ini) - Cấu hình kết nối và biến môi trường cho Alembic.
  * [`apps/api/migrations/env.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/migrations/env.py) - Script chạy migration môi trường async.
  * [`apps/api/migrations/versions`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/migrations/versions) - Thư mục chứa các file script phiên bản DB schema.
* 🌱 **Dữ liệu Mẫu (Seed Data)**:
  * [`apps/api/app/db/seed.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/app/db/seed.py) - Khởi tạo dữ liệu mẫu (danh mục chuẩn, tài khoản mặc định).
  * [`apps/api/verify_postgres.py`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/verify_postgres.py) - Kiểm tra kết nối và extension `pgvector` trên PostgreSQL.

---

## 5. QUẢN LÝ QUÁ TRÌNH RUN & DOCKER (Infrastructure)

* **Thư mục Infrastructure**: [`infra`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/infra)
* **Thư mục Docker Configuration**: [`infra/docker`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/infra/docker)

### Các File Docker & Deployment:
* 🐳 **Docker Compose (Môi trường Chạy ứng dụng)**:
  * [`infra/docker/docker-compose.dev.yml`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/infra/docker/docker-compose.dev.yml) - Đổ dồn services chạy cho môi trường Development (PostgreSQL pgvector, Redis, API, Worker).
  * [`infra/docker/docker-compose.staging.yml`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/infra/docker/docker-compose.staging.yml) - Cấu hình cho môi trường Staging.
* 📦 **Dockerfiles của từng ứng dụng**:
  * [`apps/api/Dockerfile`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/api/Dockerfile) - Dockerfile đóng gói ứng dụng Backend API.
  * [`apps/worker/Dockerfile`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/worker/Dockerfile) - Dockerfile đóng gói ứng dụng Background Worker.
* 🌐 **Cấu hình Môi trường (Environment Files)**:
  * [`.env`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/.env) - Biến môi trường hiện tại của hệ thống.
  * [`.env.example`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/.env.example) - File mẫu chứa định dạng các biến môi trường cần thiết.

---

## 6. BACKGROUND WORKER (Xử lý bất đồng bộ)

* **Thư mục chính Worker**: [`apps/worker`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/apps/worker)
* **Chức năng**: Xử lý các tác vụ nền như tạo định kỳ báo cáo, đánh chỉ mục vector RAG, gửi thông báo nhắc nhở chi tiêu bất đồng bộ.

---

## 7. KỊCH BẢN SCRIPT & CÔNG CỤ QUẢN LÝ SYSTEMS

* **Thư mục Scripts**: [`scripts`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/scripts)

### Các Script Quản Lý Tiện Ích:
* 🚀 **Quản lý Docker Environment**:
  * [`scripts/dev-up.ps1`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/scripts/dev-up.ps1) - Bật toàn bộ các dịch vụ container phát triển.
  * [`scripts/dev-down.ps1`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/scripts/dev-down.ps1) - Tắt các dịch vụ container.
* 🗄️ **Quản lý Cơ sở dữ liệu**:
  * [`scripts/migrate.ps1`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/scripts/migrate.ps1) - Chạy alembic database migrations.
  * [`scripts/reset-dev-db.ps1`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/scripts/reset-dev-db.ps1) - Reset lại DB và tạo lại schema sạch.
  * [`scripts/seed.ps1`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/scripts/seed.ps1) - Chạy nạp dữ liệu khởi tạo.
  * [`scripts/backup-restore-drill.ps1`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/scripts/backup-restore-drill.ps1) - Script kiểm tra sao lưu và khôi phục DB.
* 🧪 **Kiểm thử & Kiểm tra chất lượng (CI/CD Quality)**:
  * [`scripts/test.ps1`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/scripts/test.ps1) - Chạy bộ kiểm thử tự động pytest & flutter test.
  * [`scripts/lint.ps1`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/scripts/lint.ps1) - Kiểm tra lỗi ruff, black, dart analyze.
  * [`scripts/check-env.ps1`](file:///d:/Projects/ai-personal-finance/ai-personal-finance-app/scripts/check-env.ps1) - Kiểm tra tính sẵn sàng của biến môi trường hệ thống.

---
*Tài liệu được khởi tạo tự động nhằm quản lý đường dẫn và cấu trúc hệ thống AI Personal Finance App.*
