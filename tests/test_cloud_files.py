"""Existing file API permissions with an in-memory Supabase REST boundary."""

import json

import httpx
import pytest

from backend.core import storage
from tests.conftest import bind, issue_code, start_conversation
from tests.test_courses import SAMPLE_MIDI


@pytest.fixture
def remote_store(monkeypatch):
    objects = {}

    def handler(request):
        path = request.url.path
        prefix = "/storage/v1/object/"
        tail = path.removeprefix(prefix)
        if request.method == "POST":
            if tail in objects:
                return httpx.Response(409)
            objects[tail] = request.content
            return httpx.Response(200, json={})
        if request.method == "GET":
            tail = tail.removeprefix("authenticated/")
            return (
                httpx.Response(200, content=objects[tail])
                if tail in objects
                else httpx.Response(404)
            )
        if request.method == "DELETE":
            for key in json.loads(request.content)["prefixes"]:
                objects.pop(tail + "/" + key, None)
            return httpx.Response(200, json=[])
        raise AssertionError(request.method)

    monkeypatch.setenv("STORAGE_BACKEND", "supabase")
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "server-test-key")
    monkeypatch.setattr(
        storage,
        "client_factory",
        lambda **kw: httpx.Client(transport=httpx.MockTransport(handler), **kw),
    )
    return objects


def test_private_midi_checks_binding_before_remote_read(
    db, make_user, make_course, login, remote_store
):
    teacher = make_user("teacher")
    course = make_course(teacher)
    owner = login(teacher)
    content = SAMPLE_MIDI.read_bytes()
    response = owner.post(
        f"/courses/{course.id}/reference-midi",
        files={"midi": ("song.mid", content, "audio/midi")},
    )
    assert response.status_code == 200
    assert course.reference_midi_path.startswith("storage://teaching-files/")
    student = login(make_user("student"))
    assert (
        student.get(f"/api/student/courses/{course.id}/reference-midi").status_code
        == 403
    )
    cid = start_conversation(student, course)
    code = issue_code(owner, cid).json()["code"]
    bind(student, cid, code)
    assert (
        student.get(f"/api/student/courses/{course.id}/reference-midi").content
        == content
    )
    stranger = login(make_user("student"))
    assert (
        stranger.get(f"/api/student/courses/{course.id}/reference-midi").status_code
        == 403
    )


def test_remote_upload_is_removed_when_db_commit_fails(
    db, make_user, make_course, remote_store, monkeypatch
):
    from backend.services.course import save_reference_midi

    teacher = make_user("teacher")
    course = make_course(teacher)

    def fail():
        raise RuntimeError("commit failed")

    monkeypatch.setattr(db, "commit", fail)
    with pytest.raises(RuntimeError, match="commit failed"):
        save_reference_midi(
            db, teacher.id, course.id, "song.mid", SAMPLE_MIDI.read_bytes()
        )
    assert remote_store == {}


def test_cloud_assignment_recording_keeps_historical_midi(
    db, make_user, make_course, login, remote_store, monkeypatch
):
    from pathlib import Path

    from backend.audio_scoring import scorer
    from backend.models.student import PracticeRecording
    from tests.test_assignments import FAKE_AUDIO, create

    teacher, student = make_user("teacher"), make_user("student")
    course = make_course(teacher)
    owner, learner = login(teacher), login(student)
    cid = start_conversation(learner, course)
    bind(learner, cid, issue_code(owner, cid).json()["code"])
    body = create(owner, course, student).json()
    seen = []

    def score(midi_path, audio_path, metronome_bpm=None):
        assert Path(midi_path).read_bytes().startswith(b"MThd")
        assert Path(audio_path).read_bytes() == FAKE_AUDIO[1]
        seen.extend([Path(midi_path), Path(audio_path)])
        return scorer.ScoringResult(80, 70, "測試", score_sheet_xml="<score-partwise/>")

    monkeypatch.setattr(scorer, "score_recording", score)
    response = learner.post(
        f"/api/student/assignments/{body['id']}/recordings", files={"audio": FAKE_AUDIO}
    )
    assert response.status_code == 200, response.text
    assert all(not path.exists() for path in seen)
    recording = db.get(PracticeRecording, response.json()["id"])
    from backend.models.student import PracticeFeedback
    feedback = db.query(PracticeFeedback).filter_by(recording_id=recording.id).one()
    assert feedback.score_sheet_path.startswith("storage://teaching-files/")
    sheet_key = feedback.score_sheet_path.removeprefix("storage://")
    assert remote_store[sheet_key] == b"<score-partwise/>"
    for client, endpoint in (
        (learner, f"/api/student/recordings/{recording.id}/score-sheet"),
        (owner, f"/teacher/recordings/{recording.id}/score-sheet"),
    ):
        sheet = client.get(endpoint)
        assert sheet.status_code == 200
        assert sheet.content == b"<score-partwise/>"
        assert sheet.headers["cache-control"] == "no-store"
    before = dict(remote_store)
    stranger = login(make_user("student"))
    assert stranger.get(f"/api/student/recordings/{recording.id}/score-sheet").status_code == 404
    other_teacher = login(make_user("teacher"))
    assert other_teacher.get(f"/teacher/recordings/{recording.id}/score-sheet").status_code == 404
    assert remote_store == before
    midi_key = recording.reference_midi_path.removeprefix("storage://")
    assert midi_key in remote_store
    assert owner.delete(f"/teacher/assignments/{body['id']}").status_code == 204
    assert midi_key in remote_store  # Historical analysis retains its reference.
