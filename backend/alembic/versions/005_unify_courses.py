"""move teacher prototype courses into courses

Revision ID: 005_unify_courses
Revises: 004_student_learning
Create Date: 2026-10-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "005_unify_courses"
down_revision: Union[str, Sequence[str], None] = "004_student_learning"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """把舊的 teacher_module_courses 搬進 courses，並改掉指向舊表的外鍵。"""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "teacher_module_courses" not in tables or "courses" not in tables:
        return

    if "teacher_profiles" in tables:
        bind.execute(
            sa.text(
                """
                INSERT INTO courses (
                    id,
                    teacher_id,
                    title,
                    style,
                    price_per_lesson,
                    time_slots,
                    status,
                    created_at
                )
                SELECT
                    old_course.id,
                    profile.user_id,
                    old_course.course_name,
                    NULLIF(old_course.course_intros, ''),
                    COALESCE(old_course.price_per_lesson, old_course.course_price),
                    CAST(old_course.class_date AS varchar),
                    CASE
                        WHEN old_course.status IN ('draft', 'published', 'archived')
                        THEN old_course.status
                        ELSE 'draft'
                    END,
                    COALESCE(old_course.created_at, NOW())
                FROM teacher_module_courses AS old_course
                JOIN teacher_profiles AS profile
                    ON profile.id = old_course.teacher_profile_id
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM courses AS current_course
                    WHERE current_course.id = old_course.id
                )
                """
            )
        )

    for table_name in ("course_inquiries", "teacher_lesson_sessions", "practice_assignments"):
        if table_name not in tables:
            continue
        for foreign_key in inspector.get_foreign_keys(table_name):
            if foreign_key.get("referred_table") != "teacher_module_courses":
                continue
            if not foreign_key.get("name"):
                continue
            column_name = foreign_key["constrained_columns"][0]
            op.drop_constraint(foreign_key["name"], table_name, type_="foreignkey")
            op.create_foreign_key(
                f"fk_{table_name}_{column_name}_courses",
                table_name,
                "courses",
                [column_name],
                ["id"],
            )

    leftover = bind.execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM teacher_module_courses AS old_course
            WHERE NOT EXISTS (
                SELECT 1
                FROM courses AS current_course
                WHERE current_course.id = old_course.id
            )
            """
        )
    ).scalar()
    remaining_foreign_keys = bind.execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM pg_constraint AS con
            JOIN pg_class AS referred ON referred.oid = con.confrelid
            WHERE con.contype = 'f'
              AND referred.relname = 'teacher_module_courses'
            """
        )
    ).scalar()
    if leftover == 0 and remaining_foreign_keys == 0:
        op.drop_table("teacher_module_courses")


def downgrade() -> None:
    """舊表已經併入 courses，不把課程再拆回第二張表。"""
    pass
