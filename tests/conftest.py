"""測試共用設定。

測試連到 .env 的 DATABASE_URL，但每個測試都包在一個交易裡，結束後整個回滾，
不會在資料庫留下任何資料。服務層呼叫 commit() 時只會結束 savepoint。
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import app
from backend.core.database import engine, get_db
from backend.core.security import hash_password
from backend.models.student import Course, LessonSession
from backend.models.teacher_application import TeacherApplication
from backend.models.user import User

PASSWORD = "test-password"


@pytest.fixture
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield session
    finally:
        app.dependency_overrides.pop(get_db, None)
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(autouse=True)
def upload_root(tmp_path, monkeypatch):
    """上傳的檔案都寫到暫存資料夾，測試結束就消失。"""
    import backend.core.uploads as uploads
    import backend.services.course as course_service
    import backend.services.student as student_service

    monkeypatch.setattr(uploads, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(course_service, "MIDI_UPLOAD_DIR", tmp_path / "uploads" / "midi")
    monkeypatch.setattr(student_service, "PRACTICE_UPLOAD_DIR", tmp_path / "uploads" / "practice")
    return tmp_path


@pytest.fixture(autouse=True)
def analysis_session(db, monkeypatch):
    """背景評分也用同一個交易，測試才看得到、也才會一起回滾。"""
    import backend.services.practice as practice

    class SharedSession:
        def __getattr__(self, name):
            return getattr(db, name)

        def close(self):
            pass

    monkeypatch.setattr(practice, "session_factory", SharedSession)


@pytest.fixture
def make_user(db):
    def make(role: str, name: str | None = None) -> User:
        user = User(
            email=f"{role}-{uuid.uuid4().hex[:10]}@aipe04-test.tw",
            password_hash=hash_password(PASSWORD),
            auth_provider="password",
            name=name or role,
            role=role,
            is_active=True,
        )
        db.add(user)
        db.flush()
        if role == "teacher":
            # 老師測試頁要求申請已核准
            db.add(
                TeacherApplication(
                    user_id=user.id,
                    teaching_subjects="鋼琴",
                    teaching_experience="測試",
                    bio="測試",
                    status="approved",
                )
            )
        db.commit()
        return user

    return make


@pytest.fixture
def login(db):
    """回傳已用該帳號登入的 TestClient。每個帳號一個 client，Cookie 才不會互相蓋掉。"""

    def make_client(user: User) -> TestClient:
        client = TestClient(app, follow_redirects=False)
        response = client.post("/api/auth/login", json={"email": user.email, "password": PASSWORD})
        assert response.status_code == 200, response.text
        return client

    return make_client


@pytest.fixture
def make_course(db):
    def make(teacher: User, status: str = "published", title: str = "測試課程") -> Course:
        course = Course(teacher_id=teacher.id, title=title, status=status)
        db.add(course)
        db.commit()
        return course

    return make


@pytest.fixture
def make_lesson(db):
    def make(course: Course, student: User, starts_at: datetime) -> LessonSession:
        lesson = LessonSession(
            course_id=course.id,
            teacher_id=course.teacher_id,
            student_id=student.id,
            starts_at=starts_at,
            ends_at=starts_at + timedelta(hours=1),
            status="scheduled",
        )
        db.add(lesson)
        db.commit()
        return lesson

    return make


def start_conversation(client: TestClient, course: Course) -> str:
    response = client.post(f"/api/student/courses/{course.id}/conversation")
    assert response.status_code == 200, response.text
    return response.json()["id"]


def issue_code(client: TestClient, conversation_id: str):
    return client.post(f"/teacher/conversations/{conversation_id}/binding-code")


def bind(client: TestClient, conversation_id: str, code: str):
    return client.post(f"/api/student/conversations/{conversation_id}/bind", params={"code": code})


def next_week(hour: int) -> datetime:
    base = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0) + timedelta(days=7)
    return base.replace(hour=hour)
