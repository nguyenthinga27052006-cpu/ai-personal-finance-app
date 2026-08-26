# Database Testing Strategy

**Phase:** 03.5 Database Reconciliation & Hardening; Phase 04 authentication integration

## Unit Tests

Location: `apps/api/tests/test_database_foundation.py`

- Use in-memory SQLite for fast, isolated ORM tests.
- Verify model creation, relationships, foreign-key behavior, constraints, split structure, and seed idempotency.
- These tests are not evidence of PostgreSQL-specific types or PostgreSQL migration behavior.

Run:

```powershell
cd apps/api
..\.venv\Scripts\python.exe -m pytest tests/test_database_foundation.py -v
```

## PostgreSQL Integration Tests

Location: `apps/api/tests/integration/test_postgres_foundation.py`

- Marked with `@pytest.mark.postgres`.
- Use `POSTGRES_TEST_DATABASE_URL` to select a real PostgreSQL database.
- Verify all 14 tables, BIGINT monetary columns, foreign keys, unique email, ownership references, system category ownership, transaction entries, transfer structure, refund structure, split structure, and seed idempotency.
- Tests skip when the environment variable is absent or the schema has not been migrated. Skipped tests are not PostgreSQL evidence.

For the current Phase 04 gate, the canonical local `.env` defines the isolated host test
database as `POSTGRES_TEST_DATABASE_URL=...@localhost:5433/finance_test`. The application
database remains `postgres:5432/finance` in Docker and `localhost:5433/finance` for host
application tools. `apps/api/tests/conftest.py` loads the repository-root `.env` for pytest,
so direct root and API-directory invocations use the same test configuration without a
per-terminal environment export.

The `finance_test` database is project-local and must never be replaced with production,
staging, or the normal development database `finance` for integration testing. Migrate it
to the current Alembic head before running the suite. Test identities use unique values and
the suite does not reset the `finance` development database.

Example:

```powershell
cd apps/api
..\.venv\Scripts\python.exe -m pytest tests/integration -m postgres -v
```

The integration suite must target PostgreSQL 18 for the Phase 03.5 acceptance gate. PostgreSQL 17 is not an equivalent replacement.

## E2E Tests

E2E tests are not implemented in Phase 03.5. They will eventually exercise API + PostgreSQL + Redis, but this phase does not implement authentication or financial application services.

## Required Validation Order

1. Reset only the project-local development database.
2. Run `alembic upgrade head`.
3. Run seed twice.
4. Run direct PostgreSQL schema verification.
5. Run PostgreSQL integration tests.
6. Run full unit test suite.
7. Run Ruff.
8. Check `/health` and `/ready`.
9. Run `git diff --check`.

## CI TODO

Add a CI integration stage with a PostgreSQL 18 service/container and Redis service. The stage must run migrations before the marked PostgreSQL test suite and must publish skipped/failed counts explicitly.
