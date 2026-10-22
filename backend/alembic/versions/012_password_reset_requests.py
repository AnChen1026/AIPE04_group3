"""password reset requests handled by admins

Revision ID: 012_password_resets
Revises: 011_recommendations
Create Date: 2026-10-19

忘記密碼先做地端版本：使用者送出 Email，管理員在後台替他重設成臨時密碼。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "012_password_resets"
down_revision: Union[str, Sequence[str], None] = "011_recommendations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "password_reset_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("handled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("handled_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.CheckConstraint("status IN ('pending', 'completed', 'dismissed')", name="ck_password_reset_requests_status"),
    )
    op.create_index("ix_password_reset_requests_user_id", "password_reset_requests", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_password_reset_requests_user_id", table_name="password_reset_requests")
    op.drop_table("password_reset_requests")
