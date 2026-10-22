"""忘記密碼（地端版本）：使用者送出 Email，管理員重設成臨時密碼。"""

import uuid

from fastapi.testclient import TestClient

from backend.core.security import verify_password
from backend.main import app
from backend.models.password_reset import PasswordResetRequest
from backend.models.user import User
from tests.conftest import PASSWORD

GENERIC = "已收到申請。如果這個 Email 有註冊，管理員會協助重設密碼並另外通知你。"


def request_reset(email: str):
    return TestClient(app).post("/api/auth/password-reset-requests", json={"email": email})


def requests_of(db, user: User) -> list[PasswordResetRequest]:
    return db.query(PasswordResetRequest).filter(PasswordResetRequest.user_id == user.id).all()


def test_送出申請_不管Email有沒有註冊都回同一句話(db, make_user):
    student = make_user("student")
    known = request_reset(student.email.upper())
    unknown = request_reset("nobody@aipe04-test.tw")

    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json() == {"message": GENERIC}
    assert [item.status for item in requests_of(db, student)] == ["pending"]
    assert request_reset("not-an-email").status_code == 422


def test_同一帳號待處理時不重複建立_管理員帳號不建立(db, make_user):
    teacher = make_user("teacher")
    request_reset(teacher.email)
    request_reset(teacher.email)
    assert len(requests_of(db, teacher)) == 1

    admin = make_user("admin")
    assert request_reset(admin.email).json() == {"message": GENERIC}
    assert requests_of(db, admin) == []


def test_管理員重設後_臨時密碼可以登入_舊密碼不行(db, make_user, login):
    student = make_user("student")
    request_reset(student.email)
    admin = login(make_user("admin"))

    rows = admin.get("/api/admin/password-reset-requests").json()
    row = next(item for item in rows if item["user"]["id"] == str(student.id))
    assert row["status"] == "pending"
    assert row["user"]["email"] == student.email
    assert "password_hash" not in row["user"]

    done = admin.post(f"/api/admin/password-reset-requests/{row['id']}/reset")
    assert done.status_code == 200, done.text
    temporary = done.json()["temporary_password"]
    assert len(temporary) == 10
    assert done.json()["request"]["status"] == "completed"

    db.expire_all()
    saved = db.get(User, student.id)
    assert temporary not in saved.password_hash
    assert verify_password(temporary, saved.password_hash)

    client = TestClient(app)
    assert client.post("/api/auth/login", json={"email": student.email, "password": PASSWORD}).status_code == 401
    assert client.post("/api/auth/login", json={"email": student.email, "password": temporary}).status_code == 200

    # 處理過就不能再重設一次，列表也不再回臨時密碼
    assert admin.post(f"/api/admin/password-reset-requests/{row['id']}/reset").status_code == 409
    again = next(item for item in admin.get("/api/admin/password-reset-requests").json() if item["id"] == row["id"])
    assert "temporary_password" not in again
    assert again["handled_at"] is not None


def test_略過申請_密碼不變(db, make_user, login):
    student = make_user("student")
    request_reset(student.email)
    admin = login(make_user("admin"))
    request_id = requests_of(db, student)[0].id

    dismissed = admin.post(f"/api/admin/password-reset-requests/{request_id}/dismiss")
    assert dismissed.status_code == 200
    assert dismissed.json()["status"] == "dismissed"
    assert TestClient(app).post("/api/auth/login", json={"email": student.email, "password": PASSWORD}).status_code == 200
    assert admin.post(f"/api/admin/password-reset-requests/{request_id}/reset").status_code == 409

    # 略過後可以再送新的申請
    request_reset(student.email)
    assert sorted(item.status for item in requests_of(db, student)) == ["dismissed", "pending"]


def test_只有管理員能看與重設(db, make_user, login):
    student = make_user("student")
    request_reset(student.email)
    request_id = requests_of(db, student)[0].id

    for client in (login(make_user("student")), login(make_user("teacher"))):
        assert client.get("/api/admin/password-reset-requests").status_code == 403
        assert client.post(f"/api/admin/password-reset-requests/{request_id}/reset").status_code == 403
    assert TestClient(app).get("/api/admin/password-reset-requests").status_code == 401

    admin = login(make_user("admin"))
    assert admin.post(f"/api/admin/password-reset-requests/{uuid.uuid4()}/reset").status_code == 404
    db.expire_all()
    assert requests_of(db, student)[0].status == "pending"
