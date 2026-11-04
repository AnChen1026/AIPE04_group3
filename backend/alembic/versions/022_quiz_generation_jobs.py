"""AI 出題的背景工作：進度、AI 原本的題目與老師審查後的題目。

Revision ID: 022_quiz_generation_jobs
Revises: 021_assignment_quiz
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "022_quiz_generation_jobs"
down_revision = "021_assignment_quiz"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "quiz_generation_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("title", sa.String(200), nullable=True),
        sa.Column(
            "course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("settings", postgresql.JSONB, nullable=False),
        sa.Column("source_filename", sa.String(255), nullable=False),
        sa.Column("source_text", sa.Text, nullable=False),
        sa.Column("provider", sa.String(32), nullable=True),
        sa.Column("model", sa.String(120), nullable=True),
        sa.Column("progress", sa.Integer, nullable=False, server_default="0"),
        sa.Column("questions", postgresql.JSONB, nullable=True),
        sa.Column("final_questions", postgresql.JSONB, nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column(
            "assignment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assignments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed', 'published', 'discarded')",
            name="ck_quiz_generation_jobs_status",
        ),
    )
    op.create_index("ix_quiz_generation_jobs_teacher", "quiz_generation_jobs", ["teacher_id", "created_at"])


def downgrade():
    op.drop_index("ix_quiz_generation_jobs_teacher", table_name="quiz_generation_jobs")
    op.drop_table("quiz_generation_jobs")
