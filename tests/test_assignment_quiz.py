"""題庫作業：老師上傳教材請 AI 出題（預覽、重新生成）、存成作業；學生作答、看錯題與解析。"""

import json

import pytest

from backend.services import ai_quiz, llm
from tests.conftest import bind, issue_code, start_conversation

QUESTIONS = [
    {
        "type": "single",
        "difficulty": "easy",
        "topic": "五線譜與譜號",
        "question": "高音譜號的五條線，由下往上排列的音名為何？",
        "options": ["E、G、B、D、F", "F、A、C、E、G", "C、D、E、F、G", "G、B、D、F、A"],
        "answers": [0],
        "hint": "想想高音譜號的線間口訣。",
        "explanation": "線上的音由下往上是 E、G、B、D、F。",
    },
    {
        "type": "multiple",
        "difficulty": "medium",
        "topic": "拍號",
        "question": "下列哪些拍號每小節有三拍？",
        "options": ["3/4", "3/8", "4/4", "2/4"],
        "answers": [0, 1],
        "hint": "看上面的數字。",
        "explanation": "拍號上面的數字代表每小節的拍數。",
    },
    {
        "type": "truefalse",
        "difficulty": "easy",
        "topic": "音符時值",
        "question": "在 4/4 拍中，二分音符佔兩拍。",
        "options": ["正確", "錯誤"],
        "answers": [0],
        "hint": "二分音符是四分音符的幾倍？",
        "explanation": "二分音符的時值是四分音符的兩倍。",
    },
]


@pytest.fixture
def fake_llm(monkeypatch):
    """假的 AI：記下收到的內容，回傳固定題目（另外夾一題格式錯的，應該被剔掉）。"""
    seen = {}

    def reply(system_instruction, content, feature=None, temperature=0.3, timeout_seconds=None):
        seen["content"] = content
        seen["feature"] = feature
        broken = {"type": "single", "question": "壞掉的題目", "options": ["a", "b"], "answers": [5]}
        return "```json\n" + json.dumps({"questions": QUESTIONS + [broken]}, ensure_ascii=False) + "\n```", None

    monkeypatch.setattr(llm, "generate_text_with_reason", reply)
    return seen


@pytest.fixture
def setup(make_user, make_course, login):
    teacher = make_user("teacher", name="許雨天")
    student = make_user("student", name="林克")
    course = make_course(teacher)
    teacher_client = login(teacher)
    student_client = login(student)
    conversation_id = start_conversation(student_client, course)
    code = issue_code(teacher_client, conversation_id).json()["code"]
    assert bind(student_client, conversation_id, code).status_code == 200
    return teacher, student, course, teacher_client, student_client


def generate(client, **extra):
    data = {"count": "10", "types": "single,multiple,truefalse", "difficulty": "mixed"}
    data.update(extra)
    files = {"file": ("基礎樂理.txt", "五線譜與譜號：高音譜號……".encode("utf-8"), "text/plain")}
    return client.post("/teacher/quiz/generate", data=data, files=files)


def create_quiz(teacher_client, course, student, questions=QUESTIONS):
    return teacher_client.post(
        "/teacher/assignments",
        data={
            "course_id": str(course.id),
            "student_id": str(student.id),
            "kind": "quiz",
            "title": "基礎樂理｜單元測驗",
            "questions": json.dumps(questions, ensure_ascii=False),
        },
    )


def test_老師上傳教材AI出題_回傳預覽並剔除格式錯的題目(setup, fake_llm):
    _, _, _, teacher_client, _ = setup
    response = generate(teacher_client)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["source_filename"] == "基礎樂理.txt"
    assert [item["type"] for item in body["questions"]] == ["single", "multiple", "truefalse"]
    assert body["questions"][0]["hint"] == "想想高音譜號的線間口訣。"
    assert "五線譜與譜號" in fake_llm["content"]
    assert "single, multiple, truefalse" in fake_llm["content"]
    assert fake_llm["feature"] == llm.FEATURE_QUIZ_GENERATION


def test_出題設定不合理或檔案不支援會擋下(setup, fake_llm):
    _, _, _, teacher_client, _ = setup
    assert generate(teacher_client, count="0").status_code == 400
    assert generate(teacher_client, count="31").status_code == 400
    assert generate(teacher_client, types="essay").status_code == 400
    assert generate(teacher_client, difficulty="extreme").status_code == 400
    docx = teacher_client.post("/teacher/quiz/generate", files={"file": ("a.docx", b"PK", "application/zip")})
    assert docx.status_code == 400 and "PDF" in docx.json()["detail"]


def test_AI沒有回應時告訴老師原因(setup):
    _, _, _, teacher_client, _ = setup
    response = generate(teacher_client)
    assert response.status_code == 502
    assert "測試中不呼叫 LLM" in response.json()["detail"]


def test_PDF教材可以讀出文字():
    import pymupdf

    document = pymupdf.open()
    document.new_page().insert_text((72, 72), "Treble clef lines: E G B D F")
    text = ai_quiz.extract_text("theory.pdf", document.tobytes())
    assert "Treble clef" in text


def test_學生和其他老師不能叫AI出題(setup, make_user, login, fake_llm):
    _, _, _, _, student_client = setup
    assert generate(student_client).status_code in (401, 403)


def test_存題庫作業_學生看不到答案_老師看得到(setup):
    _, student, course, teacher_client, student_client = setup
    created = create_quiz(teacher_client, course, student)
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["kind"] == "quiz" and body["question_count"] == 3 and body["teacher_name"] == "許雨天"

    student_view = student_client.get(f"/api/student/assignments/{body['id']}/quiz").json()
    assert [item["position"] for item in student_view] == [1, 2, 3]
    assert "answers" not in student_view[0] and "explanation" not in student_view[0]
    assert student_view[0]["hint"] == "想想高音譜號的線間口訣。"
    assert student_view[2]["options"] == ["正確", "錯誤"]

    teacher_view = teacher_client.get(f"/teacher/assignments/{body['id']}/quiz").json()
    assert teacher_view[1]["answers"] == [0, 1]


def test_題庫作業一定要有題目_題目格式錯會說第幾題(setup):
    _, student, course, teacher_client, _ = setup
    assert create_quiz(teacher_client, course, student, questions=[]).status_code == 400
    bad = [QUESTIONS[0], {**QUESTIONS[1], "answers": [0]}]
    response = create_quiz(teacher_client, course, student, questions=bad)
    assert response.status_code == 400 and "第 2 題" in response.json()["detail"]


def test_學生作答_只回傳錯題與解析_可以重複練習(setup):
    _, student, course, teacher_client, student_client = setup
    assignment = create_quiz(teacher_client, course, student).json()
    questions = student_client.get(f"/api/student/assignments/{assignment['id']}/quiz").json()
    ids = [item["id"] for item in questions]
    url = f"/api/student/assignments/{assignment['id']}/quiz/attempts"

    # 第一次：第 1 題對，第 2 題多選只選一個（算錯），第 3 題錯
    first = student_client.post(
        url,
        json={"answers": [{"question_id": ids[0], "selected": [0]}, {"question_id": ids[1], "selected": [0]}, {"question_id": ids[2], "selected": [1]}]},
    )
    assert first.status_code == 201, first.text
    body = first.json()
    assert body["attempt_no"] == 1
    assert [item["position"] for item in body["wrong"]] == [2, 3]
    assert body["wrong"][0]["selected"] == [0] and body["wrong"][0]["answers"] == [0, 1]
    assert body["wrong"][1]["explanation"] == "二分音符的時值是四分音符的兩倍。"
    assert "correct_count" not in body

    second = student_client.post(
        url,
        json={"answers": [{"question_id": ids[0], "selected": [0]}, {"question_id": ids[1], "selected": [1, 0]}, {"question_id": ids[2], "selected": [1]}]},
    ).json()
    assert second["attempt_no"] == 2 and [item["position"] for item in second["wrong"]] == [3]

    history = student_client.get(url).json()
    assert [item["attempt_no"] for item in history] == [1, 2]
    assert [item["attempt_no"] for item in teacher_client.get(f"/teacher/assignments/{assignment['id']}/quiz/attempts").json()] == [1, 2]
    listed = student_client.get("/api/student/assignments").json()[0]
    assert listed["submission_count"] == 2


def test_作答要每題都答_單選不能選兩個(setup):
    _, student, course, teacher_client, student_client = setup
    assignment = create_quiz(teacher_client, course, student).json()
    ids = [item["id"] for item in student_client.get(f"/api/student/assignments/{assignment['id']}/quiz").json()]
    url = f"/api/student/assignments/{assignment['id']}/quiz/attempts"
    missing = student_client.post(url, json={"answers": [{"question_id": ids[0], "selected": [0]}]})
    assert missing.status_code == 400 and "第 2、3 題" in missing.json()["detail"]
    double = student_client.post(
        url,
        json={"answers": [{"question_id": ids[0], "selected": [0, 1]}, {"question_id": ids[1], "selected": [0, 1]}, {"question_id": ids[2], "selected": [0]}]},
    )
    assert double.status_code == 400 and "第 1 題" in double.json()["detail"]


def test_別人拿不到題目與作答(setup, make_user, login):
    _, student, course, teacher_client, _ = setup
    assignment = create_quiz(teacher_client, course, student).json()
    other_student = login(make_user("student"))
    other_teacher = login(make_user("teacher"))
    assert other_student.get(f"/api/student/assignments/{assignment['id']}/quiz").status_code == 404
    assert other_student.post(f"/api/student/assignments/{assignment['id']}/quiz/attempts", json={"answers": []}).status_code == 404
    assert other_teacher.get(f"/teacher/assignments/{assignment['id']}/quiz").status_code == 404
