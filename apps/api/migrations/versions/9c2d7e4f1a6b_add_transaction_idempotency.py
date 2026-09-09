"""add transaction idempotency keys

Revision ID: 9c2d7e4f1a6b
Revises: 7f4a9b2c1d0e
Create Date: 2026-08-27
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "9c2d7e4f1a6b"
down_revision: Union[str, None] = "7f4a9b2c1d0e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "transactions", sa.Column("idempotency_key", sa.String(length=128), nullable=True)
    )
    op.create_unique_constraint(
        "uq_transactions_user_idempotency", "transactions", ["user_id", "idempotency_key"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_transactions_user_idempotency", "transactions", type_="unique")
    op.drop_column("transactions", "idempotency_key")