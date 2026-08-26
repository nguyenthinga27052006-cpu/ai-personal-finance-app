from __future__ import annotations

import os
import sys

import psycopg

EXPECTED_TABLES = {
    "users",
    "accounts",
    "categories",
    "merchants",
    "merchant_aliases",
    "transactions",
    "transaction_entries",
    "transaction_items",
    "budgets",
    "budget_categories",
    "financial_goals",
    "goal_contributions",
    "user_preferences",
    "user_settings",
}
MONEY_COLUMNS = {
    "accounts.opening_balance",
    "accounts.current_balance",
    "accounts.credit_limit",
    "transactions.amount",
    "transaction_entries.amount",
    "transaction_items.amount",
    "budgets.total_limit",
    "budget_categories.limit_amount",
    "financial_goals.target_amount",
    "goal_contributions.amount",
}
CHECKS = {
    "ck_accounts_opening_balance_nonnegative",
    "ck_accounts_current_balance_nonnegative",
    "ck_accounts_credit_limit_nonnegative",
    "ck_categories_system_owner",
    "ck_transactions_amount_positive",
    "ck_transaction_entries_amount_nonzero",
    "ck_transaction_items_amount_positive",
    "ck_transaction_items_quantity_positive",
    "ck_budgets_period_valid",
    "ck_budgets_total_limit_positive",
    "ck_budget_categories_limit_positive",
    "ck_financial_goals_target_positive",
    "ck_goal_contributions_amount_positive",
}
INDEXES = {
    "ix_accounts_user_id",
    "ix_budgets_user_period",
    "ix_categories_user_id",
    "ix_financial_goals_user_id",
    "ix_merchants_normalized_name",
    "ix_transactions_account_date",
    "ix_transactions_category_date",
    "ix_transactions_merchant_date",
    "ix_transactions_user_date",
    "ix_transaction_entries_account_id_created_at",
    "ix_transaction_entries_transaction_id",
    "ix_transaction_items_category_id",
    "ix_transaction_items_transaction_id",
}


def main() -> int:
    database_url = os.environ["DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://", 1)
    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            print(f"PostgreSQL: {cursor.fetchone()[0].split(',')[0]}")

            cursor.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
            )
            tables = {row[0] for row in cursor.fetchall()}
            assert EXPECTED_TABLES <= tables, EXPECTED_TABLES - tables
            print(f"Tables: {len(EXPECTED_TABLES)} expected tables present")

            cursor.execute(
                "SELECT table_name || '.' || column_name, data_type "
                "FROM information_schema.columns WHERE table_schema = 'public'"
            )
            columns = dict(cursor.fetchall())
            wrong_money = {name for name in MONEY_COLUMNS if columns.get(name) != "bigint"}
            assert not wrong_money, wrong_money
            print("Money columns: BIGINT policy verified")

            cursor.execute(
                "SELECT constraint_name FROM information_schema.table_constraints "
                "WHERE table_schema = 'public'"
            )
            names = {row[0] for row in cursor.fetchall()}
            assert CHECKS <= names, CHECKS - names
            cursor.execute(
                "SELECT 1 FROM information_schema.table_constraints tc "
                "JOIN information_schema.constraint_column_usage ccu "
                "ON tc.constraint_name = ccu.constraint_name "
                "AND tc.table_schema = ccu.table_schema "
                "WHERE tc.table_schema = 'public' AND tc.table_name = 'users' "
                "AND tc.constraint_type = 'UNIQUE' AND ccu.column_name = 'email'"
            )
            assert cursor.fetchone(), "users.email unique constraint missing"
            print("Constraints: check constraints and users.email uniqueness verified")

            cursor.execute("SELECT indexname FROM pg_indexes WHERE schemaname = 'public'")
            indexes = {row[0] for row in cursor.fetchall()}
            assert INDEXES <= indexes, INDEXES - indexes
            print(f"Indexes: {len(INDEXES)} expected indexes present")

            cursor.execute(
                "SELECT COUNT(*) FILTER (WHERE is_system), "
                "COUNT(*) FILTER (WHERE is_system AND type = 'EXPENSE'), "
                "COUNT(*) FILTER (WHERE is_system AND type = 'INCOME') FROM categories"
            )
            counts = cursor.fetchone()
            assert counts == (15, 10, 5), counts
            print(f"Seed: {counts[0]} system categories ({counts[1]} expense, {counts[2]} income)")

            cursor.execute(
                "SELECT COUNT(*) FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace "
                "WHERE n.nspname = 'public' AND t.typtype = 'e'"
            )
            assert cursor.fetchone()[0] == 0
            cursor.execute("SELECT version_num FROM alembic_version")
            print(f"Alembic revision: {cursor.fetchone()[0]} (head)")

    print("REAL_POSTGRES_SCHEMA_VERIFICATION=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
