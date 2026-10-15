"""Checks that Alembic's shared model registry sees canonical learning tables."""

from backend import models


def test_alembic_metadata_contains_database_foundation_tables() -> None:
    assert {"courses", "reference_midis", "lesson_summaries"} <= set(
        models.Base.metadata.tables
    )
