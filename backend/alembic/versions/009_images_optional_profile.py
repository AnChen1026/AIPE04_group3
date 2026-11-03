"""teacher photo, course image and description; optional teacher profile fields

Revision ID: 009_images_profile
Revises: 008_lesson_summaries
Create Date: 2026-10-18

老師個人資料只有姓名、性別必填；授課方式、地區等改到每門課各自設定，這裡都改成可空。
原本自動補建時填的「未填寫」換成空值，畫面才分得出有沒有填。
另外新增老師照片、課程圖片與課程介紹。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "009_images_profile"
down_revision: Union[str, Sequence[str], None] = "008_lesson_summaries"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OPTIONAL_TEXT = (
    "expertise",
    "short_intros",
    "teaching_city",
    "teaching_district",
    "target_learning",
    "teaching_method",
    "teaching_style",
)


def upgrade() -> None:
    for column in (*OPTIONAL_TEXT, "age", "seniority"):
        op.alter_column("teacher_profiles", column, nullable=True)
    for column in OPTIONAL_TEXT:
        op.execute(f"UPDATE teacher_profiles SET {column} = NULL WHERE {column} = '未填寫'")
    op.add_column("teacher_profiles", sa.Column("photo_path", sa.String(length=500), nullable=True))

    op.add_column("courses", sa.Column("image_path", sa.String(length=500), nullable=True))
    op.add_column("courses", sa.Column("description", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("courses", "description")
    op.drop_column("courses", "image_path")
    op.drop_column("teacher_profiles", "photo_path")
    for column in OPTIONAL_TEXT:
        op.execute(f"UPDATE teacher_profiles SET {column} = '未填寫' WHERE {column} IS NULL")
    op.execute("UPDATE teacher_profiles SET age = 0 WHERE age IS NULL")
    op.execute("UPDATE teacher_profiles SET seniority = 0 WHERE seniority IS NULL")
    for column in (*OPTIONAL_TEXT, "age", "seniority"):
        op.alter_column("teacher_profiles", column, nullable=False)
