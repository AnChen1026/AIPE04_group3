"""Storage boundary tests; no external network is used."""

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.core import storage


def test_local_roundtrip_and_range(upload_root):
    value = storage.save_file(upload_root / "uploads/practice/u/song.wav", b"abcdefgh")
    assert value == "uploads/practice/u/song.wav"
    with storage.local_file(value) as path:
        assert path.read_bytes() == b"abcdefgh"
    app = FastAPI()
    app.get("/file")(lambda: storage.file_response(value))
    response = TestClient(app).get("/file", headers={"Range": "bytes=2-4"})
    assert response.status_code == 206
    assert response.content == b"cde"
    assert response.headers["cache-control"] == "no-store"
    storage.delete_file(value)
    assert not (upload_root / value).exists()


@pytest.mark.parametrize(
    "value",
    [
        "../.env",
        "/etc/passwd",
        "https://example.com/a",
        "storage://unknown/a",
        "storage://teaching-files/../a",
        "uploads/../../a",
    ],
)
def test_rejects_untrusted_keys(value):
    with pytest.raises(ValueError), storage.local_file(value):
        pass


def test_supabase_roundtrip_temp_cleanup(monkeypatch, upload_root):
    requests = []

    def handler(request):
        requests.append(request)
        if request.method == "GET":
            return httpx.Response(200, content=b"MThd1234")
        return httpx.Response(200, json={})

    monkeypatch.setenv("STORAGE_BACKEND", "supabase")
    monkeypatch.setenv("SUPABASE_URL", "https://demo.supabase.co")
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "test-server-key")
    monkeypatch.setattr(
        storage,
        "client_factory",
        lambda **kw: httpx.Client(transport=httpx.MockTransport(handler), **kw),
    )
    value = storage.save_file(upload_root / "uploads/midi/u/song.mid", b"MThd1234")
    assert value == "storage://teaching-files/midi/u/song.mid"
    assert requests[0].headers["apikey"] == "test-server-key"
    with storage.local_file(value) as path:
        assert path.read_bytes() == b"MThd1234"
    assert not path.exists()
    storage.delete_file(value)
    assert [r.method for r in requests] == ["POST", "GET", "DELETE"]


def test_remote_missing_is_404(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://demo.supabase.co")
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "test-server-key")
    monkeypatch.setattr(
        storage,
        "client_factory",
        lambda **kw: httpx.Client(
            transport=httpx.MockTransport(lambda r: httpx.Response(404)), **kw
        ),
    )
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as error:
        storage.file_response("storage://teaching-files/midi/missing.mid")
    assert error.value.status_code == 404


def test_remote_download_range_and_temp_removed(monkeypatch):
    paths = []
    original = storage.StoredFileResponse

    def track_file(path, context, **kwargs):
        paths.append(path)
        return original(path, context, **kwargs)

    monkeypatch.setattr(storage, "StoredFileResponse", track_file)
    monkeypatch.setenv("SUPABASE_URL", "https://demo.supabase.co")
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "test-server-key")
    monkeypatch.setattr(
        storage,
        "client_factory",
        lambda **kw: httpx.Client(
            transport=httpx.MockTransport(
                lambda r: httpx.Response(200, content=b"abcdefgh")
            ),
            **kw,
        ),
    )
    app = FastAPI()
    app.get("/file")(
        lambda: storage.file_response("storage://teaching-files/practice/u/song.wav")
    )
    response = TestClient(app).get("/file", headers={"Range": "bytes=2-4"})
    assert response.status_code == 206
    assert response.content == b"cde"
    assert not paths[0].exists()


def test_failed_delete_is_durable(db, monkeypatch):
    from contextlib import contextmanager

    from sqlalchemy import select

    from backend.core import database
    from backend.models.storage_cleanup import StorageCleanup

    @contextmanager
    def session():
        yield db
        db.flush()

    class Factory:
        begin = staticmethod(session)

    monkeypatch.setattr(database, "SessionLocal", Factory)
    monkeypatch.setattr(
        storage, "delete_file", lambda value: (_ for _ in ()).throw(OSError("offline"))
    )
    storage.cleanup_files(["storage://teaching-files/practice/u/song.wav"])
    job = db.scalar(select(StorageCleanup))
    assert job.storage_key == "storage://teaching-files/practice/u/song.wav"


def test_upload_transport_error_is_controlled(monkeypatch, upload_root):
    monkeypatch.setenv("STORAGE_BACKEND", "supabase")
    monkeypatch.setenv("SUPABASE_URL", "https://demo.supabase.co")
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "test-server-key")

    def offline(request):
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(
        storage,
        "client_factory",
        lambda **kw: httpx.Client(transport=httpx.MockTransport(offline), **kw),
    )
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as error:
        storage.save_file(upload_root / "uploads/midi/u/song.mid", b"MThd1234")
    assert error.value.status_code == 503


def test_retry_never_deletes_a_referenced_file(db, make_user, make_course, monkeypatch):
    from contextlib import contextmanager

    from backend.models.storage_cleanup import StorageCleanup
    from scripts import retry_storage_cleanup

    value = "storage://teaching-files/midi/song.mid"
    course = make_course(make_user("teacher"))
    course.reference_midi_path = value
    db.add(StorageCleanup(storage_key=value))
    db.flush()

    @contextmanager
    def shared_session():
        yield db

    called = []
    monkeypatch.setattr(retry_storage_cleanup, "SessionLocal", shared_session)
    monkeypatch.setattr(retry_storage_cleanup, "delete_file", called.append)
    retry_storage_cleanup.main()
    assert called == []
