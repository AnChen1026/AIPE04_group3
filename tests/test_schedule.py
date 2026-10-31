"""課務申請（SRS CHG-01；驗證情境 6）：老師同意且時段空著之前，正式課表不變。"""

from datetime import timedelta

from backend.models.student import LessonSession
from tests.conftest import bind, issue_code, next_week, start_conversation


def _bound_student(make_user, make_course, login):
    teacher = make_user("teacher")
    student = make_user("student")
    course = make_course(teacher)
    teacher_client = login(teacher)
    student_client = login(student)
    conversation_id = start_conversation(student_client, course)
    code = issue_code(teacher_client, conversation_id).json()["code"]
    assert bind(student_client, conversation_id, code).status_code == 200
    return teacher, student, course, teacher_client, student_client


def _request_reschedule(teacher_client, student_client, course, lesson, starts_at):
    """老師開放目標時段，學生再從時段選。"""
    slot = teacher_client.post(
        "/teacher/availability",
        json={"starts_at": starts_at.isoformat(), "ends_at": (starts_at + timedelta(hours=1)).isoformat()},
    )
    assert slot.status_code == 200, slot.text
    response = student_client.post(
        f"/api/student/courses/{course.id}/availability/{slot.json()['id']}/reschedule",
        json={"session_id": str(lesson.id), "starts_at": starts_at.isoformat()},
    )
    assert response.status_code == 200, response.text
    return response.json()["id"]


def test_送出申請後正式課表先不變(db, make_user, make_course, login, make_lesson):
    _, student, course, teacher_client, student_client = _bound_student(make_user, make_course, login)
    original = next_week(10)
    lesson = make_lesson(course, student, original)

    _request_reschedule(teacher_client, student_client, course, lesson, next_week(14))

    db.refresh(lesson)
    assert lesson.starts_at == original


def test_時段被占用時同意也不改課表(db, make_user, make_course, login, make_lesson):
    teacher, student, course, teacher_client, student_client = _bound_student(make_user, make_course, login)
    original = next_week(10)
    lesson = make_lesson(course, student, original)

    request_id = _request_reschedule(teacher_client, student_client, course, lesson, next_week(14))

    # 學生送出後，老師在目標時段又有了別的學生
    other_student = make_user("student")
    make_lesson(course, other_student, next_week(14))

    response = teacher_client.post(f"/teacher/change-requests/{request_id}/decision", json={"approve": True})
    assert response.status_code == 409

    db.refresh(lesson)
    assert lesson.starts_at == original


def test_時段空著時同意才更新課表(db, make_user, make_course, login, make_lesson):
    _, student, course, teacher_client, student_client = _bound_student(make_user, make_course, login)
    lesson = make_lesson(course, student, next_week(10))
    target = next_week(15)

    request_id = _request_reschedule(teacher_client, student_client, course, lesson, target)
    response = teacher_client.post(f"/teacher/change-requests/{request_id}/decision", json={"approve": True})
    assert response.status_code == 200

    db.refresh(lesson)
    assert lesson.starts_at == target


def test_別位老師不能處理這筆申請(db, make_user, make_course, login, make_lesson):
    _, student, course, teacher_client, student_client = _bound_student(make_user, make_course, login)
    lesson = make_lesson(course, student, next_week(10))
    request_id = _request_reschedule(teacher_client, student_client, course, lesson, next_week(16))

    stranger_client = login(make_user("teacher"))
    response = stranger_client.post(f"/teacher/change-requests/{request_id}/decision", json={"approve": True})
    assert response.status_code == 404

    lessons = db.query(LessonSession).filter(LessonSession.id == lesson.id).all()
    assert lessons[0].starts_at == next_week(10)
