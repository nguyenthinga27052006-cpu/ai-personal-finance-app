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

Migration và seed vẫn là các lệnh foundation của Phase 03; business APIs hiện đã bao gồm auth, accounts, catalog, transactions, budgets/goals, analytics và insights theo progress checkpoint.

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

The current master baseline covers Phase 00 through Phase 18 and is **FAIL** at final V1 regression because current Journey A failed. Phase 16 is **CLOSED**, Phase 17 is **PASS WITH DOCUMENTED LIMITATIONS**, and Phase 18 is the final V1 phase with a **NO-GO** decision pending Journey A remediation. This does not claim staging, production or store verification.

### Phase 17 local checks

```powershell
./.venv/Scripts/python.exe -m pytest apps/api/tests/test_phase17_operability.py
docker build -t finance-assistant-api:test apps/api
docker build -t finance-assistant-worker:test apps/worker
```

When the API is running locally, Prometheus-style metrics are available at `http://localhost:8000/metrics`. The backup/restore entry point is `./scripts/backup-restore-drill.ps1`; actual restore execution remains unverified.

Current evidence: `python -m pytest apps/api/tests -q` collected 119 tests, with 119 passed, 0 failed, and 9 warnings. The Phase 17 focused suite has 9 passing tests. Backup artifacts, restore execution, financial restore integrity, RPO/RTO measurement, external tracing/error tracking, production-scale metrics, and fired alerts remain NOT VERIFIED.

Phase 17 documentation: [docs/phase17/README.md](docs/phase17/README.md), [MASTER_STATUS.md](docs/project-status/MASTER_STATUS.md), [PHASE_STATUS.md](docs/project-status/PHASE_STATUS.md), [PRODUCTION_READINESS_MATRIX.md](docs/phase17/PRODUCTION_READINESS_MATRIX.md), [PHASE17_REGRESSION.md](docs/phase17/PHASE17_REGRESSION.md), [PHASE17_ACCEPTANCE_MATRIX.md](docs/phase17/PHASE17_ACCEPTANCE_MATRIX.md), and [PHASE17_FILE_INVENTORY.md](docs/phase17/PHASE17_FILE_INVENTORY.md). Final V1 report: [FINAL_V1_FULL_REGRESSION_00_18.md](docs/project-status/FINAL_V1_FULL_REGRESSION_00_18.md).