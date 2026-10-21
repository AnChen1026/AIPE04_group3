"""lesson preparation summaries

Revision ID: 008_lesson_summaries
Revises: 007_teacher_tables
Create Date: 2026-10-18

課前摘要和每一筆練習回饋分開保存（ADR-0001）。
另外記下每筆錄音當時比對的參考 MIDI，換過曲子的練習才不會被拿來直接比分數。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "008_lesson_summaries"
down_revision: Union[str, Sequence[str], None] = "007_teacher_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "practice_recordings",
        sa.Column("reference_midi_path", sa.String(length=500), nullable=True),
    )
    op.create_table(
        "lesson_preparation_summaries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("lesson_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lesson_sessions.id"), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id"), nullable=False),
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("source_recording_ids", postgresql.JSONB(), nullable=False),
        sa.Column("stats", postgresql.JSONB(), nullable=False),
        sa.Column("summary_text", sa.Text(), nullable=False),
        sa.Column("written_by", sa.String(length=16), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("lesson_id", name="uq_lesson_preparation_summaries_lesson"),
        sa.CheckConstraint("written_by IN ('llm', 'rules')", name="ck_lesson_preparation_summaries_written_by"),
    )


def downgrade() -> None:
    op.drop_table("lesson_preparation_summaries")
    op.drop_column("practice_recordings", "reference_midi_path")
