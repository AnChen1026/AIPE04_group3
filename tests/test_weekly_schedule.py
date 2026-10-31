"""調課只能選開放時段、15 分鐘單位、老師的每週可上課時間、學生的固定上課時間。"""

from datetime import date, datetime, time, timedelta, timezone

from backend.models.student import AvailabilitySlot, LessonSession, RecurringLesson, WeeklyAvailability
from backend.services.weekly_schedule import HORIZON_DAYS, TAIPEI, extend_teacher_schedule
from tests.conftest import bind, issue_code, next_week, start_conversation

EVENING = (18 * 60, 21 * 60)


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


def _add_slot(teacher_client, starts_at, hours=3):
    response = teacher_client.post(
        "/teacher/availability",
        json={"starts_at": starts_at.isoformat(), "ends_at": (starts_at + timedelta(hours=hours)).isoformat()},
    )
    assert response.status_code == 200, response.text
    return response.json()["id"]


def _reschedule(student_client, course, slot_id, lesson, starts_at):
    return student_client.post(
        f"/api/student/courses/{course.id}/availability/{slot_id}/reschedule",
        json={"session_id": str(lesson.id), "starts_at": starts_at.isoformat()},
    )


def _open_ranges(db, teacher):
    db.expire_all()
    rows = (
        db.query(AvailabilitySlot)
        .filter(AvailabilitySlot.teacher_id == teacher.id, AvailabilitySlot.status == "open")
        .order_by(AvailabilitySlot.starts_at)
        .all()
    )
    return [(row.starts_at, row.ends_at) for row in rows]


def _next_day(weekday: int, weeks: int = 1) -> date:
    today = datetime.now(TAIPEI).date()
    return today + timedelta(days=(weekday - today.weekday()) % 7 + 7 * weeks)


def _taipei(day: date, minute: int) -> datetime:
    return datetime.combine(day, time(0), TAIPEI) + timedelta(minutes=minute)


def _set_weekly(teacher_client, *windows):
    return teacher_client.put(
        "/teacher/availability/weekly",
        json={"windows": [{"weekday": w, "start_minute": s, "end_minute": e} for w, s, e in windows]},
    )


def _add_recurring(teacher_client, student, course, weekday, start, end):
    return teacher_client.post(
        "/teacher/recurring-lessons",
        json={
            "student_id": str(student.id),
            "course_id": str(course.id),
            "weekday": weekday,
            "start_minute": start,
            "end_minute": end,
        },
    )


# ---------- 學生調課、約課只能從開放時段選


def test_學生不能自己填時間調課或約課(make_user, make_course, login, make_lesson):
    _, student, course, _, student_client = _bound_student(make_user, make_course, login)
    lesson = make_lesson(course, student, next_week(10))
    for request_type in ("reschedule", "booking"):
        response = student_client.post(
            f"/api/student/courses/{course.id}/change-requests",
            params={"request_type": request_type, "session_id": str(lesson.id)},
        )
        assert response.status_code == 400
        assert "向老師聯繫" in response.json()["detail"]


def test_請假仍然可以申請(make_user, make_course, login, make_lesson):
    _, student, course, _, student_client = _bound_student(make_user, make_course, login)
    lesson = make_lesson(course, student, next_week(10))
    response = student_client.post(
        f"/api/student/courses/{course.id}/change-requests",
        params={"request_type": "leave", "session_id": str(lesson.id), "reason": "生病"},
    )
    assert response.status_code == 200, response.text


def test_調課沿用原本長度並切開時段_老師同意才改課表(db, make_user, make_course, login, make_lesson):
    teacher, student, course, teacher_client, student_client = _bound_student(make_user, make_course, login)
    original = next_week(9)
    lesson = make_lesson(course, student, original)
    window = next_week(12)
    slot_id = _add_slot(teacher_client, window)

    target = window + timedelta(minutes=75)
    response = _reschedule(student_client, course, slot_id, lesson, target)
    assert response.status_code == 200, response.text
    assert response.json()["proposed_ends_at"] == response.json()["proposed_starts_at"].replace(
        target.strftime("T%H:"), (target + timedelta(hours=1)).strftime("T%H:")
    )
    # 選走的部分保留，前後繼續開放；正式課表先不變
    assert _open_ranges(db, teacher) == [
        (window, target),
        (target + timedelta(hours=1), window + timedelta(hours=3)),
    ]
    db.refresh(lesson)
    assert lesson.starts_at == original

    decision = teacher_client.post(f"/teacher/change-requests/{response.json()['id']}/decision", json={"approve": True})
    assert decision.status_code == 200, decision.text
    db.expire_all()
    assert lesson.starts_at == target
    assert lesson.ends_at == target + timedelta(hours=1)
    assert db.get(AvailabilitySlot, slot_id).status == "booked"
    assert db.get(AvailabilitySlot, slot_id).lesson_id == lesson.id


def test_老師拒絕調課後時段併回一段(db, make_user, make_course, login, make_lesson):
    teacher, student, course, teacher_client, student_client = _bound_student(make_user, make_course, login)
    lesson = make_lesson(course, student, next_week(9))
    window = next_week(12)
    slot_id = _add_slot(teacher_client, window)
    request_id = _reschedule(student_client, course, slot_id, lesson, window + timedelta(minutes=30)).json()["id"]

    assert teacher_client.post(f"/teacher/change-requests/{request_id}/decision", json={"approve": False}).status_code == 200
    assert _open_ranges(db, teacher) == [(window, window + timedelta(hours=3))]


def test_調課成功後原本來自時段的舊時間回到可預約(db, make_user, make_course, login):
    teacher, student, course, teacher_client, student_client = _bound_student(make_user, make_course, login)
    old_start = next_week(9)
    old_slot = _add_slot(teacher_client, old_start, hours=1)
    lesson_id = teacher_client.post(
        "/teacher/lessons",
        json={
            "student_id": str(student.id),
            "course_id": str(course.id),
            "starts_at": old_start.isoformat(),
            "ends_at": (old_start + timedelta(hours=1)).isoformat(),
            "slot_id": old_slot,
        },
    ).json()["id"]
    new_start = next_week(14)
    new_slot = _add_slot(teacher_client, new_start, hours=1)
    lesson = db.get(LessonSession, lesson_id)
    request_id = _reschedule(student_client, course, new_slot, lesson, new_start).json()["id"]

    assert teacher_client.post(f"/teacher/change-requests/{request_id}/decision", json={"approve": True}).status_code == 200
    assert _open_ranges(db, teacher) == [(old_start, old_start + timedelta(hours=1))]


def test_調課不能超出時段也不能重複申請(make_user, make_course, login, make_lesson):
    _, student, course, teacher_client, student_client = _bound_student(make_user, make_course, login)
    lesson = make_lesson(course, student, next_week(9))
    window = next_week(12)
    slot_id = _add_slot(teacher_client, window)

    # 超出時段結尾、不在 15 分鐘格線上
    assert _reschedule(student_client, course, slot_id, lesson, window + timedelta(minutes=135)).status_code == 400
    assert _reschedule(student_client, course, slot_id, lesson, window + timedelta(minutes=10)).status_code == 400

    assert _reschedule(student_client, course, slot_id, lesson, window).status_code == 200
    remaining = student_client.get(f"/api/student/courses/{course.id}/availability").json()
    assert _reschedule(student_client, course, remaining[0]["id"], lesson, window + timedelta(hours=1)).status_code == 409


def test_不能調別人的課(make_user, make_course, login, make_lesson):
    teacher, _, course, teacher_client, student_client = _bound_student(make_user, make_course, login)
    *_, other = _bound_student(make_user, make_course, login, teacher=teacher, course=course)
    someone_else = make_user("student")
    lesson = make_lesson(course, someone_else, next_week(9))
    slot_id = _add_slot(teacher_client, next_week(12))
    assert _reschedule(student_client, course, slot_id, lesson, next_week(12)).status_code == 403


def test_約課可選開始時間與長度(db, make_user, make_course, login):
    teacher, _, course, teacher_client, student_client = _bound_student(make_user, make_course, login)
    window = next_week(12)
    slot_id = _add_slot(teacher_client, window)
    url = f"/api/student/courses/{course.id}/availability/{slot_id}/book"
    target = window + timedelta(minutes=15)

    assert student_client.post(url, json={"starts_at": target.isoformat(), "minutes": 45}).status_code == 400
    response = student_client.post(url, json={"starts_at": target.isoformat(), "minutes": 90, "reason": "想先試上"})
    assert response.status_code == 200, response.text
    assert response.json()["reason"] == "想先試上"
    assert _open_ranges(db, teacher) == [
        (window, target),
        (target + timedelta(minutes=90), window + timedelta(hours=3)),
    ]


# ---------- 15 分鐘單位


def test_時間單位是15分鐘(make_user, login):
    teacher_client = login(make_user("teacher"))
    start = next_week(18)
    ok = {"starts_at": start.isoformat(), "ends_at": (start + timedelta(hours=1)).isoformat()}
    assert teacher_client.post("/teacher/availability", json=ok).status_code == 200

    # 下一堂隔 15 分鐘開始：換地點用
    next_start = start + timedelta(minutes=75)
    good = {"starts_at": next_start.isoformat(), "ends_at": (next_start + timedelta(hours=1)).isoformat()}
    assert teacher_client.post("/teacher/availability", json=good).status_code == 200

    off = start + timedelta(days=1, minutes=10)
    bad = {"starts_at": off.isoformat(), "ends_at": (off + timedelta(hours=1)).isoformat()}
    assert teacher_client.post("/teacher/availability", json=bad).status_code == 400


# ---------- 老師每週可上課時間


def test_每週時間產生往後8週的時段(db, make_user, login):
    teacher = make_user("teacher")
    teacher_client = login(teacher)
    assert _set_weekly(teacher_client, (0, *EVENING)).status_code == 200

    assert [item["weekday"] for item in teacher_client.get("/teacher/availability/weekly").json()] == [0]
    slots = teacher_client.get("/teacher/availability").json()
    assert 8 <= len(slots) <= 9
    for slot in slots:
        start = datetime.fromisoformat(slot["starts_at"]).astimezone(TAIPEI)
        assert start.weekday() == 0
        assert (start.hour, start.minute) == (18, 0)
    last = datetime.fromisoformat(slots[-1]["starts_at"]).astimezone(TAIPEI).date()
    assert last <= datetime.now(TAIPEI).date() + timedelta(days=HORIZON_DAYS)


def test_每週時間單位與重疊檢查(make_user, login):
    teacher_client = login(make_user("teacher"))
    assert _set_weekly(teacher_client, (0, 1085, 1200)).status_code == 400
    assert _set_weekly(teacher_client, (0, 1200, 1080)).status_code == 400
    assert _set_weekly(teacher_client, (7, 1080, 1200)).status_code == 400
    assert _set_weekly(teacher_client, (0, 1080, 1200), (0, 1140, 1260)).status_code == 400


def test_每週時間滾動補上新的一週但不補回刪掉的時段(db, make_user, login):
    teacher = make_user("teacher")
    teacher_client = login(teacher)
    _set_weekly(teacher_client, (2, *EVENING))
    first = teacher_client.get("/teacher/availability").json()[0]
    assert teacher_client.delete(f"/teacher/availability/{first['id']}").status_code == 204
    count = len(teacher_client.get("/teacher/availability").json())

    rule = db.query(WeeklyAvailability).filter_by(teacher_id=teacher.id).one()
    rule.generated_through -= timedelta(days=7)
    db.query(AvailabilitySlot).filter(
        AvailabilitySlot.teacher_id == teacher.id,
        AvailabilitySlot.starts_at > _taipei(rule.generated_through, 0) + timedelta(days=1),
    ).delete()
    db.commit()
    assert len(teacher_client.get("/teacher/availability").json()) == count
    ids = {slot["id"] for slot in teacher_client.get("/teacher/availability").json()}
    assert first["id"] not in ids
    assert not any(
        datetime.fromisoformat(slot["starts_at"]) == datetime.fromisoformat(first["starts_at"])
        for slot in teacher_client.get("/teacher/availability").json()
    )


def test_改每週時間只重算沒人預約的時段(db, make_user, make_course, login):
    teacher, student, course, teacher_client, student_client = _bound_student(make_user, make_course, login)
    _set_weekly(teacher_client, (1, *EVENING))
    slots = teacher_client.get("/teacher/availability").json()
    target = datetime.fromisoformat(slots[1]["starts_at"])
    booked = student_client.post(
        f"/api/student/courses/{course.id}/availability/{slots[1]['id']}/book",
        json={"starts_at": target.isoformat(), "minutes": 60},
    )
    assert booked.status_code == 200, booked.text

    # 手動開的時段不受影響
    manual_day = _next_day(5)
    manual = _add_slot(teacher_client, _taipei(manual_day, 600), hours=1)

    assert _set_weekly(teacher_client, (3, *EVENING)).status_code == 200
    rows = teacher_client.get("/teacher/availability").json()
    held = [row for row in rows if row["status"] == "held"]
    assert [row["id"] for row in held] == [slots[1]["id"]]
    assert any(row["id"] == manual for row in rows)
    weekly_open = [row for row in rows if row["status"] == "open" and row["id"] != manual]
    assert weekly_open
    assert {datetime.fromisoformat(row["starts_at"]).astimezone(TAIPEI).weekday() for row in weekly_open} == {3}

    assert _set_weekly(teacher_client).status_code == 200
    assert {row["id"] for row in teacher_client.get("/teacher/availability").json()} == {slots[1]["id"], manual}


def test_每週時間讓開已排的課(db, make_user, make_course, login, make_lesson):
    teacher, student, course, teacher_client, _ = _bound_student(make_user, make_course, login)
    day = _next_day(0)
    make_lesson(course, student, _taipei(day, 19 * 60))

    _set_weekly(teacher_client, (0, *EVENING))
    assert [row for row in _open_ranges(db, teacher) if row[0].astimezone(TAIPEI).date() == day] == [
        (_taipei(day, 18 * 60), _taipei(day, 19 * 60)),
        (_taipei(day, 20 * 60), _taipei(day, 21 * 60)),
    ]


# ---------- 學生固定上課時間


def test_固定上課時間排出8週的課並占用開放時段(db, make_user, make_course, login):
    teacher, student, course, teacher_client, student_client = _bound_student(make_user, make_course, login)
    _set_weekly(teacher_client, (1, *EVENING))

    response = _add_recurring(teacher_client, student, course, 1, 19 * 60 + 15, 20 * 60 + 15)
    assert response.status_code == 200, response.text
    body = response.json()
    assert 8 <= body["created"] <= 9
    assert body["skipped"] == []

    lessons = student_client.get(f"/api/student/courses/{course.id}/schedule").json()
    assert len(lessons) == body["created"]
    first = datetime.fromisoformat(lessons[0]["starts_at"]).astimezone(TAIPEI)
    assert (first.weekday(), first.hour, first.minute) == (1, 19, 15)

    # 開放時段讓出這段時間，取消那堂後又併回來
    day = first.date()
    assert [row for row in _open_ranges(db, teacher) if row[0].astimezone(TAIPEI).date() == day] == [
        (_taipei(day, 18 * 60), _taipei(day, 19 * 60 + 15)),
        (_taipei(day, 20 * 60 + 15), _taipei(day, 21 * 60)),
    ]
    assert teacher_client.post(f"/teacher/lessons/{lessons[0]['id']}/cancel").status_code == 200
    assert [row for row in _open_ranges(db, teacher) if row[0].astimezone(TAIPEI).date() == day] == [
        (_taipei(day, 18 * 60), _taipei(day, 21 * 60)),
    ]


def test_固定上課時間跳過衝突週並列出(db, make_user, make_course, login, make_lesson):
    teacher, student, course, teacher_client, _ = _bound_student(make_user, make_course, login)
    other = make_user("student")
    day = _next_day(2)
    make_lesson(course, other, _taipei(day, 10 * 60))

    response = _add_recurring(teacher_client, student, course, 2, 10 * 60 + 30, 11 * 60 + 30)
    assert response.status_code == 200, response.text
    skipped = response.json()["skipped"]
    assert len(skipped) == 1
    assert datetime.fromisoformat(skipped[0]["starts_at"]).astimezone(TAIPEI).date() == day
    assert not db.query(LessonSession).filter(
        LessonSession.student_id == student.id, LessonSession.starts_at == _taipei(day, 10 * 60 + 30)
    ).count()


def test_固定上課時間跳過別人待確認的預約(make_user, make_course, login):
    teacher, student, course, teacher_client, _ = _bound_student(make_user, make_course, login)
    *_, other_client = _bound_student(make_user, make_course, login, teacher=teacher, course=course)
    day = _next_day(4)
    slot_id = _add_slot(teacher_client, _taipei(day, 600), hours=1)
    assert other_client.post(f"/api/student/courses/{course.id}/availability/{slot_id}/book").status_code == 200

    response = _add_recurring(teacher_client, student, course, 4, 600, 660)
    assert len(response.json()["skipped"]) == 1
    assert "等老師確認" in response.json()["skipped"][0]["reason"]


def test_固定時間彼此重疊要擋下來(make_user, make_course, login):
    teacher, student, course, teacher_client, _ = _bound_student(make_user, make_course, login)
    other, *_ = _bound_student(make_user, make_course, login, teacher=teacher, course=course)[1:]
    assert _add_recurring(teacher_client, student, course, 3, 600, 660).status_code == 200
    assert _add_recurring(teacher_client, other, course, 3, 630, 690).status_code == 409


def test_固定上課時間要是自己課程的已綁定學生(make_user, make_course, login):
    teacher = make_user("teacher")
    course = make_course(teacher)
    teacher_client = login(teacher)
    stranger = make_user("student")
    assert _add_recurring(teacher_client, stranger, course, 3, 600, 660).status_code == 403

    _, student, other_course, *_ = _bound_student(make_user, make_course, login)
    assert _add_recurring(teacher_client, student, other_course, 3, 600, 660).status_code == 404


def test_別位老師不能改別人的固定時間(make_user, make_course, login):
    _, student, course, teacher_client, _ = _bound_student(make_user, make_course, login)
    rule_id = _add_recurring(teacher_client, student, course, 3, 600, 660).json()["rule"]["id"]
    stranger = login(make_user("teacher"))
    assert stranger.get("/teacher/recurring-lessons").json() == []
    body = {"weekday": 4, "start_minute": 600, "end_minute": 660, "move_lesson_ids": []}
    assert stranger.patch(f"/teacher/recurring-lessons/{rule_id}", json=body).status_code == 404
    assert stranger.post(f"/teacher/recurring-lessons/{rule_id}/stop", json={}).status_code == 404


def test_改固定時間只移動勾選的課(db, make_user, make_course, login):
    _, student, course, teacher_client, _ = _bound_student(make_user, make_course, login)
    rule = _add_recurring(teacher_client, student, course, 3, 600, 660).json()["rule"]
    future = rule["future_lessons"]
    chosen, kept = future[1], future[2]

    response = teacher_client.patch(
        f"/teacher/recurring-lessons/{rule['id']}",
        json={"weekday": 4, "start_minute": 660, "end_minute": 720, "move_lesson_ids": [chosen["id"]]},
    )
    assert response.status_code == 200, response.text
    assert response.json()["created"] == 1

    db.expire_all()
    moved = db.get(LessonSession, chosen["id"]).starts_at.astimezone(TAIPEI)
    assert (moved.weekday(), moved.hour) == (4, 11)
    assert moved.date() - datetime.fromisoformat(chosen["starts_at"]).astimezone(TAIPEI).date() == timedelta(days=1)
    assert db.get(LessonSession, kept["id"]).starts_at == datetime.fromisoformat(kept["starts_at"])


def test_停用固定時間只取消勾選的課_之後不再排課(db, make_user, make_course, login):
    teacher, student, course, teacher_client, _ = _bound_student(make_user, make_course, login)
    rule = _add_recurring(teacher_client, student, course, 3, 600, 660).json()["rule"]
    chosen, kept = rule["future_lessons"][0], rule["future_lessons"][1]

    response = teacher_client.post(f"/teacher/recurring-lessons/{rule['id']}/stop", json={"cancel_lesson_ids": [chosen["id"]]})
    assert response.status_code == 204

    db.expire_all()
    assert db.get(LessonSession, chosen["id"]).status == "cancelled"
    assert db.get(LessonSession, kept["id"]).status == "scheduled"
    assert db.get(LessonSession, kept["id"]).recurring_lesson_id is None
    assert teacher_client.get("/teacher/recurring-lessons").json() == []


def test_解除綁定後不再往後排固定課(db, make_user, make_course, login):
    teacher, student, course, teacher_client, _ = _bound_student(make_user, make_course, login)
    _add_recurring(teacher_client, student, course, 3, 600, 660)
    rule = db.query(RecurringLesson).filter_by(teacher_id=teacher.id).one()
    assert teacher_client.post(f"/teacher/courses/{course.id}/students/{student.id}/unbind").status_code == 200
    count = db.query(LessonSession).filter(LessonSession.student_id == student.id).count()

    rule.generated_through -= timedelta(days=14)
    db.commit()
    extend_teacher_schedule(db, teacher.id)
    assert db.query(LessonSession).filter(LessonSession.student_id == student.id).count() == count


def test_學生請假那一週不會被補回來(db, make_user, make_course, login):
    teacher, student, course, teacher_client, student_client = _bound_student(make_user, make_course, login)
    rule = _add_recurring(teacher_client, student, course, 3, 600, 660).json()["rule"]
    lesson_id = rule["future_lessons"][0]["id"]
    request_id = student_client.post(
        f"/api/student/courses/{course.id}/change-requests",
        params={"request_type": "leave", "session_id": lesson_id},
    ).json()["id"]
    assert teacher_client.post(f"/teacher/change-requests/{request_id}/decision", json={"approve": True}).status_code == 200

    extend_teacher_schedule(db, teacher.id)
    db.expire_all()
    assert db.get(LessonSession, lesson_id).status == "cancelled"
    same_time = db.query(LessonSession).filter(
        LessonSession.student_id == student.id,
        LessonSession.status == "scheduled",
        LessonSession.starts_at == datetime.fromisoformat(rule["future_lessons"][0]["starts_at"]),
    )
    assert same_time.count() == 0
    assert datetime.now(timezone.utc) < datetime.fromisoformat(rule["future_lessons"][0]["starts_at"])
