"""Store rebuildable course embeddings.

Revision ID: 020_course_embeddings
Revises: 019_weekly_schedule
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "020_course_embeddings"
down_revision = "019_weekly_schedule"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "course_embeddings",
        sa.Column(
            "course_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("courses.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("model_version", sa.String(160), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("embedding", postgresql.JSONB, nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade():
    op.drop_table("course_embeddings")
