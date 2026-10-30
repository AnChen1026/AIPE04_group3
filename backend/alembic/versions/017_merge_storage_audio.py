"""Merge private storage and metronome/score-sheet migration histories."""

revision = "017_merge_storage_audio"
down_revision = ("016_storage_cleanup", "016_metronome_score")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
