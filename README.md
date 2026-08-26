# AI Personal Finance Assistant

Ứng dụng quản lý tài chính cá nhân tích hợp AI.

## Setup in <10 minutes

### Prerequisites

- Docker Desktop với Docker Compose v2 đang chạy.
- Python 3.12 hoặc 3.13 cho test/lint local.
- Git.

### Start local services

```powershell
Copy-Item .env.example .env
docker compose --env-file .env -f infra/docker/docker-compose.dev.yml up --build -d
```

Hoặc dùng script:

```powershell
./scripts/dev-up.ps1
```

PostgreSQL 18 sử dụng volume local `finance-assistant_postgres_data` được mount tại `/var/lib/postgresql`. Host mapping là `localhost:5433 -> postgres:5432`; API và worker trong Docker luôn dùng `postgres:5432`.

Kiểm tra API:

```powershell
Invoke-WebRequest http://localhost:8000/health
Invoke-WebRequest http://localhost:8000/ready
```

Swagger/OpenAPI: http://localhost:8000/docs

### Run checks

```powershell
./scripts/test.ps1
./scripts/lint.ps1
./scripts/migrate.ps1
./scripts/seed.ps1
```

Migration và seed là các lệnh foundation của Phase 03: migration tạo schema và seed tạo 15 system categories. Business APIs và business data workflows vẫn được dành cho phase sau.

### Stop local services

```powershell
./scripts/dev-down.ps1
```

Thêm `-v` vào lệnh `docker compose down` nếu cần xóa dữ liệu local và tạo lại database từ đầu.

## Troubleshooting

- `docker` không được nhận diện: cài và khởi động Docker Desktop, sau đó mở terminal mới.
- Port `5433`, `6379` hoặc `8000` đã được dùng: chỉnh port tương ứng trong `.env` và kiểm tra lại URL kết nối. Không đổi `postgres:5432` trong `DATABASE_URL` của Docker.
- `/health` trả lỗi: kiểm tra `docker compose ... ps` và `docker compose ... logs api`.
- `/ready` trả `503`: chờ PostgreSQL/Redis healthy, rồi xem `docker compose ... ps` và logs của dependency.
- Không muốn giữ dữ liệu local: chạy `docker compose --env-file .env -f infra/docker/docker-compose.dev.yml down -v`.

Nếu volume PostgreSQL cũ được tạo theo layout trước đây và PostgreSQL 18 không khởi động, dùng reset có xác nhận:

```powershell
./scripts/reset-dev-db.ps1
```

Script chỉ xóa volume local `finance-assistant_postgres_data` (hoặc tên có prefix `COMPOSE_PROJECT_NAME` trong `.env`), không tham chiếu staging/production. Dữ liệu trong volume sẽ mất vĩnh viễn; chỉ nhập `RESET-LOCAL-POSTGRES` khi đã xác nhận đó là dữ liệu development.

## Documentation

Xem [docs/README.md](docs/README.md) và [docs/IMPLEMENTATION_CONTRACT.md](docs/IMPLEMENTATION_CONTRACT.md).

## Agent Rules and Progress

- [AGENT_RULES.md](AGENT_RULES.md)
- [AGENT_PROGRESS.md](AGENT_PROGRESS.md)

## Current Status

Phase 02 foundation: API health/readiness, local PostgreSQL/Redis Compose và scaffold worker đã có. Financial business features, migrations, mobile implementation và AI provider chưa được triển khai.