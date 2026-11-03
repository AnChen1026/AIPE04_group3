"""weekly availability and recurring lessons

Revision ID: 019_weekly_schedule
Revises: 018_merge_availability_storage
Create Date: 2026-10-31

老師的每週可上課時間與學生的固定上課時間。規則記下已經產生到哪一天，
之後只往後補，老師刪掉的單一時段才不會被補回來。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "019_weekly_schedule"
down_revision: Union[str, Sequence[str], None] = "018_merge_availability_storage"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _rule_columns() -> list:
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "teacher_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("weekday", sa.SmallInteger(), nullable=False),
        sa.Column("start_minute", sa.SmallInteger(), nullable=False),
        sa.Column("end_minute", sa.SmallInteger(), nullable=False),
        sa.Column("generated_through", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    ]


def _rule_checks(table: str) -> list:
    return [
        sa.CheckConstraint("weekday BETWEEN 0 AND 6", name=f"ck_{table}_weekday"),
        sa.CheckConstraint("start_minute >= 0 AND end_minute <= 1440 AND end_minute > start_minute", name=f"ck_{table}_time"),
    ]


def upgrade() -> None:
    op.create_table("weekly_availability", *_rule_columns(), *_rule_checks("weekly_availability"))
    op.create_index("ix_weekly_availability_teacher", "weekly_availability", ["teacher_id"])
    op.create_table(
        "recurring_lessons",
        *_rule_columns(),
        sa.Column(
            "student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
        ),
        *_rule_checks("recurring_lessons"),
    )
    op.create_index("ix_recurring_lessons_teacher", "recurring_lessons", ["teacher_id"])
    op.add_column(
        "availability_slots",
        sa.Column("from_weekly", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "lesson_sessions",
        sa.Column(
            "recurring_lesson_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("recurring_lessons.id", ondelete="SET NULL", name="fk_lesson_sessions_recurring_lesson_id"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_constraint("fk_lesson_sessions_recurring_lesson_id", "lesson_sessions", type_="foreignkey")
    op.drop_column("lesson_sessions", "recurring_lesson_id")
    op.drop_column("availability_slots", "from_weekly")
    op.drop_index("ix_recurring_lessons_teacher", table_name="recurring_lessons")
    op.drop_table("recurring_lessons")
    op.drop_index("ix_weekly_availability_teacher", table_name="weekly_availability")
    op.drop_table("weekly_availability")
