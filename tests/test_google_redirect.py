"""Google 驗證回來後一律導回 Vue 的頁面，後端不再有模板頁。"""

from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient

from backend.main import app
from backend.routers import auth as auth_router


def test_驗證失敗時回Vue登入頁並帶錯誤訊息(db):
    client = TestClient(app, follow_redirects=False)
    response = client.get("/auth/google/callback", params={"code": "x", "state": "不對的 state"})

    assert response.status_code == 303
    location = urlparse(response.headers["location"])
    assert location.path == "/login"
    assert parse_qs(location.query)["error"] == ["Google 驗證失敗，請再試一次。"]


def test_驗證成功後依角色回Vue後台_老師沒申請資料也先進老師後台(db, make_user, monkeypatch):
    teacher = make_user("teacher")
    monkeypatch.setattr(auth_router, "get_google_settings", lambda: {"client_id": "x"})
    monkeypatch.setattr(auth_router, "build_google_auth_url", lambda state: f"https://google.test/?state={state}")
    monkeypatch.setattr(
        auth_router,
        "fetch_google_profile",
        lambda code: {"google_id": "g-1", "email": teacher.email, "name": teacher.name},
    )
    monkeypatch.setattr(auth_router, "login_or_register_google_user", lambda db, *args, **kwargs: teacher)
    monkeypatch.setenv("FRONTEND_URL", "https://piano.example/")

    client = TestClient(app, follow_redirects=False)
    google_url = client.get("/api/auth/google-url", params={"role": "teacher", "intent": "login"}).json()["url"]
    state = parse_qs(urlparse(google_url).query)["state"][0]
    response = client.get("/auth/google/callback", params={"code": "ok", "state": state})

    assert response.status_code == 303
    assert response.headers["location"] == "https://piano.example/teacher"
    assert client.get("/api/auth/me").json()["email"] == teacher.email


def test_模板頁與表單路由都已移除(db):
    client = TestClient(app, follow_redirects=False)
    for path in ("/", "/login", "/register", "/profile", "/teacher", "/student", "/admin", "/test", "/teacher/learning"):
        assert client.get(path).status_code == 404, path
    assert client.get("/health").json() == {"status": "ok", "database": "ok"}
