"""管理員和老師、學生的對話；老師審核通過、學生註冊時自動送出歡迎訊息。"""

import uuid

from backend.models.teacher_application import TeacherApplication
from tests.conftest import PASSWORD


def test_核准老師時自動送出審核通過與使用須知(db, make_user, login):
    admin = make_user("admin")
    # 跟老師註冊一樣：身分是老師，但審核通過前還沒啟用
    applicant = make_user("student", name="林老師")
    applicant.role = "teacher"
    applicant.is_active = False
    application = TeacherApplication(
        user_id=applicant.id, teaching_subjects="鋼琴", teaching_experience="十年", bio="你好", status="pending"
    )
    db.add(application)
    db.commit()

    admin_client = login(admin)
    response = admin_client.post(f"/api/admin/teacher-applications/{application.id}/approve")
    assert response.status_code == 200, response.text

    teacher_client = login(applicant)
    summary = teacher_client.get("/api/support/conversation").json()
    assert summary["unread_count"] == 1
    messages = teacher_client.get("/api/support/messages").json()
    assert len(messages) == 1
    assert "審核通過" in messages[0]["body"] and "使用須知" in messages[0]["body"]
    assert messages[0]["sender_id"] == str(admin.id)
    # 讀過之後未讀歸零
    assert teacher_client.get("/api/support/conversation").json()["unread_count"] == 0


def test_學生註冊成功收到歡迎訊息(make_user, login):
    make_user("admin")
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    email = f"new-{uuid.uuid4().hex[:8]}@aipe04-test.tw"
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": PASSWORD,
            "name": "新同學",
            "phone_number": "0912345678",
            "birthdate": "2000-01-01",
            "sex": "female",
        },
    )
    assert response.status_code == 201, response.text
    assert client.post("/api/auth/login", json={"email": email, "password": PASSWORD}).status_code == 200
    messages = client.get("/api/support/messages").json()
    assert len(messages) == 1
    assert "歡迎加入" in messages[0]["body"]


def test_老師與管理員可以互傳訊息(make_user, login):
    admin = make_user("admin")
    teacher = make_user("teacher", name="陳老師")
    admin_client = login(admin)
    teacher_client = login(teacher)

    sent = teacher_client.post("/api/support/messages", json={"body": "請問怎麼上傳 MIDI？"})
    assert sent.status_code == 200, sent.text

    rows = admin_client.get("/api/admin/support/conversations").json()
    row = next(item for item in rows if item["user_id"] == str(teacher.id))
    assert row["user_name"] == "陳老師" and row["user_role"] == "teacher"
    assert row["unread_count"] == 1

    reply = admin_client.post(f"/api/admin/support/conversations/{row['id']}/messages", json={"body": "到作業頁上傳。"})
    assert reply.status_code == 200
    bodies = [item["body"] for item in teacher_client.get("/api/support/messages").json()]
    assert bodies == ["請問怎麼上傳 MIDI？", "到作業頁上傳。"]


def test_一般使用者看不到別人的對話(make_user, login):
    teacher_client = login(make_user("teacher"))
    assert teacher_client.get("/api/admin/support/conversations").status_code == 403
