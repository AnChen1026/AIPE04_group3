"""課前摘要（SRS PRE-01、PRE-02；驗證情境 8；ADR-0001、ADR-0002）。"""

import json
from datetime import timedelta

import pytest

import backend.services.llm as llm
from backend.models.student import PracticeFeedback, PracticeRecording
from backend.services.lesson_summary import NO_RECORD_TEXT
from tests.conftest import bind, issue_code, next_week, start_conversation


@pytest.fixture
def setup(make_user, make_course, login, make_lesson):
    teacher = make_user("teacher")
    student = make_user("student")
    course = make_course(teacher)
    teacher_client = login(teacher)
    student_client = login(student)
    conversation_id = start_conversation(student_client, course)
    bind(student_client, conversation_id, issue_code(teacher_client, conversation_id).json()["code"])

    # 上一堂下週一 10 點，這一堂兩天後 10 點；中間就是摘要範圍
    previous = make_lesson(course, student, next_week(10))
    target = make_lesson(course, student, next_week(10) + timedelta(days=2))
    return teacher, student, course, teacher_client, student_client, previous, target


@pytest.fixture
def add_recording(db):
    def add(course, student, submitted_at, status="completed", pitch=50.0, rhythm=20.0, midi="uploads/midi/a.mid"):
        recording = PracticeRecording(
            course_id=course.id,
            teacher_id=course.teacher_id,
            student_id=student.id,
            file_path="uploads/practice/x.wav",
            reference_midi_path=midi,
            status=status,
            submitted_at=submitted_at,
        )
        db.add(recording)
        db.flush()
        done = status == "completed"
        db.add(
            PracticeFeedback(
                recording_id=recording.id,
                course_id=course.id,
                teacher_id=course.teacher_id,
                student_id=student.id,
                pitch_score=pitch if done else None,
                rhythm_score=rhythm if done else None,
                feedback_text="節奏偏快" if done else None,
                status="completed" if done else ("failed" if status == "failed" else "pending"),
            )
        )
        db.commit()
        return recording

    return add


def summary(client, lesson):
    response = client.get(f"/teacher/lessons/{lesson.id}/summary")
    assert response.status_code == 200, response.text
    return response.json()


def test_沒有平台紀錄時不說成沒有練習(setup):
    _, _, _, teacher_client, _, _, target = setup
    data = summary(teacher_client, target)
    assert data["stats"]["recording_count"] == 0
    assert data["summary_text"] == NO_RECORD_TEXT
    assert "不代表學生沒有練習" in data["summary_text"]


def test_只算上一堂結束到這一堂開始前的錄音(setup, add_recording, make_course):
    teacher, student, course, teacher_client, _, previous, target = setup
    before = add_recording(course, student, previous.ends_at - timedelta(minutes=5))
    inside = add_recording(course, student, previous.ends_at + timedelta(hours=1))
    after = add_recording(course, student, target.starts_at + timedelta(minutes=5))
    other_course = make_course(teacher, title="別門課")
    elsewhere = add_recording(other_course, student, previous.ends_at + timedelta(hours=2))

    data = summary(teacher_client, target)
    assert data["window_start"].startswith(previous.ends_at.isoformat()[:16])
    assert data["source_recording_ids"] == [str(inside.id)]
    for excluded in (before, after, elsewhere):
        assert str(excluded.id) not in data["source_recording_ids"]


def test_失敗與分析中的錄音不算進平均(setup, add_recording):
    _, student, course, teacher_client, _, previous, target = setup
    start = previous.ends_at
    add_recording(course, student, start + timedelta(hours=1), pitch=60, rhythm=20)
    add_recording(course, student, start + timedelta(hours=2), pitch=40, rhythm=10)
    add_recording(course, student, start + timedelta(hours=3), status="failed")
    add_recording(course, student, start + timedelta(hours=4), status="pending")

    stats = summary(teacher_client, target)["stats"]
    assert stats["recording_count"] == 4
    assert stats["completed_count"] == 2
    assert stats["failed_count"] == 1
    assert stats["waiting_count"] == 1
    assert stats["average_pitch_score"] == 50.0
    assert stats["average_rhythm_score"] == 15.0
    text = summary(teacher_client, target)["summary_text"]
    assert "1 次分析失敗" in text
    assert "1 次還在分析" in text


def test_同一首曲子才比較前後分數(setup, add_recording, make_lesson):
    _, student, course, teacher_client, _, previous, target = setup
    start = previous.ends_at
    add_recording(course, student, start + timedelta(hours=1), pitch=40, rhythm=10)
    add_recording(course, student, start + timedelta(hours=2), pitch=60, rhythm=20)
    data = summary(teacher_client, target)
    assert data["stats"]["comparable"] is True
    assert "多 30.0 分" in data["summary_text"]

    add_recording(course, student, start + timedelta(hours=3), pitch=70, rhythm=30, midi="uploads/midi/b.mid")
    data = summary(teacher_client, target)
    assert data["stats"]["comparable"] is False
    assert "換過參考曲" in data["summary_text"]


def test_來源沒變就沿用_有新練習就重寫(setup, add_recording):
    _, student, course, teacher_client, _, previous, target = setup
    first = summary(teacher_client, target)
    again = summary(teacher_client, target)
    assert again["generated_at"] == first["generated_at"]

    add_recording(course, student, previous.ends_at + timedelta(hours=1))
    updated = summary(teacher_client, target)
    assert updated["stats"]["recording_count"] == 1
    assert updated["generated_at"] != first["generated_at"]


def test_AI只拿到統計資料_沒有檔案路徑(setup, add_recording, monkeypatch):
    _, student, course, teacher_client, _, previous, target = setup
    add_recording(course, student, previous.ends_at + timedelta(hours=1))
    seen = {}

    def fake_llm(system_instruction, content):
        seen["system"] = system_instruction
        seen["content"] = json.loads(content)
        return "這週練了一次，節奏偏快，課堂上可以先確認速度。"

    monkeypatch.setattr(llm, "generate_text", fake_llm)
    data = summary(teacher_client, target)
    assert data["written_by"] == "llm"
    assert data["summary_text"] == "這週練了一次，節奏偏快，課堂上可以先確認速度。"
    assert "不要推論學生的正式程度" in seen["system"]
    assert seen["content"]["recording_count"] == 1
    assert "reference_midi" not in seen["content"]["completed"][0]
    assert "uploads/" not in json.dumps(seen["content"])


def test_別的老師與學生看不到課前摘要(setup, make_user, login):
    _, _, _, _, student_client, _, target = setup
    stranger = login(make_user("teacher"))
    assert stranger.get(f"/teacher/lessons/{target.id}/summary").status_code == 404
    assert student_client.get(f"/teacher/lessons/{target.id}/summary").status_code == 403


def test_解除綁定或課堂取消後不能看(setup, db):
    _, student, course, teacher_client, _, previous, target = setup
    target.status = "cancelled"
    db.commit()
    assert teacher_client.get(f"/teacher/lessons/{target.id}/summary").status_code == 400

    target.status = "scheduled"
    db.commit()
    teacher_client.post(f"/teacher/courses/{course.id}/students/{student.id}/unbind")
    assert teacher_client.get(f"/teacher/lessons/{target.id}/summary").status_code == 403


def test_沒有上一堂時從頭算(make_user, make_course, login, make_lesson, add_recording):
    teacher = make_user("teacher")
    student = make_user("student")
    course = make_course(teacher)
    teacher_client = login(teacher)
    student_client = login(student)
    conversation_id = start_conversation(student_client, course)
    bind(student_client, conversation_id, issue_code(teacher_client, conversation_id).json()["code"])
    first_lesson = make_lesson(course, student, next_week(9))
    early = add_recording(course, student, first_lesson.starts_at - timedelta(days=3))

    data = summary(teacher_client, first_lesson)
    assert data["window_start"] is None
    assert data["source_recording_ids"] == [str(early.id)]
