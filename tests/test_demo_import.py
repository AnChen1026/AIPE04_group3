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
    from scripts.import_demo_data import import_demo, identity, _known_versions
    from scripts.demo_catalog import content_fingerprint, profile_fingerprint, PROFILE_FIELDS
    from backend.models.teacher import TeacherDB

    source = json.loads(
        (Path(__file__).resolve().parents[1] / "scripts/data/aicourse-demo.json").read_text()
    )
    import_demo(db, source)
    teacher = source["teachers"][0]
    uid = identity("teacher", teacher["id"])
    user = db.get(User, uid)
    profile = db.scalar(select(TeacherDB).where(TeacherDB.user_id == uid))
    course = db.get(Course, identity("course", source["courses"][0]["id"]))
    user.name = profile.name = "林老師"
    profile.short_intros = "舊版公開介紹"
    profile.expertise = "古典"
    profile.teaching_method = "舊版教法"
    course.title = "舊版課程"
    course.level = "入門"
    course.style = "古典"
    course.description = "舊版課綱"
    # Editing status, media or scheduling is outside the catalog refresh scope.
    course.status = "archived"
    course.image_path = "existing-image.png"
    course.price_per_lesson = 999
    course.reference_midi_path = "existing.mid"
    db.flush()
    versions = _known_versions()
    versions["teachers"][teacher["id"]].append(user.name)
    versions["profiles"][teacher["id"]].append(profile_fingerprint({k: getattr(profile, k) for k in PROFILE_FIELDS}))
    from scripts.demo_catalog import REFRESH_FIELDS, course_fields
    versions["courses"][source["courses"][0]["id"]].append(content_fingerprint({k: getattr(course, k) for k in REFRESH_FIELDS}))

    counts = import_demo(db, source, refresh_existing=True, known_versions=versions)
    assert all(n == 0 for n in counts.values())
    db.expire_all()
    assert user.name == profile.name == teacher["display_name"]
    assert profile.short_intros == teacher["biography"][:200]
    assert profile.teaching_method == teacher["teaching_style"]
    for key in REFRESH_FIELDS:
        assert getattr(course, key) == course_fields(source["courses"][0])[key]
    assert (course.status, course.image_path, course.price_per_lesson, course.reference_midi_path) == ("archived", "existing-image.png", 999, "existing.mid")
    assert all(n == 0 for n in import_demo(db, source, refresh_existing=True).values())


@pytest.mark.parametrize("field,value", [
    ("title", "老師自己改的課名"), ("description", "[虛構測試資料・AICourseFinder] 人工改寫"),
    ("level", "不確定"), ("style", "人工改寫風格"),
])
def test_refresh_rejects_unknown_course_edits_before_any_mutation(db, field, value):
    from scripts.import_demo_data import import_demo, identity
    source = json.loads((Path(__file__).resolve().parents[1] / "scripts/data/aicourse-demo.json").read_text())
    import_demo(db, source)
    course = db.get(Course, identity("course", source["courses"][-1]["id"]))
    setattr(course, field, value)
    db.flush()
    with pytest.raises(ValueError, match="course ID collision"):
        import_demo(db, source, refresh_existing=True)
    assert not db.dirty
    assert getattr(course, field) == value


def test_refresh_rejects_unknown_profile_edits(db):
    from scripts.import_demo_data import import_demo
    from backend.models.teacher import TeacherDB
    source = json.loads((Path(__file__).resolve().parents[1] / "scripts/data/aicourse-demo.json").read_text())
    import_demo(db, source)
    profile = db.scalar(select(TeacherDB))
    profile.short_intros = "老師親自更新的介紹"
    db.flush()
    with pytest.raises(ValueError, match="profile ID collision"):
        import_demo(db, source, refresh_existing=True)
    assert not db.dirty
    assert profile.short_intros == "老師親自更新的介紹"
