"""練習錄音、評分與練習回饋（SRS PRA-01～04、FILE-01；驗證情境 7）。

真正的音訊辨識要跑十幾秒，這裡把評分換成假的，只測狀態、權限與資料流。
"""

from pathlib import Path

import pytest

from backend.audio_scoring import scorer
from tests.conftest import bind, issue_code, start_conversation

SAMPLE_MIDI = Path(__file__).resolve().parents[1] / "backend" / "audio_scoring" / "midi_test_data" / "test1.mid"
FAKE_AUDIO = ("practice.wav", b"RIFF-fake-audio", "audio/wav")


@pytest.fixture
def scoring(monkeypatch):
    """預設回傳固定分數；把 outcome 設成例外就模擬分析失敗。"""
    state = {"outcome": scorer.ScoringResult(pitch_score=61.5, rhythm_score=24.0, feedback_text="第 3 小節漏了兩個音。")}

    def fake_score(midi_path, audio_path):
        assert Path(midi_path).is_file()
        assert Path(audio_path).is_file()
        if isinstance(state["outcome"], Exception):
            raise state["outcome"]
        return state["outcome"]

    monkeypatch.setattr(scorer, "score_recording", fake_score)
    return state


@pytest.fixture
def bound_setup(make_user, make_course, login):
    teacher = make_user("teacher")
    student = make_user("student", name="王小明")
    course = make_course(teacher)
    teacher_client = login(teacher)
    student_client = login(student)
    conversation_id = start_conversation(student_client, course)
    code = issue_code(teacher_client, conversation_id).json()["code"]
    assert bind(student_client, conversation_id, code).status_code == 200
    return teacher, student, course, teacher_client, student_client


def add_midi(teacher_client, course):
    response = teacher_client.post(
        f"/courses/{course.id}/reference-midi",
        files={"midi": ("song.mid", SAMPLE_MIDI.read_bytes(), "audio/midi")},
    )
    assert response.status_code == 200, response.text


def upload(student_client, course):
    return student_client.post(f"/api/student/courses/{course.id}/recordings", files={"audio": FAKE_AUDIO})


def test_沒有參考MIDI時不能送出錄音(bound_setup, scoring):
    _, _, course, _, student_client = bound_setup
    response = upload(student_client, course)
    assert response.status_code == 400
    assert "參考曲" in response.json()["detail"]


def test_送出後背景評分_學生看到這次的音高節奏與文字(bound_setup, scoring):
    _, _, course, teacher_client, student_client = bound_setup
    add_midi(teacher_client, course)

    response = upload(student_client, course)
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "pending"
    recording_id = response.json()["id"]

    detail = student_client.get(f"/api/student/recordings/{recording_id}").json()
    assert detail["status"] == "completed"
    assert detail["feedback"] == {
        "pitch_score": 61.5,
        "rhythm_score": 24.0,
        "feedback_text": "第 3 小節漏了兩個音。",
        "status": "completed",
    }
    listed = student_client.get(f"/api/student/courses/{course.id}/recordings").json()
    assert [row["id"] for row in listed] == [recording_id]
    assert student_client.get(f"/api/student/recordings/{recording_id}/audio").content == FAKE_AUDIO[1]


def test_分析失敗不是0分(bound_setup, scoring):
    _, _, course, teacher_client, student_client = bound_setup
    add_midi(teacher_client, course)
    scoring["outcome"] = scorer.ScoringFailed("這段錄音聽不出彈奏的音。")

    recording_id = upload(student_client, course).json()["id"]
    detail = student_client.get(f"/api/student/recordings/{recording_id}").json()
    assert detail["status"] == "failed"
    assert detail["feedback"]["status"] == "failed"
    assert detail["feedback"]["pitch_score"] is None
    assert detail["feedback"]["rhythm_score"] is None
    assert detail["feedback"]["feedback_text"] == "這段錄音聽不出彈奏的音。"


def test_評分程式出錯也記成失敗(bound_setup, scoring):
    _, _, course, teacher_client, student_client = bound_setup
    add_midi(teacher_client, course)
    scoring["outcome"] = RuntimeError("模型載入失敗")

    recording_id = upload(student_client, course).json()["id"]
    detail = student_client.get(f"/api/student/recordings/{recording_id}").json()
    assert detail["status"] == "failed"
    assert detail["feedback"]["pitch_score"] is None


def test_老師看得到自己課程的錄音與回饋(bound_setup, scoring):
    _, student, course, teacher_client, student_client = bound_setup
    add_midi(teacher_client, course)
    recording_id = upload(student_client, course).json()["id"]

    rows = teacher_client.get(f"/teacher/courses/{course.id}/recordings").json()
    assert len(rows) == 1
    assert rows[0]["id"] == recording_id
    assert rows[0]["student_id"] == str(student.id)
    assert rows[0]["student_name"] == "王小明"
    assert rows[0]["feedback"]["pitch_score"] == 61.5
    assert teacher_client.get(f"/teacher/recordings/{recording_id}/audio").content == FAKE_AUDIO[1]


def test_別的老師與學生看不到這筆錄音(bound_setup, scoring, make_user, login):
    _, _, course, teacher_client, student_client = bound_setup
    add_midi(teacher_client, course)
    recording_id = upload(student_client, course).json()["id"]

    stranger_teacher = login(make_user("teacher"))
    assert stranger_teacher.get(f"/teacher/courses/{course.id}/recordings").status_code == 403
    assert stranger_teacher.get(f"/teacher/recordings/{recording_id}/audio").status_code == 404

    stranger_student = login(make_user("student"))
    assert stranger_student.get(f"/api/student/recordings/{recording_id}").status_code == 404
    assert stranger_student.get(f"/api/student/recordings/{recording_id}/audio").status_code == 404
    assert stranger_student.get(f"/api/student/courses/{course.id}/recordings").status_code == 403


def test_解除綁定後學生不能再送錄音或回聽(bound_setup, scoring):
    teacher, student, course, teacher_client, student_client = bound_setup
    add_midi(teacher_client, course)
    recording_id = upload(student_client, course).json()["id"]

    teacher_client.post(f"/teacher/courses/{course.id}/students/{student.id}/unbind")
    assert upload(student_client, course).status_code == 403
    assert student_client.get(f"/api/student/recordings/{recording_id}/audio").status_code == 403


def test_音檔格式與大小有限制(bound_setup, scoring):
    _, _, course, teacher_client, student_client = bound_setup
    add_midi(teacher_client, course)

    wrong_type = student_client.post(
        f"/api/student/courses/{course.id}/recordings",
        files={"audio": ("notes.txt", b"hello", "text/plain")},
    )
    assert wrong_type.status_code == 400

    too_big = student_client.post(
        f"/api/student/courses/{course.id}/recordings",
        files={"audio": ("big.wav", b"0" * (20 * 1024 * 1024 + 1), "audio/wav")},
    )
    assert too_big.status_code == 400
