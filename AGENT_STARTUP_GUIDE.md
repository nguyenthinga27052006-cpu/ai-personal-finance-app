# 🤖 AGENT STARTUP & INSTALLATION GUIDE (HƯỚNG DẪN KHỞI ĐỘNG HỆ THỐNG DÀNH CHO AGENT)

> **Mục đích tài liệu:** Hướng dẫn chi tiết, chuẩn hóa và tối ưu cho **AI Agents** (Antigravity, Cursor, Claude Code, GitHub Copilot, Roo Code, Aider, Windsurf...) hoặc bất kỳ lập trình viên nào khi tải/clone mã nguồn về có thể nhận diện ngay các phần mềm cần tải, cấu hình môi trường, và thực thi các câu lệnh để khởi động toàn bộ hệ thống từ A - Z.

---

## 📌 1. TỔNG QUAN KIẾN TRÚC HỆ THỐNG (SYSTEM OVERVIEW)

Dự án **AI Personal Finance App** là hệ thống monorepo gồm 3 thành phần chính:

| Phân hệ | Công nghệ cốt lõi | Thư mục mã nguồn | Cổng mặc định (Port) |
| :--- | :--- | :--- | :--- |
| **Backend API** | FastAPI, Python 3.12+, SQLAlchemy 2.0, Alembic, RapidOCR, Gemini/Ollama RAG | `apps/api` | `8000` |
| **Worker Service** | Celery / Redis Consumer, Python 3.12+ | `apps/worker` | Background service |
| **Database & Cache** | PostgreSQL 18 (pgvector), Redis 8 | `infra/docker` | Postgres: `5433` (Host) / `5432` (Container)<br>Redis: `6379` |
| **Frontend Client** | Flutter 3.x, Dart 3.x (Multiplatform: Web, Android, iOS, Desktop) | `apps/mobile` | Web: `8080` hoặc Chrome |

---

## 📥 2. CÁC CÔNG CỤ CẦN TẢI & CÀI ĐẶT (PREREQUISITES TO DOWNLOAD & INSTALL)

Khi bắt đầu trên một máy mới (hoặc container mới), Agent cần kiểm tra và yêu cầu/cài đặt các công cụ sau:

### 2.1. Bắt buộc cho toàn bộ Backend & CSDL (Mandatory)
1. **[Git](https://git-scm.com/)** (v2.x+)
2. **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** (Docker Compose v2+):
   - Đảm bảo Docker daemon đang chạy (`docker info` trả về thông tin thành công).
   - Docker sẽ tự động pull và dựng toàn bộ PostgreSQL 18, Redis 8, FastAPI API, và Celery Worker mà không cần cài đặt database lên hệ điều hành host.

### 2.2. Cho Lập trình viên / Chạy Script Host / Chạy Test Local (Recommended)
3. **[Python 3.12 hoặc 3.13](https://www.python.org/)**:
   - Yêu cầu phiên bản: `>=3.12, <3.15`.
   - Dùng để chạy migration Alembic trên host, chạy bộ test `pytest`, hoặc chạy scripts tiện ích.
4. **Tạo Python Virtual Environment (Khuyên dùng nếu chạy CLI trên host)**:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   # Cài đặt dependencies cho backend:
   pip install -e "apps/api[dev]"
   ```

### 2.3. Cho Ứng dụng Giao diện Frontend (Flutter Client)
5. **[Flutter SDK 3.x](https://flutter.dev/)** (Dart SDK `^3.13.1`):
   - Kiểm tra bằng lệnh: `flutter doctor`.
6. **Môi trường chạy Client**:
   - **Cách 1 (Nhanh nhất, không cần cài máy ảo)**: **Google Chrome** (Chạy Flutter Web).
   - **Cách 2**: **Android Studio** + Android SDK + Máy ảo Android Emulator (ví dụ: `Pixel_10` API 34/35).

### 2.4. Khóa AI (AI Provider Key - Tùy chọn)
7. **Google Gemini API Key** (Khuyên dùng cho tính năng RAG tiếng Việt thông minh):
   - Lấy key miễn phí tại [Google AI Studio](https://aistudio.google.com/).
   - *Lưu ý*: Nếu không có API Key, hệ thống hỗ trợ chế độ giả lập `AI_PROVIDER=fake` để chạy mượt mà mọi tính năng mà không tốn phí hoặc không gặp lỗi. Hoặc cài [Ollama](https://ollama.ai/) chạy mô hình local `qwen2.5:3b`.

---

## ⚙️ 3. THIẾT LẬP FILE MÔI TRƯỜNG (.ENV)

Agent cần khởi tạo file cấu hình `.env` tại thư mục gốc của repository:

### Bước 3.1: Copy file mẫu
- **Trên Windows (PowerShell)**:
  ```powershell
  Copy-Item .env.example .env
  ```
- **Trên Linux / macOS**:
  ```bash
  cp .env.example .env
  ```

### Bước 3.2: Các tham số quan trọng trong `.env`
Đảm bảo các giá trị cơ bản sau đã được điền:
```env
APP_ENV=development
COMPOSE_PROJECT_NAME=finance-assistant
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO

# Cấu hình CSDL PostgreSQL
POSTGRES_DB=finance
POSTGRES_USER=finance_dev
POSTGRES_PASSWORD=finance_dev_local_only
POSTGRES_PORT=5433

# Cấu hình Redis
REDIS_PORT=6379

# Kết nối CSDL bên trong mạng Docker (API -> Postgres container)
DATABASE_URL=postgresql://finance_dev:finance_dev_local_only@postgres:5432/finance

# Kết nối CSDL từ máy host (Alembic / Migrations / Tests trên host)
HOST_DATABASE_URL=postgresql://finance_dev:finance_dev_local_only@localhost:5433/finance

REDIS_URL=redis://redis:6379/0

# Cấu hình Bảo mật JWT
JWT_SECRET=development-only-change-me-32-bytes-minimum
JWT_ISSUER=ai-personal-finance-api
JWT_AUDIENCE=ai-personal-finance-mobile
ACCESS_TOKEN_TTL_MINUTES=15
REFRESH_SESSION_TTL_DAYS=30
NOTIFICATION_WORKER_TOKEN=development-worker-token

# Cấu hình AI Provider (Chọn gemini, ollama hoặc fake)
AI_PROVIDER=gemini
AI_MODEL=gemini-3.1-flash-lite
GEMINI_API_KEY=your_gemini_api_key_here
AI_ENABLED=true
```

> ⚠️ **LƯU Ý QUAN TRỌNG VỀ PORT DATABASE (AGENT TRAP):**
> Cổng PostgreSQL của Docker được map ra ngoài máy host là **`5433`** (để tránh xung đột với cổng `5432` nếu máy tính đã cài sẵn Postgres).
> - Khi gọi từ máy host (Local CLI, Alembic trên host): dùng port **`5433`** (`localhost:5433`).
> - Khi các container Docker giao tiếp với nhau: dùng port **`5432`** (`postgres:5432`).

---

## 🚀 4. THỨ TỰ CÁC BƯỚC KHỞI ĐỘNG HỆ THỐNG (EXECUTION ORDER)

Để hệ thống hoạt động trơn tru không xảy ra lỗi kết nối CSDL, Agent cần chạy theo đúng thứ tự sau:

```
┌─────────────────┐     ┌──────────────────┐     ┌────────────────┐     ┌─────────────────┐
│ 1. Docker Up    │ ──> │ 2. Run Migration │ ──> │ 3. Seed Admin  │ ──> │ 4. Start Client │
│ (Postgres/Redis)│     │ (Alembic Head)   │     │ & Categories   │     │ (Flutter Web)   │
└─────────────────┘     └──────────────────┘     └────────────────┘     └─────────────────┘
```

### Bước 1: Khởi động các Docker Containers
Chạy lệnh khởi động hạ tầng bằng Docker Compose:

- **Lệnh chuẩn (Mọi hệ điều hành)**:
  ```bash
  docker compose -f infra/docker/docker-compose.dev.yml --env-file .env up -d --build
  ```
- **Hoặc dùng script PowerShell (Windows)**:
  ```powershell
  ./scripts/dev-up.ps1
  ```

Kiểm tra trạng thái các container:
```bash
docker ps
```
*Kết quả:* 4 containers chạy bình thường:
- Postgres (port `5433->5432`)
- Redis (port `6379->6379`)
- API (port `8000->8000`)
- Worker

---

### Bước 2: Chạy Database Migration (Alembic)
Cập nhật toàn bộ cấu trúc bảng vào CSDL PostgreSQL mới:

- **Cách 1: Chạy trực tiếp qua Docker (Khuyên dùng cho Agent, không phụ thuộc môi trường host)**:
  ```bash
  docker compose -f infra/docker/docker-compose.dev.yml exec api alembic upgrade head
  ```
- **Cách 2: Chạy qua PowerShell script (Windows host)**:
  ```powershell
  ./scripts/migrate.ps1
  ```
- **Cách 3: Chạy trực tiếp qua Python trên host**:
  ```bash
  cd apps/api
  DATABASE_URL="postgresql://finance_dev:finance_dev_local_only@localhost:5433/finance" python -m alembic upgrade head
  cd ../..
  ```

---

### Bước 3: Nạp Dữ Liệu Ban Đầu (Seed Data)
Khởi tạo tài khoản Quản trị viên (Super Admin) và các Danh mục tài chính mẫu (Ăn uống, Mua sắm, Tiền lương, Vay nợ...):

- **Cách 1: Chạy trực tiếp qua Docker (Khuyên dùng)**:
  ```bash
  docker compose -f infra/docker/docker-compose.dev.yml exec api python -m app.db.seed
  ```
- **Cách 2: Chạy qua PowerShell script (Windows host)**:
  ```powershell
  ./scripts/seed.ps1
  ```

---

### Bước 4: Kiểm tra trạng thái Backend (Healthcheck Verification)
Agent có thể gửi request để xác minh Backend đã sẵn sàng 100%:

- **Health check**:
  ```bash
  curl http://localhost:8000/health
  # Trả về: {"status":"ok"}
  ```
- **Readiness check (Postgres & Redis connectivity)**:
  ```bash
  curl http://localhost:8000/ready
  # Trả về: {"status":"ready","database":"connected","redis":"connected"}
  ```
- **Swagger / OpenAPI Documentation**:
  Mở trình duyệt: `http://localhost:8000/docs`

---

### Bước 5: Khởi động Ứng dụng Giao diện Frontend (Flutter)

Mở terminal mới, di chuyển vào thư mục client:
```bash
cd apps/mobile
flutter pub get
```

#### Lựa chọn A: Chạy trên Trình duyệt Chrome (Khuyên dùng, khởi động nhanh nhất)
```bash
flutter run -d chrome
```
Hoặc chạy độc lập dưới dạng Web Server (Port 8080):
```bash
flutter run -d web-server --web-port 8080 --web-hostname localhost
```
👉 Sau đó truy cập: **`http://localhost:8080`**

#### Lựa chọn B: Chạy trên Máy ảo Android (Android Emulator)
```bash
# Khởi động máy ảo (ví dụ Pixel_10)
flutter emulators --launch Pixel_10

# Xem ID máy ảo
flutter devices

# Chạy ứng dụng lên máy ảo
flutter run -d emulator-5554
```
*(Ghi chú: Khi chạy trên Android Emulator, ứng dụng tự động cấu hình gọi API về host thông qua IP `http://10.0.2.2:8000`)*.

---

## 🔑 5. THÔNG TIN TÀI KHOẢN MẪU (DEFAULT TEST CREDENTIALS)

Sau khi hoàn tất bước Seed dữ liệu, Agent hoặc người dùng có thể đăng nhập ngay bằng các tài khoản sau:

| Loại tài khoản | Email | Mật khẩu | Quyền hạn & Chức năng |
| :--- | :--- | :--- | :--- |
| **Super Admin** | `admin@finance.app` | `AdminPass123!` | Toàn quyền Quản trị: Xem Analytics toàn hệ thống, Quản lý người dùng, Giám sát Token AI |
| **Demo User** | `user@example.com` | `User123456!` | Người dùng cá nhân: Quản lý ví, Thu/chi, Ngân sách, Vay nợ, Chat AI RAG |
| **Mã PIN bảo mật** | *(Áp dụng cho User)* | `123456` | Mã PIN 6 số dùng để xác thực nhanh và khôi phục mật khẩu khi quên |

---

## 🧪 6. BỘ LỆNH KIỂM THỬ TỰ ĐỘNG (AUTOMATED TEST SUITES)

Agent có thể chạy các bộ kiểm thử sau để kiểm tra tính toàn vẹn của mã nguồn:

### 6.1. Backend Unit & Integration Tests (Pytest)
```bash
cd apps/api
pytest tests/
# Hoặc trên Windows:
./scripts/test.ps1
```

### 6.2. Frontend Tests (Flutter)
```bash
cd apps/mobile
flutter test
flutter analyze
```

### 6.3. Kiểm tra toàn diện môi trường (Check Environment)
```powershell
powershell -ExecutionPolicy Bypass -File scripts/check-env.ps1
```

---

## 🛠️ 7. CẨM NANG XỬ LÝ LỖI PHỔ BIẾN CHO AGENT (TROUBLESHOOTING & GOTCHAS)

| Vấn đề gặp phải | Nguyên nhân | Giải pháp xử lý chuẩn cho Agent |
| :--- | :--- | :--- |
| **Lỗi kết nối CSDL khi chạy Alembic trên host** | Dùng sai cổng (cố kết nối cổng `5432`) | Sửa chuỗi kết nối host sang port `5433`: `postgresql://finance_dev:finance_dev_local_only@localhost:5433/finance` |
| **Port `8000`, `5433` hoặc `6379` bị chiếm dụng** | Một ứng dụng khác đang chiếm port | Chỉnh sửa port tương ứng trong file `.env` (ví dụ `POSTGRES_PORT=5434`, `APP_PORT=8001`) |
| **Không có Gemini API Key hoặc quota bị hết hạn** | Chưa cấu hình key AI | Đổi trong file `.env`: `AI_PROVIDER=fake`. Ứng dụng sẽ tự động kích hoạt Mock AI Provider mà không cần gọi API ngoài |
| **Muốn xóa sạch CSDL và tạo lại từ đầu** | CSDL chứa dữ liệu test cũ | Chạy script: `./scripts/reset-dev-db.ps1` hoặc `docker compose -f infra/docker/docker-compose.dev.yml down -v` |
| **Dừng toàn bộ hệ thống** | Giải phóng tài nguyên máy | Chạy lệnh: `docker compose -f infra/docker/docker-compose.dev.yml down` hoặc `./scripts/dev-down.ps1` |
| **Flutter Web bị lỗi CORS** | Domain chưa được thêm vào whitelist backend | Backend đã cho phép `localhost:8080`, `localhost:3000`, `10.0.2.2`. Hãy chạy web ở port 8080: `flutter run -d web-server --web-port 8080` |

---

## 📁 8. SƠ ĐỒ CÁC FILE ĐIỀU KHIỂN CHÍNH (KEY FILES MAP)

```
ai-personal-finance-app/
├── AGENT_STARTUP_GUIDE.md          # 📍 FILE NÀY: Hướng dẫn khởi động cho Agent
├── README.md                       # Giới thiệu dự án & Hướng dẫn cơ bản
├── SYSTEM_STARTUP_GUIDE_AZ.md      # Hướng dẫn chi tiết A-Z
├── .env.example                    # File mẫu cấu hình môi trường
├── infra/docker/
│   └── docker-compose.dev.yml      # Cấu hình 4 container (API, Worker, Postgres 18, Redis 8)
├── apps/api/
│   ├── app/main.py                 # FastAPI Application & Auto-seed Lifespan
│   ├── app/db/seed.py              # Script nạp dữ liệu Admin & Danh mục
│   └── pyproject.toml              # Dependencies Backend Python
├── apps/mobile/
│   ├── pubspec.yaml                # Dependencies Flutter Frontend
│   └── lib/main.dart               # Điểm khởi chạy ứng dụng Flutter
└── scripts/
    ├── dev-up.ps1                  # Khởi động Docker 1-click
    ├── dev-down.ps1                # Dừng Docker
    ├── migrate.ps1                 # Chạy migration CSDL
    ├── seed.ps1                    # Nạp dữ liệu mẫu
    ├── test.ps1                    # Chạy Pytest
    └── check-env.ps1               # Kiểm tra công cụ đã cài đặt
```

---
*Tài liệu được tạo và bảo trì tự động cho hệ thống AI Personal Finance App.* 🚀
