"""add security_pin_hash to users

Revision ID: d91e847321a5
Revises: b9eb44868406
Create Date: 2026-09-21 16:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d91e847321a5"
down_revision: Union[str, None] = "b9eb44868406"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("security_pin_hash", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "security_pin_hash")
