"""老師設定：修改密碼、修改基本資料時同步老師個人資料的姓名。"""

import uuid

from fastapi.testclient import TestClient

from backend.core.security import verify_password
from backend.main import app
from backend.models.teacher import TeacherDB
from backend.models.user import User
from tests.conftest import FULL_TEACHER_PROFILE, PASSWORD

NEW_PASSWORD = "New-Password-2026"


def login_ok(email: str, password: str) -> int:
    return TestClient(app).post("/api/auth/login", json={"email": email, "password": password}).status_code


def test_修改密碼成功後只能用新密碼登入(db, make_user, login):
    teacher = make_user("teacher")
    client = login(teacher)
    assert client.get("/api/auth/me").json()["has_password"] is True

    response = client.post("/api/auth/me/password", json={"current_password": PASSWORD, "new_password": NEW_PASSWORD})
    assert response.status_code == 200, response.text

    db.expire_all()
    assert verify_password(NEW_PASSWORD, db.get(User, teacher.id).password_hash)
    assert login_ok(teacher.email, PASSWORD) == 401
    assert login_ok(teacher.email, NEW_PASSWORD) == 200


def test_目前密碼錯誤或新舊相同都不能改(db, make_user, login):
    student = make_user("student")
    client = login(student)

    wrong = client.post("/api/auth/me/password", json={"current_password": "wrong", "new_password": NEW_PASSWORD})
    assert wrong.status_code == 400
    assert wrong.json()["detail"] == "目前密碼不正確。"
    missing = client.post("/api/auth/me/password", json={"new_password": NEW_PASSWORD})
    assert missing.status_code == 400
    same = client.post("/api/auth/me/password", json={"current_password": PASSWORD, "new_password": PASSWORD})
    assert same.status_code == 400
    assert same.json()["detail"] == "新密碼不能和目前密碼一樣。"
    short = client.post("/api/auth/me/password", json={"current_password": PASSWORD, "new_password": "1234567"})
    assert short.status_code == 422

    assert login_ok(student.email, PASSWORD) == 200


def test_未登入不能改密碼():
    response = TestClient(app).post("/api/auth/me/password", json={"current_password": PASSWORD, "new_password": NEW_PASSWORD})
    assert response.status_code == 401


def test_只用Google註冊的帳號可以直接設定密碼(db, login):
    from backend.core.security import hash_password

    user = User(
        email=f"google-{uuid.uuid4().hex[:8]}@aipe04-test.tw",
        password_hash=hash_password(PASSWORD),
        auth_provider="google",
        name="Google 老師",
        role="teacher",
        is_active=True,
    )
    db.add(user)
    db.commit()
    client = login(user)
    # 模擬只用 Google、沒有密碼的帳號
    user.password_hash = None
    db.commit()
    assert client.get("/api/auth/me").json()["has_password"] is False

    response = client.post("/api/auth/me/password", json={"new_password": NEW_PASSWORD})
    assert response.status_code == 200, response.text
    assert login_ok(user.email, NEW_PASSWORD) == 200


def test_老師改基本資料的姓名_個人資料與課程頁一起更新(db, make_user, make_course, login):
    teacher = make_user("teacher", name="舊名字")
    client = login(teacher)
    assert client.post("/teacher/profile", json={**FULL_TEACHER_PROFILE, "name": "舊名字"}).status_code == 200
    course = make_course(teacher, title="姓名同步課")

    response = client.patch("/api/auth/me", json={"name": "林新名", "phone_number": "0912345678", "birthdate": "1990-01-01", "sex": "female"})
    assert response.status_code == 200, response.text

    db.expire_all()
    assert db.query(TeacherDB).filter(TeacherDB.user_id == teacher.id).one().name == "林新名"
    assert client.get("/teacher/me").json()["name"] == "林新名"
    public = {row["id"]: row for row in TestClient(app).get("/api/courses").json()}
    assert public[str(course.id)]["teacher_name"] == "林新名"


def test_學生註冊不用填手機生日性別_之後在基本資料選填(make_user):
    client = TestClient(app)
    email = f"new-{uuid.uuid4().hex[:8]}@aipe04-test.tw"
    response = client.post("/api/auth/register", json={"email": email, "password": PASSWORD, "name": "新同學"})
    assert response.status_code == 201, response.text
    assert client.post("/api/auth/login", json={"email": email, "password": PASSWORD}).status_code == 200
    me = client.get("/api/auth/me").json()
    assert (me["phone_number"], me["birthdate"], me["sex"]) == (None, None, None)

    # 學生改姓名時性別可以不填，之後也可以補
    assert client.patch("/api/auth/me", json={"name": "新同學二"}).status_code == 200
    filled = client.patch("/api/auth/me", json={"name": "新同學二", "sex": "male", "phone_number": "0912345678"})
    assert filled.status_code == 200, filled.text
    assert filled.json()["sex"] == "male"


def test_老師改基本資料不能清掉性別(make_user, login):
    client = login(make_user("teacher"))
    assert client.patch("/api/auth/me", json={"name": "林老師"}).status_code == 400
