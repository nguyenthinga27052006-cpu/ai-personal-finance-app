# Database Schema Documentation

**Version**: Phase 03 Foundation  
**Last Updated**: 2026-01-XX  
**Database**: PostgreSQL 18  
**ORM**: SQLAlchemy 2.x  
**Migrations**: Alembic 1.19+

## Overview

The financial database is designed with a **ledger-first architecture** where:
- `Transaction` represents domain events (deposits, withdrawals, transfers)
- `TransactionEntry` represents ledger impacts (the double-entry or multi-entry bookkeeping entries)
- `Account` represents financial accounts with cached balances
- Money is always stored as **integers** (representing the smallest currency unit, e.g., cents for USD, paise for INR)
- Ownership is enforced via foreign keys (`user_id` on all user-owned entities)

## Core Tables

### 1. **users**

User accounts and authentication.

| Column | Type | Constraints | Notes |
|--------|------|-----------|-------|
| id | UUID | PK | Auto-generated UUID |
| email | VARCHAR(320) | NOT NULL, UNIQUE | Email address |
| email_verified_at | DATETIME | Nullable | Timestamp when email was verified |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt/argon2 hash |
| display_name | VARCHAR(120) | Nullable | User's display name |
| default_currency | VARCHAR(3) | NOT NULL, DEFAULT "VND" | ISO 4217 currency code |
| timezone | VARCHAR(64) | NOT NULL, DEFAULT "UTC" | IANA timezone |
| locale | VARCHAR(16) | NOT NULL, DEFAULT "vi-VN" | BCP 47 locale |
| status | VARCHAR(32) | NOT NULL, DEFAULT "ACTIVE" | Enum: ACTIVE, INACTIVE, SUSPENDED |
| created_at | DATETIME | NOT NULL | Server timestamp |
| updated_at | DATETIME | NOT NULL | Server timestamp |
| deleted_at | DATETIME | Nullable | Soft delete timestamp |

**Indexes**: (email), (created_at), (status)  
**Relationships**: → accounts, categories, budgets, transactions, financial_goals, user_preferences, user_settings

---

### 2. **accounts**

Financial accounts (bank, cash, credit card, wallet, etc.).

| Column | Type | Constraints | Notes |
|--------|------|-----------|-------|
| id | UUID | PK | Auto-generated UUID |
| user_id | UUID | NOT NULL, FK→users | Account owner |
| name | VARCHAR(120) | NOT NULL | User-friendly account name |
| type | VARCHAR(32) | NOT NULL | Enum: CASH, BANK, E_WALLET, CREDIT_CARD, SAVINGS, OTHER |
| currency | VARCHAR(3) | NOT NULL | ISO 4217 code |
| opening_balance | BIGINT | NOT NULL, ≥ 0 | Initial balance in smallest unit |
| current_balance | BIGINT | NOT NULL, ≥ 0, DEFAULT 0 | Cached current balance |
| credit_limit | BIGINT | Nullable, ≥ 0 | For credit cards, may be NULL |
| status | VARCHAR(32) | NOT NULL, DEFAULT "ACTIVE" | Enum: ACTIVE, INACTIVE, ARCHIVED |
| is_archived | BOOLEAN | NOT NULL, DEFAULT false | Soft archive flag |
| created_at | DATETIME | NOT NULL | Server timestamp |
| updated_at | DATETIME | NOT NULL | Server timestamp |
| deleted_at | DATETIME | Nullable | Soft delete timestamp |

**Constraints**:
- `ck_accounts_opening_balance_nonnegative`: opening_balance ≥ 0
- `ck_accounts_current_balance_nonnegative`: current_balance ≥ 0
- `ck_accounts_credit_limit_nonnegative`: credit_limit IS NULL OR credit_limit ≥ 0

**Indexes**: (user_id), (created_at), (status)  
**Relationships**: ← users | → transactions, transaction_entries, goal_contributions

---

### 3. **categories**

Transaction categories (expense, income, system-defined or user-created).

| Column | Type | Constraints | Notes |
|--------|------|-----------|-------|
| id | UUID | PK | Auto-generated UUID |
| user_id | UUID | Nullable, FK→users | NULL for system categories |
| name | VARCHAR(120) | NOT NULL | Category name |
| type | VARCHAR(32) | NOT NULL | Enum: EXPENSE, INCOME |
| parent_id | UUID | Nullable, FK→categories | For hierarchical categories |
| icon | VARCHAR(64) | Nullable | Icon identifier (e.g., emoji or icon name) |
| color_token | VARCHAR(64) | Nullable | Color token for UI rendering |
| is_system | BOOLEAN | NOT NULL, DEFAULT false | true = system category |
| is_active | BOOLEAN | NOT NULL, DEFAULT true | Active/inactive flag |
| sort_order | INTEGER | NOT NULL, DEFAULT 0 | Display order |
| created_at | DATETIME | NOT NULL | Server timestamp |
| updated_at | DATETIME | NOT NULL | Server timestamp |
| deleted_at | DATETIME | Nullable | Soft delete timestamp |

**Constraints**:
- `ck_categories_system_owner`: (is_system = true AND user_id IS NULL) OR (is_system = false AND user_id IS NOT NULL)
  - Ensures system categories have no user, and user categories belong to a user

**Indexes**: (user_id), (type), (parent_id)  
**Relationships**: ← users | → merchants (category_hint), budget_categories, transaction_items, transactions

---

### 4. **merchants**

Merchant/vendor entities with canonical names and aliases.

| Column | Type | Constraints | Notes |
|--------|------|-----------|-------|
| id | UUID | PK | Auto-generated UUID |
| canonical_name | VARCHAR(160) | NOT NULL | Primary merchant name |
| normalized_name | VARCHAR(160) | NOT NULL, UNIQUE | Normalized for matching (lowercase, no whitespace) |
| category_hint | UUID | Nullable, FK→categories | Suggested category for transactions from this merchant |
| logo_url | VARCHAR(500) | Nullable | URL to merchant logo |
| status | VARCHAR(32) | NOT NULL, DEFAULT "ACTIVE" | Enum: ACTIVE, INACTIVE |
| created_at | DATETIME | NOT NULL | Server timestamp |
| updated_at | DATETIME | NOT NULL | Server timestamp |
| deleted_at | DATETIME | Nullable | Soft delete timestamp |

**Indexes**: (normalized_name), (canonical_name)  
**Relationships**: ← categories (via category_hint) | → merchant_aliases, transactions

---

### 5. **merchant_aliases**

Alternative names for merchants (autocomplete, matching).

| Column | Type | Constraints | Notes |
|--------|------|-----------|-------|
| id | UUID | PK | Auto-generated UUID |
| merchant_id | UUID | NOT NULL, FK→merchants | Parent merchant |
| alias | VARCHAR(160) | NOT NULL | Alternative name |
| normalized_alias | VARCHAR(160) | NOT NULL | Normalized version |
| source | VARCHAR(32) | NOT NULL, DEFAULT "MANUAL" | Enum: MANUAL, BANK_IMPORT, USER_IMPORT |
| confidence | FLOAT | Nullable | Confidence score for matches (0-1) |
| created_at | DATETIME | NOT NULL | Server timestamp |
| updated_at | DATETIME | NOT NULL | Server timestamp |

**Constraints**:
- `uq_merchant_alias`: UNIQUE(merchant_id, normalized_alias)

**Relationships**: ← merchants

---

### 6. **transactions**

Domain events representing financial transactions.

| Column | Type | Constraints | Notes |
|--------|------|-----------|-------|
| id | UUID | PK | Auto-generated UUID |
| user_id | UUID | NOT NULL, FK→users | Transaction owner |
| account_id | UUID | Nullable, FK→accounts | Primary account (may be NULL for transfers) |
| type | VARCHAR(32) | NOT NULL | Enum: INCOME, EXPENSE, TRANSFER, REFUND, ADJUSTMENT |
| status | VARCHAR(32) | NOT NULL | Enum: DRAFT, POSTED, VOIDED, CANCELLED |
| currency | VARCHAR(3) | NOT NULL | ISO 4217 code |
| amount | BIGINT | NOT NULL, > 0 | Absolute amount in smallest unit |
| transaction_date | DATETIME | NOT NULL, DEFAULT now() | When the transaction occurred |
| description | TEXT | Nullable | User notes |
| merchant_id | UUID | Nullable, FK→merchants | Associated merchant |
| category_id | UUID | Nullable, FK→categories | Associated category |
| source | VARCHAR(32) | NOT NULL, DEFAULT "MANUAL" | Enum: MANUAL, BANK_IMPORT, API, RECURRING |
| external_reference | VARCHAR(255) | Nullable | External system reference (bank ID, etc.) |
| parent_transaction_id | UUID | Nullable, FK→transactions | For refunds/adjustments |
| transfer_group_id | UUID | Nullable | Groups related transfer transactions (A→B, B←A) |
| created_at | DATETIME | NOT NULL | Server timestamp |
| updated_at | DATETIME | NOT NULL | Server timestamp |
| deleted_at | DATETIME | Nullable | Soft delete timestamp |

**Constraints**:
- `ck_transactions_amount_positive`: amount > 0

**Indexes**: (user_id, transaction_date), (account_id, transaction_date), (category_id, transaction_date), (merchant_id, transaction_date), (status)  
**Relationships**: ← users | → accounts, merchants, categories, transaction_entries (1-to-many), transaction_items (1-to-many), parent_transaction_id

---

### 7. **transaction_entries**

Ledger entries (the authoritative financial record).

Each `Transaction` can create multiple `TransactionEntry` records (multi-account transfers, splits).
Entry amount is signed: positive = CREDIT (increase), negative = DEBIT (decrease).

| Column | Type | Constraints | Notes |
|--------|------|-----------|-------|
| id | UUID | PK | Auto-generated UUID |
| transaction_id | UUID | NOT NULL, FK→transactions | Parent transaction |
| account_id | UUID | NOT NULL, FK→accounts | Account affected by this entry |
| amount | BIGINT | NOT NULL, ≠ 0 | Signed amount (+ CREDIT, - DEBIT) |
| currency | VARCHAR(3) | NOT NULL | ISO 4217 code |
| entry_type | VARCHAR(32) | NOT NULL | Enum: CREDIT, DEBIT |
| created_at | DATETIME | NOT NULL | Server timestamp |
| updated_at | DATETIME | NOT NULL | Server timestamp |

**Constraints**:
- `ck_transaction_entries_amount_nonzero`: amount <> 0

**Indexes**: (transaction_id), (account_id, created_at)  
**Relationships**: ← transactions, accounts

---

### 8. **transaction_items**

Line items within a transaction (splits, detailed expenses).

| Column | Type | Constraints | Notes |
|--------|------|-----------|-------|
| id | UUID | PK | Auto-generated UUID |
| transaction_id | UUID | NOT NULL, FK→transactions | Parent transaction |
| category_id | UUID | Nullable, FK→categories | Item category |
| description | TEXT | Nullable | Item description |
| amount | BIGINT | NOT NULL, > 0 | Item amount in smallest unit |
| quantity | INTEGER | NOT NULL, > 0, DEFAULT 1 | Item quantity |
| unit_price | BIGINT | Nullable, > 0 | Price per unit |
| created_at | DATETIME | NOT NULL | Server timestamp |
| updated_at | DATETIME | NOT NULL | Server timestamp |

**Constraints**:
- `ck_transaction_items_amount_positive`: amount > 0
- `ck_transaction_items_quantity_positive`: quantity > 0

**Indexes**: (transaction_id), (category_id)  
**Relationships**: ← transactions, categories

---

### 9. **budgets**

Budget definitions (spending plans).

| Column | Type | Constraints | Notes |
|--------|------|-----------|-------|
| id | UUID | PK | Auto-generated UUID |
| user_id | UUID | NOT NULL, FK→users | Budget owner |
| name | VARCHAR(120) | NOT NULL | Budget name |
| period_type | VARCHAR(32) | NOT NULL | Enum: DAILY, WEEKLY, MONTHLY, QUARTERLY, ANNUAL |
| start_date | DATE | NOT NULL | Budget start |
| end_date | DATE | NOT NULL | Budget end |
| total_limit | BIGINT | NOT NULL, > 0 | Total budget limit in smallest unit |
| currency | VARCHAR(3) | NOT NULL | ISO 4217 code |
| status | VARCHAR(32) | NOT NULL | Enum: ACTIVE, PAUSED, ENDED, ARCHIVED |
| created_at | DATETIME | NOT NULL | Server timestamp |
| updated_at | DATETIME | NOT NULL | Server timestamp |

**Constraints**:
- `ck_budgets_period_valid`: start_date ≤ end_date
- `ck_budgets_total_limit_positive`: total_limit > 0

**Indexes**: (user_id, start_date, end_date), (status)  
**Relationships**: ← users | → budget_categories (1-to-many)

---

### 10. **budget_categories**

Categories assigned to a budget with sub-limits.

| Column | Type | Constraints | Notes |
|--------|------|-----------|-------|
| id | UUID | PK | Auto-generated UUID |
| budget_id | UUID | NOT NULL, FK→budgets | Parent budget |
| category_id | UUID | NOT NULL, FK→categories | Budget category |
| limit_amount | BIGINT | NOT NULL, > 0 | Category-specific limit in smallest unit |
| created_at | DATETIME | NOT NULL | Server timestamp |
| updated_at | DATETIME | NOT NULL | Server timestamp |

**Constraints**:
- `ck_budget_categories_limit_positive`: limit_amount > 0

**Relationships**: ← budgets, categories

---

### 11. **financial_goals**

Savings/financial goals.

| Column | Type | Constraints | Notes |
|--------|------|-----------|-------|
| id | UUID | PK | Auto-generated UUID |
| user_id | UUID | NOT NULL, FK→users | Goal owner |
| name | VARCHAR(120) | NOT NULL | Goal name |
| target_amount | BIGINT | NOT NULL, > 0 | Target amount in smallest unit |
| currency | VARCHAR(3) | NOT NULL | ISO 4217 code |
| status | VARCHAR(32) | NOT NULL, DEFAULT "ACTIVE" | Enum: ACTIVE, ON_HOLD, COMPLETED, ABANDONED |
| created_at | DATETIME | NOT NULL | Server timestamp |
| updated_at | DATETIME | NOT NULL | Server timestamp |

**Relationships**: ← users | → goal_contributions (1-to-many)

---

### 12. **goal_contributions**

Contributions toward a financial goal.

| Column | Type | Constraints | Notes |
|--------|------|-----------|-------|
| id | UUID | PK | Auto-generated UUID |
| goal_id | UUID | NOT NULL, FK→financial_goals | Parent goal |
| account_id | UUID | Nullable, FK→accounts | Account from which contribution was made |
| amount | BIGINT | NOT NULL, > 0 | Contribution amount in smallest unit |
| contribution_date | DATE | NOT NULL | Date of contribution |
| note | TEXT | Nullable | User note |
| created_at | DATETIME | NOT NULL | Server timestamp |
| updated_at | DATETIME | NOT NULL | Server timestamp |

**Constraints**:
- `ck_goal_contributions_amount_positive`: amount > 0

**Indexes**: (goal_id), (contribution_date)  
**Relationships**: ← financial_goals, accounts

---

### 13. **user_preferences**

User notification and feature preferences.

| Column | Type | Constraints | Notes |
|--------|------|-----------|-------|
| id | UUID | PK | Auto-generated UUID |
| user_id | UUID | NOT NULL, FK→users, UNIQUE | One per user |
| ai_enabled | BOOLEAN | NOT NULL, DEFAULT false | Enable AI features |
| smart_notifications_enabled | BOOLEAN | NOT NULL, DEFAULT true | Smart alerts |
| weekly_report_enabled | BOOLEAN | NOT NULL, DEFAULT false | Weekly summary |
| monthly_report_enabled | BOOLEAN | NOT NULL, DEFAULT false | Monthly summary |
| budget_alert_enabled | BOOLEAN | NOT NULL, DEFAULT true | Budget alerts |
| anomaly_alert_enabled | BOOLEAN | NOT NULL, DEFAULT true | Unusual activity alerts |
| recurring_reminder_enabled | BOOLEAN | NOT NULL, DEFAULT false | Recurring expense reminders |
| quiet_hours_start | VARCHAR(5) | Nullable | HH:MM format, e.g., "22:00" |
| quiet_hours_end | VARCHAR(5) | Nullable | HH:MM format, e.g., "08:00" |
| max_notifications_per_day | INTEGER | NOT NULL, DEFAULT 10 | Rate limit |
| created_at | DATETIME | NOT NULL | Server timestamp |
| updated_at | DATETIME | NOT NULL | Server timestamp |

**Relationships**: ← users

---

### 14. **user_settings**

User-specific application settings.

| Column | Type | Constraints | Notes |
|--------|------|-----------|-------|
| id | UUID | PK | Auto-generated UUID |
| user_id | UUID | NOT NULL, FK→users, UNIQUE | One per user |
| theme | VARCHAR(32) | NOT NULL, DEFAULT "system" | Enum: light, dark, system |
| week_starts_on | INTEGER | NOT NULL, DEFAULT 1 | 0=Sunday, 1=Monday, etc. |
| financial_month_start | INTEGER | NOT NULL, DEFAULT 1 | Day of month (1-31) |
| minimum_safe_balance | INTEGER | NOT NULL, DEFAULT 0 | Alert threshold (smallest unit) |
| default_account_id | UUID | Nullable, FK→accounts | Default account for transactions |
| created_at | DATETIME | NOT NULL | Server timestamp |
| updated_at | DATETIME | NOT NULL | Server timestamp |

**Relationships**: ← users

---

## Financial Rules Enforced at Schema Level

1. **Money as Integers**: All monetary values (`amount`, `opening_balance`, `current_balance`, etc.) are stored as `BIGINT` (PostgreSQL's 64-bit signed integer). This eliminates floating-point rounding errors.

2. **Positive Money Constraints**:
   - `amount > 0` on `Transaction` (absolute value)
   - `amount > 0` and `quantity > 0` on `TransactionItem`
   - `total_limit > 0` on `Budget`
   - `limit_amount > 0` on `BudgetCategory`
   - `target_amount > 0` on `FinancialGoal`
   - `amount > 0` on `GoalContribution`

3. **Ownership via Foreign Keys**:
   - Every user-owned entity has a `user_id` FK to `users` table
   - Deletion of a user cascades to all owned entities (cascade delete)

4. **Ledger Integrity**:
   - `TransactionEntry.amount <> 0`: Ensures ledger entries are non-zero
   - `TransactionEntry` is the source of truth for account balances
   - `Account.current_balance` is cached and should be reconciled

5. **Transfer/Refund/Split Semantics**:
   - **Transfers**: `parent_transaction_id` is NULL, `transfer_group_id` groups related entries
   - **Refunds**: `parent_transaction_id` references the original transaction
   - **Splits**: Multiple `TransactionItem` records with individual amounts and categories
   - **Adjustments**: `type = ADJUSTMENT`, `parent_transaction_id` references the transaction being adjusted

6. **System vs. User Categories**:
   - Constraint ensures: system categories (is_system=true) have user_id=NULL
   - Constraint ensures: user categories (is_system=false) have user_id≠NULL

## Enumerations

### UserStatus
- ACTIVE
- INACTIVE
- SUSPENDED
- DELETED

### AccountType
- CASH
- BANK
- E_WALLET
- CREDIT_CARD
- SAVINGS
- OTHER

### AccountStatus
- ACTIVE
- INACTIVE
- ARCHIVED

### CategoryType
- EXPENSE
- INCOME

### TransactionType
- INCOME
- EXPENSE
- TRANSFER
- REFUND
- ADJUSTMENT

### TransactionStatus
- DRAFT
- POSTED
- VOIDED
- CANCELLED

### TransactionSource
- MANUAL
- BANK_IMPORT
- API
- RECURRING

### EntryType
- CREDIT (increase balance)
- DEBIT (decrease balance)

### BudgetPeriodType
- DAILY
- WEEKLY
- MONTHLY
- QUARTERLY
- ANNUAL

### BudgetStatus
- ACTIVE
- PAUSED
- ENDED
- ARCHIVED

### GoalStatus
- ACTIVE
- ON_HOLD
- COMPLETED
- ABANDONED

---

## Database Initialization Checklist

- [ ] PostgreSQL 18 instance running
- [ ] Database created (e.g., `ai_finance_db`)
- [ ] User with appropriate permissions created
- [ ] `.env` file configured with `DATABASE_URL`
- [ ] Alembic migrations applied: `alembic upgrade head`
- [ ] Seed system categories: `python -c "from app.db.session import SessionLocal; from app.db.seed import seed_system_categories; s = SessionLocal(); seed_system_categories(s); s.commit()"`

---

## Related Documentation

- [Migration Guide](./MIGRATION_GUIDE.md)
- [Seed Strategy](./SEED.md)
- [Financial Data Rules](./FINANCIAL_DATA_RULES.md)
