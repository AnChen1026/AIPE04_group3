from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.main import app
from backend.models.student import CourseBinding, LessonSession
from backend.models.user import User
from backend.services import demo_accounts
from tests.conftest import PASSWORD

TEACHER_EMAIL = "demo-teacher@aipe04-test.tw"
STUDENT_EMAIL = "demo-student@aipe04-test.tw"


@pytest.fixture
def demo_env(monkeypatch):
    values = {
        "DEMO_TEACHER_EMAIL": TEACHER_EMAIL,
        "DEMO_TEACHER_PASSWORD": PASSWORD,
        "DEMO_STUDENT_EMAIL": STUDENT_EMAIL,
        "DEMO_STUDENT_PASSWORD": PASSWORD,
    }
    monkeypatch.setattr(demo_accounts, "read_env_value", values.get)


def login_as(email):
    client = TestClient(app, follow_redirects=False)
    response = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200, response.text
    return client


def test_demo_accounts_are_bound_with_schedule(db, demo_env):
    demo_accounts.seed_demo_accounts_if_needed(db)

    student = db.scalar(select(User).where(User.email == STUDENT_EMAIL))
    binding = db.scalar(select(CourseBinding).where(CourseBinding.student_id == student.id))
    assert binding.status == "bound"
    lessons = db.scalars(select(LessonSession).where(LessonSession.student_id == student.id)).all()
    now = datetime.now(timezone.utc)
    assert len([lesson for lesson in lessons if lesson.starts_at < now]) == demo_accounts.PAST_LESSON_WEEKS
    assert any(lesson.starts_at > now for lesson in lessons)

    student_client = login_as(STUDENT_EMAIL)
    course_id = binding.course_id
    assert student_client.get(f"/api/student/courses/{course_id}/schedule").json()
    conversations = student_client.get("/api/student/conversations").json()
    assert len(conversations) == 1
    messages = student_client.get(f"/api/student/conversations/{conversations[0]['id']}/messages").json()
    assignments = {item["kind"]: item for item in student_client.get("/api/student/assignments").json()}
    # 對話之後是每份作業各一則作業提醒
    assert [item["body"] for item in messages[: len(demo_accounts.MESSAGES)]] == [body for _, body in demo_accounts.MESSAGES]
    reminders = messages[len(demo_accounts.MESSAGES) :]
    assert len(reminders) == len(assignments)
    assert all(item["body"].startswith("【作業提醒】") for item in reminders)

    assert assignments["performance"]["submission_count"] == len(demo_accounts.RECORDING_FEEDBACK)
    assert assignments["quiz"]["question_count"] == len(demo_accounts.QUIZ_QUESTIONS)
    assert assignments["quiz"]["submission_count"] == 1
    recordings = student_client.get(f"/api/student/courses/{course_id}/recordings").json()
    assert {item["status"] for item in recordings} == {"completed"}

    teacher_client = login_as(TEACHER_EMAIL)
    requests = teacher_client.get("/teacher/change-requests").json()
    assert sorted(item["request_type"] for item in requests) == ["booking", "leave"]


def test_demo_accounts_are_not_recreated(db, demo_env):
    demo_accounts.seed_demo_accounts_if_needed(db)
    teacher = db.scalar(select(User).where(User.email == TEACHER_EMAIL))
    teacher.name = "改過的名字"
    db.commit()

    demo_accounts.seed_demo_accounts_if_needed(db)

    assert db.scalar(select(User).where(User.email == TEACHER_EMAIL)).name == "改過的名字"
    assert len(db.scalars(select(User).where(User.email.in_([TEACHER_EMAIL, STUDENT_EMAIL]))).all()) == 2


def test_no_demo_accounts_without_env(db, monkeypatch):
    monkeypatch.setattr(demo_accounts, "read_env_value", lambda name: None)

    demo_accounts.seed_demo_accounts_if_needed(db)

    assert db.scalar(select(User).where(User.email == TEACHER_EMAIL)) is None
