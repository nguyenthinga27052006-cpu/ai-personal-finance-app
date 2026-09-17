# ⚙️ TÀI LIỆU BÁO CÁO & BẢO VỆ CHUYÊN SÂU: THÀNH VIÊN 2 - BACKEND CORE & DATABASE LEAD

---

## 👨‍💻 I. THÔNG TIN THÀNH VIÊN & NỀN TẢNG CÔNG NGHỆ
* **Họ và tên**: Thành viên 2 (Backend Core Lead)
* **Vai trò**: Trưởng nhóm Kiến trúc Backend, Logic Nghiệp vụ & Cơ sở dữ liệu Cốt lõi
* **Ngôn ngữ lập trình & Framework**: 
  - **Language**: **Python 3.12** (Sử dụng Type Hinting mạnh mẽ, Async/Await chuẩn ASGI, Pydantic v2 data parsing nhanh gấp 5-17 lần v1 nhờ core Rust).
  - **Framework**: **FastAPI** (Tốc độ tương đương NodeJS/Go, tích hợp sẵn OpenAPI/Swagger documentation).
  - **Database System**: **PostgreSQL 18** (Hệ quản trị CSDL Quan hệ mạnh mẽ nhất hiện nay với chuẩn ACID tuyệt đối).
  - **Database Driver & ORM**: **psycopg 3.3** (Driver native C/Python hỗ trợ Async) + **SQLAlchemy 2.0** (Async ORM).
  - **Database Migration**: **Alembic 1.20** (Quản lý các phiên bản schema DB dạng code versioning).
  - **Authentication**: **Argon2id** (`pwdlib`) + **PyJWT 2.14** (Mã hóa JWT Access/Refresh Tokens).

---

## 🎯 II. CHI TIẾT KỸ THUẬT & NHIỆM VỤ ĐÃ THỰC HIỆN

### 1. Thiết kế Schema Cơ sở dữ liệu Quan hệ (ERD & Database Architecture)
```
[Users] (1) ─── (N) [Accounts] (1) ─── (N) [Transactions] (N) ─── (1) [Categories]
   │
   ├── (N) [Budgets]
   ├── (N) [SavingGoals]
   ├── (N) [RefreshTokens]
   └── (N) [AIFeedbacks]
```
- **Chuẩn hóa dữ liệu (Database Normalization)**: Đạt chuẩn 3NF (Third Normal Form), đảm bảo không dư thừa dữ liệu và loại bỏ hoàn toàn nguy cơ bất nhất khi cập nhật.
- **Ràng buộc Toàn vẹn (Integrity Constraints)**:
  - Tất cả các khóa ngoại (`foreign_key`) đều có chỉ mục Index và chính sách `ON DELETE CASCADE` hoặc `ON DELETE RESTRICT` được kiểm soát chặt chẽ.
  - Các cột số tiền (`amount`, `current_balance`) lưu ở kiểu dữ liệu `DECIMAL` / `NUMERIC` chính xác cao, tuyệt đối **không** dùng `FLOAT` để tránh lỗi sai số dấu phẩy động trong tài chính.

### 2. Xử lý Logic Nghiệp vụ & Giao dịch An toàn (ACID & Unit of Work)
- **Transaction Safety**: Mỗi khi người dùng tạo/sửa/xóa Giao dịch (Thu/Chi), logic Backend mở một **SQL Transaction Unit of Work**:
  1. Thêm bản ghi vào bảng `transactions`.
  2. Lấy số dư hiện tại của `accounts`, cộng hoặc trừ tương ứng với loại giao dịch.
  3. Kiểm tra điều kiện số dư (không cho phép âm nếu loại ví hạn chế).
  4. Thực thi `await db.commit()`. Nếu phát sinh bất kỳ lỗi gì, toàn bộ quá trình tự động `rollback()`.

### 3. Xây dựng Hệ thống Xác thực Bảo mật Cao (Auth Subsystem)
- **Mã hóa Mật khẩu với Argon2id**: Sử dụng thuật toán thắng giải Password Hashing Competition. Cấu hình thông số an toàn chống GPU Brute-force: `time_cost=3`, `memory_cost=65536 KB`, `parallelism=4`.
- **Cơ chế Cặp Token Dual-JWT**:
  - `access_token`: Hạn dùng ngắn (15 phút), dùng truy cập API.
  - `refresh_token`: Hạn dùng dài (30 ngày), lưu mã băm trong DB (`refresh_tokens`), kèm thông tin thiết bị (`user_agent`, `ip_address`). Khi đăng xuất, server đánh dấu `revoked=True` vô hiệu hóa token ngay lập tức.

---

## ❓ III. BỘ CÂU HỎI & ĐÁP BẢO VỆ KÍN KẼ (DÀNH CHO HỘI ĐỒNG/GIẢNG VIÊN)

### ❓ Câu 1: tại sao bạn chọn Python 3.12 & FastAPI cho hệ thống Backend Tài chính mà không dùng Node.js (Express) hay Java (Spring Boot)?
> **Trả lời kín kẽ**: 
> 1. **Tính tương thích hoàn hảo với AI/Data**: Python là ngôn ngữ số 1 về xử lý dữ liệu và AI. Chọn FastAPI giúp Backend tích hợp trực tiếp, mượt mà với các thư viện AI (Gemini, Data Analytics) mà không phải qua lớp gọi gượng ép giữa 2 ngôn ngữ khác nhau.
> 2. **Hiệu năng Async I/O của FastAPI**: FastAPI dựa trên Starlette và Pydantic v2 (viết bằng Rust), chạy trên máy chủ ASGI (Uvicorn/uvloop), cho tốc độ xử lý I/O bất đồng bộ tiệm cận với Go và Node.js.
> 3. **Type Safety & OpenAPI**: Khai báo Type Hints trong Python 3.12 giúp Pydantic tự động validate dữ liệu đầu vào/đầu ra và tự động sinh Swagger Documentation chuẩn xác mà không cần viết tay file OpenAPI YAML.

### ❓ Câu 2: Tại sao lưu dữ liệu tiền tệ lại phải chọn kiểu DECIMAL/NUMERIC trong PostgreSQL mà không được chọn FLOAT hay DOUBLE?
> **Trả lời kín kẽ**: 
> - Kiểu `FLOAT` / `DOUBLE` trong máy tính biểu diễn số thực theo chuẩn IEEE 754 (dấu phẩy động hệ nhị phân). Khi thực hiện các phép tính cộng trừ tiền tệ (ví dụ: `0.1 + 0.2`), nó sẽ cho ra kết quả `0.30000000000000004`, gây sai lệch kế toán.
> - Kiểu `DECIMAL` / `NUMERIC` trong PostgreSQL lưu trữ số liệu dưới dạng chuỗi số thập phân chính xác tuyệt đối (Fixed-point arithmetic), đảm bảo tính đúng đắn 100% cho các con số tài chính.

### ❓ Câu 3: Làm sao bạn giải quyết vấn đề Concurrency (Nhiều request cùng cập nhật số dư một Ví tài khoản cùng một lúc)?
> **Trả lời kín kẽ**: 
> - Chúng tôi áp dụng kỹ thuật **Pessimistic Locking (Khóa bi quan)** hoặc **Optimistic Locking**:
> - Trong SQL: Sử dụng cú pháp `SELECT ... FOR UPDATE` khi đọc số dư tài khoản trước khi thực hiện cộng/trừ. Câu lệnh này sẽ khóa (lock) dòng bản ghi tài khoản đó trong Postgres cho tới khi Transaction hiện tại `COMMIT`. Các request khác muốn sửa số dư tài khoản đó sẽ phải chờ xếp hàng, triệt tiêu hoàn toàn nguy cơ tranh chấp dữ liệu (Race Condition / Lost Update).

### ❓ Câu 4: Sự khác biệt giữa Authentication (Xác thực) và Authorization (Phân quyền) trong hệ thống của bạn là gì?
> **Trả lời kín kẽ**: 
> - **Authentication (Ai là người truy cập?)**: Kiểm tra Identity người dùng qua Email/Mật khẩu hoặc Access Token. Nếu token hợp lệ, hệ thống trích xuất được `user_id`.
> - **Authorization (Người này có quyền làm gì?)**: Dựa trên thông tin Role (`user` hay `admin`) trích xuất từ token, Middleware sẽ kiểm tra xem người dùng có quyền gọi API đó không. Ví dụ: User chỉ được xem/sửa tài chính của chính mình (`WHERE user_id = current_user.id`), còn các API `/api/v1/admin/*` yêu cầu bắt buộc `current_user.role == 'admin'`.

### ❓ Câu 5: Bạn tối ưu hiệu năng truy vấn SQL như thế nào khi bảng Transactions lên đến hàng triệu bản ghi?
> **Trả lời kín kẽ**: 
> 1. **B-Tree Indexing**: Đặt Index trên các cột tìm kiếm tần suất cao: `(user_id, created_at)`, `account_id`, `category_id`.
> 2. **Composite Indexing**: Tạo Composite Index `(user_id, transaction_date DESC)` để tối ưu các truy vấn trang chủ (lấy 20 giao dịch mới nhất của user).
> 3. **Avoid SELECT \***: Chỉ SELECT các cột cần thiết trong SQLAlchemy queries để giảm tải Memory và Bandwidth mạng giữa Postgres và FastAPI Server.
