"""Persist failed object deletions for explicit retries."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "016_storage_cleanup"
down_revision = "015_studios"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "storage_cleanup_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("storage_key", sa.String(500), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade():
    op.drop_table("storage_cleanup_jobs")
