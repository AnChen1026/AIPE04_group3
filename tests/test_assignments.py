"""老師替已綁定的學生發作業（參考 MIDI、教材、期限），學生下載與錄音繳交。"""

from pathlib import Path

import pytest

from backend.audio_scoring import scorer
from backend.models.student import PracticeRecording
from tests.conftest import bind, issue_code, start_conversation

SAMPLE_MIDI = Path(__file__).resolve().parents[1] / "backend" / "audio_scoring" / "midi_test_data" / "test1.mid"
FAKE_AUDIO = ("practice.wav", b"RIFF-fake-audio", "audio/wav")


@pytest.fixture
def scoring(monkeypatch):
    seen = {}

    def fake_score(midi_path, audio_path):
        seen["midi"] = Path(midi_path)
        return scorer.ScoringResult(pitch_score=80.0, rhythm_score=70.0, feedback_text="很好。")

    monkeypatch.setattr(scorer, "score_recording", fake_score)
    return seen


@pytest.fixture
def setup(make_user, make_course, login):
    teacher = make_user("teacher")
    student = make_user("student", name="王小明")
    course = make_course(teacher)
    teacher_client = login(teacher)
    student_client = login(student)
    conversation_id = start_conversation(student_client, course)
    code = issue_code(teacher_client, conversation_id).json()["code"]
    assert bind(student_client, conversation_id, code).status_code == 200
    return teacher, student, course, teacher_client, student_client


def create(teacher_client, course, student, **extra):
    files = [("midi", ("song.mid", SAMPLE_MIDI.read_bytes(), "audio/midi"))]
    files += [("materials", ("score.pdf", b"%PDF-1.4 fake", "application/pdf"))]
    data = {"course_id": str(course.id), "student_id": str(student.id), "title": "練習給愛麗絲", "due_at": "2026-11-05T23:59:00+08:00"}
    data.update(extra)
    return teacher_client.post("/teacher/assignments", data=data, files=files)


def test_老師發作業附MIDI與教材_學生看得到也能下載(setup):
    _, student, course, teacher_client, student_client = setup
    response = create(teacher_client, course, student)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["title"] == "練習給愛麗絲"
    assert body["has_midi"] is True
    assert [item["filename"] for item in body["materials"]] == ["score.pdf"]
    assert body["due_at"].startswith("2026-11-05")

    mine = student_client.get("/api/student/assignments").json()
    assert [item["id"] for item in mine] == [body["id"]]
    midi = student_client.get(f"/api/student/assignments/{body['id']}/midi")
    assert midi.status_code == 200 and midi.content.startswith(b"MThd")
    material = student_client.get(f"/api/student/assignment-materials/{body['materials'][0]['id']}")
    assert material.status_code == 200 and material.content == b"%PDF-1.4 fake"


def test_同一門課可以有多份作業各自的MIDI(setup):
    _, student, course, teacher_client, _ = setup
    first = create(teacher_client, course, student).json()
    second = create(teacher_client, course, student, title="小步舞曲").json()
    assert first["id"] != second["id"]
    assert len(teacher_client.get("/teacher/assignments").json()) == 2


def test_不能發給沒有綁定的學生(setup, make_user):
    _, _, course, teacher_client, _ = setup
    stranger = make_user("student")
    response = create(teacher_client, course, stranger)
    assert response.status_code == 400
    assert "沒有綁定" in response.json()["detail"]


def test_其他老師與其他學生拿不到作業檔案(setup, make_user, login):
    _, student, course, teacher_client, _ = setup
    body = create(teacher_client, course, student).json()
    other_teacher = login(make_user("teacher"))
    other_student = login(make_user("student"))
    assert other_teacher.get(f"/teacher/assignments/{body['id']}/midi").status_code == 404
    assert other_student.get(f"/api/student/assignments/{body['id']}/midi").status_code == 404
    assert other_student.get(f"/api/student/assignment-materials/{body['materials'][0]['id']}").status_code == 404


def test_繳交作業時用作業的MIDI評分(setup, scoring, db):
    _, student, course, teacher_client, student_client = setup
    body = create(teacher_client, course, student).json()
    response = student_client.post(f"/api/student/assignments/{body['id']}/recordings", files={"audio": FAKE_AUDIO})
    assert response.status_code == 200, response.text
    assert response.json()["assignment_id"] == body["id"]

    recording = db.get(PracticeRecording, response.json()["id"])
    assert recording.reference_midi_path.startswith("uploads/assignments/")
    assert scoring["midi"].as_posix().endswith(recording.reference_midi_path)

    listed = teacher_client.get("/teacher/assignments").json()[0]
    assert listed["submission_count"] == 1
    assert len(student_client.get(f"/api/student/assignments/{body['id']}/recordings").json()) == 1


def test_題庫作業不能附MIDI也不能錄音繳交(setup):
    _, student, course, teacher_client, student_client = setup
    assert create(teacher_client, course, student, kind="quiz").status_code == 400
    quiz = teacher_client.post(
        "/teacher/assignments",
        data={"course_id": str(course.id), "student_id": str(student.id), "title": "樂理練習", "kind": "quiz"},
    )
    assert quiz.status_code == 201, quiz.text
    response = student_client.post(f"/api/student/assignments/{quiz.json()['id']}/recordings", files={"audio": FAKE_AUDIO})
    assert response.status_code == 400


def test_老師刪除作業(setup):
    _, student, course, teacher_client, student_client = setup
    body = create(teacher_client, course, student).json()
    assert teacher_client.delete(f"/teacher/assignments/{body['id']}").status_code == 204
    assert student_client.get("/api/student/assignments").json() == []
