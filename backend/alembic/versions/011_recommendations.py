"""新增首頁找課推薦對談與結果。

Revision ID: 011_recommendations
Revises: 010_reference_midis
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "011_recommendations"
down_revision: str | None = "010_reference_midis"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "recommendation_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_hash", sa.String(length=64), nullable=False),
        sa.Column("messages", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("criteria", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("asked_fields", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("question_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("question", sa.Text(), nullable=True),
        sa.Column("result_message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "question_count >= 0 AND question_count <= 2",
            name="ck_recommendation_sessions_question_count",
        ),
        sa.CheckConstraint(
            "status IN ('asking', 'done', 'unsupported')",
            name="ck_recommendation_sessions_status",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_recommendation_sessions_owner_hash", "recommendation_sessions", ["owner_hash"])
    op.create_index("ix_recommendation_sessions_expires_at", "recommendation_sessions", ["expires_at"])

    op.create_table(
        "recommendation_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("matched", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("unknown", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["course_id"],
            ["courses.id"],
            name="fk_recommendation_items_course_id_courses",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["recommendation_sessions.id"],
            name="fk_recommendation_items_session_id_recommendation_sessions",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "course_id", name="uq_recommendation_items_session_course"),
        sa.UniqueConstraint("session_id", "position", name="uq_recommendation_items_session_position"),
    )


def downgrade() -> None:
    op.drop_table("recommendation_items")
    op.drop_index("ix_recommendation_sessions_expires_at", table_name="recommendation_sessions")
    op.drop_index("ix_recommendation_sessions_owner_hash", table_name="recommendation_sessions")
    op.drop_table("recommendation_sessions")
