"""老師個人資料選填、老師照片與課程圖片、只輸入綁定碼加入課程。"""

from tests.conftest import issue_code, start_conversation

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 64


def test_老師資料只有姓名性別必填(make_user, login):
    client = login(make_user("teacher"))
    saved = client.post("/teacher/profile", json={"name": "林老師", "gender": "女"})
    assert saved.status_code == 200, saved.text
    data = saved.json()
    assert data["name"] == "林老師"
    assert data["teaching_city"] is None
    assert data["age"] is None
    assert "photo_path" not in data

    # 空白字串存成空值
    updated = client.post("/teacher/profile", json={"name": "林老師", "gender": "女", "expertise": "  "}).json()
    assert updated["expertise"] is None
    assert client.post("/teacher/profile", json={"name": "", "gender": "女"}).status_code == 422
    assert client.post("/teacher/profile", json={"name": "林老師"}).status_code == 422


def test_老師照片只收圖片_沒上傳時沒有網址(make_user, login):
    teacher = make_user("teacher")
    client = login(teacher)
    assert client.get("/teacher/me").json()["photo_url"] is None
    assert client.get(f"/api/images/teachers/{teacher.id}").status_code == 404

    bad = client.post("/teacher/photo", files={"photo": ("a.png", b"not image", "image/png")})
    assert bad.status_code == 400
    too_big = client.post("/teacher/photo", files={"photo": ("a.png", PNG + b"0" * (5 * 1024 * 1024), "image/png")})
    assert too_big.status_code == 400

    ok = client.post("/teacher/photo", files={"photo": ("me.png", PNG, "image/png")})
    assert ok.status_code == 200, ok.text
    assert ok.json()["photo_url"] == f"/api/images/teachers/{teacher.id}"
    visitor = client.get(f"/api/images/teachers/{teacher.id}")
    assert visitor.status_code == 200
    assert visitor.content == PNG


def test_課程圖片與介紹_首頁課程帶網址(make_user, make_course, login):
    teacher = make_user("teacher", name="陳老師")
    course = make_course(teacher)
    client = login(teacher)

    client.patch(f"/courses/{course.id}", json={"description": "從手型開始的入門課"})
    uploaded = client.post(f"/courses/{course.id}/image", files={"image": ("c.jpg", JPG, "image/jpeg")})
    assert uploaded.status_code == 200, uploaded.text
    assert uploaded.json()["image_url"] == f"/api/images/courses/{course.id}"
    client.post("/teacher/photo", files={"photo": ("me.png", PNG, "image/png")})

    row = next(item for item in client.get("/api/courses").json() if item["id"] == str(course.id))
    assert row["description"] == "從手型開始的入門課"
    assert row["image_url"] == f"/api/images/courses/{course.id}"
    assert row["teacher_photo_url"] == f"/api/images/teachers/{teacher.id}"
    assert client.get(row["image_url"]).content == JPG

    stranger = login(make_user("teacher"))
    assert stranger.post(f"/courses/{course.id}/image", files={"image": ("c.jpg", JPG, "image/jpeg")}).status_code == 403


def test_沒上傳圖片的課程沒有網址(make_user, make_course, login):
    course = make_course(make_user("teacher"))
    client = login(make_user("student"))
    row = next(item for item in client.get("/api/courses").json() if item["id"] == str(course.id))
    assert row["image_url"] is None
    assert client.get(f"/api/images/courses/{course.id}").status_code == 404


def test_只輸入綁定碼就能加入課程(make_user, make_course, login):
    teacher = make_user("teacher")
    student = make_user("student")
    course = make_course(teacher)
    teacher_client = login(teacher)
    student_client = login(student)
    conversation_id = start_conversation(student_client, course)
    code = issue_code(teacher_client, conversation_id).json()["code"]

    # 老師在對話列表看得到還沒用掉的碼
    row = teacher_client.get(f"/teacher/conversations/{conversation_id}").json()
    assert row["binding_code"] == code
    # 學生自己的列表不帶碼，碼只會出現在老師貼進對話的訊息裡
    assert student_client.get("/api/student/conversations").json()[0]["binding_code"] is None

    other_student = login(make_user("student"))
    assert other_student.post("/api/student/bind", json={"code": code}).status_code == 400

    joined = student_client.post("/api/student/bind", json={"code": code.lower()})
    assert joined.status_code == 200, joined.text
    assert joined.json()["conversation_id"] == conversation_id
    assert student_client.get(f"/api/student/courses/{course.id}/schedule").status_code == 200
    assert teacher_client.get(f"/teacher/conversations/{conversation_id}").json()["binding_code"] is None
    assert student_client.post("/api/student/bind", json={"code": code}).status_code == 400


def test_草稿圖片只有擁有者可讀(make_user, make_course, login):
    from fastapi.testclient import TestClient
    from backend.main import app
    owner = make_user('teacher')
    course = make_course(owner, status='draft')
    client = login(owner)
    assert client.post(f'/courses/{course.id}/image', files={'image': ('c.png', PNG, 'image/png')}).status_code == 200
    url = f'/api/images/courses/{course.id}'
    assert client.get(url).status_code == 200
    assert client.get(url).headers['cache-control'] == 'no-store'
    assert TestClient(app).get(url).status_code == 404
    assert login(make_user('teacher')).get(url).status_code == 404
