# 🤖 AI Personal Finance Assistant (Trợ lý Tài chính Cá nhân AI)

Ứng dụng quản lý tài chính cá nhân thông minh tích hợp **Trợ lý AI RAG (Retrieval-Augmented Generation)**, cho phép theo dõi giao dịch, lập ngân sách, phân tích chi tiêu và trò chuyện bằng ngôn ngữ tự nhiên với AI tư vấn tài chính.

---

## 🌟 Tính Năng Nổi Bật (Key Features)

- 🔐 **Hệ thống Xác thực (Authentication & AuthZ)**: Đăng ký, đăng nhập JWT, làm mới token (Refresh Token), phân quyền người dùng (`user` và `admin`).
- 💰 **Quản lý Tài chính Cốt lõi (Core Finance)**:
  - Quản lý tài khoản (Ví điện tử, Ngân hàng, Tiền mặt).
  - Quản lý danh mục thu/chi (Categories).
  - Ghi nhận & truy vấn giao dịch (Transactions).
  - Lập ngân sách & mục tiêu tiết kiệm (Budgets & Goals).
- 📊 **Phân tích & Báo cáo (Analytics & Insights)**: Thống kê tổng thu/chi theo tháng, tỷ lệ tiết kiệm, cảnh báo vượt ngân sách, biểu đồ phân bổ chi tiêu.
- 🧠 **Trợ lý AI & RAG Chatbot (AI Financial Advisor)**:
  - Hỏi đáp tài chính bằng tiếng Việt tự nhiên.
  - Tự động truy xuất ngữ cảnh giao dịch & tài liệu tri thức (RAG - Hybrid Retriever + Vector/Dense Search).
  - Hỗ trợ đa mô hình AI (Google Gemini, OpenAI GPT, Fallback Local Mode).
- 🛡️ **Bảng Quản trị (Admin Dashboard)**: Cho phép Admin xem thống kê hệ thống, quản lý người dùng, theo dõi tần suất gọi AI và chi phí token.
- 📱 **Ứng dụng Mobile/Web Đa nền tảng**: Xây dựng bằng Flutter (Hỗ trợ Android, iOS, Web & Desktop).

---

## 🏗️ Kiến Trúc Hệ Thống (Architecture Overview)

```
                       +-----------------------------------+
                       |    Flutter App (Mobile / Web)     |
                       +-----------------+-----------------+
                                         | HTTP / REST API
                                         v
                       +-----------------+-----------------+
                       |       FastAPI Backend (API)       |
                       +--------+----------------+---------+
                                |                |
             +------------------+                +------------------+
             | PostgreSQL 18                     | Redis Cache &    |
             | (Database & Vector Store)         | Celery Worker    |
             +------------------+                +------------------+
                                |
                                v
                       +-----------------+
                       | AI Engine (RAG) |  ---> Google Gemini API / OpenAI API
                       +-----------------+
```

### Công nghệ sử dụng (Tech Stack)
- **Backend**: Python 3.12+, FastAPI, SQLAlchemy, Alembic, Celery, Pytest.
- **Database & Cache**: PostgreSQL 18, Redis 7.
- **AI & RAG**: Google Gemini API (`google-genai`), Hybrid Dense/BM25 Retrieval, Prompt Engineering.
- **Mobile Client**: Flutter 3.x, Dart, Provider (State Management), Dynamic Themes.
- **Infrastructure**: Docker & Docker Compose.

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy Hệ Thống (Quick Start Guide)

### 📋 Yêu cầu tiên quyết (Prerequisites)
- [Git](https://git-scm.com/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Docker Compose v2 đang chạy)
- [Python 3.12+](https://www.python.org/) (Cho test/migration local nếu không dùng Docker)
- [Flutter SDK 3.x](https://flutter.dev/) (Nếu muốn chạy ứng dụng Mobile client)

---

### 1️⃣ Bước 1: Clone Repository
```bash
git clone https://github.com/<your-username>/<your-repo-name>.git
cd ai-personal-finance-app
```

---

### 2️⃣ Bước 2: Cấu hình Môi trường (Environment Setup)
Tạo file `.env` từ file mẫu `.env.example`:

**Trên Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```
**Trên Linux / macOS:**
```bash
cp .env.example .env
```

Mở file `.env` và điền **API Key AI** của bạn (ví dụ Google Gemini API Key):
```env
AI_PROVIDER=gemini
AI_MODEL=gemini-3.1-flash-lite
GEMINI_API_KEY=dán-api-key-gemini-của-bạn-vào-đây
```
*(Nếu chưa có API Key, bạn có thể để `AI_PROVIDER=fake` để ứng dụng hoạt động với dữ liệu giả lập AI)*.

---

### 3️⃣ Bước 3: Khởi chạy Backend Services bằng Docker

**Sử dụng PowerShell Script (Windows):**
```powershell
./scripts/dev-up.ps1
```

**Hoặc lệnh Docker Compose trực tiếp (Mọi hệ điều hành):**
```bash
docker compose --env-file .env -f infra/docker/docker-compose.dev.yml up --build -d
```

Hệ thống Docker sẽ tự động khởi tạo:
- **API Server** tại `http://localhost:8000`
- **PostgreSQL 18** tại `localhost:5433`
- **Redis Cache & Queue** tại `localhost:6379`
- **Background Worker**

---

### 4️⃣ Bước 4: Chạy Migration & Seed Dữ Liệu Mẫu

Tạo bảng trong Database và nạp dữ liệu mẫu ban đầu (Categories, Demo User, Admin, Sample Transactions):

**Sử dụng PowerShell Script:**
```powershell
./scripts/migrate.ps1
./scripts/seed.ps1
```

**Hoặc chạy qua Python / Docker:**
```bash
docker exec -it finance-assistant-api python app/db/seed.py
```

---

### 5️⃣ Bước 5: Kiểm tra Backend & API Documentation

- **Health Check**: Truy cập `http://localhost:8000/health` (Trả về `{"status": "ok"}`)
- **Ready Check**: Truy cập `http://localhost:8000/ready` (Trả về status của Database & Redis)
- **OpenAPI / Swagger UI**: Truy cập `http://localhost:8000/docs` để xem và tương tác trực tiếp với toàn bộ RESTful APIs.

---

### 6️⃣ Bước 6: Khởi chạy Ứng dụng Mobile Client (Flutter)

Mở terminal mới và chuyển đến thư mục client:
```bash
cd apps/mobile
flutter pub get
```

Khởi chạy ứng dụng:
- **Chạy trên Trình duyệt Web (Nhanh nhất):**
  ```bash
  flutter run -d chrome
  ```
- **Chạy trên Thiết bị Android / iOS / Emulator:**
  ```bash
  flutter run
  ```

---

## 🔑 Tài Khoản Mẫu Để Đăng Nhập (Demo Accounts)

Sau khi chạy script `seed.ps1`, bạn có thể đăng nhập bằng các tài khoản sau:

| Vai trò (Role) | Email | Mật khẩu (Password) | Quyền hạn |
| :--- | :--- | :--- | :--- |
| **User (Người dùng)** | `user@example.com` | `User123456!` | Quản lý tài chính cá nhân, dùng AI Chatbot |
| **Admin (Quản trị)** | `admin@example.com` | `Admin123456!` | Xem Dashboard Admin, Quản lý User, Thống kê AI |

---

## 📁 Cấu Trúc Thư Mục Dự Án (Project Structure)

```
ai-personal-finance-app/
├── apps/
│   ├── api/                    # FastAPI Backend Source Code
│   │   ├── app/
│   │   │   ├── admin/          # Admin Dashboard APIs
│   │   │   ├── ai/             # AI Gateway, RAG Engine, Retrievers
│   │   │   ├── auth/           # Authentication & User Management
│   │   │   ├── core/           # Config, Security, JWT Tokens
│   │   │   ├── db/             # Database Models, Seeds, Alembic
│   │   │   └── transactions/   # Transactions, Accounts, Budgets APIs
│   │   └── tests/              # Pytest Unit & Integration Test Suites
│   │
│   └── mobile/                 # Flutter Multi-platform Application
│       ├── lib/
│       │   ├── admin/          # Admin UI Screens
│       │   ├── ai/             # AI Assistant & Chatbot UI
│       │   ├── auth/           # Login, Register & Auth Controllers
│       │   ├── finance/        # Accounts, Transactions & Budget Screens
│       │   └── settings/       # App Settings UI
│       └── test/               # Flutter Widget & Unit Tests
│
├── docs/                       # Tài liệu thiết kế & Chi tiết kỹ thuật
├── infra/                      # Docker & Deployment configurations
│   └── docker/
│       └── docker-compose.dev.yml
└── scripts/                    # Các script PowerShell tiện ích (Dev up, Migrate, Seed, Test)
```

---

## 🧪 Chạy Automated Tests (Kiểm thử hệ thống)

Dự án đi kèm bộ test kiểm thử tự động toàn diện:

### Backend Tests (Pytest)
```powershell
./scripts/test.ps1
```
Hoặc:
```bash
cd apps/api
pytest tests/
```

### Mobile Tests (Flutter)
```bash
cd apps/mobile
flutter test
```

---

## 🛠️ Hướng Dẫn Sửa Lỗi Thường Gặp (Troubleshooting)

- **Lỗi Port đã bị chiếm dụng (`5433`, `6379` hoặc `8000`)**:
  Kiểm tra xem ứng dụng khác có đang dùng các port này không, hoặc chỉnh sửa port trong file `.env`.
- **Reset lại Database từ đầu**:
  Nếu muốn xóa sạch dữ liệu dev local để tạo lại:
  ```powershell
  ./scripts/reset-dev-db.ps1
  ```
- **Lỗi Docker không khởi động**:
  Đảm bảo Docker Desktop đã được mở và chạy thành công trước khi gõ lệnh `dev-up.ps1`.
- **Tắt toàn bộ hệ thống Docker**:
  ```powershell
  ./scripts/dev-down.ps1
  ```

---

## 📄 License & Đóng Góp (Contribution)

Dự án được xây dựng phục vụ mục đích học tập, nghiên cứu và quản lý tài chính cá nhân ứng dụng AI. Mọi đóng góp (Pull Request / Issue) đều được hoan nghênh!