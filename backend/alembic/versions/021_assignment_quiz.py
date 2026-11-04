"""題庫作業的題目與學生作答紀錄。

Revision ID: 021_assignment_quiz
Revises: 020_course_embeddings
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "021_assignment_quiz"
down_revision = "020_course_embeddings"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "assignment_quiz_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "assignment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assignments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer, nullable=False),
        sa.Column("question_type", sa.String(16), nullable=False),
        sa.Column("difficulty", sa.String(16), nullable=True),
        sa.Column("topic", sa.String(100), nullable=True),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("options", postgresql.JSONB, nullable=False),
        sa.Column("answers", postgresql.JSONB, nullable=False),
        sa.Column("explanation", sa.Text, nullable=True),
        sa.Column("hint", sa.Text, nullable=True),
        sa.CheckConstraint("question_type IN ('single', 'multiple', 'truefalse')", name="ck_quiz_questions_type"),
    )
    op.create_index("ix_quiz_questions_assignment", "assignment_quiz_questions", ["assignment_id", "position"])

    op.create_table(
        "quiz_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "assignment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assignments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("attempt_no", sa.Integer, nullable=False),
        sa.Column("correct_count", sa.Integer, nullable=False),
        sa.Column("question_count", sa.Integer, nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_quiz_attempts_assignment_student", "quiz_attempts", ["assignment_id", "student_id"])

    op.create_table(
        "quiz_attempt_answers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "attempt_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("quiz_attempts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "question_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assignment_quiz_questions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("selected", postgresql.JSONB, nullable=False),
        sa.Column("is_correct", sa.Boolean, nullable=False),
    )
    op.create_index("ix_quiz_attempt_answers_attempt", "quiz_attempt_answers", ["attempt_id"])


def downgrade():
    op.drop_index("ix_quiz_attempt_answers_attempt", table_name="quiz_attempt_answers")
    op.drop_table("quiz_attempt_answers")
    op.drop_index("ix_quiz_attempts_assignment_student", table_name="quiz_attempts")
    op.drop_table("quiz_attempts")
    op.drop_index("ix_quiz_questions_assignment", table_name="assignment_quiz_questions")
    op.drop_table("assignment_quiz_questions")
