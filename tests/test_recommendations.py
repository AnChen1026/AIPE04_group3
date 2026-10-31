"""首頁對話找課的公開行為。"""

from fastapi.testclient import TestClient

from backend.main import app
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


def test_找課助理可依本輪需求提出不同追問並支援結果後更正(db, make_user, monkeypatch):
    from backend.services import ai_model_planner

    teacher = make_user('teacher')
    _course(db, teacher, level='入門', delivery_mode='online', price_per_lesson=1000)
    prompts = iter(['你比較想先學哪一首電影配樂？', '你希望從基礎重新開始嗎？', ''])
    def plan(message, previous, previous_question=None):
        return dict(previous), next(prompts, "")
    monkeypatch.setattr(ai_model_planner, 'plan_turn', plan)
    client = TestClient(app)
    first = client.post('/api/recommendations', json={'message': '想學電影配樂'}).json()
    assert first['question'] == '你比較想先學哪一首電影配樂？'
    second = client.post(f"/api/recommendations/{first['session_id']}/answer", json={'message': '星際效應'}).json()
    assert second['question'] == '你希望從基礎重新開始嗎？'
    third = client.post(f"/api/recommendations/{first['session_id']}/answer", json={'message': '入門'}).json()
    assert third['status'] == 'done'
    # Result refinements are user-initiated and do not increase question_count.
    fourth = client.post(f"/api/recommendations/{first['session_id']}/answer", json={'message': '預算1200元以下'}).json()
    assert fourth['criteria']['max_price'] == 1200
    assert fourth['questions_asked'] == 2


def test_模型認為資訊足夠可直接搜尋(db, make_user, monkeypatch):
    from backend.services import ai_model_planner

    teacher = make_user('teacher')
    course = _course(db, teacher, level='入門', delivery_mode='online')
    monkeypatch.setattr(ai_model_planner, 'plan_turn', lambda message, previous, previous_question=None: (dict(previous), ''))
    body = TestClient(app).post('/api/recommendations', json={'message': '我想找鋼琴課'}).json()
    assert body['status'] == 'done'
    assert body['questions_asked'] == 0
    assert str(course.id) in [x['course']['id'] for x in body['results']]


def test_結果後的模型能取消預算且不增加追問(db, make_user, monkeypatch):
    from backend.services import ai_model_planner

    _course(db, make_user('teacher'), price_per_lesson=1000)
    def plan(message, previous, previous_question=None):
        updated = dict(previous)
        if message == '預算不限':
            updated['max_price'] = None
        question = '希望學什麼？' if message == '預算1200元以下' else ('有特定曲子嗎？' if message == '流行' else '')
        return updated, question
    monkeypatch.setattr(ai_model_planner, 'plan_turn', plan)
    client = TestClient(app)
    first = client.post('/api/recommendations', json={'message': '預算1200元以下'}).json()
    second = client.post(f"/api/recommendations/{first['session_id']}/answer", json={'message': '流行'}).json()
    third = client.post(f"/api/recommendations/{first['session_id']}/answer", json={'message': '沒有'}).json()
    assert third['questions_asked'] == 2
    assert third['criteria']['max_price'] == 1200
    result = client.post(f"/api/recommendations/{first['session_id']}/answer", json={'message': '預算不限'}).json()
    assert result['criteria']['max_price'] is None
    assert result['questions_asked'] == third['questions_asked']


def test_模型服務已設定但斷線時不冒充AI回答(db, monkeypatch):
    from backend.services import ai_model_planner

    monkeypatch.setenv('AI_COURSE_GATEWAY_URL', 'https://gateway.example')
    monkeypatch.setattr(ai_model_planner, 'plan_turn', lambda message, previous, previous_question=None: None)
    response = TestClient(app).post('/api/recommendations', json={'message': '我想學鋼琴'})
    assert response.status_code == 503
    assert '暫時' in response.json()['detail']


def test_AI找課匿名請求受到速率限制(db, monkeypatch):
    from backend.services import ai_model_planner
    from backend.services.ai_rate_limit import RateLimiter
    import backend.routers.recommendations as router_module

    monkeypatch.setenv('AI_COURSE_GATEWAY_URL', 'https://gateway.example')
    monkeypatch.setattr(ai_model_planner, 'plan_turn', lambda message, previous, previous_question=None: (dict(previous), ''))
    monkeypatch.setattr(router_module, 'ai_limiter', RateLimiter(per_owner=2, total=20))
    client = TestClient(app)
    assert client.post('/api/recommendations', json={'message': '找鋼琴課'}).status_code == 200
    assert client.post('/api/recommendations', json={'message': '找鋼琴課'}).status_code == 200
    assert client.post('/api/recommendations', json={'message': '找鋼琴課'}).status_code == 429


def test_不明確條件應要求澄清並保留原對話(db, monkeypatch):
    from types import SimpleNamespace
    from backend.services import ai_model_planner

    client = TestClient(app)
    first = client.post('/api/recommendations', json={'message': '想學鋼琴'}).json()
    monkeypatch.setenv('AI_COURSE_GATEWAY_URL', 'https://gateway.example')
    monkeypatch.setenv('AI_COURSE_GATEWAY_TOKEN', 'k' * 48)
    monkeypatch.setattr(ai_model_planner.httpx, 'post', lambda *args, **kwargs: SimpleNamespace(
        raise_for_status=lambda: None,
        json=lambda: {'choices': [{'message': {'content': '{"changes":[{"field":"delivery_mode","value":"online","quote":"線上"}],"question":""}'}}]},
    ))
    response = client.post(f"/api/recommendations/{first['session_id']}/answer", json={'message': '我不喜歡線上上課'})
    assert response.status_code == 422
    assert '確認' in response.json()['detail']
    after = client.get(f"/api/recommendations/{first['session_id']}").json()
    assert after['criteria']['delivery_mode'] is None
    assert after['questions_asked'] == first['questions_asked']


def test_AI回答收到上一個追問以理解使用者回覆(db, monkeypatch):
    from backend.services import ai_model_planner

    seen = []
    def plan(message, previous, previous_question=None):
        seen.append(previous_question)
        return dict(previous), '你希望快一點還是慢一點？' if len(seen) == 1 else ''
    monkeypatch.setattr(ai_model_planner, 'plan_turn', plan)
    client = TestClient(app)
    first = client.post('/api/recommendations', json={'message': '我想找鋼琴課'}).json()
    response = client.post(f"/api/recommendations/{first['session_id']}/answer", json={'message': '慢一點'})
    assert response.status_code == 200
    assert seen == [None, '你希望快一點還是慢一點？']


def test_課程價格更新後不再顯示不符合預算的舊推薦(db, make_user, monkeypatch):
    from backend.services import ai_model_planner

    teacher = make_user('teacher')
    course = _course(db, teacher, price_per_lesson=1000)
    monkeypatch.setattr(ai_model_planner, 'plan_turn', lambda message, previous, previous_question=None: (dict(previous), ''))
    client = TestClient(app)
    first = client.post('/api/recommendations', json={'message': '預算1200元以下'}).json()
    assert str(course.id) in [item['course']['id'] for item in first['results']]
    course.price_per_lesson = 2000
    db.commit()
    result = client.get(f"/api/recommendations/{first['session_id']}").json()
    assert str(course.id) not in [item['course']['id'] for item in result['results']]
    assert '更新' in result['message']


def test_可根據系統提出的明確選項解析前者(db, monkeypatch):
    from backend.services import ai_model_planner

    monkeypatch.setattr(ai_model_planner, 'plan_turn', lambda message, previous, previous_question=None: (dict(previous), '你希望線上還是實體？'))
    client = TestClient(app)
    first = client.post('/api/recommendations', json={'message': '找鋼琴課'}).json()
    second = client.post(f"/api/recommendations/{first['session_id']}/answer", json={'message': '前者'}).json()
    assert second['criteria']['delivery_mode'] == 'online'
    assert second['status'] == 'done'


def test_開始新找課時只清理到期對談(db, monkeypatch):
    from datetime import datetime, timedelta, timezone
    from backend.models.student import RecommendationSession
    from backend.services import ai_model_planner

    now = datetime.now(timezone.utc)
    expired = RecommendationSession(owner_hash='1' * 64, messages=[{'role':'user','content':'old'}], criteria={}, asked_fields=[], question_count=0, status='asking', result_message='', expires_at=now - timedelta(seconds=1))
    active = RecommendationSession(owner_hash='2' * 64, messages=[], criteria={}, asked_fields=[], question_count=0, status='asking', result_message='', expires_at=now + timedelta(hours=1))
    db.add_all([expired, active]);db.commit(); old_id=expired.id; active_id=active.id
    monkeypatch.setattr(ai_model_planner, 'plan_turn', lambda message, previous, previous_question=None: (dict(previous), ''))
    assert TestClient(app).post('/api/recommendations', json={'message':'我想找鋼琴課'}).status_code == 200
    db.expire_all()
    assert db.get(RecommendationSession, old_id) is None
    assert db.get(RecommendationSession, active_id) is not None


def test_明確取消曲風會清除先前語意偏好(db, monkeypatch):
    from backend.services import ai_model_planner
    monkeypatch.setattr(ai_model_planner, 'plan_turn', lambda message, previous, previous_question=None: ({**previous, '_semantic_query': '電影配樂'}, ''))
    client = TestClient(app)
    first = client.post('/api/recommendations', json={'message':'想學電影配樂'}).json()
    assert first['criteria']['learning_goal'] == '電影配樂'
    second = client.post(f"/api/recommendations/{first['session_id']}/answer", json={'message':'取消曲風限制'}).json()
    assert 'learning_goal' not in second['criteria']
    assert second['criteria']['style'] is None
