"""add debts and financial_contacts tables

Revision ID: e41d89b3a012
Revises: c93e2b7f4a18
Create Date: 2026-09-30 16:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "e41d89b3a012"
down_revision: Union[str, None] = "d91e847321a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "financial_contacts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("relationship_type", sa.String(length=80), nullable=True),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("is_support_contact", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_financial_contacts_user_id", "financial_contacts", ["user_id"])

    op.create_table(
        "debts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("counterparty_name", sa.String(length=120), nullable=False),
        sa.Column("contact_id", sa.String(length=36), nullable=True),
        sa.Column("total_amount", sa.BigInteger(), nullable=False),
        sa.Column("remaining_amount", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="VND", nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("interest_rate", sa.Integer(), server_default=sa.text("0"), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="ACTIVE", nullable=False),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.CheckConstraint("total_amount > 0", name="ck_debts_total_amount_positive"),
        sa.CheckConstraint("remaining_amount >= 0", name="ck_debts_remaining_amount_non_negative"),
        sa.ForeignKeyConstraint(["contact_id"], ["financial_contacts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_debts_user_id", "debts", ["user_id"])
    op.create_index("ix_debts_due_date", "debts", ["due_date"])
    op.create_index("ix_debts_user_status", "debts", ["user_id", "status"])

    op.create_table(
        "debt_payments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("debt_id", sa.String(length=36), nullable=False),
        sa.Column("account_id", sa.String(length=36), nullable=True),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("payment_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.CheckConstraint("amount > 0", name="ck_debt_payments_amount_positive"),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["debt_id"], ["debts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_debt_payments_debt_id", "debt_payments", ["debt_id"])


def downgrade() -> None:
    op.drop_table("debt_payments")
    op.drop_table("debts")
    op.drop_table("financial_contacts")
