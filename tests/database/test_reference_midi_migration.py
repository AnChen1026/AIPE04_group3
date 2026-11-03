"""Migration contract for reference MIDI metadata."""

from __future__ import annotations

import uuid

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, inspect, text


UPSTREAM_REVISION = "009_images_profile"
REFERENCE_MIDI_REVISION = "010_reference_midis"


def _insert_legacy_course(engine: Engine) -> dict[str, uuid.UUID | str]:
    teacher_id = uuid.uuid4()
    course_id = uuid.uuid4()
    legacy_path = r"uploads\midi\legacy\reference-song.mid"

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO users (id, email, password_hash, name, role)
                VALUES (:teacher_id, :email, 'test-only-hash', 'Migration Teacher', 'teacher')
                """
            ),
            {"teacher_id": teacher_id, "email": f"teacher-{teacher_id}@example.test"},
        )
        connection.execute(
            text(
                """
                INSERT INTO courses (id, teacher_id, title, status, reference_midi_path)
                VALUES (:course_id, :teacher_id, 'Legacy MIDI Course', 'draft', :legacy_path)
                """
            ),
            {"course_id": course_id, "teacher_id": teacher_id, "legacy_path": legacy_path},
        )

    return {"teacher_id": teacher_id, "course_id": course_id, "legacy_path": legacy_path}


def _constraint_names(items: list[dict[str, object]]) -> set[str]:
    return {str(item["name"]) for item in items if item.get("name")}


def test_009_to_head_backfills_reference_midi_metadata(
    migration_database: tuple[Config, Engine],
) -> None:
    config, engine = migration_database
    command.upgrade(config, UPSTREAM_REVISION)
    legacy = _insert_legacy_course(engine)

    # 這個測試只驗證 010 自己；後續 migration 不應改變它的預期版本。
    command.upgrade(config, REFERENCE_MIDI_REVISION)

    inspector = inspect(engine)
    assert "reference_midis" in inspector.get_table_names()
    assert _constraint_names(inspector.get_unique_constraints("reference_midis")) == {
        "uq_reference_midis_course_id"
    }
    assert _constraint_names(inspector.get_check_constraints("reference_midis")) == {
        "ck_reference_midis_file_size_nonnegative"
    }
    assert _constraint_names(inspector.get_foreign_keys("reference_midis")) == {
        "fk_reference_midis_course_id_courses",
        "fk_reference_midis_teacher_id_users",
    }
    assert "ix_reference_midis_teacher_course" in _constraint_names(
        inspector.get_indexes("reference_midis")
    )

    with engine.connect() as connection:
        revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        row = connection.execute(
            text(
                """
                SELECT course_id, teacher_id, storage_key, original_filename,
                       content_sha256, file_size_bytes
                FROM reference_midis
                WHERE course_id = :course_id
                """
            ),
            {"course_id": legacy["course_id"]},
        ).mappings().one()

    assert revision == REFERENCE_MIDI_REVISION
    assert row["course_id"] == legacy["course_id"]
    assert row["teacher_id"] == legacy["teacher_id"]
    assert row["storage_key"] == legacy["legacy_path"]
    assert row["original_filename"] == "reference-song.mid"
    assert row["content_sha256"] is None
    assert row["file_size_bytes"] is None


def test_downgrade_to_009_preserves_legacy_course_path(
    migration_database: tuple[Config, Engine],
) -> None:
    config, engine = migration_database
    command.upgrade(config, UPSTREAM_REVISION)
    legacy = _insert_legacy_course(engine)
    command.upgrade(config, "head")

    command.downgrade(config, UPSTREAM_REVISION)

    assert "reference_midis" not in inspect(engine).get_table_names()
    with engine.connect() as connection:
        midi_path = connection.execute(
            text("SELECT reference_midi_path FROM courses WHERE id = :course_id"),
            {"course_id": legacy["course_id"]},
        ).scalar_one()
    assert midi_path == legacy["legacy_path"]
    command.upgrade(config, "head")
    with engine.connect() as connection:
        assert connection.execute(
            text("SELECT storage_key FROM reference_midis WHERE course_id = :course_id"),
            {"course_id": legacy["course_id"]},
        ).scalar_one() == legacy["legacy_path"]


def test_fresh_database_upgrades_to_single_head(migration_database):
    from alembic.script import ScriptDirectory
    from backend.models.base import Base

    config, engine = migration_database
    command.upgrade(config, "head")
    heads = ScriptDirectory.from_config(config).get_heads()
    assert len(heads) == 1
    tables = set(inspect(engine).get_table_names())
    assert set(Base.metadata.tables) <= tables
    assert "lesson_preparation_summaries" in tables
    assert "lesson_summaries" not in tables
    with engine.connect() as connection:
        assert connection.exec_driver_sql(
            "SELECT version_num FROM alembic_version"
        ).scalar_one() == heads[0]
    command.upgrade(config, "head")  # 重跑不應重複建立資料表或 metadata。
