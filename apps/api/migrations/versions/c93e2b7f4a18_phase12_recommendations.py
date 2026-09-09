"""add Phase 12 recommendations and events"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c93e2b7f4a18"
down_revision: Union[str, None] = "b82f1a6c9d07"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "recommendations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("suggested_action", sa.String(), nullable=False),
        sa.Column("expected_impact", sa.String(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("source_insight_id", sa.String(length=36), nullable=True),
        sa.Column("source_metric", sa.String(length=160), nullable=False),
        sa.Column("subject_id", sa.String(length=36), nullable=True),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("deterministic_id", sa.String(length=64), nullable=False),
        sa.Column("dedupe_key", sa.String(length=255), nullable=False),
        sa.Column("ranking_score", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("feedback_score", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("deterministic_id"),
        sa.UniqueConstraint("dedupe_key"),
    )
    op.create_index("ix_recommendations_user_status", "recommendations", ["user_id", "status"])
    op.create_index("ix_recommendations_user_created", "recommendations", ["user_id", "created_at"])
    op.create_table(
        "recommendation_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recommendation_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("feedback", sa.String(length=32), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["recommendation_id"], ["recommendations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_recommendation_events_recommendation",
        "recommendation_events",
        ["recommendation_id", "created_at"],
    )
    op.create_index(
        "ix_recommendation_events_user", "recommendation_events", ["user_id", "created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_recommendation_events_user", table_name="recommendation_events")
    op.drop_index("ix_recommendation_events_recommendation", table_name="recommendation_events")
    op.drop_table("recommendation_events")
    op.drop_index("ix_recommendations_user_created", table_name="recommendations")
    op.drop_index("ix_recommendations_user_status", table_name="recommendations")
    op.drop_table("recommendations")