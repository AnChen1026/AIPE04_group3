"""allow optional teacher proof files

Revision ID: 003_optional_proof
Revises: 002_teacher_apps
Create Date: 2026-10-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003_optional_proof"
down_revision: Union[str, Sequence[str], None] = "002_teacher_apps"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "teacher_applications",
        "proof_file_path",
        existing_type=sa.String(length=500),
        nullable=True,
    )
    op.alter_column(
        "teacher_applications",
        "proof_file_name",
        existing_type=sa.String(length=255),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "teacher_applications",
        "proof_file_name",
        existing_type=sa.String(length=255),
        nullable=False,
    )
    op.alter_column(
        "teacher_applications",
        "proof_file_path",
        existing_type=sa.String(length=500),
        nullable=False,
    )
