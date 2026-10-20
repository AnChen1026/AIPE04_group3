"""資料依老師與課程隔離（ADR-0002；SRS 驗證情境 9）與公開課程範圍（CAT-01）。"""

from tests.conftest import bind, issue_code, next_week, start_conversation


def test_老師看不到別位老師的洽詢與學生(make_user, make_course, login, make_lesson):
    teacher_a = make_user("teacher")
    teacher_b = make_user("teacher")
    student = make_user("student")
    course_a = make_course(teacher_a)
    a_client = login(teacher_a)
    b_client = login(teacher_b)
    student_client = login(student)

    conversation_id = start_conversation(student_client, course_a)
    code = issue_code(a_client, conversation_id).json()["code"]
    bind(student_client, conversation_id, code)
    make_lesson(course_a, student, next_week(10))

    assert a_client.get("/teacher/inquiries").json() != []
    assert b_client.get("/teacher/inquiries").json() == []
    assert b_client.get("/teacher/conversations").json() == []
    assert b_client.get("/teacher/students").json() == []
    assert b_client.get("/teacher/lessons").json() == []
    assert b_client.get(f"/courses/{course_a.id}").status_code == 403


def test_老師不能對別人的對話發碼或解除別人課程的綁定(make_user, make_course, login):
    teacher_a = make_user("teacher")
    teacher_b = make_user("teacher")
    student = make_user("student")
    course_a = make_course(teacher_a)
    a_client = login(teacher_a)
    b_client = login(teacher_b)
    student_client = login(student)

    conversation_id = start_conversation(student_client, course_a)
    assert issue_code(b_client, conversation_id).status_code == 404

    code = issue_code(a_client, conversation_id).json()["code"]
    bind(student_client, conversation_id, code)
    unbind = b_client.post(f"/teacher/courses/{course_a.id}/students/{student.id}/unbind")
    assert unbind.status_code == 404
    assert student_client.get(f"/api/student/courses/{course_a.id}/schedule").status_code == 200


def test_學生看不到別人的對話(make_user, make_course, login):
    teacher = make_user("teacher")
    course = make_course(teacher)
    owner_client = login(make_user("student"))
    other_client = login(make_user("student"))

    conversation_id = start_conversation(owner_client, course)
    assert other_client.get(f"/api/student/conversations/{conversation_id}/messages").status_code == 404
    send = other_client.post(f"/api/student/conversations/{conversation_id}/messages", json={"body": "hi"})
    assert send.status_code == 404
    assert other_client.get("/api/student/conversations").json() == []


def test_學生不能呼叫老師的課程管理(make_user, login):
    student_client = login(make_user("student"))
    response = student_client.post("/courses", json={"title": "偷開課", "status": "published"})
    assert response.status_code == 403


def test_刪掉的舊API已經不存在(make_user, login):
    teacher_client = login(make_user("teacher"))
    for method, path in [
        ("post", "/chat"),
        ("post", "/bindings"),
        ("get", "/teacher/submissions"),
        ("get", "/teacher/assignments"),
    ]:
        assert getattr(teacher_client, method)(path).status_code in (404, 405)


def test_公開課程只列已發布_不含MIDI路徑(make_user, make_course, login):
    teacher = make_user("teacher")
    published = make_course(teacher, title="已發布")
    draft = make_course(teacher, status="draft", title="草稿")
    archived = make_course(teacher, status="archived", title="封存")

    client = login(make_user("student"))
    client.cookies.clear()  # 訪客
    rows = client.get("/api/courses").json()
    ids = {row["id"] for row in rows}
    assert str(published.id) in ids
    assert str(draft.id) not in ids
    assert str(archived.id) not in ids
    assert all("reference_midi_path" not in row for row in rows)


def test_教材與測驗只看得到自己的(make_user, login):
    owner = login(make_user("teacher"))
    stranger = login(make_user("teacher"))

    upload = owner.post("/teacher/materials/upload", files={"file": ("scale.pdf", b"%PDF-1.4", "application/pdf")})
    assert upload.status_code == 200, upload.text

    assert [row["filename"] for row in owner.get("/teacher/materials").json()] == ["scale.pdf"]
    assert stranger.get("/teacher/materials").json() == []
    assert stranger.get("/teacher/quizzes").json() == []


def test_首頁推薦端口已實作(db):
    from fastapi.testclient import TestClient

    from backend.main import app

    client = TestClient(app)
    started = client.post("/api/recommendations", json={"message": "想學鋼琴"})
    assert started.status_code == 200
    assert started.json()["status"] == "asking"
    session_id = "00000000-0000-0000-0000-000000000000"
    assert client.post(f"/api/recommendations/{session_id}/answer", json={"message": "沒學過"}).status_code == 404
    assert client.get(f"/api/recommendations/{session_id}").status_code == 404
