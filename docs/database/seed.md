# Seed Data Strategy

**Version**: Phase 03  
**Scope**: System categories only

## Overview

Seed data initializes system-wide reference data that all users can access. For MVP Phase 03, we only seed **system categories** (expense and income types).

**Design Principle**: Idempotent seeding — running seed multiple times produces the same result (no duplicates).

## System Categories

### Expense Categories (10)

| Order | Name | Type | Description |
|-------|------|------|-------------|
| 1 | Food & Dining | EXPENSE | Groceries, restaurants, cafes |
| 2 | Housing | EXPENSE | Rent, mortgage, utilities |
| 3 | Transportation | EXPENSE | Gas, public transit, car maintenance |
| 4 | Shopping | EXPENSE | Clothing, general retail |
| 5 | Health & Medical | EXPENSE | Doctor visits, prescriptions, health |
| 6 | Education | EXPENSE | Tuition, books, courses |
| 7 | Entertainment | EXPENSE | Movies, games, hobbies |
| 8 | Utilities & Services | EXPENSE | Internet, phone, subscriptions |
| 9 | Subscriptions | EXPENSE | Software, streaming, memberships |
| 10 | Other (Expense) | EXPENSE | Miscellaneous expenses |

### Income Categories (5)

| Order | Name | Type | Description |
|-------|------|------|-------------|
| 1 | Salary | INCOME | Regular employment income |
| 2 | Bonus | INCOME | Performance bonuses |
| 3 | Freelance | INCOME | Freelance or contract work |
| 4 | Investment Income | INCOME | Dividends, interest, capital gains |
| 5 | Other (Income) | INCOME | Miscellaneous income |

## Seeding Implementation

### Code Location

`apps/api/app/db/seed.py` contains the `seed_system_categories(session)` function.

### Idempotency Strategy

The seed function checks for existing system categories before inserting:

```python
def seed_system_categories(session: Session) -> None:
    """Seed system categories if not already present."""
    # Check if already seeded
    existing = session.query(Category).filter(Category.is_system == True).count()
    if existing > 0:
        return  # Already seeded
    
    # Create categories
    categories = [
        Category(name="Food & Dining", type=CategoryType.EXPENSE.value, is_system=True, ...),
        ...
    ]
    session.add_all(categories)
    session.flush()
```

**Idempotency Guarantee**: Query before insert — if any system categories exist, skip insertion entirely. This ensures:
- First run: Creates 15 categories
- Second run: Detects existing categories, skips
- Nth run: No changes, no duplicates

### Running Seed

#### Option 1: Python Script

```bash
cd apps/api
python -c "
from app.db.session import SessionLocal
from app.db.seed import seed_system_categories

session = SessionLocal()
try:
    seed_system_categories(session)
    session.commit()
    print('✓ Seed completed')
finally:
    session.close()
"
```

#### Option 2: PowerShell Script

```bash
.\scripts\seed.ps1
```

#### Option 3: Programmatic (in tests or initialization)

```python
from app.db.seed import seed_system_categories

def startup():
    session = SessionLocal()
    try:
        seed_system_categories(session)
        session.commit()
    finally:
        session.close()

app.add_event_handler("startup", startup)
```

## Verification

### Check Seeded Categories

```bash
psql -U finance_user -d ai_finance_db -c "
SELECT COUNT(*) as total, type, is_system 
FROM categories 
WHERE is_system = true 
GROUP BY type, is_system;
"

# Expected output:
# total | type    | is_system
# -------+---------+----------
#    10 | EXPENSE | t
#     5 | INCOME  | t
```

### List All System Categories

```bash
psql -U finance_user -d ai_finance_db -c "
SELECT name, type, sort_order 
FROM categories 
WHERE is_system = true 
ORDER BY type DESC, sort_order ASC;
"
```

### Test Idempotency

```bash
# Run seed twice and verify counts are identical

# First run
python -c "
from app.db.session import SessionLocal
from app.db.seed import seed_system_categories
s = SessionLocal()
seed_system_categories(s)
s.commit()
count1 = s.query(Category).filter(Category.is_system == True).count()
s.close()
print(f'Count after first run: {count1}')
"

# Second run
python -c "
from app.db.session import SessionLocal
from app.db.seed import seed_system_categories
s = SessionLocal()
seed_system_categories(s)
s.commit()
count2 = s.query(Category).filter(Category.is_system == True).count()
s.close()
print(f'Count after second run: {count2}')
"

# Should print same count both times
```

## Future Seed Data

For Phase 04+ when implementing additional features:

- **Merchants**: Common merchants with category hints (e.g., Starbucks → Food & Dining)
- **Budget Templates**: Starter budgets (e.g., "60/30/10 rule")
- **Financial Goals**: Common goal types (e.g., Emergency Fund, Vacation, Home Down Payment)
- **User Defaults**: Default settings and preferences for new users

Each would follow the same idempotent pattern:
1. Check if data exists
2. If not, insert
3. Commit
4. No duplicates on repeat runs

## Testing Seed Functionality

Unit test in `tests/test_database_foundation.py`:

```python
def test_seed_is_idempotent(session):
    """Verify seed can run multiple times without duplicates."""
    seed_system_categories(session)
    count1 = session.query(Category).filter(Category.is_system == True).count()
    
    seed_system_categories(session)
    count2 = session.query(Category).filter(Category.is_system == True).count()
    
    assert count1 == count2, "Idempotency broken: counts differ"
    assert count1 >= 10, "Insufficient system categories seeded"
```

Status: PASS

## Related Documentation

- [Schema Reference](./SCHEMA.md)
- [Migration Guide](./MIGRATION_GUIDE.md)
- [Financial Rules](./FINANCIAL_DATA_RULES.md)
