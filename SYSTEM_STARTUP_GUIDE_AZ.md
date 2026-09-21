# 📖 HƯỚNG DẪN KHỞI ĐỘNG HỆ THỐNG TỪ A - Z (FULL SYSTEM STARTUP GUIDE)

Tài liệu này hướng dẫn chi tiết từng bước không bỏ sót bước nào để cài đặt, thiết lập môi trường, vận hành toàn bộ hệ thống **AI Personal Finance Assistant** (bao gồm Backend Docker, CSDL PostgreSQL, Migration, Seed Data, và Frontend Flutter trên Web / Android).

---

## 📋 YÊU CẦU TIÊN QUYẾT (PREREQUISITES)

Trước khi bắt đầu, hãy đảm bảo máy tính của bạn đã cài đặt các công cụ sau:
1. **[Git](https://git-scm.com/)**: Quản lý mã nguồn.
2. **[Docker Desktop](https://www.docker.com/products/docker-desktop/)**: Chạy PostgreSQL, Redis, FastAPI Backend và Worker. *(Đảm bảo Docker Desktop đang ở trạng thái Running)*.
3. **[Python 3.12 hoặc 3.13+](https://www.python.org/)**: Chạy các câu lệnh Migration local & pytest.
4. **[Flutter SDK 3.x](https://flutter.dev/)**: Biên dịch và chạy ứng dụng Flutter.
5. **[Android Studio](https://developer.android.com/studio)** *(Tùy chọn nếu chạy App Android)*: Có ít nhất 1 thiết bị máy ảo Android Emulator (ví dụ: `Pixel_10`).

---

## 🚀 BƯỚC 1: CẤU HÌNH MÔI TRƯỜNG (.ENV)

1. **Mở Terminal/PowerShell tại thư mục gốc của dự án**:
   ```powershell
   cd d:\Projects\ai-personal-finance\ai-personal-finance-app
   ```

2. **Tạo file `.env` từ file mẫu `.env.example`**:
   - **Windows (PowerShell)**:
     ```powershell
     Copy-Item .env.example .env
     ```
   - **Linux / macOS**:
     ```bash
     cp .env.example .env
     ```

3. **Kiểm tra/Chỉnh sửa file `.env`**:
   Đảm bảo các cấu hình cơ bản như sau:
   ```env
   APP_ENV=development
   APP_HOST=0.0.0.0
   APP_PORT=8000
   LOG_LEVEL=INFO

   POSTGRES_DB=finance
   POSTGRES_USER=finance_dev
   POSTGRES_PASSWORD=finance_dev_local_only
   POSTGRES_PORT=5433

   REDIS_PORT=6379
   DATABASE_URL=postgresql://finance_dev:finance_dev_local_only@postgres:5432/finance
   HOST_DATABASE_URL=postgresql://finance_dev:finance_dev_local_only@localhost:5433/finance
   REDIS_URL=redis://redis:6379/0

   JWT_SECRET=development-only-change-me-32-bytes-minimum
   JWT_ISSUER=ai-personal-finance-api
   JWT_AUDIENCE=ai-personal-finance-mobile

   # Cấu hình AI Gemini Key
   AI_PROVIDER=gemini
   AI_MODEL=gemini-3.1-flash-lite
   GEMINI_API_KEY=your_gemini_api_key_here
   AI_ENABLED=true
   ```

---

## 🐳 BƯỚC 2: KHỞI ĐỘNG HỆ THỐNG BACKEND BẰNG DOCKER

1. **Chạy Docker Compose**:
   Mở PowerShell tại thư mục gốc dự án và chạy:
   ```powershell
   docker compose -f infra/docker/docker-compose.dev.yml --env-file .env up -d --build
   ```

2. **Kiểm tra trạng thái các Container**:
   ```powershell
   docker ps
   ```
   *Kết quả cần đạt được*: Bạn sẽ thấy 4 container đang ở trạng thái `Up (healthy)`:
   - `docker-api-1` (Port 8000)
   - `docker-worker-1`
   - `docker-postgres-1` (Port 5433 -> 5432)
   - `docker-redis-1` (Port 6379)

3. **Kiểm tra Healthcheck API**:
   Mở trình duyệt hoặc dùng cURL truy cập `http://localhost:8000/health`. Trả về `{"status":"ok"}` là thành công.

---

## 🗄️ BƯỚC 3: MIGRATION CƠ SỞ DỮ LIỆU & SEED TÀI KHOẢN ADMIN

1. **Chạy Migration CSDL (Alembic)**:
   Chạy lệnh PowerShell sau để cập nhật đầy đủ các bảng dữ liệu mới nhất (bao gồm trường `security_pin_hash` cho tính năng PIN 6 số):
   ```powershell
   cd apps/api
   $env:DATABASE_URL="postgresql://finance_dev:finance_dev_local_only@localhost:5433/finance"
   python -m alembic upgrade head
   cd ../..
   ```

2. **Khởi tạo dữ liệu Super Admin ban đầu (Seed Data)**:
   Chạy lệnh khởi tạo tài khoản Admin chính vào Docker Database:
   ```powershell
   docker exec docker-api-1 python -c "from app.db.session import SessionLocal; from app.db.seed import seed_super_admin; db = SessionLocal(); seed_super_admin(db); print('Seeded admin successfully!')"
   ```

3. **Thông tin tài khoản Super Admin sẵn có**:
   - **Email**: `admin@finance.app`
   - **Mật khẩu**: `AdminPass123!`

---

## 📱 BƯỚC 4: KHỞI ĐỘNG ỨNG DỤNG FLUTTER CLIENT

### Phương Án A: Chạy Ứng Dụng Trên Web (Google Chrome)

1. **Di chuyển vào thư mục mobile client**:
   ```powershell
   cd apps/mobile
   ```

2. **Chạy ứng dụng Web trên Chrome**:
   ```powershell
   flutter run -d chrome
   ```
   *Hoặc chạy Web Server độc lập ở Port 8080*:
   ```powershell
   flutter run -d web-server --web-port 8080 --web-hostname localhost
   ```
3. Truy cập **`http://localhost:8080`** trên trình duyệt.

---

### Phương Án B: Chạy Ứng Dụng Trên Máy Ảo Android (Android Emulator)

1. **Khởi tạo Máy ảo Android (Nếu chưa mở)**:
   ```powershell
   flutter emulators --launch Pixel_10
   ```

2. **Kiểm tra danh sách thiết bị nhận diện**:
   ```powershell
   flutter devices
   ```
   *Xác nhận thấy thiết bị `emulator-5554` hoặc tương tự.*

3. **Khởi chạy ứng dụng lên Máy ảo**:
   ```powershell
   cd apps/mobile
   flutter run -d emulator-5554
   ```

---

## 🔐 BƯỚC 5: SỬ DỤNG VÀ THỬ NGHIỆM TÍNH NĂNG SECURITY PIN 6 SỐ

1. **Đăng Ký Tài Khoản Mới**:
   - Mở màn hình đăng ký (`Create an account`).
   - Nhập Name, Email, Mật khẩu và **Security PIN 6 số** (ví dụ: `123456`).

2. **Khôi Phục Mật Khẩu Bằng PIN**:
   - Ở màn hình Đăng nhập (`Login`), bấm nút **"Quên mật khẩu?"**.
   - Nhập **Email đã đăng ký**, **Mã PIN 6 số**, và **Mật khẩu mới**.
   - Bấm **"Đổi mật khẩu & Đăng nhập"** để truy cập ứng dụng.

3. **Cập Nhật / Đổi Mã PIN**:
   - Đăng nhập vào ứng dụng -> Mở nút **Cài đặt (Bánh răng)** -> Tab **Hồ sơ**.
   - Bấm **"Đổi / Tạo mã PIN 6 số"** để cập nhật mã PIN mới.

---

## 🛠️ XỬ LÝ LỖI THƯỜNG GẶP (TROUBLESHOOTING)

| Hiện tượng / Lỗi | Nguyên nhân | Cách khắc phục |
| :--- | :--- | :--- |
| **`Invalid credentials` khi Đăng nhập Admin** | Mật khẩu Admin chưa được khởi tạo trong DB | Chạy lại lệnh seed admin: `docker exec docker-api-1 python -c "from app.db.session import SessionLocal; from app.db.seed import seed_super_admin; db = SessionLocal(); seed_super_admin(db)"` |
| **`Unsupported HTTP method`** | Chưa nạp file `api_client.dart` có hỗ trợ `PUT` | Bấm **Hot Restart (`R`)** hoặc dừng app và chạy lại `flutter run`. |
| **Màn hình máy ảo Android bị đen (`Lost connection`)** | Máy ảo bị đứt kết nối debug session | Chạy lại lệnh: `flutter run -d emulator-5554` |
| **Lỗi kết nối CSDL khi chạy migration local** | Sai cổng PostgreSQL host | Đảm bảo truyền đúng URL với cổng `5433`: `$env:DATABASE_URL="postgresql://finance_dev:finance_dev_local_only@localhost:5433/finance"` |

---

*Chúc bạn vận hành hệ thống thành công!* 🚀
