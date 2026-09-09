"""add Phase 07 budget and goal indexes"""

from typing import Sequence, Union

from alembic import op

revision: str = "a71f07b2c8e4"
down_revision: Union[str, None] = "9c2d7e4f1a6b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_budget_definition",
        "budgets",
        ["user_id", "period_type", "start_date", "end_date", "currency"],
    )
    op.create_index("ix_budget_categories_category_id", "budget_categories", ["category_id"])
    op.create_index("ix_goal_contributions_goal_id", "goal_contributions", ["goal_id"])
    op.create_index("ix_goal_contributions_date", "goal_contributions", ["contribution_date"])


def downgrade() -> None:
    op.drop_index("ix_goal_contributions_date", table_name="goal_contributions")
    op.drop_index("ix_goal_contributions_goal_id", table_name="goal_contributions")
    op.drop_index("ix_budget_categories_category_id", table_name="budget_categories")
    op.drop_constraint("uq_budget_definition", "budgets", type_="unique")
