import json
from pathlib import Path

import pytest
from sqlalchemy import func, select

from backend.models.student import Course
from backend.models.user import User


def test_seed_is_idempotent_and_preserves_existing(db, make_user):
    from scripts.import_demo_data import import_demo

    source = json.loads(
        (
            Path(__file__).resolve().parents[1] / "scripts/data/aicourse-demo.json"
        ).read_text()
    )
    existing = make_user("student")
    first = import_demo(db, source)
    assert first["users"] == 226
    assert first["courses"] == 426
    second = import_demo(db, source)
    assert all(n == 0 for n in second.values())
    assert db.get(User, existing.id).role == "student"
    assert db.scalar(select(func.count()).select_from(Course)) == 426


def test_seed_rejects_modified_existing_user(db):
    from scripts.import_demo_data import import_demo

    source = json.loads(
        (
            Path(__file__).resolve().parents[1] / "scripts/data/aicourse-demo.json"
        ).read_text()
    )
    import_demo(db, source)
    user = db.scalar(select(User).where(User.email.like("aicourse-%")))
    user.name = "changed"
    db.flush()
    with pytest.raises(ValueError, match="collision"):
        import_demo(db, source)


def test_refresh_legacy_demo_content_and_names(db):
    from scripts.import_demo_data import import_demo, identity
    from backend.models.teacher import TeacherDB

    source = json.loads(
        (Path(__file__).resolve().parents[1] / "scripts/data/aicourse-demo.json").read_text()
    )
    import_demo(db, source)
    teacher = source["teachers"][0]
    uid = identity("teacher", teacher["id"])
    user = db.get(User, uid)
    user.name = "示範教師 0001"
    profile = db.scalar(select(TeacherDB).where(TeacherDB.user_id == uid))
    profile.name = user.name
    profile.short_intros = "[虛構測試資料] 舊介紹"
    course = db.get(Course, identity("course", source["courses"][0]["id"]))
    course.description = "[虛構測試資料・AICourseFinder]\n來源課程：XXX。原型有效期限XXXX"
    db.flush()

    counts = import_demo(db, source, refresh_existing=True)
    assert all(n == 0 for n in counts.values())
    assert user.name == profile.name == teacher["display_name"]
    assert profile.short_intros == teacher["biography"][:200]
    assert "雙手協調" in course.description
    assert all(word not in course.description for word in ("虛構", "來源課程", "有效期限"))
    assert all(n == 0 for n in import_demo(db, source, refresh_existing=True).values())
