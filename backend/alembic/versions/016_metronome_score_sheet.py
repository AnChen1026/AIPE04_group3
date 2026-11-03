"""metronome tempo and comparison score sheets

Revision ID: 016_metronome_score
Revises: 015_studios
Create Date: 2026-10-27

作業記下參考 MIDI 的速度與老師指定的練習速度；練習錄音記下節拍器速度（有開時節奏照它評分）；
練習回饋記下答案與學生上下對照樂譜（MusicXML）的位置。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "016_metronome_score"
down_revision: Union[str, Sequence[str], None] = "015_studios"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("assignments", sa.Column("midi_bpm", sa.Float(), nullable=True))
    op.add_column("assignments", sa.Column("practice_bpm", sa.Integer(), nullable=True))
    op.add_column("practice_recordings", sa.Column("metronome_bpm", sa.Float(), nullable=True))
    op.add_column("practice_feedbacks", sa.Column("score_sheet_path", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("practice_feedbacks", "score_sheet_path")
    op.drop_column("practice_recordings", "metronome_bpm")
    op.drop_column("assignments", "practice_bpm")
    op.drop_column("assignments", "midi_bpm")
