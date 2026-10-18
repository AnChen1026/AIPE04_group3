"""給 Vue 前端用的 JSON API：對話列表、老師讀寫訊息、課務申請、解除綁定。"""

from datetime import timedelta

from tests.conftest import bind, issue_code, next_week, start_conversation


def test_對話列表帶課程_對方姓名_綁定狀態與未讀數(make_user, make_course, login):
    teacher = make_user("teacher", name="林老師")
    student = make_user("student", name="王小明")
    course = make_course(teacher, title="古典鋼琴入門")
    teacher_client = login(teacher)
    student_client = login(student)
    conversation_id = start_conversation(student_client, course)

    student_client.post(f"/api/student/conversations/{conversation_id}/messages", json={"body": "老師好"})
    student_client.post(f"/api/student/conversations/{conversation_id}/messages", json={"body": "想約時間"})

    rows = teacher_client.get("/teacher/conversations").json()
    assert len(rows) == 1
    row = rows[0]
    assert row["student_name"] == "王小明"
    assert row["course_title"] == "古典鋼琴入門"
    assert row["bound"] is False
    assert row["unread_count"] == 2
    assert row["last_message"] == "想約時間"

    messages = teacher_client.get(f"/teacher/conversations/{conversation_id}/messages").json()
    assert [message["body"] for message in messages] == ["老師好", "想約時間"]
    assert teacher_client.get("/teacher/conversations").json()[0]["unread_count"] == 0

    reply = teacher_client.post(
        f"/teacher/conversations/{conversation_id}/messages", json={"body": "你好，週六可以", "client_message_id": "c1"}
    )
    assert reply.status_code == 200
    again = teacher_client.post(
        f"/teacher/conversations/{conversation_id}/messages", json={"body": "你好，週六可以", "client_message_id": "c1"}
    )
    assert again.json()["id"] == reply.json()["id"]

    mine = student_client.get("/api/student/conversations").json()[0]
    assert mine["teacher_name"] == "林老師"
    assert mine["unread_count"] == 1
    assert student_client.get(f"/api/student/conversations/{conversation_id}").json()["course_title"] == "古典鋼琴入門"


def test_老師讀不到別人的對話(make_user, make_course, login):
    owner = make_user("teacher")
    course = make_course(owner)
    student_client = login(make_user("student"))
    conversation_id = start_conversation(student_client, course)

    stranger = login(make_user("teacher"))
    assert stranger.get("/teacher/conversations").json() == []
    assert stranger.get(f"/teacher/conversations/{conversation_id}/messages").status_code == 404
    assert stranger.post(f"/teacher/conversations/{conversation_id}/messages", json={"body": "hi"}).status_code == 404
    assert student_client.get("/teacher/conversations").status_code == 403


def test_老師用JSON處理課務申請(db, make_user, make_course, login, make_lesson):
    teacher = make_user("teacher")
    student = make_user("student", name="陳同學")
    course = make_course(teacher, title="爵士鋼琴")
    teacher_client = login(teacher)
    student_client = login(student)
    conversation_id = start_conversation(student_client, course)
    bind(student_client, conversation_id, issue_code(teacher_client, conversation_id).json()["code"])
    lesson = make_lesson(course, student, next_week(10))

    target = next_week(15)
    created = student_client.post(
        f"/api/student/courses/{course.id}/change-requests",
        params={
            "request_type": "reschedule",
            "session_id": str(lesson.id),
            "proposed_starts_at": target.isoformat(),
            "proposed_ends_at": (target + timedelta(hours=1)).isoformat(),
            "reason": "週一要加班",
        },
    ).json()

    pending = teacher_client.get("/teacher/change-requests").json()
    assert len(pending) == 1
    assert pending[0]["student_name"] == "陳同學"
    assert pending[0]["course_title"] == "爵士鋼琴"
    assert pending[0]["reason"] == "週一要加班"
    assert pending[0]["session_starts_at"] is not None

    stranger = login(make_user("teacher"))
    assert stranger.get("/teacher/change-requests").json() == []
    assert stranger.post(f"/teacher/change-requests/{created['id']}/decision", json={"approve": True}).status_code == 404

    decided = teacher_client.post(f"/teacher/change-requests/{created['id']}/decision", json={"approve": True})
    assert decided.json()["status"] == "approved"
    assert teacher_client.get("/teacher/change-requests").json() == []

    lessons = teacher_client.get("/teacher/lessons").json()
    assert lessons[0]["student_name"] == "陳同學"
    assert lessons[0]["course_title"] == "爵士鋼琴"
    history = student_client.get(f"/api/student/courses/{course.id}/change-requests").json()
    assert history[0]["status"] == "approved"


def test_老師用JSON解除綁定(make_user, make_course, login):
    teacher = make_user("teacher")
    student = make_user("student")
    course = make_course(teacher)
    teacher_client = login(teacher)
    student_client = login(student)
    conversation_id = start_conversation(student_client, course)
    bind(student_client, conversation_id, issue_code(teacher_client, conversation_id).json()["code"])

    students = teacher_client.get("/teacher/students").json()
    assert students[0]["courses"][0]["course_id"] == str(course.id)

    stranger = login(make_user("teacher"))
    assert stranger.post(f"/teacher/courses/{course.id}/students/{student.id}/unbind").status_code == 404

    response = teacher_client.post(f"/teacher/courses/{course.id}/students/{student.id}/unbind")
    assert response.json()["status"] == "unbound"
    assert student_client.get(f"/api/student/courses/{course.id}/schedule").status_code == 403
    assert teacher_client.get("/teacher/students").json() == []
