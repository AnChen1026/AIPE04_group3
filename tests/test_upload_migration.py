import pytest

from backend.core import storage
from scripts.migrate_uploads import migrate, plan


def test_upload_migration_keeps_local_file_and_updates_all_references(
    db, make_user, make_course, upload_root, monkeypatch
):
    path = upload_root / "uploads/midi/song.mid"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"MThd1234")
    teacher = make_user("teacher")
    course = make_course(teacher)
    course.reference_midi_path = "uploads/midi/song.mid"
    db.flush()
    references = plan(db, upload_root)
    assert len(references) == 1
    assert course.reference_midi_path == "uploads/midi/song.mid"
    objects = {}

    def save(target, content, content_type=None):
        value = (
            "storage://teaching-files/"
            + target.relative_to(upload_root / "uploads").as_posix()
        )
        objects[value] = content
        return value

    from contextlib import contextmanager

    from fastapi import HTTPException

    @contextmanager
    def read(value):
        if value not in objects:
            raise HTTPException(404)
        assert objects[value] == path.read_bytes()
        yield path

    monkeypatch.setattr(storage, "save_file", save)
    monkeypatch.setattr(storage, "local_file", read)
    assert migrate(db, references) == 1
    assert course.reference_midi_path.startswith(
        "storage://teaching-files/materials/migrated/"
    )
    assert path.read_bytes() == b"MThd1234"
    assert plan(db, upload_root) == []


def test_missing_upload_refuses_to_plan(db, make_user, make_course, upload_root):
    course = make_course(make_user("teacher"))
    course.reference_midi_path = "uploads/midi/missing.mid"
    db.flush()
    with pytest.raises(ValueError, match="Missing or unsafe"):
        plan(db, upload_root)
    assert course.reference_midi_path == "uploads/midi/missing.mid"


def test_equal_content_in_distinct_files_keeps_distinct_objects(
    db, make_user, make_course, upload_root, monkeypatch
):
    from contextlib import contextmanager

    from fastapi import HTTPException

    a = upload_root / "uploads/midi/a.mid"
    b = upload_root / "uploads/midi/b.mid"
    a.parent.mkdir(parents=True)
    a.write_bytes(b"MThd1234")
    b.write_bytes(b"MThd1234")
    teacher = make_user("teacher")
    first, second = make_course(teacher), make_course(teacher)
    first.reference_midi_path, second.reference_midi_path = (
        "uploads/midi/a.mid",
        "uploads/midi/b.mid",
    )
    db.flush()
    objects = {}

    def save(target, content, content_type=None):
        value = (
            "storage://teaching-files/"
            + target.relative_to(upload_root / "uploads").as_posix()
        )
        objects[value] = content
        return value

    @contextmanager
    def read(value):
        if value not in objects:
            raise HTTPException(404)
        yield a

    monkeypatch.setattr(storage, "save_file", save)
    monkeypatch.setattr(storage, "local_file", read)
    assert migrate(db, plan(db, upload_root)) == 2
    assert first.reference_midi_path != second.reference_midi_path
    assert len(objects) == 2
