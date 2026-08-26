# Financial Data Rules

**Version**: Phase 03  
**Purpose**: Enforce financial invariants and constraints at the database, ORM, and application levels

## Core Principle: Database as Source of Truth

All financial data is authoritative in PostgreSQL. No client-side calculations override database state.

## Money Representation Rule

### Requirement

**Money is always stored as INTEGER (64-bit signed), never FLOAT or DECIMAL.**

Represents the smallest currency unit (e.g., cents for USD, paise for INR).

### Why

- Eliminates floating-point rounding errors
- Ensures exact financial calculations
- Complies with accounting standards
- PostgreSQL `BIGINT` range: ±9,223,372,036,854,775,807 (sufficient for 92 quintillion cents)

### Implementation

**Column Definitions:**
- `Transaction.amount`: `BIGINT NOT NULL`
- `TransactionEntry.amount`: `BIGINT NOT NULL`
- `Account.opening_balance`: `BIGINT NOT NULL`
- `Account.current_balance`: `BIGINT NOT NULL`
- `TransactionItem.amount`: `BIGINT NOT NULL`
- `Budget.total_limit`: `BIGINT NOT NULL`
- `BudgetCategory.limit_amount`: `BIGINT NOT NULL`
- `FinancialGoal.target_amount`: `BIGINT NOT NULL`
- `GoalContribution.amount`: `BIGINT NOT NULL`

**ORM Type Mapping:**
```python
amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
```

### Enforcement

1. **Database Level**: Column type is `BIGINT`, no floating-point types
2. **ORM Level**: SQLAlchemy `BigInteger` type, validated on session flush
3. **Application Level**: API must reject non-integer amounts, convert to integer before storing

### Example: 150 VND

```python
# Currency: VND (Vietnamese Dong, 0 decimal places)
amount_vnd = 150  # Represents 150 VND

# Currency: USD (2 decimal places)
amount_usd = 15000  # Represents $150.00 (15000 cents)

# Currency: BHD (Bahraini Dinar, 3 decimal places)
amount_bhd = 150000  # Represents 150.000 BHD
```

API Documentation must specify currency precision (decimal places) for client conversion.

---

## Positive Money Constraint

### Requirement

**All monetary amounts must be positive (> 0) at the atomic transaction level.**

Signs are represented in entry types (DEBIT/CREDIT), not in amount signs.

### Implementation

**Check Constraints:**
```sql
-- Transactions
ALTER TABLE transactions ADD CONSTRAINT ck_transactions_amount_positive CHECK (amount > 0);

-- Transaction Items
ALTER TABLE transaction_items ADD CONSTRAINT ck_transaction_items_amount_positive CHECK (amount > 0);

-- Budgets
ALTER TABLE budgets ADD CONSTRAINT ck_budgets_total_limit_positive CHECK (total_limit > 0);

-- Budget Categories
ALTER TABLE budget_categories ADD CONSTRAINT ck_budget_categories_limit_positive CHECK (limit_amount > 0);

-- Financial Goals
ALTER TABLE financial_goals ADD CONSTRAINT ck_financial_goals_target_amount_positive CHECK (target_amount > 0);

-- Goal Contributions
ALTER TABLE goal_contributions ADD CONSTRAINT ck_goal_contributions_amount_positive CHECK (amount > 0);
```

**ORM Validation:**
```python
class Transaction(Base):
    amount: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        server_default="1"  # Ensure non-zero default
    )
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_transactions_amount_positive"),
    )
```

### Sign Representation

Directional signs are captured in entry types, not amount signs:

| Entry Type | Meaning | Balance Impact |
|------------|---------|-----------------|
| CREDIT | Money in | + amount |
| DEBIT | Money out | - amount |

**Example: $50 expense**
```python
# Database storage:
transaction = Transaction(
    type=TransactionType.EXPENSE,
    amount=5000,  # Always positive
)
entry = TransactionEntry(
    entry_type=EntryType.DEBIT,  # Represents outflow
    amount=-5000,  # Signed in ledger entry
)
```

---

## Ownership Enforcement via Foreign Keys

### Requirement

**Every user-owned entity MUST have a `user_id` foreign key referencing `users.id`.**

Ensures only entity owners can access or modify their data.

### User-Owned Entities

| Table | Column | Constraint |
|-------|--------|-----------|
| accounts | user_id | FK→users, NOT NULL, ondelete=CASCADE |
| categories | user_id | FK→users, Nullable for system categories |
| transactions | user_id | FK→users, NOT NULL, ondelete=CASCADE |
| budgets | user_id | FK→users, NOT NULL, ondelete=CASCADE |
| financial_goals | user_id | FK→users, NOT NULL, ondelete=CASCADE |
| user_preferences | user_id | FK→users, NOT NULL, UNIQUE, ondelete=CASCADE |
| user_settings | user_id | FK→users, NOT NULL, UNIQUE, ondelete=CASCADE |

### Cascade Delete

When a user is deleted:
- All accounts are deleted
- All transactions are deleted
- All categories (user-created) are deleted
- All budgets are deleted
- All financial goals are deleted
- All preferences and settings are deleted

**SQL Impact**:
```sql
DELETE FROM users WHERE id = 'user-uuid';
-- Cascades to all owned entities
```

**ORM Implementation**:
```python
class User(Base):
    accounts: Mapped[list["Account"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"  # Cascade delete
    )
```

### System vs. User Ownership

**System Categories**: 
- `is_system = true`
- `user_id = NULL`
- Not deleted when user is deleted
- Accessible to all users

**User Categories**:
- `is_system = false`
- `user_id ≠ NULL`
- Deleted when user is deleted
- Owned by specific user

**Constraint**:
```sql
CHECK (
  (is_system = true AND user_id IS NULL) 
  OR 
  (is_system = false AND user_id IS NOT NULL)
)
```

---

## Transfer Semantics

### Single Account Transfer

An expense transaction with no explicit partner:
```python
Transaction(
    type=TransactionType.EXPENSE,
    account_id="checking-uuid",      # Source account
    amount=5000,                      # $50
    transfer_group_id=None,           # Not grouped
)
TransactionEntry(
    account_id="checking-uuid",
    entry_type=EntryType.DEBIT,
    amount=-5000
)
```

### Multi-Account Transfer (A→B)

Two related transactions representing a movement of funds:

**Transaction 1 (Source → Out)**:
```python
Transaction(
    type=TransactionType.TRANSFER,
    account_id="checking-uuid",      # Source
    amount=5000,
    transfer_group_id="group-1"       # Links to Transaction 2
)
TransactionEntry(
    account_id="checking-uuid",
    entry_type=EntryType.DEBIT,
    amount=-5000
)
```

**Transaction 2 (Destination → In)**:
```python
Transaction(
    type=TransactionType.TRANSFER,
    account_id="savings-uuid",       # Destination
    amount=5000,
    transfer_group_id="group-1"       # Same group
)
TransactionEntry(
    account_id="savings-uuid",
    entry_type=EntryType.CREDIT,
    amount=5000
)
```

**Invariant**: Both transactions in the group MUST have:
- Same `amount`
- Same `currency`
- Matching entry types (DEBIT ↔ CREDIT)

### Query for Related Transfers

```python
related = session.query(Transaction).filter(
    Transaction.transfer_group_id == "group-1"
).all()
```

---

## Refund Semantics

A refund is a reversal of a previous transaction.

**Original Transaction**:
```python
original = Transaction(
    type=TransactionType.EXPENSE,
    amount=5000,
    account_id="checking-uuid",
)
```

**Refund Transaction**:
```python
refund = Transaction(
    type=TransactionType.REFUND,
    amount=5000,              # Same amount as original
    account_id="checking-uuid",
    parent_transaction_id=original.id,  # Links to original
)
TransactionEntry(
    account_id="checking-uuid",
    entry_type=EntryType.CREDIT,      # Opposite of original DEBIT
    amount=5000
)
```

**Invariant**: Refund must have:
- `parent_transaction_id` pointing to the original transaction
- Same `amount` as original
- Opposite entry type (CREDIT if original was DEBIT)

### Query for Refunds

```python
refunds = session.query(Transaction).filter(
    Transaction.type == TransactionType.REFUND,
    Transaction.parent_transaction_id == original_id
).all()
```

---

## Split Transaction Semantics

One transaction can have multiple line items (split across categories or payees).

**Example: Grocery receipt with multiple categories**
```python
transaction = Transaction(
    type=TransactionType.EXPENSE,
    amount=10000,              # $100 total
)

items = [
    TransactionItem(
        description="Produce",
        amount=3000,            # $30
        category_id="food-uuid"
    ),
    TransactionItem(
        description="Dairy",
        amount=4000,            # $40
        category_id="dairy-uuid"  # Different category
    ),
    TransactionItem(
        description="Household",
        amount=3000,            # $30
        category_id="supplies-uuid"
    ),
]
```

**Invariant**: Sum of `TransactionItem.amount` MUST equal `Transaction.amount`:
```
3000 + 4000 + 3000 == 10000  ✓
```

### Query for Split Items

```python
items = session.query(TransactionItem).filter(
    TransactionItem.transaction_id == transaction_id
).all()

total = sum(item.amount for item in items)
assert total == transaction.amount
```

---

## Account Balance Rules

### Opening Balance

Set when account is created. Represents the initial balance.

```python
account = Account(
    opening_balance=100000,   # $1000 as starting point
    current_balance=100000,   # Initially equal to opening
)
```

### Current Balance Calculation

**Source of Truth**: Sum of all `TransactionEntry` records for this account.

```sql
SELECT 
  a.id,
  a.opening_balance + COALESCE(SUM(te.amount), 0) as calculated_balance
FROM accounts a
LEFT JOIN transaction_entries te ON a.id = te.account_id
GROUP BY a.id;
```

### Cached Balance Reconciliation

`Account.current_balance` is a denormalized field for performance. It MUST be kept in sync:

```python
# Update after each transaction entry
def update_account_balance(session, account_id):
    account = session.query(Account).get(account_id)
    entries = session.query(TransactionEntry).filter(
        TransactionEntry.account_id == account_id
    ).all()
    
    total = sum(e.amount for e in entries)
    account.current_balance = account.opening_balance + total
    session.flush()
```

**Phase 03 Status**: Calculation logic implemented in ORM tests; production reconciliation deferred to Phase 04.

---

## Constraint Hierarchy

1. **Database Constraints** (REQUIRED, enforced by PostgreSQL)
   - Primary keys, foreign keys
   - Unique constraints
   - Check constraints (amount > 0, system owner rule)
   - NOT NULL defaults

2. **ORM Validation** (RECOMMENDED, enforced by SQLAlchemy)
   - Column types (Integer, String, Enum)
   - Relationships
   - Cascade rules

3. **Application Logic** (OPTIONAL, enforced by FastAPI validators)
   - Business rule validation (e.g., budget not exceeded)
   - Idempotency checks
   - Rate limiting
   - Reconciliation tasks

**Enforcement Order**: Database > ORM > Application

---

## Audit Trail

All financial transactions create audit trail via timestamps:

| Field | Purpose |
|-------|---------|
| created_at | When record was created (immutable) |
| updated_at | When record was last modified |
| deleted_at | When record was soft-deleted (if applicable) |

Timestamps are:
- Server-side generated (database server time)
- Timezone-aware (UTC)
- Automatically managed by ORM

```python
class Transaction(Base):
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
```

---

## Enforcement Checklist

- [x] All monetary columns are `INTEGER` (not FLOAT/DECIMAL)
- [x] Positive amount checks on all relevant tables
- [x] User ownership (`user_id` FK) on all user-owned entities
- [x] Cascade delete for user ownership
- [x] Transfer group ID for multi-account transfers
- [x] Parent transaction ID for refunds and adjustments
- [x] Enum types for transaction types, entry types, statuses
- [x] System vs. user category distinction enforced
- [x] Ledger entry sign representation (DEBIT/CREDIT)
- [x] Timestamps (created_at, updated_at, deleted_at)

---

## Testing

See `tests/test_database_foundation.py` for validation of:
- ✅ Money representation (integer)
- ✅ Ownership enforcement (FK constraints)
- ✅ Transaction entry structure
- ✅ Split transaction structure
- ✅ Refund relationships
- ✅ Financial goal relationships

All tests: **7 PASSED**

---

## Related Documentation

- [Schema Reference](./SCHEMA.md)
- [Migration Guide](./MIGRATION_GUIDE.md)
- [Seed Strategy](./SEED.md)
