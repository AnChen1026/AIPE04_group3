"""課程限時綁定碼：期限內拿到碼的學生都能加入這門課，老師可以重發或停用。"""

from datetime import datetime, timedelta, timezone

from backend.models.student import CourseJoinCode


def _join(client, code):
    return client.post("/api/student/bind", json={"code": code})


def test_限時碼讓多位學生加入_也開好對話(make_user, make_course, login):
    teacher = make_user("teacher")
    course = make_course(teacher)
    teacher_client = login(teacher)

    assert teacher_client.get(f"/teacher/courses/{course.id}/join-code").json() is None
    created = teacher_client.post(f"/teacher/courses/{course.id}/join-code", json={"hours": 24})
    assert created.status_code == 200, created.text
    code = created.json()["code"]
    assert teacher_client.get(f"/teacher/courses/{course.id}/join-code").json()["code"] == code

    for _ in range(2):
        student_client = login(make_user("student"))
        joined = _join(student_client, code.lower())
        assert joined.status_code == 200, joined.text
        assert joined.json()["course_id"] == str(course.id)
        assert joined.json()["conversation_id"]
        assert student_client.get(f"/api/student/courses/{course.id}/schedule").status_code == 200


def test_重發或停用後舊碼不能用(make_user, make_course, login):
    teacher = make_user("teacher")
    course = make_course(teacher)
    teacher_client = login(teacher)
    student_client = login(make_user("student"))

    old = teacher_client.post(f"/teacher/courses/{course.id}/join-code", json={}).json()["code"]
    new = teacher_client.post(f"/teacher/courses/{course.id}/join-code", json={"hours": 1}).json()["code"]
    assert _join(student_client, old).status_code == 400

    assert teacher_client.delete(f"/teacher/courses/{course.id}/join-code").status_code == 200
    assert _join(student_client, new).status_code == 400
    assert teacher_client.get(f"/teacher/courses/{course.id}/join-code").json() is None


def test_過期的碼不能用(db, make_user, make_course, login):
    teacher = make_user("teacher")
    course = make_course(teacher)
    teacher_client = login(teacher)
    code = teacher_client.post(f"/teacher/courses/{course.id}/join-code", json={}).json()["code"]

    join_code = db.query(CourseJoinCode).filter_by(code=code).one()
    join_code.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.commit()

    assert _join(login(make_user("student")), code).status_code == 400
    assert teacher_client.get(f"/teacher/courses/{course.id}/join-code").json() is None


def test_只能管自己的已發布課程_時效只能選固定值(make_user, make_course, login):
    teacher = make_user("teacher")
    other_teacher_client = login(make_user("teacher"))
    course = make_course(teacher)
    draft = make_course(teacher, status="draft")
    teacher_client = login(teacher)

    assert other_teacher_client.post(f"/teacher/courses/{course.id}/join-code", json={}).status_code == 403
    assert teacher_client.post(f"/teacher/courses/{draft.id}/join-code", json={}).status_code == 400
    assert teacher_client.post(f"/teacher/courses/{course.id}/join-code", json={"hours": 5}).status_code == 400
