"""add reference MIDI and lesson summary tables

Revision ID: 007_database_foundation
Revises: 006_message_client_id
Create Date: 2026-10-15

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "007_database_foundation"
down_revision: Union[str, Sequence[str], None] = "006_message_client_id"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reference_midis",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("storage_key", sa.String(length=500), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("content_sha256", sa.String(length=64), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["course_id"],
            ["courses.id"],
            name="fk_reference_midis_course_id_courses",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["teacher_id"],
            ["users.id"],
            name="fk_reference_midis_teacher_id_users",
        ),
        sa.UniqueConstraint("course_id", name="uq_reference_midis_course_id"),
        sa.CheckConstraint(
            "file_size_bytes >= 0",
            name="ck_reference_midis_file_size_nonnegative",
        ),
    )
    op.create_index(
        "ix_reference_midis_teacher_course",
        "reference_midis",
        ["teacher_id", "course_id"],
    )

    op.create_table(
        "lesson_summaries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("lesson_session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("previous_lesson_session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("window_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("window_ended_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "source_recording_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("summary_text", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["lesson_session_id"],
            ["lesson_sessions.id"],
            name="fk_lesson_summaries_lesson_session_id_lesson_sessions",
        ),
        sa.ForeignKeyConstraint(
            ["previous_lesson_session_id"],
            ["lesson_sessions.id"],
            name="fk_lesson_summaries_previous_session_id_lesson_sessions",
        ),
        sa.ForeignKeyConstraint(
            ["course_id"],
            ["courses.id"],
            name="fk_lesson_summaries_course_id_courses",
        ),
        sa.ForeignKeyConstraint(
            ["teacher_id"],
            ["users.id"],
            name="fk_lesson_summaries_teacher_id_users",
        ),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["users.id"],
            name="fk_lesson_summaries_student_id_users",
        ),
        sa.UniqueConstraint(
            "lesson_session_id",
            name="uq_lesson_summaries_lesson_session_id",
        ),
        sa.CheckConstraint(
            "source_recording_count >= 0",
            name="ck_lesson_summaries_source_count_nonnegative",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'completed', 'failed')",
            name="ck_lesson_summaries_status",
        ),
        sa.CheckConstraint(
            "window_started_at IS NULL OR window_ended_at > window_started_at",
            name="ck_lesson_summaries_window_order",
        ),
    )
    op.create_index(
        "ix_lesson_summaries_teacher_course_student",
        "lesson_summaries",
        ["teacher_id", "course_id", "student_id"],
    )
    op.create_index(
        "ix_lesson_summaries_course_student_window_end",
        "lesson_summaries",
        ["course_id", "student_id", "window_ended_at"],
    )

    op.execute(
        sa.text(
            """
            INSERT INTO reference_midis (
                id,
                course_id,
                teacher_id,
                storage_key,
                original_filename,
                content_sha256,
                file_size_bytes
            )
            SELECT
                gen_random_uuid(),
                course.id,
                course.teacher_id,
                course.reference_midi_path,
                CASE
                    WHEN rtrim(replace(course.reference_midi_path, chr(92), '/'), '/') = ''
                    THEN 'reference.mid'
                    ELSE right(
                        regexp_replace(
                            rtrim(replace(course.reference_midi_path, chr(92), '/'), '/'),
                            '^.*/',
                            ''
                        ),
                        255
                    )
                END,
                NULL,
                NULL
            FROM courses AS course
            WHERE course.reference_midi_path IS NOT NULL
            """
        )
    )


def downgrade() -> None:
    op.drop_index(
        "ix_lesson_summaries_course_student_window_end",
        table_name="lesson_summaries",
    )
    op.drop_index(
        "ix_lesson_summaries_teacher_course_student",
        table_name="lesson_summaries",
    )
    op.drop_table("lesson_summaries")
    op.drop_index("ix_reference_midis_teacher_course", table_name="reference_midis")
    op.drop_table("reference_midis")
