"""Integration tests for reference MIDI persistence during course creation."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session

from backend.models.student import Course, ReferenceMidi
from backend.models.user import User
from backend.services import student as student_service
from backend.services.student import StudentBusinessError


MIDI_BYTES = b"MThd\x00\x00\x00\x06\x00\x00\x00\x01\x00\x60"
MIDI_SHA256 = "fd67325f6fe391b8c952d50266e5f6006be37cfcc3bb548031b0e7150278e147"


def _create_teacher(db: Session) -> User:
    teacher = User(
        id=uuid.uuid4(),
        email=f"course-teacher-{uuid.uuid4()}@example.test",
        password_hash="test-only-hash",
        auth_provider="password",
        name="Course Teacher",
        role="teacher",
        is_active=True,
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher


def _create_course(db: Session, teacher: User, midi_name: str, midi_content: bytes) -> Course:
    return student_service.create_course(
        db=db,
        teacher=teacher,
        title="Reference MIDI Course",
        level="beginner",
        style="classical",
        delivery_mode="online",
        region=None,
        price_per_lesson=1200,
        time_slots="Saturday morning",
        publish=False,
        midi_name=midi_name,
        midi_content=midi_content,
    )


def test_create_course_with_midi_dual_writes_reference_metadata(
    alembic_config: Config,
    database_engine: Engine,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command.upgrade(alembic_config, "head")
    upload_root = tmp_path / "uploads"
    monkeypatch.setattr(student_service, "UPLOAD_DIR", upload_root)

    with Session(database_engine) as db:
        teacher = _create_teacher(db)
        course = _create_course(db, teacher, "song.mid", MIDI_BYTES)
        reference = db.execute(
            select(ReferenceMidi).where(ReferenceMidi.course_id == course.id)
        ).scalar_one()

        assert course.reference_midi_path == reference.storage_key
        assert reference.teacher_id == teacher.id
        assert reference.original_filename == "song.mid"
        assert reference.content_sha256 == MIDI_SHA256
        assert reference.file_size_bytes == len(MIDI_BYTES)

    stored_files = [path for path in upload_root.rglob("*") if path.is_file()]
    assert stored_files == [Path(reference.storage_key)]
    assert stored_files[0].read_bytes() == MIDI_BYTES


def test_create_course_rejects_non_midi_file_without_side_effects(
    alembic_config: Config,
    database_engine: Engine,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command.upgrade(alembic_config, "head")
    upload_root = tmp_path / "uploads"
    monkeypatch.setattr(student_service, "UPLOAD_DIR", upload_root)

    with Session(database_engine) as db:
        teacher = _create_teacher(db)
        with pytest.raises(StudentBusinessError, match="MIDI"):
            _create_course(db, teacher, "notes.txt", b"not a MIDI file")

        assert db.scalar(select(func.count()).select_from(Course)) == 0
        assert db.scalar(select(func.count()).select_from(ReferenceMidi)) == 0

    assert [path for path in upload_root.rglob("*") if path.is_file()] == []
