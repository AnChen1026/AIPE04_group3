from fastapi.testclient import TestClient


def test_cloud_serves_spa_and_prefixed_api(tmp_path):
    from backend.cloud_app import create_app

    (tmp_path / "index.html").write_text("<html>melo</html>")
    app = create_app(tmp_path)
    client = TestClient(app)
    assert client.get("/").text == "<html>melo</html>"
    assert client.head("/").status_code == 200
    assert client.get("/courses").text == "<html>melo</html>"
    assert client.get("/backend/health").json() == {"status": "ok"}
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/backend/does-not-exist").status_code == 404
    assert client.get("/api/not-a-route").status_code == 404
    assert client.get("/missing.js").status_code == 404
    assert client.get("/%2e%2e/.env").status_code == 404


def test_cloud_session_cookie_is_secure_in_deployment(monkeypatch):
    from scripts.validate_cloud_config import validate

    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("STORAGE_BACKEND", "supabase")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://user:secret@db.test/postgres?sslmode=verify-full",
    )
    monkeypatch.setenv("SESSION_SECRET_KEY", "x" * 48)
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "server-test-key")
    monkeypatch.setenv("SESSION_HTTPS_ONLY", "false")
    import pytest

    with pytest.raises(RuntimeError, match="Secure cookies"):
        validate()
    monkeypatch.setenv("SESSION_HTTPS_ONLY", "true")
    validate()


def test_prefixed_websocket_keeps_authentication(tmp_path):
    from backend.cloud_app import create_app

    client = TestClient(create_app(tmp_path))
    with client.websocket_connect(
        "/backend/ws/conversations/00000000-0000-0000-0000-000000000001"
    ) as socket:
        assert socket.receive() == {
            "type": "websocket.close",
            "code": 4401,
            "reason": "",
        }
