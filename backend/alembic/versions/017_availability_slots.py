"""teacher availability slots

Revision ID: 017_availability_slots
Revises: 016_metronome_score
Create Date: 2026-10-28

老師在課表上開放的可上課時段；已綁定的學生點選後送出約課，時段先保留給他，
老師完成約課才排進正式課表。課務申請記下是從哪個時段來的。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "017_availability_slots"
down_revision: Union[str, Sequence[str], None] = "016_metronome_score"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "availability_slots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="open"),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id"), nullable=True),
        sa.Column(
            "lesson_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("lesson_sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("ends_at > starts_at", name="ck_availability_slots_time_order"),
        sa.CheckConstraint("status IN ('open', 'held', 'booked')", name="ck_availability_slots_status"),
        sa.CheckConstraint(
            "status = 'open' OR (student_id IS NOT NULL AND course_id IS NOT NULL)",
            name="ck_availability_slots_holder",
        ),
    )
    op.create_index("ix_availability_slots_teacher_starts", "availability_slots", ["teacher_id", "starts_at"])
    op.add_column(
        "change_requests",
        sa.Column(
            "availability_slot_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "availability_slots.id",
                ondelete="SET NULL",
                name="fk_change_requests_availability_slot_id",
            ),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_constraint("fk_change_requests_availability_slot_id", "change_requests", type_="foreignkey")
    op.drop_column("change_requests", "availability_slot_id")
    op.drop_index("ix_availability_slots_teacher_starts", table_name="availability_slots")
    op.drop_table("availability_slots")
