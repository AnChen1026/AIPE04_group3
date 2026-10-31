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
