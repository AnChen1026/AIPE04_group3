"""接洽與綁定碼（SRS INQ-01、BIND-01～03；驗證情境 3、4、5）。"""

from tests.conftest import bind, issue_code, start_conversation


def test_未綁定學生只能聊天_不能用課表與錄音(make_user, make_course, login):
    teacher = make_user("teacher")
    student = make_user("student")
    course = make_course(teacher)
    student_client = login(student)

    conversation_id = start_conversation(student_client, course)
    sent = student_client.post(f"/api/student/conversations/{conversation_id}/messages", json={"body": "想上課"})
    assert sent.status_code == 200

    assert student_client.get(f"/api/student/courses/{course.id}/schedule").status_code == 403
    upload = student_client.post(
        f"/api/student/courses/{course.id}/recordings",
        files={"audio": ("practice.wav", b"RIFF", "audio/wav")},
    )
    assert upload.status_code == 403


def test_草稿與封存課程不能洽詢(make_user, make_course, login):
    teacher = make_user("teacher")
    student_client = login(make_user("student"))
    for status in ("draft", "archived"):
        course = make_course(teacher, status=status)
        response = student_client.post(f"/api/student/courses/{course.id}/conversation")
        assert response.status_code == 404


def test_綁定碼只給這位學生的這門課(make_user, make_course, login):
    teacher = make_user("teacher")
    student = make_user("student")
    other_student = make_user("student")
    course = make_course(teacher)
    other_course = make_course(teacher, title="另一門課")
    teacher_client = login(teacher)
    student_client = login(student)
    other_client = login(other_student)

    conversation_id = start_conversation(student_client, course)
    other_conversation_id = start_conversation(student_client, other_course)
    code = issue_code(teacher_client, conversation_id).json()["code"]

    # 別門課的對話不能用這組碼
    assert bind(student_client, other_conversation_id, code).status_code == 400
    # 別的學生拿不到這段對話
    assert bind(other_client, conversation_id, code).status_code == 404
    # 別的學生在自己的對話裡也不能用
    other_own_conversation = start_conversation(other_client, course)
    assert bind(other_client, other_own_conversation, code).status_code == 400

    assert bind(student_client, conversation_id, code).status_code == 200
    assert student_client.get(f"/api/student/courses/{course.id}/schedule").status_code == 200
    # 另一門課還沒綁定
    assert student_client.get(f"/api/student/courses/{other_course.id}/schedule").status_code == 403


def test_發新碼後舊碼失效(make_user, make_course, login):
    teacher = make_user("teacher")
    student = make_user("student")
    course = make_course(teacher)
    teacher_client = login(teacher)
    student_client = login(student)
    conversation_id = start_conversation(student_client, course)

    old_code = issue_code(teacher_client, conversation_id).json()["code"]
    new_code = issue_code(teacher_client, conversation_id).json()["code"]

    assert bind(student_client, conversation_id, old_code).status_code == 400
    assert bind(student_client, conversation_id, new_code).status_code == 200
    # 綁定後不能再發碼
    assert issue_code(teacher_client, conversation_id).status_code == 400


def test_解除綁定後教學功能關閉_對話保留_舊碼不能再用(make_user, make_course, login):
    teacher = make_user("teacher")
    student = make_user("student")
    course = make_course(teacher)
    other_course = make_course(teacher, title="另一門課")
    teacher_client = login(teacher)
    student_client = login(student)

    conversation_id = start_conversation(student_client, course)
    other_conversation_id = start_conversation(student_client, other_course)
    code = issue_code(teacher_client, conversation_id).json()["code"]
    other_code = issue_code(teacher_client, other_conversation_id).json()["code"]
    assert bind(student_client, conversation_id, code).status_code == 200
    assert bind(student_client, other_conversation_id, other_code).status_code == 200

    unbind = teacher_client.post(f"/teacher/courses/{course.id}/students/{student.id}/unbind")
    assert unbind.status_code == 200
    assert unbind.json()["status"] == "unbound"

    assert student_client.get(f"/api/student/courses/{course.id}/schedule").status_code == 403
    assert student_client.get(f"/api/student/conversations/{conversation_id}/messages").status_code == 200
    assert bind(student_client, conversation_id, code).status_code == 400
    # 另一門課不受影響
    assert student_client.get(f"/api/student/courses/{other_course.id}/schedule").status_code == 200

    # 老師重新發碼後才能再進來
    new_code = issue_code(teacher_client, conversation_id).json()["code"]
    assert bind(student_client, conversation_id, new_code).status_code == 200


def test_課程封存後不能發碼也不能綁定(db, make_user, make_course, login):
    teacher = make_user("teacher")
    student = make_user("student")
    course = make_course(teacher)
    teacher_client = login(teacher)
    student_client = login(student)
    conversation_id = start_conversation(student_client, course)
    code = issue_code(teacher_client, conversation_id).json()["code"]

    course.status = "archived"
    db.commit()

    assert bind(student_client, conversation_id, code).status_code == 400
    assert issue_code(teacher_client, conversation_id).status_code == 400
