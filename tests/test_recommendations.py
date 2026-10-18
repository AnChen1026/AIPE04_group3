"""首頁對話找課的公開行為。"""

from fastapi.testclient import TestClient

from app import app
from backend.models.student import Course
from backend.services.recommendation import parse_criteria


def _course(db, teacher, **values):
    course = Course(
        teacher_id=teacher.id,
        title=values.pop("title", "鋼琴課"),
        status=values.pop("status", "published"),
        **values,
    )
    db.add(course)
    db.commit()
    return course


def test_最多問兩題後只推薦符合的已發布正式課程(db, make_user):
    teacher = make_user("teacher", "王老師")
    matched = _course(
        db,
        teacher,
        title="零基礎線上鋼琴",
        level="入門",
        style="流行鋼琴",
        delivery_mode="online",
        price_per_lesson=1000,
    )
    _course(db, teacher, title="草稿課", status="draft", level="入門", delivery_mode="online")
    _course(db, teacher, title="實體課", level="入門", delivery_mode="in_person")

    client = TestClient(app)
    first = client.post("/api/recommendations", json={"message": "我想學鋼琴"})
    assert first.status_code == 200
    assert first.json()["status"] == "asking"
    assert first.json()["questions_asked"] == 1

    second = client.post(
        f"/api/recommendations/{first.json()['session_id']}/answer",
        json={"message": "完全沒學過"},
    )
    assert second.json()["status"] == "asking"
    assert second.json()["criteria"]["level"] == "入門"
    assert second.json()["questions_asked"] == 2

    final = client.post(
        f"/api/recommendations/{first.json()['session_id']}/answer",
        json={"message": "想要線上上課"},
    )
    body = final.json()
    assert body["status"] == "done"
    assert body["questions_asked"] == 2
    assert [item["course"]["id"] for item in body["results"]] == [str(matched.id)]
    assert body["results"][0]["course"]["teacher_name"] == "王老師"


def test_不確定的回答保持未知且不會問第三題(db, make_user):
    teacher = make_user("teacher")
    _course(db, teacher, level="入門", delivery_mode="online")
    client = TestClient(app)

    started = client.post("/api/recommendations", json={"message": "想學鋼琴"}).json()
    second = client.post(
        f"/api/recommendations/{started['session_id']}/answer", json={"message": "不確定"}
    ).json()
    final = client.post(
        f"/api/recommendations/{started['session_id']}/answer", json={"message": "都可以"}
    ).json()

    assert second["criteria"]["level"] is None
    assert final["criteria"]["delivery_mode"] is None
    assert final["status"] == "done"
    assert final["questions_asked"] == 2


def test_別的瀏覽器不能讀取或回答對談(db):
    owner = TestClient(app)
    stranger = TestClient(app)
    session_id = owner.post("/api/recommendations", json={"message": "想學鋼琴"}).json()["session_id"]

    assert owner.get(f"/api/recommendations/{session_id}").status_code == 200
    assert stranger.get(f"/api/recommendations/{session_id}").status_code == 404
    assert stranger.post(
        f"/api/recommendations/{session_id}/answer", json={"message": "入門"}
    ).status_code == 404


def test_非鋼琴需求會明確說不支援(db):
    response = TestClient(app).post("/api/recommendations", json={"message": "我想學吉他"})
    assert response.status_code == 200
    assert response.json()["status"] == "unsupported"
    assert response.json()["results"] == []


def test_不確定與否定文字不會被誤認為已確認條件():
    assert parse_criteria("程度不確定，但我想線上上課") == {"delivery_mode": "online"}
    assert parse_criteria("不要古典，我想學流行鋼琴") == {"style": "流行"}
    assert "delivery_mode" not in parse_criteria("線上或實體都可以")
