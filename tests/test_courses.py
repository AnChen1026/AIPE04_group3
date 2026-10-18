"""老師管理課程與參考 MIDI（SRS CAT-02、PRA-01、FILE-01）。"""

from pathlib import Path

from tests.conftest import bind, issue_code, start_conversation

SAMPLE_MIDI = Path(__file__).resolve().parents[1] / "backend" / "audio_scoring" / "midi_test_data" / "test1.mid"


def upload_midi(client, course_id, content: bytes, filename: str = "song.mid"):
    return client.post(
        f"/courses/{course_id}/reference-midi",
        files={"midi": (filename, content, "audio/midi")},
    )


def test_老師可以修改草稿並發布(make_user, make_course, login):
    teacher = make_user("teacher")
    course = make_course(teacher, status="draft")
    client = login(teacher)

    response = client.patch(
        f"/courses/{course.id}",
        json={"title": "古典入門", "level": "入門", "delivery_mode": "online", "price_per_lesson": 1200},
    )
    assert response.status_code == 200, response.text
    assert response.json()["title"] == "古典入門"
    assert response.json()["status"] == "draft"
    assert str(course.id) not in {row["id"] for row in client.get("/api/courses").json()}

    assert client.patch(f"/courses/{course.id}", json={"status": "published"}).status_code == 200
    assert str(course.id) in {row["id"] for row in client.get("/api/courses").json()}


def test_課程欄位要符合規格(make_user, make_course, login):
    teacher = make_user("teacher")
    course = make_course(teacher)
    client = login(teacher)

    for body in (
        {"level": "大師"},
        {"delivery_mode": "到府"},
        {"price_per_lesson": -1},
        {"status": "paused"},
        {"title": "   "},
    ):
        assert client.patch(f"/courses/{course.id}", json=body).status_code == 400, body
    assert client.post("/courses", json={"title": "新課", "level": "大師"}).status_code == 400


def test_不能修改別人的課程或上傳別人的MIDI(make_user, make_course, login):
    owner = make_user("teacher")
    course = make_course(owner)
    stranger = login(make_user("teacher"))

    assert stranger.patch(f"/courses/{course.id}", json={"title": "改掉"}).status_code == 403
    assert upload_midi(stranger, course.id, SAMPLE_MIDI.read_bytes()).status_code == 403
    assert stranger.delete(f"/courses/{course.id}").status_code == 403


def test_參考MIDI只收真的MIDI(make_user, make_course, login):
    teacher = make_user("teacher")
    course = make_course(teacher)
    client = login(teacher)

    assert upload_midi(client, course.id, b"not a midi file").status_code == 400
    assert upload_midi(client, course.id, SAMPLE_MIDI.read_bytes(), "song.txt").status_code == 400
    assert upload_midi(client, course.id, b"").status_code == 400

    response = upload_midi(client, course.id, SAMPLE_MIDI.read_bytes())
    assert response.status_code == 200, response.text
    assert response.json()["has_reference_midi"] is True
    assert "reference_midi_path" not in response.json()
    assert client.get(f"/courses/{course.id}/reference-midi").content == SAMPLE_MIDI.read_bytes()


def test_參考MIDI只有綁定學生能下載(make_user, make_course, login):
    teacher = make_user("teacher")
    course = make_course(teacher)
    teacher_client = login(teacher)
    upload_midi(teacher_client, course.id, SAMPLE_MIDI.read_bytes())

    student_client = login(make_user("student"))
    conversation_id = start_conversation(student_client, course)
    assert student_client.get(f"/api/student/courses/{course.id}/reference-midi").status_code == 403

    code = issue_code(teacher_client, conversation_id).json()["code"]
    bind(student_client, conversation_id, code)
    response = student_client.get(f"/api/student/courses/{course.id}/reference-midi")
    assert response.status_code == 200
    assert response.content == SAMPLE_MIDI.read_bytes()
