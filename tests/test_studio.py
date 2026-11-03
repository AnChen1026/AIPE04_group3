"""工作室資料：老師自己填寫，編號由系統產生且建立後不變。"""


def test_老師建立與修改自己的工作室_編號不變(make_user, login):
    teacher_client = login(make_user("teacher"))
    assert teacher_client.get("/teacher/studio").json() is None

    created = teacher_client.put(
        "/teacher/studio",
        json={"name": "晨光鋼琴教室", "owner_name": "林老師", "city": "台北市", "district": "大安區", "intro": "小班教學"},
    )
    assert created.status_code == 200, created.text
    code = created.json()["code"]
    assert code.startswith("ST") and len(code) == 8

    updated = teacher_client.put("/teacher/studio", json={"name": "晨光音樂工作室", "owner_name": "林老師", "code": "HACK"})
    assert updated.status_code == 200
    assert updated.json()["code"] == code
    assert updated.json()["name"] == "晨光音樂工作室"
    assert updated.json()["city"] is None
    assert teacher_client.get("/teacher/studio").json()["name"] == "晨光音樂工作室"


def test_名稱與擁有者必填_老師之間互不影響(make_user, login):
    first = login(make_user("teacher"))
    second = login(make_user("teacher"))
    assert first.put("/teacher/studio", json={"name": " ", "owner_name": "林老師"}).status_code == 400
    assert first.put("/teacher/studio", json={"name": "A 教室", "owner_name": ""}).status_code == 400

    first.put("/teacher/studio", json={"name": "A 教室", "owner_name": "甲"})
    assert second.get("/teacher/studio").json() is None


def test_學生不能用工作室API(make_user, login):
    student_client = login(make_user("student"))
    assert student_client.get("/teacher/studio").status_code == 403
