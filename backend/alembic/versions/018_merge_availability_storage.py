"""Merge teacher availability and private storage migration histories.

Revision ID: 018_merge_availability_storage
Revises: 017_merge_storage_audio, 017_availability_slots
Create Date: 2026-10-30

可預約時段和私有檔案儲存是同時開發的兩條資料庫更新，這裡把兩條接回同一個版本；
不改任何資料表。
"""

revision = "018_merge_availability_storage"
down_revision = ("017_merge_storage_audio", "017_availability_slots")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
