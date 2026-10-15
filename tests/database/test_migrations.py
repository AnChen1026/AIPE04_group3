"""Contract tests for the database-foundation Alembic revision."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, inspect, text


UPSTREAM_REVISION = "006_message_client_id"
FOUNDATION_REVISION = "007_database_foundation"


def _insert_legacy_learning_data(engine: Engine) -> dict[str, uuid.UUID | str]:
    teacher_id = uuid.uuid4()
    student_id = uuid.uuid4()
    course_id = uuid.uuid4()
    session_id = uuid.uuid4()
    legacy_path = r"uploads\midi\legacy\reference-song.mid"
    starts_at = datetime.now(timezone.utc) + timedelta(days=1)

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO users (id, email, password_hash, name, role, auth_provider)
                VALUES
                    (:teacher_id, :teacher_email, :password_hash, :teacher_name, 'teacher', 'password'),
                    (:student_id, :student_email, :password_hash, :student_name, 'student', 'password')
                """
            ),
            {
                "teacher_id": teacher_id,
                "teacher_email": f"teacher-{teacher_id}@example.test",
                "student_id": student_id,
                "student_email": f"student-{student_id}@example.test",
                "password_hash": "test-only-hash",
                "teacher_name": "Migration Teacher",
                "student_name": "Migration Student",
            },
        )
        connection.execute(
            text(
                """
                INSERT INTO courses (
                    id, teacher_id, title, status, reference_midi_path
                ) VALUES (
                    :course_id, :teacher_id, :title, 'draft', :legacy_path
                )
                """
            ),
            {
                "course_id": course_id,
                "teacher_id": teacher_id,
                "title": "Legacy MIDI Course",
                "legacy_path": legacy_path,
            },
        )
        connection.execute(
            text(
                """
                INSERT INTO lesson_sessions (
                    id, course_id, teacher_id, student_id, starts_at, ends_at, status
                ) VALUES (
                    :session_id, :course_id, :teacher_id, :student_id,
                    :starts_at, :ends_at, 'scheduled'
                )
                """
            ),
            {
                "session_id": session_id,
                "course_id": course_id,
                "teacher_id": teacher_id,
                "student_id": student_id,
                "starts_at": starts_at,
                "ends_at": starts_at + timedelta(hours=1),
            },
        )

    return {
        "teacher_id": teacher_id,
        "student_id": student_id,
        "course_id": course_id,
        "session_id": session_id,
        "legacy_path": legacy_path,
    }


def _constraint_names(items: list[dict[str, object]]) -> set[str]:
    return {str(item["name"]) for item in items if item.get("name")}


def test_upgrade_backfills_reference_midi_and_creates_lesson_summaries(
    alembic_config: Config,
    database_engine: Engine,
) -> None:
    command.upgrade(alembic_config, UPSTREAM_REVISION)
    legacy = _insert_legacy_learning_data(database_engine)

    command.upgrade(alembic_config, "head")

    inspector = inspect(database_engine)
    assert {"reference_midis", "lesson_summaries"} <= set(inspector.get_table_names())

    with database_engine.connect() as connection:
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

    assert row["course_id"] == legacy["course_id"]
    assert row["teacher_id"] == legacy["teacher_id"]
    assert row["storage_key"] == legacy["legacy_path"]
    assert row["original_filename"] == "reference-song.mid"
    assert row["content_sha256"] is None
    assert row["file_size_bytes"] is None

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
    assert _constraint_names(inspector.get_indexes("reference_midis")) >= {
        "ix_reference_midis_teacher_course"
    }

    assert _constraint_names(inspector.get_unique_constraints("lesson_summaries")) == {
        "uq_lesson_summaries_lesson_session_id"
    }
    assert _constraint_names(inspector.get_check_constraints("lesson_summaries")) == {
        "ck_lesson_summaries_source_count_nonnegative",
        "ck_lesson_summaries_status",
        "ck_lesson_summaries_window_order",
    }
    assert _constraint_names(inspector.get_foreign_keys("lesson_summaries")) == {
        "fk_lesson_summaries_course_id_courses",
        "fk_lesson_summaries_lesson_session_id_lesson_sessions",
        "fk_lesson_summaries_previous_session_id_lesson_sessions",
        "fk_lesson_summaries_student_id_users",
        "fk_lesson_summaries_teacher_id_users",
    }
    assert _constraint_names(inspector.get_indexes("lesson_summaries")) >= {
        "ix_lesson_summaries_teacher_course_student",
        "ix_lesson_summaries_course_student_window_end",
    }


def test_downgrade_to_006_keeps_legacy_midi_path(
    alembic_config: Config,
    database_engine: Engine,
) -> None:
    command.upgrade(alembic_config, UPSTREAM_REVISION)
    legacy = _insert_legacy_learning_data(database_engine)
    command.upgrade(alembic_config, "head")

    with database_engine.connect() as connection:
        current_revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    assert current_revision == FOUNDATION_REVISION

    command.downgrade(alembic_config, UPSTREAM_REVISION)

    inspector = inspect(database_engine)
    assert "reference_midis" not in inspector.get_table_names()
    assert "lesson_summaries" not in inspector.get_table_names()
    with database_engine.connect() as connection:
        midi_path = connection.execute(
            text("SELECT reference_midi_path FROM courses WHERE id = :course_id"),
            {"course_id": legacy["course_id"]},
        ).scalar_one()
    assert midi_path == legacy["legacy_path"]
