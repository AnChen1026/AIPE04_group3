"""add client_message_id for chat dedupe

Revision ID: 006_message_client_id
Revises: 005_unify_courses
Create Date: 2026-10-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "006_message_client_id"
down_revision: Union[str, Sequence[str], None] = "005_unify_courses"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """同一段對話裡，同一個 client_message_id 只會存一筆。"""
    op.add_column(
        "conversation_messages",
        sa.Column("client_message_id", sa.String(length=64), nullable=True),
    )
    op.create_unique_constraint(
        "uq_conversation_messages_client_id",
        "conversation_messages",
        ["conversation_id", "client_message_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_conversation_messages_client_id",
        "conversation_messages",
        type_="unique",
    )
    op.drop_column("conversation_messages", "client_message_id")
