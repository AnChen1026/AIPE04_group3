"""teacher_profiles, learning_materials and quizzes become real migrations

Revision ID: 007_teacher_tables
Revises: 006_message_client_id
Create Date: 2026-10-18

這三張表以前由 app.py 啟動時的 create_all() 補建，所以有人的資料庫已經有，有人沒有。
這裡沒有就建立，有就沿用；教材與測驗的 teacher_id 也從 teacher_profiles.id 改成 users.id，
和課程、對話、綁定等其他資料一致。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "007_teacher_tables"
down_revision: Union[str, Sequence[str], None] = "006_message_client_id"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OWNED_TABLES = ("learning_materials", "quizzes")


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _drop_teacher_fks(table: str, referred_table: str) -> None:
    for foreign_key in sa.inspect(op.get_bind()).get_foreign_keys(table):
        if foreign_key["referred_table"] == referred_table and foreign_key["constrained_columns"] == ["teacher_id"]:
            op.drop_constraint(foreign_key["name"], table, type_="foreignkey")


def upgrade() -> None:
    existing = _tables()

    if "teacher_profiles" not in existing:
        op.create_table(
            "teacher_profiles",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, unique=True),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("gender", sa.String(20), nullable=False),
            sa.Column("age", sa.Integer(), nullable=False),
            sa.Column("seniority", sa.Integer(), nullable=False),
            sa.Column("expertise", sa.String(200), nullable=False),
            sa.Column("short_intros", sa.String(200), nullable=False),
            sa.Column("teaching_city", sa.String(100), nullable=False),
            sa.Column("teaching_district", sa.String(100), nullable=False),
            sa.Column("target_learning", sa.String(255), nullable=False),
            sa.Column("teaching_method", sa.String(255), nullable=False),
            sa.Column("teaching_style", sa.String(100), nullable=False),
            sa.Column("status", sa.String(20), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )

    if "learning_materials" not in existing:
        op.create_table(
            "learning_materials",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("filename", sa.String(255), nullable=True),
            sa.Column("file_type", sa.String(50), nullable=True),
            sa.Column("file_path", sa.String(500), nullable=True),
            sa.Column("uploaded_at", sa.DateTime(), nullable=True),
        )
    if "quizzes" not in existing:
        op.create_table(
            "quizzes",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("title", sa.String(200), nullable=True),
            sa.Column("question", sa.Text(), nullable=True),
            sa.Column("answer", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )

    for table in OWNED_TABLES:
        _drop_teacher_fks(table, "teacher_profiles")
        # 舊資料存的是 teacher_profiles.id，換成對應的 users.id
        op.execute(
            f"UPDATE {table} SET teacher_id = teacher_profiles.user_id "
            f"FROM teacher_profiles WHERE teacher_profiles.id = {table}.teacher_id"
        )
        op.create_foreign_key(f"fk_{table}_teacher_user", table, "users", ["teacher_id"], ["id"])


def downgrade() -> None:
    for table in OWNED_TABLES:
        op.drop_constraint(f"fk_{table}_teacher_user", table, type_="foreignkey")
        op.execute(
            f"UPDATE {table} SET teacher_id = teacher_profiles.id "
            f"FROM teacher_profiles WHERE teacher_profiles.user_id = {table}.teacher_id"
        )
        op.create_foreign_key(f"{table}_teacher_id_fkey", table, "teacher_profiles", ["teacher_id"], ["id"])
    # 表本身保留：舊版程式啟動時本來就會用 create_all() 建這三張表
