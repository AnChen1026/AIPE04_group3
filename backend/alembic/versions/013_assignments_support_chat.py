"""assignments with materials, and admin support chat

Revision ID: 013_assignments_support
Revises: 012_password_resets
Create Date: 2026-10-27

作業和課程分開：老師替已綁定的學生發作業，作業可以有自己的參考 MIDI 與多份教材，
學生的練習錄音可以指到某一份作業。另外加上管理員和老師、學生之間的對話。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "013_assignments_support"
down_revision: Union[str, Sequence[str], None] = "012_password_resets"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False, server_default="performance"),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("midi_path", sa.String(length=500), nullable=True),
        sa.Column("midi_filename", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("kind IN ('performance', 'quiz')", name="ck_assignments_kind"),
    )
    op.create_index("ix_assignments_teacher", "assignments", ["teacher_id"])
    op.create_index("ix_assignments_student_course", "assignments", ["student_id", "course_id"])

    op.create_table(
        "assignment_materials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "assignment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assignments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=True),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_assignment_materials_assignment", "assignment_materials", ["assignment_id"])

    op.add_column(
        "practice_recordings",
        sa.Column(
            "assignment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assignments.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    op.create_table(
        "support_conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "support_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("support_conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sender_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("client_message_id", sa.String(length=64), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("conversation_id", "client_message_id", name="uq_support_messages_client_id"),
    )


def downgrade() -> None:
    op.drop_table("support_messages")
    op.drop_table("support_conversations")
    op.drop_column("practice_recordings", "assignment_id")
    op.drop_index("ix_assignment_materials_assignment", table_name="assignment_materials")
    op.drop_table("assignment_materials")
    op.drop_index("ix_assignments_student_course", table_name="assignments")
    op.drop_index("ix_assignments_teacher", table_name="assignments")
    op.drop_table("assignments")
