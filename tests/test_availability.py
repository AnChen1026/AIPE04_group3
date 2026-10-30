"""可上課時段：老師在課表拖出時段，已綁定的學生點選預約，老師按完成約課才進正式課表。"""

from datetime import timedelta

from backend.models.student import AvailabilitySlot, LessonSession
from tests.conftest import bind, issue_code, next_week, start_conversation


def _bound_student(make_user, make_course, login, teacher=None, course=None):
    teacher = teacher or make_user("teacher")
    course = course or make_course(teacher)
    student = make_user("student")
    teacher_client = login(teacher)
    student_client = login(student)
    conversation_id = start_conversation(student_client, course)
    code = issue_code(teacher_client, conversation_id).json()["code"]
    assert bind(student_client, conversation_id, code).status_code == 200
    return teacher, student, course, teacher_client, student_client


def _add_slot(teacher_client, starts_at, hours=1):
    return teacher_client.post(
        "/teacher/availability",
        json={"starts_at": starts_at.isoformat(), "ends_at": (starts_at + timedelta(hours=hours)).isoformat()},
    )


def _book(student_client, course, slot_id):
    return student_client.post(f"/api/student/courses/{course.id}/availability/{slot_id}/book")


def test_老師新增修改刪除時段(make_user, login):
    teacher_client = login(make_user("teacher"))

    created = _add_slot(teacher_client, next_week(10))
    assert created.status_code == 200, created.text
    slot_id = created.json()["id"]
    assert created.json()["status"] == "open"

    moved = teacher_client.patch(
        f"/teacher/availability/{slot_id}",
        json={"starts_at": next_week(14).isoformat(), "ends_at": next_week(15).isoformat()},
    )
    assert moved.status_code == 200, moved.text

    slots = teacher_client.get("/teacher/availability").json()
    assert [slot["id"] for slot in slots] == [slot_id]
    assert slots[0]["starts_at"] == moved.json()["starts_at"]

    assert teacher_client.delete(f"/teacher/availability/{slot_id}").status_code == 204
    assert teacher_client.get("/teacher/availability").json() == []


def test_時段不能重疊也不能在過去(make_user, login):
    teacher_client = login(make_user("teacher"))
    assert _add_slot(teacher_client, next_week(10), hours=2).status_code == 200

    assert _add_slot(teacher_client, next_week(11)).status_code == 409
    assert _add_slot(teacher_client, next_week(10) - timedelta(days=14)).status_code == 400


def test_未綁定學生看不到也不能預約(make_user, make_course, login):
    teacher = make_user("teacher")
    course = make_course(teacher)
    teacher_client = login(teacher)
    slot_id = _add_slot(teacher_client, next_week(10)).json()["id"]

    stranger = login(make_user("student"))
    start_conversation(stranger, course)  # 只有接洽、還沒綁定
    assert stranger.get(f"/api/student/courses/{course.id}/availability").status_code == 403
    assert _book(stranger, course, slot_id).status_code == 403


def test_已綁定學生預約後等老師完成約課(db, make_user, make_course, login):
    _, student, course, teacher_client, student_client = _bound_student(make_user, make_course, login)
    slot_id = _add_slot(teacher_client, next_week(10)).json()["id"]

    visible = student_client.get(f"/api/student/courses/{course.id}/availability")
    assert visible.status_code == 200
    assert [slot["id"] for slot in visible.json()] == [slot_id]

    booked = _book(student_client, course, slot_id)
    assert booked.status_code == 200, booked.text
    assert booked.json()["request_type"] == "booking"
    assert booked.json()["status"] == "pending"
    # 送出後時段保留給他，別人看不到；正式課表先不變
    assert student_client.get(f"/api/student/courses/{course.id}/availability").json() == []
    assert db.query(LessonSession).filter(LessonSession.student_id == student.id).count() == 0

    decision = teacher_client.post(f"/teacher/change-requests/{booked.json()['id']}/decision", json={"approve": True})
    assert decision.status_code == 200, decision.text

    lesson = db.query(LessonSession).filter(LessonSession.student_id == student.id).one()
    assert lesson.starts_at == next_week(10)
    slot = db.get(AvailabilitySlot, slot_id)
    assert slot.status == "booked"
    assert slot.lesson_id == lesson.id


def test_老師拒絕後時段重新開放(db, make_user, make_course, login):
    _, _, course, teacher_client, student_client = _bound_student(make_user, make_course, login)
    slot_id = _add_slot(teacher_client, next_week(10)).json()["id"]
    request_id = _book(student_client, course, slot_id).json()["id"]

    assert teacher_client.post(f"/teacher/change-requests/{request_id}/decision", json={"approve": False}).status_code == 200
    assert [slot["id"] for slot in student_client.get(f"/api/student/courses/{course.id}/availability").json()] == [slot_id]


def test_同一時段不能被兩位學生預約(make_user, make_course, login):
    teacher, _, course, teacher_client, first_client = _bound_student(make_user, make_course, login)
    *_, second_client = _bound_student(make_user, make_course, login, teacher=teacher, course=course)
    slot_id = _add_slot(teacher_client, next_week(10)).json()["id"]

    assert _book(first_client, course, slot_id).status_code == 200
    second = _book(second_client, course, slot_id)
    assert second.status_code == 409


def test_綁定別門課的學生也看得到同一位老師的時段(make_user, make_course, login):
    teacher = make_user("teacher")
    other_course = make_course(teacher, title="另一門課")
    _, _, course, teacher_client, student_client = _bound_student(make_user, make_course, login, teacher=teacher)
    slot_id = _add_slot(teacher_client, next_week(10)).json()["id"]

    assert [slot["id"] for slot in student_client.get(f"/api/student/courses/{course.id}/availability").json()] == [slot_id]
    # 沒綁定的那門課仍然不行
    assert student_client.get(f"/api/student/courses/{other_course.id}/availability").status_code == 403


def test_老師之間的時段互相隔離(make_user, make_course, login):
    teacher_a_client = login(make_user("teacher"))
    slot_id = _add_slot(teacher_a_client, next_week(10)).json()["id"]

    # 綁定 B 老師的學生，不能透過 B 的課看到或預約 A 的時段
    _, _, course_b, teacher_b_client, student_client = _bound_student(make_user, make_course, login)
    assert student_client.get(f"/api/student/courses/{course_b.id}/availability").json() == []
    assert _book(student_client, course_b, slot_id).status_code == 404

    # B 老師看不到、也不能改 A 的時段
    assert teacher_b_client.get("/teacher/availability").json() == []
    moved = teacher_b_client.patch(
        f"/teacher/availability/{slot_id}",
        json={"starts_at": next_week(14).isoformat(), "ends_at": next_week(15).isoformat()},
    )
    assert moved.status_code == 404
    assert teacher_b_client.delete(f"/teacher/availability/{slot_id}").status_code == 404
    assert teacher_b_client.post(f"/teacher/availability/{slot_id}/release").status_code == 404


def test_老師直接把時段排給已綁定學生(db, make_user, make_course, login):
    _, student, course, teacher_client, _ = _bound_student(make_user, make_course, login)
    slot_id = _add_slot(teacher_client, next_week(10)).json()["id"]

    response = teacher_client.post(
        "/teacher/lessons",
        json={
            "student_id": str(student.id),
            "course_id": str(course.id),
            "starts_at": next_week(10).isoformat(),
            "ends_at": next_week(11).isoformat(),
            "slot_id": slot_id,
        },
    )
    assert response.status_code == 200, response.text
    assert db.get(AvailabilitySlot, slot_id).status == "booked"

    # 取消預約：課堂取消，時段回到可預約
    assert teacher_client.post(f"/teacher/availability/{slot_id}/release").status_code == 200
    assert db.get(LessonSession, response.json()["id"]).status == "cancelled"
    assert db.get(AvailabilitySlot, slot_id).status == "open"


def test_老師不能把課排給沒綁定的學生(make_user, make_course, login):
    teacher = make_user("teacher")
    course = make_course(teacher)
    teacher_client = login(teacher)
    stranger = make_user("student")

    response = teacher_client.post(
        "/teacher/lessons",
        json={
            "student_id": str(stranger.id),
            "course_id": str(course.id),
            "starts_at": next_week(10).isoformat(),
            "ends_at": next_week(11).isoformat(),
        },
    )
    assert response.status_code == 403


def test_取消待確認的預約會退回申請(db, make_user, make_course, login):
    _, _, course, teacher_client, student_client = _bound_student(make_user, make_course, login)
    slot_id = _add_slot(teacher_client, next_week(10)).json()["id"]
    request_id = _book(student_client, course, slot_id).json()["id"]

    assert teacher_client.post(f"/teacher/availability/{slot_id}/release").status_code == 200
    requests = student_client.get(f"/api/student/courses/{course.id}/change-requests").json()
    assert next(item for item in requests if item["id"] == request_id)["status"] == "rejected"
    assert db.get(AvailabilitySlot, slot_id).status == "open"
