"""reference MIDI metadata with legacy-path backfill

Revision ID: 010_reference_midis
Revises: 009_images_profile
Create Date: 2026-10-18

先保留 courses.reference_midi_path 供既有下載、評分與摘要讀取；新表保存可稽核的
檔案資訊。所有讀取端搬完後，再由後續 migration 移除舊欄位。
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "010_reference_midis"
down_revision: Union[str, Sequence[str], None] = "009_images_profile"
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
            WHERE NULLIF(btrim(course.reference_midi_path), '') IS NOT NULL
            """
        )
    )


def downgrade() -> None:
    op.drop_index("ix_reference_midis_teacher_course", table_name="reference_midis")
    op.drop_table("reference_midis")
