# Database Migration Guide

**Version**: Phase 03  
**Tool**: Alembic 1.19+  
**Database**: PostgreSQL 18

## Prerequisites

1. **PostgreSQL 18** installed and running
2. **Python 3.12+** with project dependencies installed
3. **SQLAlchemy 2.x** and **Alembic 1.19+** (in project `pyproject.toml`)
4. `.env` file with both Docker and host database URLs configured

The URLs have different network contexts:
```bash
# Used by API/worker containers inside Docker Compose.
DATABASE_URL=postgresql://username:password@postgres:5432/ai_finance_db
# Used by Alembic and host-side tools on Windows.
HOST_DATABASE_URL=postgresql://username:password@localhost:5433/ai_finance_db
```

## Initial Setup (Fresh Database)

### Step 1: Create PostgreSQL Database and User

```bash
# Connect to PostgreSQL as admin
psql -U postgres

# Create database
CREATE DATABASE ai_finance_db;

# Create user with password
CREATE USER finance_user WITH PASSWORD 'secure_password';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE ai_finance_db TO finance_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO finance_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO finance_user;

# Exit psql
\q
```

### Step 2: Configure `.env`

```bash
DATABASE_URL=postgresql://finance_user:secure_password@postgres:5432/ai_finance_db
HOST_DATABASE_URL=postgresql://finance_user:secure_password@localhost:5433/ai_finance_db
```

### Step 3: Verify Database Connection

```bash
python -c "from app.core.config import get_settings; print(f'Host URL: {get_settings().host_database_url}')"
```

### Step 4: Run Migrations

```bash
\.venv\Scripts\python.exe -m alembic -c .\apps\api\alembic.ini upgrade head
```

**Expected Output**:
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 03811dfc2d31, create MVP foundation schema
```

### Step 5: Verify Schema Creation

```bash
# Connect to the database
psql -U finance_user -d ai_finance_db

# List tables
\dt

# Should show all 14 tables:
# users, accounts, categories, merchants, merchant_aliases, transactions,
# transaction_entries, transaction_items, budgets, budget_categories,
# financial_goals, goal_contributions, user_preferences, user_settings
```

### Step 6: Seed System Categories

```bash
cd apps/api
python -c "
from app.db.session import SessionLocal
from app.db.seed import seed_system_categories

session = SessionLocal()
try:
    seed_system_categories(session)
    session.commit()
    print('✓ System categories seeded successfully')
finally:
    session.close()
"
```

**Verification**:
```bash
psql -U finance_user -d ai_finance_db -c "
  SELECT type, COUNT(*) 
  FROM categories 
  WHERE is_system = true 
  GROUP BY type;
"

# Expected output:
# type   | count
# --------+-------
# EXPENSE | 10
# INCOME  | 5
```

## Migration Management

### View Current Migration Status

```bash
\.venv\Scripts\python.exe -m alembic -c .\apps\api\alembic.ini current
```

### View Migration History

```bash
\.venv\Scripts\python.exe -m alembic -c .\apps\api\alembic.ini history --verbose
```

### Downgrade to Previous Migration

```bash
\.venv\Scripts\python.exe -m alembic -c .\apps\api\alembic.ini downgrade -1
```

### Generate New Migration

When ORM models change, auto-generate a migration:

```bash
\.venv\Scripts\python.exe -m alembic -c .\apps\api\alembic.ini revision --autogenerate -m "Add new field to User"
```

Then review the generated file in `migrations/versions/` and adjust if needed.

### Manual Migration

Create a migration file manually:

```bash
\.venv\Scripts\python.exe -m alembic -c .\apps\api\alembic.ini revision -m "custom migration message"
```

Edit `migrations/versions/XXXX_custom_migration_message.py` with upgrade/downgrade logic.

## Development Workflow

### Fresh Database for Testing

```bash
# Drop and recreate database
psql -U postgres -c "DROP DATABASE IF EXISTS ai_finance_db; CREATE DATABASE ai_finance_db;"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE ai_finance_db TO finance_user;"

# Run migrations
cd apps/api
python -m alembic upgrade head

# Seed system data
python -c "
from app.db.session import SessionLocal
from app.db.seed import seed_system_categories
s = SessionLocal()
try:
    seed_system_categories(s)
    s.commit()
finally:
    s.close()
"
```

### Running Tests

Tests use an in-memory SQLite database (not PostgreSQL) for speed:

```bash
cd apps/api
python -m pytest tests/ -v
```

### Production Deployment

1. Backup existing database
2. Run `python -m alembic upgrade head` in production environment
3. Monitor for errors in application logs
4. Seed system categories if first deployment

## Troubleshooting

### Issue: `FATAL: database does not exist`

**Solution**: Ensure database is created and `DATABASE_URL` is correct in `.env`

### Issue: `alembic: error: the database is now at an earlier version than the version of the migration`

**Solution**: Likely a downgrade was performed. Check `alembic current` and reconcile with git history.

### Issue: Migration fails with constraint violation

**Solution**: 
1. Downgrade the failed migration: `alembic downgrade -1`
2. Check for data conflicts in the database
3. Fix the migration SQL or data
4. Retry upgrade

### Issue: Schema drift (database doesn't match ORM models)

**Solution**:
1. Generate a new migration: `alembic revision --autogenerate -m "fix schema drift"`
2. Review generated migration
3. Test on a staging environment first
4. Apply: `alembic upgrade head`

## Alembic Configuration

Configuration file: `alembic.ini`

Key settings:
- `sqlalchemy.url`: Overridden by `DATABASE_URL` environment variable in `env.py`
- `script_location`: Path to migrations directory
- Logging level: Configurable in `alembic.ini`

## Environment-Specific Configurations

### Local Development

```bash
DATABASE_URL=postgresql://localhost:5433/ai_finance_db
```

### Staging

```bash
DATABASE_URL=postgresql://user:password@staging-host:5432/ai_finance_staging
```

### Production

```bash
DATABASE_URL=postgresql://user:password@prod-host:5432/ai_finance_prod
```

Always use strong passwords and consider using AWS Secrets Manager or similar for production credentials.

## Backup and Recovery

### Backup Database

```bash
pg_dump -U finance_user -d ai_finance_db > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restore Database

```bash
psql -U finance_user -d ai_finance_db < backup_20260101_120000.sql
```

## Related Documentation

- [Schema Reference](./SCHEMA.md)
- [Seed Strategy](./SEED.md)
- [Financial Rules](./FINANCIAL_DATA_RULES.md)
