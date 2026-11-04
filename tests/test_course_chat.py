import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.student import Course
from backend.services import course_chat


@pytest.fixture
def fake_model(monkeypatch):
    """記下交給模型的內容，回覆由測試指定。語意排序維持原順序，不連閘道。"""
    calls = []
    state = {"reply": "可以看看這門課。"}

    def generate(system_instruction, content, *args, **kwargs):
        calls.append({"system": system_instruction, "content": content, "feature": kwargs.get("feature")})
        return state["reply"], None

    monkeypatch.setattr(course_chat.llm, "generate_text_with_reason", generate)
    monkeypatch.setattr(course_chat, "rank_public_courses_with_status", lambda db, rows, query: (list(rows), "ready"))
    return calls, state


def add_course(db, teacher, title, **fields):
    course = Course(teacher_id=teacher.id, title=title, status=fields.pop("status", "published"), **fields)
    db.add(course)
    db.commit()
    return course


def ask(*texts):
    messages = []
    for index, text in enumerate(texts):
        messages.append({"role": "user" if index % 2 == 0 else "assistant", "content": text})
    return TestClient(app).post("/api/course-chat", json={"messages": messages})


def test_reply_attaches_cards_for_courses_it_names(db, make_user, fake_model):
    calls, state = fake_model
    teacher = make_user("teacher", "測試老師")
    course = add_course(db, teacher, "聊天測試流行鋼琴", style="流行", price_per_lesson=900)
    draft = add_course(db, teacher, "聊天測試草稿課", status="draft")
    state["reply"] = "推薦你「聊天測試流行鋼琴」，一堂 NT$ 500。"

    response = ask("我想學流行鋼琴")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["reply"] == state["reply"]
    # 卡片的價格來自資料庫，不是模型寫的 500
    assert [(card["id"], card["price_per_lesson"]) for card in body["courses"]] == [(str(course.id), 900)]
    assert course.title in calls[0]["system"]
    assert draft.title not in calls[0]["system"]
    assert calls[0]["feature"] == course_chat.FEATURE_COURSE_CHAT


def test_whole_conversation_goes_to_model(db, make_user, fake_model):
    calls, _state = fake_model

    response = ask("我想學鋼琴", "你的程度如何？", "完全沒學過")

    assert response.status_code == 200, response.text
    assert "學生：我想學鋼琴\n顧問：你的程度如何？\n學生：完全沒學過" in calls[0]["content"]


def test_conditions_the_student_said_come_first(db, make_user, fake_model):
    calls, _state = fake_model
    teacher = make_user("teacher")
    cheap = add_course(db, teacher, "聊天測試台中便宜課", region="台中市西屯區", price_per_lesson=800, delivery_mode="線上")
    add_course(db, teacher, "聊天測試台北課", region="台北市大安區", price_per_lesson=800, delivery_mode="線上")

    ask("想找台中的課", "好的", "一堂 1000 元以內，線上")

    listed = calls[0]["system"].split("可以推薦的課程：")[1]
    # 資料庫裡可能還有別的台中課，台北的課就算有列出也要排在後面
    assert cheap.title in listed
    assert "聊天測試台北課" not in listed or listed.index(cheap.title) < listed.index("聊天測試台北課")


def test_same_title_needs_teacher_name_for_a_card(db, make_user, fake_model):
    _calls, state = fake_model
    first = make_user("teacher", "甲老師")
    second = make_user("teacher", "乙老師")
    add_course(db, first, "聊天測試同名課")
    picked = add_course(db, second, "聊天測試同名課")

    state["reply"] = "很多老師都有開聊天測試同名課。"
    assert ask("推薦一下").json()["courses"] == []

    state["reply"] = "推薦乙老師的聊天測試同名課。"
    assert [card["id"] for card in ask("推薦一下").json()["courses"]] == [str(picked.id)]


def test_model_failure_is_503(db, monkeypatch):
    monkeypatch.setattr(course_chat.llm, "generate_text_with_reason", lambda *args, **kwargs: (None, "閘道沒開"))

    response = ask("我想學鋼琴")

    assert response.status_code == 503
    assert "暫時沒有回應" in response.json()["detail"]


def test_last_message_must_be_from_student(db, fake_model):
    response = TestClient(app).post(
        "/api/course-chat",
        json={"messages": [{"role": "user", "content": "嗨"}, {"role": "assistant", "content": "你好"}]},
    )

    assert response.status_code == 422
