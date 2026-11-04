"""作業的規則：老師替已綁定的學生發作業、附參考 MIDI 與教材；學生只看得到發給自己的作業。

檔案放在 uploads/assignments/<老師 id>/，資料表只記相對路徑。
"""

import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path

from fastapi import status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.core.uploads import ASSIGNMENT_UPLOAD_DIR
from backend.core.storage import save_file, cleanup_files
from backend.models.assignment import Assignment, AssignmentMaterial, AssignmentQuizQuestion, QuizAttempt, QuizAttemptAnswer
from backend.models.student import Course, CourseBinding, PracticeRecording
from backend.models.user import User
from backend.services.ai_quiz import MAX_QUESTIONS, clean_question, grade
from backend.services.course import MAX_MIDI_BYTES, MIDI_SUFFIXES
from backend.services.student import StudentBusinessError, _commit, require_bound

KINDS = ("performance", "quiz")
MAX_MATERIAL_BYTES = 30 * 1024 * 1024
MAX_MATERIALS = 10
# 節拍器與練習速度的範圍
MIN_BPM = 30
MAX_BPM = 240


def _clean_filename(filename: str, fallback: str) -> str:
    return filename.replace("\\", "/").rsplit("/", 1)[-1][-255:] or fallback


def _write(teacher_id: uuid.UUID, suffix: str, content: bytes) -> str:
    folder = ASSIGNMENT_UPLOAD_DIR / str(teacher_id)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{uuid.uuid4()}{suffix}"
    return save_file(path, content)


def _midi_bpm(content: bytes) -> float | None:
    """參考 MIDI 開頭的速度。讀不到時回傳 None，前端就用 120。"""
    try:
        import pretty_midi

        _, tempos = pretty_midi.PrettyMIDI(BytesIO(content)).get_tempo_changes()
        return round(float(tempos[0]), 1) if len(tempos) else None
    except Exception:
        return None


def _check_midi(filename: str, content: bytes) -> None:
    if not filename.lower().endswith(MIDI_SUFFIXES):
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "參考 MIDI 請上傳 .mid 或 .midi 檔。")
    if len(content) == 0 or not content.startswith(b"MThd"):
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "這不是有效的 MIDI 檔。")
    if len(content) > MAX_MIDI_BYTES:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "參考 MIDI 最大 2 MB。")


def create_assignment(
    db: Session,
    teacher_id: uuid.UUID,
    course_id: uuid.UUID,
    student_id: uuid.UUID,
    kind: str,
    title: str,
    description: str | None,
    due_at: datetime | None,
    midi: tuple[str, bytes] | None,
    materials: list[tuple[str, str | None, bytes]],
    practice_bpm: int | None = None,
    questions: list[dict] | None = None,
) -> Assignment:
    """materials 是 (檔名, content type, 內容)。只能發給目前綁定在這門課的學生。
    題庫作業要帶 questions（老師在 AI 出題預覽後確認的題目），格式同 services/ai_quiz.clean_question。"""
    course = db.get(Course, course_id)
    if course is None or course.teacher_id != teacher_id:
        raise StudentBusinessError(status.HTTP_404_NOT_FOUND, "找不到這門課。")
    bound = db.scalar(
        select(CourseBinding).where(
            CourseBinding.course_id == course_id,
            CourseBinding.student_id == student_id,
            CourseBinding.status == "bound",
        )
    )
    if bound is None:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "這位學生沒有綁定這門課。")
    if kind not in KINDS:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "作業類型不正確。")
    text = title.strip()
    if not text:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "請填寫作業內容。")
    if len(text) > 200:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "作業內容最多 200 字，詳細說明請寫在備註。")
    if kind == "quiz" and midi is not None:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "題庫作業不用上傳參考 MIDI。")
    if len(materials) > MAX_MATERIALS:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, f"一份作業最多 {MAX_MATERIALS} 個教材檔。")
    for name, _, content in materials:
        if len(content) == 0:
            raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, f"「{name}」是空的檔案。")
        if len(content) > MAX_MATERIAL_BYTES:
            raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, f"「{name}」超過 30 MB。")
    if midi is not None:
        _check_midi(*midi)
    cleaned_questions: list[dict] = []
    if kind == "quiz":
        cleaned = [clean_question(item) for item in questions or []]
        if not cleaned:
            raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "題庫作業至少要有一題，請先用 AI 生成題目。")
        if len(cleaned) > MAX_QUESTIONS:
            raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, f"一份題庫作業最多 {MAX_QUESTIONS} 題。")
        bad = [str(index + 1) for index, item in enumerate(cleaned) if item is None]
        if bad:
            raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, f"第 {'、'.join(bad)} 題的格式不正確（選項或答案有問題）。")
        cleaned_questions = [item for item in cleaned if item is not None]
    elif questions:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "演奏作業不用題目。")
    if practice_bpm is not None and not MIN_BPM <= practice_bpm <= MAX_BPM:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, f"練習速度請填 {MIN_BPM}～{MAX_BPM} BPM。")

    written: list[str] = []
    try:
        assignment = Assignment(
            id=uuid.uuid4(),
            teacher_id=teacher_id,
            course_id=course_id,
            student_id=student_id,
            kind=kind,
            title=text,
            description=(description or "").strip() or None,
            due_at=due_at,
            practice_bpm=practice_bpm if kind == "performance" else None,
        )
        if midi is not None:
            path = _write(teacher_id, ".mid", midi[1])
            written.append(path)
            assignment.midi_path = path
            assignment.midi_filename = _clean_filename(midi[0], "reference.mid")
            assignment.midi_bpm = _midi_bpm(midi[1])
        db.add(assignment)
        db.flush()
        for position, item in enumerate(cleaned_questions, start=1):
            db.add(
                AssignmentQuizQuestion(
                    assignment_id=assignment.id,
                    position=position,
                    question_type=item["type"],
                    difficulty=item["difficulty"],
                    topic=item["topic"],
                    question=item["question"],
                    options=item["options"],
                    answers=item["answers"],
                    explanation=item["explanation"],
                    hint=item["hint"],
                )
            )
        for name, content_type, content in materials:
            path = _write(teacher_id, Path(name).suffix.lower()[:16], content)
            written.append(path)
            db.add(
                AssignmentMaterial(
                    assignment_id=assignment.id,
                    filename=_clean_filename(name, "material"),
                    content_type=(content_type or None) and content_type[:255],
                    file_path=path,
                    file_size_bytes=len(content),
                )
            )
        _commit(db)
    except Exception:
        db.rollback()
        cleanup_files(written)
        raise
    db.refresh(assignment)
    return assignment


def delete_assignment(db: Session, teacher_id: uuid.UUID, assignment_id: uuid.UUID) -> None:
    """刪除作業與教材檔。已繳交的錄音保留，只是不再指到這份作業。"""
    assignment = own_assignment(db, teacher_id, assignment_id)
    paths = [assignment.midi_path] + [item.file_path for item in materials_of(db, [assignment.id])[assignment.id]]
    db.delete(assignment)
    _commit(db)
    from backend.services.storage_files import is_file_referenced
    cleanup_files([value for value in paths if value and not is_file_referenced(db, value)])


def own_assignment(db: Session, teacher_id: uuid.UUID, assignment_id: uuid.UUID) -> Assignment:
    assignment = db.get(Assignment, assignment_id)
    if assignment is None or assignment.teacher_id != teacher_id:
        raise StudentBusinessError(status.HTTP_404_NOT_FOUND, "找不到這份作業。")
    return assignment


def student_assignment(db: Session, student_id: uuid.UUID, assignment_id: uuid.UUID) -> Assignment:
    """學生自己的作業，而且這門課還綁定著。"""
    assignment = db.get(Assignment, assignment_id)
    if assignment is None or assignment.student_id != student_id:
        raise StudentBusinessError(status.HTTP_404_NOT_FOUND, "找不到這份作業。")
    require_bound(db, student_id, assignment.course_id)
    return assignment


def material_for_teacher(db: Session, teacher_id: uuid.UUID, material_id: uuid.UUID) -> AssignmentMaterial:
    material = db.get(AssignmentMaterial, material_id)
    if material is None:
        raise StudentBusinessError(status.HTTP_404_NOT_FOUND, "找不到這份教材。")
    own_assignment(db, teacher_id, material.assignment_id)
    return material


def material_for_student(db: Session, student_id: uuid.UUID, material_id: uuid.UUID) -> AssignmentMaterial:
    material = db.get(AssignmentMaterial, material_id)
    if material is None:
        raise StudentBusinessError(status.HTTP_404_NOT_FOUND, "找不到這份教材。")
    student_assignment(db, student_id, material.assignment_id)
    return material


def materials_of(db: Session, assignment_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[AssignmentMaterial]]:
    result: dict[uuid.UUID, list[AssignmentMaterial]] = {item: [] for item in assignment_ids}
    if not assignment_ids:
        return result
    for material in db.scalars(
        select(AssignmentMaterial)
        .where(AssignmentMaterial.assignment_id.in_(assignment_ids))
        .order_by(AssignmentMaterial.created_at.asc())
    ):
        result[material.assignment_id].append(material)
    return result


def assignment_rows(db: Session, assignments: list[Assignment]) -> list[dict]:
    """列表用：加上課程名稱、學生姓名、教材與繳交次數。"""
    ids = [item.id for item in assignments]
    materials = materials_of(db, ids)
    courses = dict(
        db.execute(select(Course.id, Course.title).where(Course.id.in_({item.course_id for item in assignments}))).all()
    ) if assignments else {}
    people = {item.student_id for item in assignments} | {item.teacher_id for item in assignments}
    names = dict(db.execute(select(User.id, User.name).where(User.id.in_(people))).all()) if assignments else {}
    stats = {
        row.assignment_id: row
        for row in db.execute(
            select(
                PracticeRecording.assignment_id,
                func.count().label("count"),
                func.max(PracticeRecording.submitted_at).label("latest"),
            )
            .where(PracticeRecording.assignment_id.in_(ids))
            .group_by(PracticeRecording.assignment_id)
        )
    } if ids else {}
    quiz_stats = {
        row.assignment_id: row
        for row in db.execute(
            select(
                QuizAttempt.assignment_id,
                func.count().label("count"),
                func.max(QuizAttempt.submitted_at).label("latest"),
            )
            .where(QuizAttempt.assignment_id.in_(ids))
            .group_by(QuizAttempt.assignment_id)
        )
    } if ids else {}
    question_counts = dict(
        db.execute(
            select(AssignmentQuizQuestion.assignment_id, func.count())
            .where(AssignmentQuizQuestion.assignment_id.in_(ids))
            .group_by(AssignmentQuizQuestion.assignment_id)
        ).all()
    ) if ids else {}
    rows = []
    for item in assignments:
        # 演奏作業算錄音次數，題庫作業算作答次數
        stat = quiz_stats.get(item.id) if item.kind == "quiz" else stats.get(item.id)
        rows.append(
            {
                "id": item.id,
                "course_id": item.course_id,
                "course_title": courses.get(item.course_id, "課程"),
                "student_id": item.student_id,
                "student_name": names.get(item.student_id, "學生"),
                "teacher_name": names.get(item.teacher_id, "老師"),
                "kind": item.kind,
                "title": item.title,
                "description": item.description,
                "due_at": item.due_at,
                "has_midi": item.midi_path is not None,
                "midi_filename": item.midi_filename,
                "midi_bpm": item.midi_bpm,
                "practice_bpm": item.practice_bpm,
                "materials": materials[item.id],
                "question_count": question_counts.get(item.id, 0),
                "submission_count": stat.count if stat else 0,
                "last_submitted_at": stat.latest if stat else None,
                "created_at": item.created_at,
            }
        )
    return rows


def list_teacher_assignments(db: Session, teacher_id: uuid.UUID) -> list[dict]:
    assignments = list(
        db.scalars(select(Assignment).where(Assignment.teacher_id == teacher_id).order_by(Assignment.created_at.desc()))
    )
    return assignment_rows(db, assignments)


def list_student_assignments(db: Session, student_id: uuid.UUID) -> list[dict]:
    """只列還綁定著的課程裡的作業。"""
    bound_courses = select(CourseBinding.course_id).where(
        CourseBinding.student_id == student_id, CourseBinding.status == "bound"
    )
    assignments = list(
        db.scalars(
            select(Assignment)
            .where(Assignment.student_id == student_id, Assignment.course_id.in_(bound_courses))
            .order_by(Assignment.created_at.desc())
        )
    )
    return assignment_rows(db, assignments)


# ---------- 題庫作業：題目與作答


def quiz_questions(db: Session, assignment_id: uuid.UUID) -> list[AssignmentQuizQuestion]:
    return list(
        db.scalars(
            select(AssignmentQuizQuestion)
            .where(AssignmentQuizQuestion.assignment_id == assignment_id)
            .order_by(AssignmentQuizQuestion.position.asc())
        )
    )


def submit_quiz_attempt(
    db: Session, student_id: uuid.UUID, assignment_id: uuid.UUID, answers: dict[uuid.UUID, list[int]]
) -> QuizAttempt:
    """學生交一次作答。每一題都要作答；同一份作業可以重複練習，attempt_no 依序加一。"""
    assignment = student_assignment(db, student_id, assignment_id)
    if assignment.kind != "quiz":
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "演奏作業請用錄音繳交。")
    questions = quiz_questions(db, assignment.id)
    if not questions:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "這份作業還沒有題目。")
    known = {item.id for item in questions}
    if set(answers) - known:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "有答案對不到這份作業的題目，請重新整理頁面。")
    missing = [str(item.position) for item in questions if not answers.get(item.id)]
    if missing:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, f"第 {'、'.join(missing)} 題還沒作答。")
    for item in questions:
        chosen = answers[item.id]
        if any(not 0 <= value < len(item.options) for value in chosen):
            raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, f"第 {item.position} 題的選項不正確。")
        if item.question_type != "multiple" and len(set(chosen)) != 1:
            raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, f"第 {item.position} 題只能選一個答案。")

    previous = db.scalar(
        select(func.max(QuizAttempt.attempt_no)).where(
            QuizAttempt.assignment_id == assignment.id, QuizAttempt.student_id == student_id
        )
    )
    results = {item.id: grade(item.answers, answers[item.id]) for item in questions}
    attempt = QuizAttempt(
        id=uuid.uuid4(),
        assignment_id=assignment.id,
        student_id=student_id,
        attempt_no=(previous or 0) + 1,
        correct_count=sum(results.values()),
        question_count=len(questions),
    )
    db.add(attempt)
    db.flush()
    for item in questions:
        db.add(
            QuizAttemptAnswer(
                attempt_id=attempt.id,
                question_id=item.id,
                selected=sorted(set(answers[item.id])),
                is_correct=results[item.id],
            )
        )
    _commit(db)
    db.refresh(attempt)
    return attempt


def quiz_attempt_rows(db: Session, assignment_id: uuid.UUID) -> list[dict]:
    """一份作業的每次作答，附上答錯的題目（學生的答案、正確答案、解析）。舊的在前。"""
    attempts = list(
        db.scalars(
            select(QuizAttempt).where(QuizAttempt.assignment_id == assignment_id).order_by(QuizAttempt.attempt_no.asc())
        )
    )
    questions = {item.id: item for item in quiz_questions(db, assignment_id)}
    wrong: dict[uuid.UUID, list[dict]] = {item.id: [] for item in attempts}
    if attempts:
        for answer in db.scalars(
            select(QuizAttemptAnswer).where(
                QuizAttemptAnswer.attempt_id.in_(list(wrong)), QuizAttemptAnswer.is_correct.is_(False)
            )
        ):
            question = questions.get(answer.question_id)
            if question is not None:
                wrong[answer.attempt_id].append(
                    {
                        "question_id": question.id,
                        "position": question.position,
                        "question_type": question.question_type,
                        "topic": question.topic,
                        "question": question.question,
                        "options": question.options,
                        "selected": answer.selected,
                        "answers": question.answers,
                        "explanation": question.explanation,
                    }
                )
    return [
        {
            "id": item.id,
            "attempt_no": item.attempt_no,
            "submitted_at": item.submitted_at,
            "question_count": item.question_count,
            "wrong": sorted(wrong[item.id], key=lambda row: row["position"]),
        }
        for item in attempts
    ]
